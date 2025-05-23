"""
微信小程序通知API接口
"""
from typing import Optional
from fastapi import Query, APIRouter
from api.models.common import Response, Request, validate_params
from core.utils.logger import register_logger
from etl.load.db_core import (
    async_query_records, async_insert, async_count_records, async_execute_custom_query
)
import asyncio

logger = register_logger('api.routes.wxapp.notification')
router = APIRouter()

@router.get("/notification")
async def get_notification_list(
    openid: str = Query(..., description="用户openid"),
    type: Optional[str] = Query(None, description="通知类型"),
    is_read: Optional[int] = Query(None, description="是否已读"),
    page: int = Query(1, description="页码"),
    page_size: int = Query(10, description="每页数量")
):
    """获取用户通知列表，并返回未读通知数量"""
    try:
        # 计算偏移量
        offset = (page - 1) * page_size
        
        # 构建查询条件
        conditions = {"openid": openid, "status": 1}
        
        if type:
            conditions["type"] = type
            
        if is_read is not None:
            conditions["is_read"] = is_read
        
        # 只获取必要的通知字段以减少数据传输量
        fields = ["id", "sender", "openid", "type", "content", "target_id", "target_type", "is_read", "create_time"]
            
        # 获取通知列表和未读数量并行执行
        notifications_query = async_query_records(
            "wxapp_notification",
            conditions=conditions,
            fields=fields,
            limit=page_size,
            offset=offset,
            order_by="create_time DESC"
        )
        
        # 统计未读通知总数
        unread_conditions = {"openid": openid, "is_read": 0, "status": 1}
        unread_count_query = async_count_records("wxapp_notification", unread_conditions)
        
        # 使用total_count参数优化查询
        count_conditions = conditions.copy()
        total_count_query = async_count_records("wxapp_notification", count_conditions)
        
        # 并行执行查询以提高性能
        notifications, unread_count, total_count = await asyncio.gather(
            notifications_query, unread_count_query, total_count_query
        )
        
        # 转换字段名，将数据库中的openid字段转换为API响应中的receiver字段
        notifications_data = notifications.get("data", [])
        for notification in notifications_data:
            if "openid" in notification:
                notification["receiver"] = notification["openid"]
                del notification["openid"]
            
            # 解析sender字段中的JSON字符串为JSON对象
            if "sender" in notification:
                try:
                    import json
                    if isinstance(notification["sender"], str):
                        notification["sender"] = json.loads(notification["sender"])
                except Exception as e:
                    logger.warning(f"解析sender JSON失败: {str(e)}")
                    # 保持原始数据不变

        # 添加未读通知数量到返回数据
        result_data = {
            "list": notifications_data,
            "unread_count": unread_count
        }
        
        # 计算总页数
        total_pages = (total_count + page_size - 1) // page_size if page_size > 0 else 1
        
        # 构建标准分页信息
        pagination = {
            "total": total_count,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "has_more": page < total_pages
        }
        
        return Response.paged(
            data=result_data,
            pagination=pagination,
            details={"message": "获取通知列表成功"}
        )
    except Exception as e:
        logger.error(f"获取通知列表失败: {str(e)}")
        return Response.error(details={"message": f"获取通知列表失败: {str(e)}"})

@router.get("/notification/detail")
async def get_notification_detail(
    notification_id: int = Query(..., description="通知ID")
):
    """获取通知详情"""
    try:
        # 使用参数化查询防止SQL注入
        query = """
        SELECT * FROM wxapp_notification 
        WHERE id = %s AND status = 1 
        LIMIT 1
        """
        
        notification = await async_execute_custom_query(query, [notification_id])
        
        if not notification:
            return Response.not_found(resource="通知")
            
        # 转换字段名，将数据库中的openid字段转换为API响应中的receiver字段
        notification_data = notification[0]
        if "openid" in notification_data:
            notification_data["receiver"] = notification_data["openid"]
            del notification_data["openid"]
        
        # 解析sender字段的JSON字符串为JSON对象
        if "sender" in notification_data:
            try:
                import json
                if isinstance(notification_data["sender"], str):
                    notification_data["sender"] = json.loads(notification_data["sender"])
            except Exception as e:
                logger.warning(f"解析sender JSON失败: {str(e)}")
                # 保持原始数据不变
            
        return Response.success(data=notification_data)
    except Exception as e:
        logger.error(f"获取通知详情失败: {str(e)}")
        return Response.error(details={"message": f"获取通知详情失败: {str(e)}"})

