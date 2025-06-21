"""
微信小程序通知API接口
"""
from typing import Optional, List, Dict, Any
from fastapi import Query, APIRouter, Depends, Body
from api.models.common import Response, Request, validate_params, PaginationInfo
from core.utils.logger import register_logger
from etl.load import (
    query_records, 
    insert_record, 
    update_record, 
    execute_custom_query, 
    count_records
)
import asyncio
import json

logger = register_logger('api.routes.wxapp.notification')
router = APIRouter()

@router.get("/list", summary="获取通知列表")
async def get_notifications(
    openid: str = Query(..., description="要查询通知的openid"),
    page: int = 1,
    page_size: int = 10
):
    """获取当前用户的通知列表，按时间倒序排列。"""
    conditions = {"openid": openid}
    total = await count_records("wxapp_notification", conditions)
    
    notifications = await query_records(
            "wxapp_notification",
        conditions,
        order_by="create_time DESC",
            limit=page_size,
        offset=(page - 1) * page_size
    )

    enriched_notifications = []
    for notification in notifications['data']:
        # 如果通知是未读的，则将其标记为已读
        if not notification.get('is_read'):
            update_sql = "UPDATE wxapp_notification SET is_read = 1, update_time = NOW() WHERE id = %s"
            await execute_custom_query(update_sql, [notification['id']], fetch=False)
            notification['is_read'] = 1
        enriched_notifications.append(notification)

    pagination = PaginationInfo(
        total=total,
        page=page,
        page_size=page_size
    )
    return Response.paged(data=enriched_notifications, pagination=pagination)

@router.get("/detail", summary="获取通知详情")
async def get_notification_detail(
    notification_id: int,
    openid: str = Query(..., description="要查询通知的openid")
):
    """获取单条通知的详细信息"""
    query = "SELECT * FROM wxapp_notification WHERE id = %s AND openid = %s"
    notification = await execute_custom_query(query, [notification_id, openid], fetch='one')
        
    if not notification:
        return Response.error(message="通知不存在或无权访问")

    # 如果通知是未读的，则将其标记为已读
    if not notification.get('is_read'):
        update_sql = "UPDATE wxapp_notification SET is_read = 1, update_time = NOW() WHERE id = %s"
        await execute_custom_query(update_sql, [notification_id], fetch=False)
        notification['is_read'] = 1

    return Response.success(data=notification)

@router.get("/count", summary="获取未读通知数量")
async def get_unread_notification_count(
    openid: str = Query(..., description="要查询通知的openid")
):
    """获取用户未读通知的总数"""
    summary_sql = "SELECT COUNT(*) as unread_count FROM wxapp_notification WHERE openid = %s AND is_read = 0"
    result = await execute_custom_query(summary_sql, [openid], fetch='one')
    
    unread_count = result['unread_count'] if result else 0
    return Response.success(data={'unread_count': unread_count})

@router.post("/read", summary="标记通知为已读")
async def mark_as_read(
    body: Dict[str, Any] = Body(...)
):
    """将一个或多个通知标记为已读。"""
    notification_ids = body.get('notification_ids', [])
    openid = body.get('openid')

    if not notification_ids:
        return Response.error(message="通知ID列表不能为空")

    placeholders = ', '.join(['%s'] * len(notification_ids))
    update_sql = f"UPDATE wxapp_notification SET is_read = 1, update_time = NOW() WHERE id IN ({placeholders}) AND openid = %s"
    update_params = notification_ids + [openid]
    
    await execute_custom_query(update_sql, update_params, fetch=False)
    return Response.success(message="操作成功")

@router.post("/delete", summary="删除通知")
async def delete_notification(
    body: Dict[str, Any] = Body(...)
):
    """删除单条通知"""
    notification_id = body.get('notification_id')
    openid = body.get('openid')

    if not notification_id or not openid:
        return Response.bad_request(message="缺少 notification_id 或 openid")

    # 实际项目中可能是逻辑删除
    delete_sql = "DELETE FROM wxapp_notification WHERE id = %s AND openid = %s"
    await execute_custom_query(delete_sql, [notification_id, openid], fetch=False)
    return Response.success(message="删除成功")

@router.get("/summary", summary="获取通知摘要")
async def get_notification_summary(
    openid: str = Query(..., description="要查询通知摘要的openid")
):
    """获取未读通知摘要，包含总览和分类计数。"""
    summary_sql = """
        SELECT 
            type, 
            COUNT(*) as count 
        FROM wxapp_notification 
        WHERE openid = %s AND is_read = 0 
        GROUP BY type
    """
    results = await execute_custom_query(summary_sql, [openid], fetch='all')

    summary = {
        "total_unread": 0,
        "unread_by_type": {
            "like": 0,
            "comment": 0,
            "follow": 0,
            "system": 0
        }
    }

    for row in results:
        if row['type'] in summary['unread_by_type']:
            summary['unread_by_type'][row['type']] = row['count']
            summary['total_unread'] += row['count']

    return Response.success(data=summary)
