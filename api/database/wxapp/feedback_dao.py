"""
反馈数据访问对象
提供反馈相关的数据库操作方法
"""
from typing import Dict, Any, List, Optional, Tuple
from loguru import logger
import json

# 状态映射常量
STATUS_MAP = {
    "pending": 0,     # 待处理 
    "processing": 1,  # 处理中
    "resolved": 2,    # 已处理
    "rejected": 3     # 已关闭
}

# 反向状态映射
STATUS_REVERSE_MAP = {
    0: "pending",
    1: "processing", 
    2: "resolved",
    3: "rejected"
}

# 直接使用数据库核心模块
from etl.load import db_core

# 反馈表名
TABLE_NAME = "wxapp_feedback"

async def create_feedback(feedback_data: Dict[str, Any]) -> int:
    """
    创建新反馈
    
    Args:
        feedback_data: 反馈数据
        
    Returns:
        int: 反馈ID
    """
    logger.debug(f"创建新反馈: {feedback_data}")
    
    # 复制反馈数据，避免修改原始数据
    processed_data = feedback_data.copy()
    
    # 将列表和字典类型转换为JSON字符串
    if "images" in processed_data and processed_data["images"] is not None:
        processed_data["images"] = json.dumps(processed_data["images"])
    
    # 状态从字符串转为整数
    if "status" in processed_data:
        if isinstance(processed_data["status"], str):
            processed_data["status"] = STATUS_MAP.get(processed_data["status"], 0)
    
    # 如果device_info是字典，转换为JSON字符串
    if "device_info" in processed_data and processed_data["device_info"] is not None:
        if isinstance(processed_data["device_info"], dict):
            processed_data["device_info"] = json.dumps(processed_data["device_info"])
    
    return await db_core.async_insert(TABLE_NAME, processed_data)

async def get_feedback_by_id(feedback_id: int) -> Optional[Dict[str, Any]]:
    """
    根据ID获取反馈
    
    Args:
        feedback_id: 反馈ID
        
    Returns:
        Optional[Dict[str, Any]]: 反馈数据，不存在则返回None
    """
    logger.debug(f"获取反馈 (ID: {feedback_id})")
    feedback = await db_core.async_get_by_id(TABLE_NAME, feedback_id)
    
    # 状态从整数转为字符串
    if feedback and "status" in feedback:
        feedback["status"] = STATUS_REVERSE_MAP.get(feedback["status"], "pending")
    
    return feedback

async def get_user_feedback(
    openid: str,
    feedback_type: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 20,
    offset: int = 0
) -> Tuple[List[Dict[str, Any]], int]:
    """
    获取用户的反馈列表
    
    Args:
        openid: 用户openid
        feedback_type: 反馈类型(bug/suggestion/other)
        status: 反馈状态(pending/processing/resolved/rejected)
        limit: 返回数量限制
        offset: 起始偏移量
        
    Returns:
        Tuple[List[Dict[str, Any]], int]: (反馈列表, 总数)
    """
    logger.debug(f"获取用户反馈列表: openid={openid}, type={feedback_type}, status={status}")
    
    # 构建查询条件
    conditions = {
        "openid": openid,
        "is_deleted": 0
    }
    
    if feedback_type:
        conditions["type"] = feedback_type
    
    if status:
        # 状态从字符串转为整数
        conditions["status"] = STATUS_MAP.get(status, 0)
    
    # 查询反馈列表
    feedback_list = await db_core.async_query_records(
        TABLE_NAME,
        conditions=conditions,
        order_by="create_time DESC",
        limit=limit,
        offset=offset
    )
    
    # 获取总数
    total = await db_core.count_records(TABLE_NAME, conditions=conditions)
    
    # 转换状态从整数为字符串
    for feedback in feedback_list:
        if "status" in feedback:
            feedback["status"] = STATUS_REVERSE_MAP.get(feedback["status"], "pending")
    
    return feedback_list, total

async def update_feedback(feedback_id: int, update_data: Dict[str, Any]) -> bool:
    """
    更新反馈
    
    Args:
        feedback_id: 反馈ID
        update_data: 更新数据
        
    Returns:
        bool: 更新是否成功
    """
    logger.debug(f"更新反馈 (ID: {feedback_id}): {update_data}")
    
    # 复制更新数据，避免修改原始数据
    processed_data = update_data.copy()
    
    # 状态从字符串转为整数
    if "status" in processed_data and isinstance(processed_data["status"], str):
        processed_data["status"] = STATUS_MAP.get(processed_data["status"], 0)
    
    return await db_core.async_update(TABLE_NAME, feedback_id, processed_data)

async def mark_feedback_deleted(feedback_id: int) -> bool:
    """
    标记反馈为已删除
    
    Args:
        feedback_id: 反馈ID
        
    Returns:
        bool: 操作是否成功
    """
    logger.debug(f"标记反馈删除 (ID: {feedback_id})")
    return await db_core.async_update(TABLE_NAME, feedback_id, {"is_deleted": 1}) 