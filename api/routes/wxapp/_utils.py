"""
微信小程序API的内部工具函数
"""
import json
import logging
from typing import Dict, Any, Optional, List

from etl.load import insert_record, get_by_id, execute_custom_query

logger = logging.getLogger("wxapp.utils")

async def batch_enrich_posts_with_user_info(posts: List[Dict[str, Any]], current_user_openid: Optional[str]) -> List[Dict[str, Any]]:
    if not posts:
        return []

    post_ids = [post['id'] for post in posts]
    author_openids = list(set(post.get('openid') for post in posts if post.get('openid')))

    user_info_map = {}
    actions_map = {}
    following_map = {}

    # 1. 批量获取作者信息
    if author_openids:
        placeholders = ', '.join(['%s'] * len(author_openids))
        user_query = f"SELECT openid, nickname, avatar, bio FROM wxapp_user WHERE openid IN ({placeholders})"
        user_results = await execute_custom_query(user_query, author_openids, fetch='all')
        user_info_map = {user['openid']: user for user in user_results}

    # 2. 批量获取当前用户的互动状态 (点赞、收藏)
    if current_user_openid:
        placeholders_posts = ', '.join(['%s'] * len(post_ids))
        action_query = f"""
            SELECT target_id, action_type 
            FROM wxapp_action 
            WHERE openid = %s AND target_type = 'post' AND target_id IN ({placeholders_posts})
        """
        action_results = await execute_custom_query(action_query, [current_user_openid] + post_ids, fetch='all')
        for action in action_results:
            if action['target_id'] not in actions_map:
                actions_map[action['target_id']] = set()
            actions_map[action['target_id']].add(action['action_type'])
        
        # 3. 批量检查是否关注了作者
        if author_openids:
            placeholders_authors = ', '.join(['%s'] * len(author_openids))
            follow_query = f"""
                SELECT target_id 
                FROM wxapp_action 
                WHERE openid = %s AND target_type = 'user' AND action_type = 'follow' AND target_id IN ({placeholders_authors})
            """
            follow_results = await execute_custom_query(follow_query, [current_user_openid] + author_openids, fetch='all')
            following_map = {result['target_id'] for result in follow_results}


    # 4. 组装最终结果
    for post in posts:
        author_openid = post.get('openid')
        post['user_info'] = user_info_map.get(author_openid, {})
        
        post_actions = actions_map.get(post['id'], set())
        post['is_liked'] = 'like' in post_actions
        post['is_favorited'] = 'favorite' in post_actions
        post['is_following_author'] = author_openid in following_map
            
    return posts

async def _update_count(cursor, table: str, field: str, record_id: Any, amount: int = 1, id_column: str = 'id'):
    """
    通用计数更新函数。
    """
    operator = '+' if amount > 0 else '-'
    abs_amount = abs(amount)
    
    where_clause = ""
    if amount < 0:
        where_clause = f" AND {field} >= {abs_amount}"

    query = f"UPDATE {table} SET {field} = {field} {operator} {abs_amount} WHERE {id_column} = %s{where_clause}"
    await cursor.execute(query, [record_id])


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