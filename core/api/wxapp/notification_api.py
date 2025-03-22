"""
微信小程序消息通知API
提供消息通知相关的API接口
"""
from datetime import datetime
from fastapi import HTTPException, Path as PathParam, Depends, Query, Body
from pydantic import BaseModel, Field, validator
from typing import Dict, Any, Optional, List

# 导入通用组件
from core.api.common import get_api_logger, handle_api_errors, create_standard_response
from core.api import wxapp_router as router
from core.api.wxapp.common_utils import format_datetime, prepare_db_data, process_json_fields

# 导入数据库操作函数
from etl.load.py_mysql import (
    insert_record, update_record, delete_record, 
    query_records, count_records, get_record_by_id
)

# 通知基础模型
class NotificationBase(BaseModel):
    """通知基础信息"""
    user_id: str = Field(..., description="接收者用户ID")
    title: str = Field(..., description="通知标题")
    content: str = Field(..., description="通知内容")
    type: str = Field(..., description="通知类型: system-系统通知, like-点赞, comment-评论, follow-关注")
    is_read: bool = Field(False, description="是否已读")
    sender_id: Optional[str] = Field(None, description="发送者ID，如系统通知则为null")
    related_id: Optional[str] = Field(None, description="关联ID，比如帖子ID或评论ID")
    
    @validator('type')
    def validate_type(cls, v):
        valid_types = ['system', 'like', 'comment', 'follow']
        if v not in valid_types:
            raise ValueError(f"通知类型必须是以下之一: {', '.join(valid_types)}")
        return v

class NotificationCreate(NotificationBase):
    """创建通知请求"""
    pass

class NotificationUpdate(BaseModel):
    """更新通知请求"""
    title: Optional[str] = None
    content: Optional[str] = None
    is_read: Optional[bool] = None

class NotificationResponse(NotificationBase):
    """通知响应"""
    id: int
    create_time: datetime
    update_time: Optional[datetime] = None

# API端点
@router.post("/notifications", response_model=Dict[str, Any], summary="创建通知")
@handle_api_errors("创建通知")
async def create_notification(
    notification: NotificationCreate,
    api_logger=Depends(get_api_logger)
):
    """创建新通知"""
    # 准备数据
    notification_data = prepare_db_data(notification.dict(), is_create=True)
    
    # 插入记录
    api_logger.debug(f"创建通知: {notification_data}")
    notification_id = insert_record('wxapp_notifications', notification_data)
    if not notification_id:
        raise HTTPException(status_code=500, detail="创建通知失败")
    
    # 获取创建的通知
    created_notification = get_record_by_id('wxapp_notifications', notification_id)
    if not created_notification:
        raise HTTPException(status_code=404, detail="找不到创建的通知")
    
    return create_standard_response(created_notification)

@router.get("/notifications/{notification_id}", response_model=Dict[str, Any], summary="获取通知详情")
@handle_api_errors("获取通知")
async def get_notification(
    notification_id: int = PathParam(..., description="通知ID"),
    api_logger=Depends(get_api_logger)
):
    """获取指定通知详情"""
    notification = get_record_by_id('wxapp_notifications', notification_id)
    if not notification:
        raise HTTPException(status_code=404, detail="通知不存在")
    
    # 处理日期格式
    if 'create_time' in notification:
        notification['create_time'] = str(notification['create_time'])
    if 'update_time' in notification:
        notification['update_time'] = str(notification['update_time'])
    
    return create_standard_response(notification)

@router.get("/users/{user_id}/notifications", response_model=Dict[str, Any], summary="获取用户通知列表")
@handle_api_errors("获取用户通知列表")
async def list_user_notifications(
    user_id: str = PathParam(..., description="用户ID"),
    type: Optional[str] = Query(None, description="通知类型: system-系统通知, like-点赞, comment-评论, follow-关注"),
    is_read: Optional[bool] = Query(None, description="是否已读: true-已读, false-未读"),
    limit: int = Query(20, description="返回记录数量限制", ge=1, le=100),
    offset: int = Query(0, description="分页偏移量", ge=0),
    api_logger=Depends(get_api_logger)
):
    """获取用户通知列表"""
    api_logger.debug(f"获取用户ID={user_id}的通知列表, 类型={type}, 已读状态={is_read}")
    
    # 构建查询条件
    conditions = {"user_id": user_id}
    if type:
        conditions["type"] = type
    if is_read is not None:
        conditions["is_read"] = 1 if is_read else 0
    
    # 查询通知
    try:
        notifications = query_records(
            'wxapp_notifications',
            conditions=conditions,
            order_by='create_time DESC',
            limit=limit,
            offset=offset
        )
        
        # 查询未读通知数量
        unread_conditions = {"user_id": user_id, "is_read": 0}
        unread_count = count_records('wxapp_notifications', unread_conditions)
        
        # 查询总通知数量
        total_conditions = {"user_id": user_id}
        total_count = count_records('wxapp_notifications', total_conditions)
        
        # 处理通知数据
        for notification in notifications:
            # 处理日期格式
            if 'create_time' in notification:
                notification['create_time'] = str(notification['create_time'])
            if 'update_time' in notification:
                notification['update_time'] = str(notification['update_time'])
            
            # 处理发送者信息
            if notification.get('sender_id'):
                sender = get_record_by_id('wxapp_users', notification['sender_id'])
                if sender:
                    notification['sender'] = {
                        'id': sender['id'],
                        'nickname': sender.get('nickname', ''),
                        'avatar_url': sender.get('avatar_url', '')
                    }
        
        return create_standard_response(
            code=200,
            message="获取通知列表成功",
            data={
                "notifications": notifications,
                "unread_count": unread_count,
                "total": total_count
            }
        )
    except Exception as e:
        api_logger.error(f"获取通知列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取通知列表失败: {str(e)}")