@router.get("/notification/summary")
async def get_notification_summary(
    openid: str = Query(..., description="用户openid")
):
    """获取各类型通知汇总"""
    try:
        # 使用单一SQL查询获取所有分类统计，减少数据库查询次数
        summary_sql = """
        SELECT 
            SUM(CASE WHEN is_read = 0 THEN 1 ELSE 0 END) as unread_count,
            SUM(CASE WHEN type = 'system' THEN 1 ELSE 0 END) as system_count,
            SUM(CASE WHEN type = 'comment' THEN 1 ELSE 0 END) as comment_count,
            SUM(CASE WHEN type = 'like' THEN 1 ELSE 0 END) as like_count,
            SUM(CASE WHEN type = 'follow' THEN 1 ELSE 0 END) as follow_count,
            SUM(CASE WHEN type = 'favorite' THEN 1 ELSE 0 END) as favorite_count
        FROM wxapp_notification 
        WHERE openid = %s AND status = 1
        """
        
        result = await async_execute_custom_query(summary_sql, [openid])
        
        if not result:
            # 默认返回全部为0的结果
            summary = {
                "unread_count": 0,
                "type_counts": {
                    "system": 0,
                    "comment": 0,
                    "like": 0,
                    "follow": 0,
                    "favorite": 0
                }
            }
        else:
            # 构建结果，将Decimal类型转换为int
            data = result[0]
            summary = {
                "unread_count": int(data["unread_count"] or 0),
                "type_counts": {
                    "system": int(data["system_count"] or 0),
                    "comment": int(data["comment_count"] or 0),
                    "like": int(data["like_count"] or 0),
                    "follow": int(data["follow_count"] or 0),
                    "favorite": int(data["favorite_count"] or 0)
                }
            }
        
        return Response.success(data=summary)
    except Exception as e:
        logger.error(f"获取通知汇总失败: {str(e)}")
        return Response.error(details={"message": f"获取通知汇总失败: {str(e)}"})

@router.post("/notification/read")
async def mark_notification_read(
    request: Request
):
    """标记通知为已读"""
    try:
        # 记录原始请求
        logger.info(f"收到标记通知已读请求: {request.client.host}")
        
        req_data = await request.json()
        logger.info(f"请求数据: {req_data}")
        
        required_params = ["notification_id", "openid"]
        error_response = validate_params(req_data, required_params)
        if error_response:
            logger.warning(f"标记通知已读参数验证失败: {req_data}")
            return error_response
            
        notification_id = req_data.get("notification_id")
        openid = req_data.get("openid")
        
        # 支持通过receiver字段接收参数
        if not openid and "receiver" in req_data:
            openid = req_data.get("receiver")
            
        if not openid:
            logger.warning(f"标记通知已读缺少openid参数: {req_data}")
            return Response.bad_request(details={"message": "缺少必要参数: openid"})
        
        logger.info(f"处理标记通知已读请求: notification_id={notification_id}, openid={openid}")
        
        # 使用单一原子操作实现检查和更新
        update_sql = """
        UPDATE wxapp_notification 
        SET is_read = 1 
        WHERE id = %s AND openid = %s AND status = 1 AND is_read = 0
        """
        
        await async_execute_custom_query(update_sql, [notification_id, openid], fetch=False)
        
        logger.info(f"通知标记已读成功: notification_id={notification_id}, openid={openid}")
        return Response.success(details={"message": "已标记通知为已读"})
    except Exception as e:
        logger.error(f"标记通知已读失败: {str(e)}")
        return Response.error(details={"message": f"标记通知已读失败: {str(e)}"})

