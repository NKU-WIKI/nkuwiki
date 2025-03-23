"""
微信小程序消息通知API
提供消息通知相关的API接口
"""
from datetime import datetime
from fastapi import HTTPException, Path as PathParam, Depends, Query, Body
from pydantic import BaseModel, Field, validator
from typing import Dict, Any, Optional, List
import json

# 导入通用组件
from api.common import get_api_logger, handle_api_errors, create_standard_response
from api import wxapp_router as router
from api.wxapp.common_utils import format_datetime, prepare_db_data, process_json_fields

# 导入数据库操作函数
from etl.load.py_mysql import (
    insert_record, update_record, delete_record, 
    query_records, count_records, get_record_by_id
)

# 通知基础模型
class NotificationBase(BaseModel):
    """通知基础信息"""
    openid: str = Field(..., description="接收者用户openid")
    title: str = Field(..., description="通知标题")
    content: str = Field(..., description="通知内容")
    type: str = Field(..., description="通知类型: system-系统通知, like-点赞, comment-评论, follow-关注")
    is_read: int = Field(0, description="是否已读: 1-已读, 0-未读")
    sender_openid: Optional[str] = Field(None, description="发送者openid，如系统通知则为null")
    related_id: Optional[str] = Field(None, description="关联ID，比如帖子ID或评论ID")
    related_type: Optional[str] = Field(None, description="关联类型，如post, comment等")
    
    @validator('type')
    def validate_type(cls, v):
        valid_types = ['system', 'like', 'comment', 'follow']
        if v not in valid_types:
            raise ValueError(f"通知类型必须是以下之一: {', '.join(valid_types)}")
        return v
    
    @validator('is_read')
    def validate_is_read(cls, v):
        if v not in [0, 1]:
            raise ValueError("is_read字段必须是0或1")
        return v

class NotificationCreate(NotificationBase):
    """创建通知请求"""
    pass

class NotificationUpdate(BaseModel):
    """更新通知请求"""
    title: Optional[str] = None
    content: Optional[str] = None
    is_read: Optional[int] = None
    extra: Optional[Dict[str, Any]] = None

class NotificationResponse(NotificationBase):
    """通知响应"""
    id: int
    create_time: datetime
    update_time: datetime
    platform: str = "wxapp"
    is_deleted: int = 0
    extra: Optional[Dict[str, Any]] = None

# API端点
@router.post("/notifications", response_model=Dict[str, Any], summary="创建通知")
@handle_api_errors("创建通知")
async def create_notification(
    notification: NotificationCreate,
    api_logger=Depends(get_api_logger)
):
    """创建新通知"""
    # 准备数据
    notification_data = notification.dict()
    
    # 添加默认值
    notification_data['platform'] = 'wxapp'
    notification_data['is_deleted'] = 0
    notification_data['extra'] = json.dumps({})
    
    notification_data = prepare_db_data(notification_data, is_create=True)
    
    # 插入记录
    api_logger.debug(f"创建通知: {notification_data}")
    notification_id = insert_record('wxapp_notifications', notification_data)
    if not notification_id:
        raise HTTPException(status_code=500, detail="创建通知失败")
    
    # 获取创建的通知
    created_notification = get_record_by_id('wxapp_notifications', notification_id)
    if not created_notification:
        raise HTTPException(status_code=404, detail="找不到创建的通知")
    
    # 处理JSON字段
    created_notification = process_json_fields(created_notification)
    
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
    
    # 处理JSON字段
    notification = process_json_fields(notification)
    
    return create_standard_response(notification)

@router.get("/users/{openid}/notifications", response_model=Dict[str, Any], summary="获取用户通知列表")
@handle_api_errors("获取用户通知列表")
async def list_user_notifications(
    openid: str = PathParam(..., description="用户openid"),
    type: Optional[str] = Query(None, description="通知类型: system-系统通知, like-点赞, comment-评论, follow-关注"),
    is_read: Optional[bool] = Query(None, description="是否已读: true-已读, false-未读"),
    limit: int = Query(20, description="返回记录数量限制", ge=1, le=100),
    offset: int = Query(0, description="分页偏移量", ge=0),
    api_logger=Depends(get_api_logger)
):
    """获取用户通知列表"""
    api_logger.debug(f"获取用户openid={openid}的通知列表, 类型={type}, 已读状态={is_read}")
    
    # 构建查询条件
    conditions = {"openid": openid, "is_deleted": 0}
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
        unread_conditions = {"openid": openid, "is_read": 0, "is_deleted": 0}
        unread_count = count_records('wxapp_notifications', unread_conditions)
        
        # 查询总通知数量
        total_conditions = {"openid": openid, "is_deleted": 0}
        total_count = count_records('wxapp_notifications', total_conditions)
        
        # 处理通知数据
        for notification in notifications:
            # 处理JSON字段
            notification = process_json_fields(notification)
            
            # 如果有发送者ID，尝试获取发送者信息
            if notification.get('sender_openid'):
                try:
                    sender = query_records(
                        'wxapp_users',
                        conditions={"openid": notification['sender_openid']}
                    )
                    if sender and len(sender) > 0:
                        notification['sender'] = {
                            "openid": sender[0]['openid'],
                            "nick_name": sender[0]['nick_name'],
                            "avatar": sender[0]['avatar']
                        }
                except Exception as e:
                    api_logger.error(f"获取通知发送者信息失败: {str(e)}")
        
        # 返回通知列表
        return create_standard_response({
            "notifications": notifications,
            "unread_count": unread_count,
            "total": total_count,
            "limit": limit,
            "offset": offset
        })
    except Exception as e:
        api_logger.error(f"获取用户通知列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取用户通知列表失败: {str(e)}")