@router.put("/notifications/{notification_id}", response_model=Dict[str, Any], summary="更新通知")
@handle_api_errors("更新通知")
async def update_notification(
    notification_update: NotificationUpdate,
    notification_id: int = PathParam(..., description="通知ID"),
    api_logger=Depends(get_api_logger)
):
    """更新通知信息，主要用于标记已读"""
    # 检查通知是否存在
    notification = get_record_by_id('wxapp_notifications', notification_id)
    if not notification:
        raise HTTPException(status_code=404, detail="通知不存在")
    
    # 过滤掉None值
    update_data = {k: v for k, v in notification_update.dict().items() if v is not None}
    if not update_data:
        return create_standard_response(notification)
    
    # 添加更新时间
    update_data['update_time'] = format_datetime(datetime.now())
    
    # 更新记录
    api_logger.debug(f"更新通知ID={notification_id}: {update_data}")
    success = update_record('wxapp_notifications', notification_id, update_data)
    if not success:
        raise HTTPException(status_code=500, detail="更新通知失败")
    
    # 获取更新后的通知
    updated_notification = get_record_by_id('wxapp_notifications', notification_id)
    
    # 处理日期格式
    if 'create_time' in updated_notification:
        updated_notification['create_time'] = str(updated_notification['create_time'])
    if 'update_time' in updated_notification:
        updated_notification['update_time'] = str(updated_notification['update_time'])
    
    return create_standard_response(updated_notification)

@router.put("/users/{user_id}/notifications/read-all", response_model=Dict[str, Any], summary="标记所有通知为已读")
@handle_api_errors("标记所有通知为已读")
async def mark_all_notifications_read(
    user_id: str = PathParam(..., description="用户ID"),
    type: Optional[str] = Query(None, description="通知类型，如果指定则只标记特定类型的通知"),
    api_logger=Depends(get_api_logger)
):
    """标记用户所有未读通知为已读"""
    api_logger.debug(f"标记用户ID={user_id}的所有通知为已读, 类型={type}")
    
    try:
        # 构建查询条件
        conditions = {"user_id": user_id, "is_read": 0}
        if type:
            conditions["type"] = type
        
        # 查询符合条件的未读通知
        notifications = query_records('wxapp_notifications', conditions)
        
        # 批量更新通知状态
        update_count = 0
        for notification in notifications:
            update_data = {
                "is_read": 1,
                "update_time": format_datetime(datetime.now())
            }
            success = update_record('wxapp_notifications', notification['id'], update_data)
            if success:
                update_count += 1
        
        return create_standard_response(
            code=200,
            message="标记通知为已读成功",
            data={"updated_count": update_count}
        )
    except Exception as e:
        api_logger.error(f"标记通知为已读失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"标记通知为已读失败: {str(e)}")

@router.delete("/notifications/{notification_id}", response_model=Dict[str, Any], summary="删除通知")
@handle_api_errors("删除通知")
async def delete_notification(
    notification_id: int = PathParam(..., description="通知ID"),
    api_logger=Depends(get_api_logger)
):
    """删除指定通知"""
    # 检查通知是否存在
    notification = get_record_by_id('wxapp_notifications', notification_id)
    if not notification:
        raise HTTPException(status_code=404, detail="通知不存在")
    
    # 删除通知
    api_logger.debug(f"删除通知ID={notification_id}")
    success = delete_record('wxapp_notifications', notification_id)
    if not success:
        raise HTTPException(status_code=500, detail="删除通知失败")
    
    return create_standard_response(
        code=200,
        message="删除通知成功",
        data={"id": notification_id}
    ) 