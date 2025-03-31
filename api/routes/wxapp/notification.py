"""
微信小程序通知API接口
"""
from typing import List, Dict, Any, Optional
from fastapi import Depends, Query, APIRouter, Request as FastAPIRequest
from api.models.common import Response, Request, validate_params
from etl.load.db_core import (
    async_query_records, async_get_by_id, async_insert, async_update, async_count_records
)
from fastapi import APIRouter

router = APIRouter()

@router.get("/notification/list")
async def get_user_notifications(
    request: FastAPIRequest,
    openid: str = Query(..., description="用户openid"),
    type: Optional[str] = Query(None, description="通知类型"),
    is_read: Optional[bool] = Query(None, description="是否已读"),
    limit: int = Query(20, description="每页数量"),
    offset: int = Query(0, description="偏移量")
):
    """获取用户通知列表"""
    try:
        conditions = {"openid": openid, "status": 1}
        if type:
            conditions["type"] = type
        if is_read is not None:
            conditions["is_read"] = is_read

        notifications = await async_query_records(
            table_name="wxapp_notification",
            conditions=conditions,
            limit=limit,
            offset=offset,
            order_by="create_time DESC"
        )
        return Response.paged(data=notifications["data"],pagination=notifications["pagination"],details={"message":"获取用户通知列表成功"})
    except Exception as e:
        return Response.error(details={"message": f"获取用户通知列表失败: {str(e)}"})


@router.get("/notification/detail")
async def get_notification_detail(
    notification_id: int = Query(..., description="通知ID")
):
    """获取通知详情"""
    try:
        if not notification_id:
            return Response.bad_request(details={"message": "缺少notification_id参数"})
        
        notification = await async_get_by_id("wxapp_notification", notification_id)
        if not notification:
            return Response.not_found(resource="通知")
        
        return Response.success(data=notification, details={"message": "获取通知详情成功"})
    except Exception as e:
        return Response.error(details={"message": f"获取通知详情失败: {str(e)}"})

@router.get("/notification/status")
async def get_notification_status(
    openid: str = Query(..., description="用户openid")
):
    """获取用户通知状态（是否有未读通知）"""
    try:
        if not openid:
            return Response.bad_request(details={"message": "缺少openid参数"})
        
        conditions = {"openid": openid, "is_read": False, "status": 1}
        count = await async_count_records(
            table_name="wxapp_notification",
            conditions=conditions
        )
        
        return Response.success(
            data={"has_unread": count > 0, "unread_count": count},
            details={"message": "获取通知状态成功"}
        )
    except Exception as e:
        return Response.error(details={"message": f"获取通知状态失败: {str(e)}"})

@router.get("/notification/count")
async def get_unread_notifications_count(
    openid: str = Query(..., description="用户openid"),
    type: Optional[str] = Query(None, description="通知类型"),
):
    """获取未读通知数量"""
    if(not openid):
        return Response.bad_request(details={"message": "缺少openid参数"})
    try:
        conditions = {"openid": openid, "is_read": False, "status": 1}
        if type:
            conditions["type"] = type

        count = await async_count_records(
            table_name="wxapp_notification",
            conditions=conditions
        )

        return Response.success(data={"count": count},details={"message":"获取未读通知数量成功"})
    except Exception as e:
        return Response.error(details={"message": f"获取未读通知数量失败: {str(e)}"})

@router.post("/notification/mark-read")
async def mark_notification_read(request: Request):
    """标记通知已读"""
    try:
        req_data = await request.json()
        required_params = ["notification_id", "openid"]
        error_response = validate_params(req_data, required_params)
        if(error_response):
            return error_response

        notification_id = req_data.get("notification_id")
        openid = req_data.get("openid")

        # 验证通知归属权
        notification = await async_get_by_id("wxapp_notification", notification_id)
        if not notification:
            return Response.not_found(resource="通知")
        
        if notification.get("openid") != openid:
            return Response.forbidden(details={"message": "无权限操作此通知"})

        update_data = {"is_read": True}

        await async_update(
            table_name="wxapp_notification",
            record_id=notification_id,
            data=update_data
        )

        return Response.success(details={"message":"标记已读成功"})
    except Exception as e:
        return Response.error(details={"message": f"标记已读失败: {str(e)}"})

@router.post("/notification/mark-read-batch")
async def mark_notifications_read(request: Request):
    """批量标记通知为已读"""
    try:
        req_data = await request.json()
        required_params = ["openid", "notification_ids"]
        error_response = validate_params(req_data, required_params)
        if(error_response):
            return error_response

        openid = req_data.get("openid")
        notification_ids = req_data.get("notification_ids", [])
        
        if not notification_ids:
            return Response.bad_request(details={"message": "notification_ids不能为空"})
        
        # 验证通知归属权
        for notification_id in notification_ids:
            notification = await async_get_by_id("wxapp_notification", notification_id)
            if not notification:
                continue
            
            if notification.get("openid") != openid:
                return Response.forbidden(details={"message": "无权限操作此通知"})
        
        update_data = {"is_read": True}
        
        # 更新每个通知的状态
        updated_count = 0
        for notification_id in notification_ids:
            success = await async_update(
                table_name="wxapp_notification",
                record_id=notification_id,
                data=update_data
            )
            if success:
                updated_count += 1

        return Response.success(details={"message": f"成功标记 {updated_count} 条通知为已读"})
    except Exception as e:
        return Response.error(details={"message": f"批量标记已读失败: {str(e)}"})

@router.post("/notification/delete")
async def delete_notification(request: Request):
    """删除通知"""
    try:
        req_data = await request.json()
        required_params = ["notification_id"]
        error_response = validate_params(req_data, required_params)
        if(error_response):
            return error_response
            
        notification_id = req_data.get("notification_id")
        openid = req_data.get("openid")
        
        # 验证通知归属权
        notification = await async_get_by_id("wxapp_notification", notification_id)
        if not notification:
            return Response.not_found(resource="通知")
        
        if notification.get("openid") != openid:
            return Response.forbidden(details={"message": "无权限操作此通知"})

        await async_update(
            table_name="wxapp_notification",
            record_id=notification_id,
            data={"status": 0}
        )

        return Response.success(details={"message":"通知删除成功"})
    except Exception as e:
        return Response.error(details={"message": f"删除通知失败: {str(e)}"}) 