"""
微信小程序通知API接口
"""
from typing import Optional, List, Dict, Any
from fastapi import Query, APIRouter, Depends, Body

from api.models.common import Response, PaginationInfo
from core.utils.logger import register_logger
from etl.load import db_core
from api.common.dependencies import get_current_active_user

logger = register_logger('api.routes.wxapp.notification')
router = APIRouter()


@router.get("/list", summary="获取通知列表")
async def get_notifications(
    current_user: Dict[str, Any] = Depends(get_current_active_user),
    page: int = Query(1, description="页码"),
    page_size: int = Query(10, description="每页数量")
):
    """获取当前用户的通知列表，并附带发送者信息，按时间倒序排列。"""
    receiver_id = current_user.get("id")
    offset = (page - 1) * page_size

    # 查询总数
    total_sql = "SELECT COUNT(*) as total FROM wxapp_notification WHERE receiver_id = %s AND status = 1"
    total_result = await db_core.execute_custom_query(total_sql, [receiver_id], fetch='one')
    total = total_result['total'] if total_result else 0

    # 使用JOIN一次性获取通知和发送者信息
    query_sql = """
        SELECT
            n.id, n.title, n.content, n.type, n.is_read,
            n.target_id, n.target_type, n.create_time,
            u.nickname as sender_nickname,
            u.avatar as sender_avatar
        FROM wxapp_notification n
        LEFT JOIN wxapp_user u ON n.sender_id = u.id
        WHERE n.receiver_id = %s AND n.status = 1
        ORDER BY n.create_time DESC
        LIMIT %s OFFSET %s
    """
    notifications = await db_core.execute_custom_query(query_sql, [receiver_id, page_size, offset])

    # 处理系统通知的发送者名称
    for n in notifications:
        if not n.get('sender_nickname'):
            n['sender_nickname'] = '系统通知'

    pagination = PaginationInfo(total=total, page=page, page_size=page_size)
    return Response.paged(data=notifications, pagination=pagination)


@router.get("/unread-count", summary="获取未读通知数量")
async def get_unread_notification_count(
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """获取用户未读通知的总数。"""
    receiver_id = current_user.get("id")
    sql = "SELECT COUNT(*) as unread_count FROM wxapp_notification WHERE receiver_id = %s AND is_read = 0 AND status = 1"
    result = await db_core.execute_custom_query(sql, [receiver_id], fetch='one')
    unread_count = result['unread_count'] if result else 0
    return Response.success(data={'unread_count': unread_count})


@router.post("/read", summary="标记通知为已读")
async def mark_as_read(
    body: Dict[str, List[int]] = Body(..., example={"notification_ids": [1, 2]}),
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """将一个或多个通知标记为已读。"""
    notification_ids = body.get('notification_ids')
    if not notification_ids or not isinstance(notification_ids, list):
        return Response.bad_request(message="notification_ids 必须是一个包含通知ID的列表")

    receiver_id = current_user.get("id")
    placeholders = ', '.join(['%s'] * len(notification_ids))
    update_sql = f"UPDATE wxapp_notification SET is_read = 1 WHERE id IN ({placeholders}) AND receiver_id = %s"
    update_params = notification_ids + [receiver_id]

    await db_core.execute_custom_query(update_sql, update_params, fetch=False)
    return Response.success(message="操作成功")


@router.post("/read-all", summary="全部标记为已读")
async def mark_all_as_read(
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """将当前用户的所有未读通知标记为已读。"""
    receiver_id = current_user.get("id")
    update_sql = "UPDATE wxapp_notification SET is_read = 1 WHERE receiver_id = %s AND is_read = 0"
    await db_core.execute_custom_query(update_sql, [receiver_id], fetch=False)
    return Response.success(message="所有未读通知已标记为已读")


@router.post("/delete", summary="删除通知")
async def delete_notification(
    body: Dict[str, int] = Body(..., example={"notification_id": 1}),
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """逻辑删除单条通知。"""
    notification_id = body.get("notification_id")
    if not notification_id:
        return Response.bad_request(message="缺少 notification_id")

    receiver_id = current_user.get("id")
    update_sql = "UPDATE wxapp_notification SET status = 0 WHERE id = %s AND receiver_id = %s"
    await db_core.execute_custom_query(update_sql, [notification_id, receiver_id], fetch=False)
    return Response.success(message="删除成功")


@router.get("/summary", summary="获取通知摘要")
async def get_notification_summary(
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """获取未读通知摘要，包含总览和分类计数。"""
    receiver_id = current_user.get("id")
    summary_sql = """
        SELECT type, COUNT(*) as count
        FROM wxapp_notification
        WHERE receiver_id = %s AND is_read = 0 AND status = 1
        GROUP BY type
    """
    results = await db_core.execute_custom_query(summary_sql, [receiver_id])

    summary = { "total_unread": 0, "unread_by_type": {} }
    if results:
        for row in results:
            summary['unread_by_type'][row['type']] = row['count']
            summary['total_unread'] += row['count']

    return Response.success(data=summary)