@router.put("/notifications/{notification_id}", response_model=Dict[str, Any], summary="更新通知")
@handle_api_errors("更新通知")
async def update_notification(
    notification_update: NotificationUpdate,
    notification_id: int = PathParam(..., description="通知ID"),
    api_logger=Depends(get_api_logger)
):
    """更新通知信息"""
    # 检查通知是否存在
    notification = get_record_by_id('wxapp_notifications', notification_id)
    if not notification:
        raise HTTPException(status_code=404, detail="通知不存在")
    
    # 过滤掉None值
    update_data = {k: v for k, v in notification_update.dict().items() if v is not None}
    if not update_data:
        # 没有需要更新的字段，返回原通知
        return create_standard_response(process_json_fields(notification))
    
    # 处理extra字段
    if 'extra' in update_data:
        update_data['extra'] = json.dumps(update_data['extra'])
    
    # 添加更新时间
    update_data = prepare_db_data(update_data, is_create=False)
    
    # 更新记录
    success = update_record('wxapp_notifications', notification_id, update_data)
    if not success:
        raise HTTPException(status_code=500, detail="更新通知失败")
    
    # 获取更新后的通知
    updated_notification = get_record_by_id('wxapp_notifications', notification_id)
    
    # 处理JSON字段
    updated_notification = process_json_fields(updated_notification)
    
    return create_standard_response(updated_notification)

@router.put("/users/{openid}/notifications/read", response_model=Dict[str, Any], summary="将用户通知标记为已读")
@handle_api_errors("标记通知已读")
async def mark_notifications_as_read(
    openid: str = PathParam(..., description="用户openid"),
    notification_ids: Optional[List[int]] = Body(None, description="通知ID列表，如果为空则标记所有未读通知"),
    api_logger=Depends(get_api_logger)
):
    """将用户通知标记为已读"""
    api_logger.debug(f"标记用户openid={openid}的通知为已读, 通知IDs={notification_ids}")
    
    try:
        success = False
        if notification_ids:
            # 标记指定通知为已读
            for notification_id in notification_ids:
                # 首先检查通知是否属于该用户
                notification = get_record_by_id('wxapp_notifications', notification_id)
                if notification and notification.get('openid') == openid:
                    success = update_record(
                        'wxapp_notifications',
                        notification_id,
                        {'is_read': 1, 'update_time': format_datetime(None)}
                    )
                    api_logger.debug(f"标记通知ID={notification_id}为已读: {'成功' if success else '失败'}")
                else:
                    api_logger.warning(f"通知ID={notification_id}不存在或不属于用户openid={openid}")
        else:
            # 标记所有未读通知为已读
            # 先获取用户所有未读通知
            unread_notifications = query_records(
                'wxapp_notifications',
                conditions={"openid": openid, "is_read": 0, "is_deleted": 0}
            )
            
            if unread_notifications:
                for notification in unread_notifications:
                    success = update_record(
                        'wxapp_notifications',
                        notification['id'],
                        {'is_read': 1, 'update_time': format_datetime(None)}
                    )
                    api_logger.debug(f"标记通知ID={notification['id']}为已读: {'成功' if success else '失败'}")
            
            api_logger.debug(f"标记用户openid={openid}的所有未读通知为已读: {'成功' if success else '无未读通知'}")
        
        # 查询未读通知数量
        unread_count = count_records(
            'wxapp_notifications',
            {"openid": openid, "is_read": 0, "is_deleted": 0}
        )
        
        return create_standard_response({
            "success": True,
            "message": "标记通知已读成功",
            "unread_count": unread_count
        })
    except Exception as e:
        api_logger.error(f"标记通知已读失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"标记通知已读失败: {str(e)}")

@router.delete("/notifications/{notification_id}", response_model=Dict[str, Any], summary="删除通知")
@handle_api_errors("删除通知")
async def delete_notification(
    notification_id: int = PathParam(..., description="通知ID"),
    api_logger=Depends(get_api_logger)
):
    """删除通知（标记删除）"""
    # 检查通知是否存在
    notification = get_record_by_id('wxapp_notifications', notification_id)
    if not notification:
        raise HTTPException(status_code=404, detail="通知不存在")
    
    # 标记删除
    success = update_record('wxapp_notifications', notification_id, {
        'is_deleted': 1,
        'update_time': format_datetime(None)
    })
    
    if not success:
        raise HTTPException(status_code=500, detail="删除通知失败")
    
    return create_standard_response({
        'success': True,
        'message': '通知已删除'
    }) 