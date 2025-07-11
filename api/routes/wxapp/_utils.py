"""
微信小程序API的内部工具函数
"""
import json
import logging
from typing import Dict, Any, Optional

from etl.load import insert_record, get_by_id

logger = logging.getLogger("wxapp.utils")

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