@router.post("/notification/read-all")
async def mark_all_notification_read(
    request: Request
):
    """标记所有通知为已读"""
    try:
        req_data = await request.json()
        required_params = ["openid"]
        error_response = validate_params(req_data, required_params)
        if error_response:
            return error_response
            
        # 支持通过receiver字段接收参数
        openid = req_data.get("openid")
        if not openid and "receiver" in req_data:
            openid = req_data.get("receiver")
            
        if not openid:
            return Response.bad_request(details={"message": "缺少openid参数"})
            
        type = req_data.get("type")
        
        # 构建更新SQL，一次性标记所有符合条件的通知为已读
        update_sql = "UPDATE wxapp_notification SET is_read = 1 WHERE openid = %s AND is_read = 0 AND status = 1"
        update_params = [openid]
        
        if type:
            update_sql += " AND type = %s"
            update_params.append(type)
            
        # 执行批量更新
        await async_execute_custom_query(update_sql, update_params, fetch=False)
        
        return Response.success(details={"message": "已标记所有通知为已读"})
    except Exception as e:
        logger.error(f"批量标记通知已读失败: {str(e)}")
        return Response.error(details={"message": f"批量标记通知已读失败: {str(e)}"})

@router.post("/notification/delete")
async def delete_notification(
    request: Request
):
    """删除通知"""
    try:
        req_data = await request.json()
        required_params = ["notification_id"]
        error_response = validate_params(req_data, required_params)
        if error_response:
            return error_response
            
        notification_id = req_data.get("notification_id")
        
        # 直接使用SQL更新删除标记，无需先检查存在性
        update_sql = "UPDATE wxapp_notification SET status = 0 WHERE id = %s"
        await async_execute_custom_query(update_sql, [notification_id], fetch=False)
        
        return Response.success(details={"message": "删除通知成功"})
    except Exception as e:
        logger.error(f"删除通知失败: {str(e)}")
        return Response.error(details={"message": f"删除通知失败: {str(e)}"})

@router.post("/notification")
async def create_notification(
    request: Request
):
    """创建新通知"""
    try:
        req_data = await request.json()
        required_params = ["openid", "type", "content"]
        error_response = validate_params(req_data, required_params)
        if error_response:
            return error_response
            
        # 支持通过receiver字段接收参数，兼容前端传参习惯
        openid = req_data.get("openid")
        if not openid and "receiver" in req_data:
            openid = req_data.get("receiver")
            
        if not openid:
            return Response.bad_request(details={"message": "缺少接收者openid参数"})
            
        # 获取target_id，并确保是整数类型
        target_id = req_data.get("target_id", "")
        target_type = req_data.get("target_type", "")
        
        # 如果target_type是user且target_id是openid，需要进行转换
        if target_type == "user" and target_id and not isinstance(target_id, int):
            try:
                # 查询用户数字ID
                user_query = "SELECT id FROM wxapp_user WHERE openid = %s LIMIT 1"
                user_result = await async_execute_custom_query(user_query, [target_id])
                if user_result:
                    target_id = user_result[0]["id"]
                else:
                    # 找不到用户，使用默认值
                    target_id = 0
            except Exception as e:
                logger.warning(f"转换用户openid到id失败: {str(e)}")
                target_id = 0
        
        # 验证并获取sender信息
        sender = req_data.get("sender", {})
        if not isinstance(sender, dict):
            # 如果sender不是字典，尝试将其当作openid获取用户信息
            try:
                sender_openid = str(sender)
                user_query = "SELECT openid, nickname, avatar FROM wxapp_user WHERE openid = %s LIMIT 1"
                user_result = await async_execute_custom_query(user_query, [sender_openid])
                if user_result:
                    sender = {
                        "openid": user_result[0]["openid"],
                        "nickname": user_result[0]["nickname"],
                        "avatar": user_result[0]["avatar"]
                    }
                else:
                    # 找不到用户，使用默认值
                    sender = {"openid": sender_openid, "nickname": "", "avatar": ""}
            except Exception as e:
                logger.warning(f"获取sender用户信息失败: {str(e)}")
                sender = {"openid": str(sender), "nickname": "", "avatar": ""}
        
        # 构造通知数据
        notification_data = {
            "openid": openid,  # 存储到数据库使用openid字段
            "type": req_data.get("type"),
            "content": req_data.get("content"),
            "sender": sender,  # 已经是JSON对象
            "target_id": target_id,
            "target_type": target_type,
            "is_read": 0,
            "status": 1
        }
        
        # 创建通知
        notification_id = await async_insert("wxapp_notification", notification_data)
        
        if not notification_id:
            return Response.db_error(details={"message": "创建通知失败"})
            
        return Response.success(details={"notification_id": notification_id, "message": "创建通知成功"})
    except Exception as e:
        logger.error(f"创建通知失败: {str(e)}")
        return Response.error(details={"message": f"创建通知失败: {str(e)}"}) 