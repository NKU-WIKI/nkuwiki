"""
微信小程序API的内部工具函数
"""
import json
import logging
from typing import Dict, Any, Optional, List

from etl.load import insert_record, get_by_id, execute_custom_query

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
        
        post_actions = actions_map.get(post['id'], set())
        post['is_liked'] = 'like' in post_actions
        post['is_favorited'] = 'favorite' in post_actions
        post['is_following_author'] = author_id in following_map
        
        # 清理掉顶层的冗余用户信息
        for key in ['nickname', 'avatar', 'bio']:
            post.pop(key, None)

    return posts

async def _update_count(table: str, field: str, record_id: Any, delta: int = 1):
    """
    安全地更新数据库中的计数字段。
    
    Args:
        table (str): 表名。
        field (str): 要更新的计数字段名。
        record_id (Any): 记录的ID。
        delta (int): 变化的数量，可以是正数或负数。
    """
    if not all([table, field, record_id]):
        logger.warning(f"更新计数的参数不完整: table={table}, field={field}, record_id={record_id}")
        return

    operator = '+' if delta > 0 else '-'
    abs_delta = abs(delta)

    # 使用参数化查询来防止SQL注入
    query = f"UPDATE `{table}` SET `{field}` = `{field}` {operator} %s WHERE `id` = %s"
    
    # 对于减少操作，可以添加一个检查以防止字段变为负数
    if delta < 0:
        query += f" AND `{field}` >= %s"
        params = [abs_delta, record_id, abs_delta]
    else:
        params = [abs_delta, record_id]

    try:
        await execute_custom_query(query, params)
        logger.debug(f"成功更新计数: {table}.{field} for record {record_id} by {delta}")
    except Exception as e:
        logger.exception(f"更新计数失败 (table={table}, record_id={record_id}): {e}")


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