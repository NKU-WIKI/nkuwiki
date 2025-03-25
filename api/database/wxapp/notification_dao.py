"""
通知数据访问对象
提供通知相关的数据库操作方法
"""
from typing import Dict, Any, List, Optional, Tuple
from loguru import logger

# 直接从etl模块导入方法
from etl.load.py_mysql import (
    insert_record,
    update_record,
    delete_record,
    query_records,
    count_records,
    get_record_by_id,
    execute_raw_query,
    execute_custom_query
)

# 通知表名
TABLE_NAME = "wxapp_notifications"

async def create_notification(notification_data: Dict[str, Any]) -> int:
    """
    创建新通知
    
    Args:
        notification_data: 通知数据
        
    Returns:
        int: 通知ID
    """
    logger.debug(f"创建新通知: {notification_data}")
    return insert_record(TABLE_NAME, notification_data)

async def get_notification_by_id(notification_id: int) -> Optional[Dict[str, Any]]:
    """
    根据ID获取通知
    
    Args:
        notification_id: 通知ID
        
    Returns:
        Optional[Dict[str, Any]]: 通知数据，不存在则返回None
    """
    logger.debug(f"获取通知 (ID: {notification_id})")
    return get_record_by_id(TABLE_NAME, notification_id)

async def get_user_notifications(
    openid: str,
    notification_type: Optional[str] = None,
    is_read: Optional[bool] = None,
    limit: int = 20,
    offset: int = 0
) -> Tuple[List[Dict[str, Any]], int, int]:
    """
    获取用户的通知列表
    
    Args:
        openid: 用户openid
        notification_type: 通知类型(system/like/comment/follow)
        is_read: 是否已读
        limit: 返回数量限制
        offset: 起始偏移量
        
    Returns:
        Tuple[List[Dict[str, Any]], int, int]: (通知列表, 总数, 未读数)
    """
    logger.debug(f"获取用户通知列表: openid={openid}, type={notification_type}, is_read={is_read}")
    
    # 构建查询条件
    conditions = {
        "openid": openid,
        "is_deleted": 0
    }
    
    if notification_type:
        conditions["type"] = notification_type
    
    if is_read is not None:
        conditions["is_read"] = 1 if is_read else 0
    
    # 查询通知列表
    notifications = query_records(
        TABLE_NAME,
        conditions=conditions,
        order_by="create_time DESC",
        limit=limit,
        offset=offset
    )
    
    # 获取总数
    total = count_records(TABLE_NAME, conditions=conditions)
    
    # 获取未读数量
    unread_conditions = {
        "openid": openid,
        "is_deleted": 0,
        "is_read": 0
    }
    
    if notification_type:
        unread_conditions["type"] = notification_type
        
    unread_count = count_records(TABLE_NAME, conditions=unread_conditions)
    
    # 如果有发送者信息，获取发送者详情
    if notifications:
        from api.database.wxapp import user_dao
        for notification in notifications:
            if notification.get("sender_openid"):
                sender = user_dao.get_user_by_openid(notification["sender_openid"])
                if sender:
                    notification["sender"] = {
                        "id": sender.get("id"),
                        "openid": sender.get("openid"),
                        "nick_name": sender.get("nick_name"),
                        "avatar": sender.get("avatar")
                    }
    
    return notifications, total, unread_count

async def mark_notification_read(notification_id: int) -> bool:
    """
    标记通知为已读
    
    Args:
        notification_id: 通知ID
        
    Returns:
        bool: 操作是否成功
    """
    logger.debug(f"标记通知已读 (ID: {notification_id})")
    return update_record(TABLE_NAME, notification_id, {"is_read": 1})

async def mark_notifications_read(openid: str, notification_ids: Optional[List[int]] = None) -> int:
    """
    批量标记通知为已读
    
    Args:
        openid: 用户openid
        notification_ids: 通知ID列表，为None时标记所有通知
        
    Returns:
        int: 标记的通知数量
    """
    logger.debug(f"批量标记通知已读: openid={openid}, ids={notification_ids}")
    
    # 构建更新条件
    conditions = ["openid = %s", "is_deleted = 0", "is_read = 0"]
    params = [openid]
    
    if notification_ids:
        id_list = ",".join([str(id) for id in notification_ids])
        conditions.append(f"id IN ({id_list})")
    
    where_clause = " AND ".join(conditions)
    
    # 更新通知状态
    sql = f"UPDATE {TABLE_NAME} SET is_read = 1 WHERE {where_clause}"
    execute_raw_query(sql, params)
    
    # 返回更新的数量
    if notification_ids:
        return len(notification_ids) 
    else:
        # 使用conditions字典而不是condition字符串
        return count_records(
            TABLE_NAME,
            conditions={"openid": openid, "is_deleted": 0, "is_read": 1}
        )

async def mark_notification_deleted(notification_id: int) -> bool:
    """
    标记通知为已删除
    
    Args:
        notification_id: 通知ID
        
    Returns:
        bool: 操作是否成功
    """
    logger.debug(f"标记通知删除 (ID: {notification_id})")
    return update_record(TABLE_NAME, notification_id, {"is_deleted": 1})

async def get_unread_notification_count(openid: str, notification_type: Optional[str] = None) -> int:
    """
    获取用户未读通知数量
    
    Args:
        openid: 用户openid
        notification_type: 通知类型，可选
        
    Returns:
        int: 未读通知数量
    """
    logger.debug(f"获取未读通知数量 (openid: {openid[:8]}...)")
    
    # 构建查询条件
    conditions = {
        "openid": openid,
        "is_deleted": 0,
        "is_read": 0
    }
    
    if notification_type:
        conditions["type"] = notification_type
    
    # 计算未读通知数量
    return count_records(TABLE_NAME, conditions=conditions) 