"""
微信小程序API的内部工具函数
"""
import json
import logging
from typing import Dict, Any, Optional, List

from etl.load import insert_record, execute_custom_query

logger = logging.getLogger("wxapp.utils")

async def batch_enrich_posts_with_user_info(posts: List[Dict[str, Any]], current_user_id: Optional[int]) -> List[Dict[str, Any]]:
    if not posts:
        return []

    post_ids = [post['id'] for post in posts]
    author_ids = list(set(post.get('user_id') for post in posts if post.get('user_id')))

    author_info_map = {}
    actions_map = {}
    following_map = {}

    # 1. 批量获取作者信息
    if author_ids:
        placeholders = ', '.join(['%s'] * len(author_ids))
        user_query = f"SELECT id, nickname, avatar, bio, level FROM wxapp_user WHERE id IN ({placeholders})"
        user_results = await execute_custom_query(user_query, author_ids, fetch='all')
        author_info_map = {user['id']: user for user in user_results}

    # 2. 批量获取当前用户的互动状态 (点赞、收藏)
    if current_user_id:
        placeholders_posts = ', '.join(['%s'] * len(post_ids))
        action_query = f"""
            SELECT target_id, action_type 
            FROM wxapp_action 
            WHERE user_id = %s AND target_type = 'post' AND target_id IN ({placeholders_posts})
        """
        action_results = await execute_custom_query(action_query, [current_user_id] + post_ids, fetch='all')
        for action in action_results:
            if action['target_id'] not in actions_map:
                actions_map[action['target_id']] = set()
            actions_map[action['target_id']].add(action['action_type'])
        
        # 3. 批量检查是否关注了作者
        if author_ids:
            placeholders_authors = ', '.join(['%s'] * len(author_ids))
            follow_query = f"""
                SELECT target_id 
                FROM wxapp_action 
                WHERE user_id = %s AND target_type = 'user' AND action_type = 'follow' AND target_id IN ({placeholders_authors})
            """
            follow_results = await execute_custom_query(follow_query, [current_user_id] + author_ids, fetch='all')
            following_map = {result['target_id'] for result in follow_results}


    # 4. 组装最终结果
    for post in posts:
        author_id = post.get('user_id')
        post['author_info'] = author_info_map.get(author_id, {})
        
        if current_user_id:
            post_actions = actions_map.get(post['id'], set())
            post['is_liked'] = 'like' in post_actions
            post['is_favorited'] = 'favorite' in post_actions
            post['is_following_author'] = author_id in following_map
        else:
            post['is_liked'] = False
            post['is_favorited'] = False
            post['is_following_author'] = False
        
        # 清理掉顶层的冗余用户信息
        for key in ['nickname', 'avatar', 'bio']:
            post.pop(key, None)

    return posts

async def _update_count(table: str, record_id: Any, field: str, delta: int = 1, *, cursor: Optional[Any] = None) -> Optional[int]:
    """
    安全地更新数据库中的计数字段，并返回更新后的值。
    如果提供了 cursor，则在该事务内执行，否则创建新事务。

    Args:
        table (str): 表名。
        record_id (Any): 记录的ID。
        field (str): 要更新的计数字段名。
        delta (int): 变化的数量，可以是正数或负数。
        cursor (Optional[Any]): 可选的数据库游标，用于在现有事务中执行。

    Returns:
        Optional[int]: 更新后的计数值，如果操作失败则返回None。
    """
    if not all([table, field, record_id]):
        logger.warning(f"更新计数的参数不完整: table={table}, field={field}, record_id={record_id}")
        return None

    # 使用 GREATEST(0, ...) 来防止计数值变为负数
    update_query = f'UPDATE {table} SET {field} = GREATEST(0, IFNULL({field}, 0) + %s) WHERE id = %s'
    params = [delta, record_id]
    select_query = f'SELECT {field} FROM {table} WHERE id = %s'

    try:
        result = None
        if cursor:
            # 使用传入的游标，不管理事务
            await cursor.execute(update_query, params)
            await cursor.execute(select_query, [record_id])
            result = await cursor.fetchone()
        else:
            # 创建新的连接和事务
            from etl.load.db_pool_manager import get_db_connection
            import aiomysql
            async with get_db_connection() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cur:
                    await conn.begin()
                    try:
                        await cur.execute(update_query, params)
                        await cur.execute(select_query, [record_id])
                        result = await cur.fetchone()
                        await conn.commit()
                    except Exception as inner_exc:
                        await conn.rollback()
                        logger.error(f"在事务中更新计数失败: {inner_exc}")
                        raise

        if result:
            # 处理不同类型的cursor返回结果
            if isinstance(result, dict):
                new_count = result[field]
            else:
                # 如果是元组，需要通过索引访问（这种情况下需要知道字段在SELECT中的位置）
                new_count = result[0]  # 因为我们只SELECT了一个字段
            logger.debug(f"成功更新计数: {table}.{field} for record {record_id} to {new_count}")
            return new_count
        else:
            logger.warning(f"更新计数后未能查询到记录: {table}, id={record_id}")
            return None

    except Exception as e:
        logger.exception(f"更新计数时发生数据库错误 (table={table}, record_id={record_id}): {e}")
        return None


async def create_notification(openid: str, title: str, content: str, target_id: Any, target_type: str, sender_payload: Dict, notification_type: str = "comment"):
    """创建并插入一条通知"""
    notification_data = {
        "openid": openid,
        "title": title,
        "content": content,
        "type": notification_type,
        "is_read": 0,
        "sender": json.dumps(sender_payload),
        "target_id": target_id,
        "target_type": target_type,
        "status": 1,
    }
    try:
        await insert_record("wxapp_notification", notification_data)
        logger.debug(f"通知创建成功: openid={openid}, target_id={target_id}, target_type={target_type}")
    except Exception as e:
        logger.exception(f"数据库插入通知失败: {e}")