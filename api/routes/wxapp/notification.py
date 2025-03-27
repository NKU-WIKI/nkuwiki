"""
通知相关API接口
处理通知的查询、标记已读和删除等功能
"""
from typing import Dict, Any, Optional, List
from fastapi import Depends, HTTPException, Query, Path

from api import wxapp_router
from api.common import handle_api_errors, get_api_logger_dep
from api.models.common import SimpleOperationResponse
from api.models.wxapp.notification import (
    NotificationModel, 
    NotificationReadRequest, 
    NotificationQueryParams,
    BatchOperationResponse,
    NotificationListResponse
)

@wxapp_router.get("/users/{openid}/notifications", response_model=NotificationListResponse)
@handle_api_errors("获取用户通知列表")
async def get_user_notifications(
    openid: str = Path(..., description="用户openid"),
    type: Optional[str] = Query(None, description="通知类型：system-系统通知, like-点赞, comment-评论, follow-关注"),
    is_read: Optional[bool] = Query(None, description="是否已读：true-已读, false-未读"),
    limit: int = Query(20, description="返回记录数量限制", ge=1, le=100),
    offset: int = Query(0, description="分页偏移量", ge=0),
    api_logger=Depends(get_api_logger_dep)
):
    """
    获取用户的通知列表
    
    支持按类型和已读状态筛选，分页获取
    """
    from api.database.wxapp import notification_dao
    
    api_logger.debug(f"获取用户通知列表 (用户: {openid[:8]}..., 类型: {type}, 已读: {is_read})")
    
    # 获取通知列表
    notifications, total, unread = await notification_dao.get_user_notifications(
        openid=openid,
        notification_type=type,
        is_read=is_read,
        limit=limit,
        offset=offset
    )
    
    # 处理datetime类型字段
    for notification in notifications:
        if "create_time" in notification and notification["create_time"]:
            notification["create_time"] = notification["create_time"].strftime("%Y-%m-%d %H:%M:%S")
        if "update_time" in notification and notification["update_time"]:
            notification["update_time"] = notification["update_time"].strftime("%Y-%m-%d %H:%M:%S")
    
    return {
        "notifications": notifications,
        "total": total,
        "unread": unread,
        "limit": limit,
        "offset": offset
    }

@wxapp_router.get("/notifications/{notification_id}", response_model=NotificationModel)
@handle_api_errors("获取通知详情")
async def get_notification_detail(
    notification_id: int = Path(..., description="通知ID"),
    api_logger=Depends(get_api_logger_dep)
):
    """
    获取通知详情
    
    根据ID获取通知的详细信息
    """
    from api.database.wxapp import notification_dao
    
    api_logger.debug(f"获取通知详情 (ID: {notification_id})")
    
    # 获取通知信息
    notification = await notification_dao.get_notification_by_id(notification_id)
    
    if not notification:
        raise HTTPException(status_code=404, detail="通知不存在")
    
    # 处理datetime类型字段
    if "create_time" in notification and notification["create_time"]:
        notification["create_time"] = notification["create_time"].strftime("%Y-%m-%d %H:%M:%S")
    if "update_time" in notification and notification["update_time"]:
        notification["update_time"] = notification["update_time"].strftime("%Y-%m-%d %H:%M:%S")
    
    return notification

@wxapp_router.put("/notifications/{notification_id}", response_model=NotificationModel)
@handle_api_errors("标记通知已读")
async def mark_notification_read(
    notification_id: int = Path(..., description="通知ID"),
    api_logger=Depends(get_api_logger_dep)
):
    """
    标记单个通知为已读
    """
    from api.database.wxapp import notification_dao
    
    api_logger.debug(f"标记通知已读 (ID: {notification_id})")
    
    # 检查通知是否存在
    notification = await notification_dao.get_notification_by_id(notification_id)
    
    if not notification:
        raise HTTPException(status_code=404, detail="通知不存在")
    
    # 标记已读
    await notification_dao.mark_notification_read(notification_id)
    
    # 获取更新后的通知
    updated_notification = await notification_dao.get_notification_by_id(notification_id)
    
    # 处理datetime类型字段
    if "create_time" in updated_notification and updated_notification["create_time"]:
        updated_notification["create_time"] = updated_notification["create_time"].strftime("%Y-%m-%d %H:%M:%S")
    if "update_time" in updated_notification and updated_notification["update_time"]:
        updated_notification["update_time"] = updated_notification["update_time"].strftime("%Y-%m-%d %H:%M:%S")
    
    return updated_notification

@wxapp_router.put("/users/{openid}/notifications/read", response_model=BatchOperationResponse)
@handle_api_errors("批量标记通知已读")
async def mark_notifications_read(
    request: NotificationReadRequest,
    openid: str = Path(..., description="用户openid"),
    api_logger=Depends(get_api_logger_dep)
):
    """
    批量标记通知为已读
    
    可以指定通知ID列表，或标记所有通知为已读
    """
    from api.database.wxapp import notification_dao
    
    api_logger.debug(f"批量标记通知已读 (用户: {openid[:8]}..., IDs: {request.notification_ids})")
    
    # 标记已读
    count = await notification_dao.mark_notifications_read(openid, request.notification_ids)
    
    return BatchOperationResponse(
        success=True,
        message=f"已将{count}条通知标记为已读",
        count=count
    )

@wxapp_router.delete("/notifications/{notification_id}", response_model=SimpleOperationResponse)
@handle_api_errors("删除通知")
async def delete_notification(
    notification_id: int = Path(..., description="通知ID"),
    api_logger=Depends(get_api_logger_dep)
):
    """
    删除通知
    
    标记删除指定通知
    """
    from api.database.wxapp import notification_dao
    
    api_logger.debug(f"删除通知 (ID: {notification_id})")
    
    # 检查通知是否存在
    notification = await notification_dao.get_notification_by_id(notification_id)
    
    if not notification:
        raise HTTPException(status_code=404, detail="通知不存在")
    
    # 标记删除
    await notification_dao.mark_notification_deleted(notification_id)
    
    return SimpleOperationResponse(
        success=True,
        message="通知已删除",
        affected_items=1
    )

@wxapp_router.get("/users/{openid}/notifications/count")
@handle_api_errors("获取未读通知数量")
async def get_unread_notifications_count(
    openid: str = Path(..., description="用户openid"),
    type: Optional[str] = Query(None, description="通知类型：system-系统通知, like-点赞, comment-评论, follow-关注"),
    api_logger=Depends(get_api_logger_dep)
):
    """
    获取用户未读通知数量
    
    返回用户的未读通知数量，可按类型筛选
    """
    from api.database.wxapp import notification_dao
    
    api_logger.debug(f"获取未读通知数量 (用户: {openid[:8]}..., 类型: {type})")
    
    # 获取未读通知数量
    count = await notification_dao.get_unread_notification_count(
        openid=openid,
        notification_type=type
    )
    
    return {
        "unread_count": count,
        "openid": openid,
        "type": type
    } 