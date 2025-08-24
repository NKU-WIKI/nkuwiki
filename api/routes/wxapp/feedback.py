"""
微信小程序用户反馈API
"""
from typing import List, Dict, Any, Optional
from fastapi import Query, APIRouter, Depends, Body, HTTPException
from api.models.common import Response, Request, validate_params, PaginationInfo
from etl.load import (
    execute_custom_query, 
    insert_record, 
    get_by_id, 
    update_record, 
    query_records, 
    count_records
)
from core.utils.logger import register_logger
import json
from pydantic import BaseModel

router = APIRouter()
logger = register_logger('api.routes.wxapp.feedback')

class FeedbackRequest(BaseModel):
    openid: str
    title: str
    content: str
    category: str
    contact: Optional[str] = None
    image: Optional[List[str]] = []
    device_info: Optional[Dict[str, Any]] = None

class UpdateStatusRequest(BaseModel):
    feedback_id: int
    status: str
    admin_id: str

class ReplyRequest(BaseModel):
    feedback_id: int
    reply_content: str
    admin_id: str

class DeleteRequest(BaseModel):
    feedback_id: int
    admin_id: str

@router.get("/detail", summary="获取反馈详情")
async def get_feedback_detail(feedback_id: int):
    """获取单条反馈的详细信息，包括处理记录"""
    sql = """
    SELECT f.*, u.nickname as user_nickname, u.avatar as user_avatar
    FROM wxapp_feedback f
    LEFT JOIN wxapp_user u ON f.openid = u.openid
    WHERE f.id = %s
    """
    feedback = await execute_custom_query(sql, [feedback_id], fetch='one')
    if not feedback:
        return Response.error(message="反馈不存在")
    
    # 获取处理记录
    history_sql = "SELECT * FROM wxapp_feedback_history WHERE feedback_id = %s ORDER BY create_time ASC"
    history = await execute_custom_query(history_sql, [feedback_id])
    feedback['history'] = history
    
    return Response.success(data=feedback)

@router.get("/list", summary="获取反馈列表")
async def get_feedback_list(
    page: int = 1,
    page_size: int = 10,
    status: Optional[str] = None,
    category: Optional[str] = None
):
    """获取反馈列表，支持按状态和分类筛选"""
    conditions = {}
    if status:
        conditions['status'] = status
    if category:
        conditions['category'] = category

    total = await count_records("wxapp_feedback", conditions)
    
    offset = (page - 1) * page_size
    
    base_sql = """
    SELECT f.id, f.title, f.content, f.category, f.status, f.create_time, 
           u.nickname as user_nickname, u.avatar as user_avatar
    FROM wxapp_feedback f
    LEFT JOIN wxapp_user u ON f.openid = u.openid
    """
    
    where_clauses = []
    params = []
    
    if status:
        where_clauses.append("f.status = %s")
        params.append(status)
    if category:
        where_clauses.append("f.category = %s")
        params.append(category)
        
    if where_clauses:
        base_sql += " WHERE " + " AND ".join(where_clauses)
        
    base_sql += " ORDER BY f.create_time DESC LIMIT %s OFFSET %s"
    params.extend([page_size, offset])
    
    feedbacks = await execute_custom_query(base_sql, params)
    
    pagination = PaginationInfo(
        total=total, 
        page=page, 
        page_size=page_size
    )
    return Response.paged(data=feedbacks, pagination=pagination)

@router.post("/")
async def create_feedback(feedback_data: Dict[str, Any] = Body(...)):
    """用户提交反馈"""
    # 验证请求体
    required_fields = ['openid', 'content']
    if error_msg := validate_params(feedback_data, required_fields):
        return Response.bad_request(error_msg)

    # 如果存在image字段且是列表，则转换为JSON字符串
    if 'image' in feedback_data and isinstance(feedback_data['image'], list):
        feedback_data['image'] = json.dumps(feedback_data['image'], ensure_ascii=False)
    
    # 如果存在device_info字段且是字典，则转换为JSON字符串
    if 'device_info' in feedback_data and isinstance(feedback_data['device_info'], dict):
        feedback_data['device_info'] = json.dumps(feedback_data['device_info'], ensure_ascii=False)

    # 插入新反馈
    feedback_id = await insert_record("wxapp_feedback", feedback_data)
    if not feedback_id:
        return Response.db_error("创建反馈失败")

    return Response.success(data={"feedback_id": feedback_id}, message="反馈成功提交")

@router.post("/update-status", summary="更新反馈状态 (管理员)")
async def update_feedback_status(
    request: UpdateStatusRequest
):
    """更新反馈状态 (管理员操作)"""
    # 更新记录
    updated_count = await update_record(
        "wxapp_feedback", 
        conditions={"id": request.feedback_id}, 
        data={"status": request.status, "admin_id": request.admin_id}
    )

    if updated_count == 0:
        return Response.not_found("未找到该反馈或状态未改变")
    
    # 插入历史记录
    history_data = {
        "feedback_id": request.feedback_id,
        "operator": request.admin_id,
        "action_type": "status_change",
        "details": json.dumps({"new_status": request.status})
    }
    await insert_record("wxapp_feedback_history", history_data)

    return Response.success(message="状态更新成功")

@router.post("/{feedback_id}/reply")
async def reply_to_feedback(
    feedback_id: int, 
    reply_data: Dict[str, Any] = Body(...)
):
    """回复用户反馈 (管理员操作)"""
    reply_content = reply_data.get("reply_content")
    admin_id = reply_data.get("admin_id") # 从请求体获取操作员信息

    if not reply_content or not admin_id:
        return Response.bad_request("缺少'reply_content'或'admin_id'参数")
    
    # 更新记录
    updated_count = await update_record(
        "wxapp_feedback",
        conditions={"id": feedback_id},
        data={"admin_reply": reply_content, "admin_id": admin_id, "status": "replied"}
    )
    
    if updated_count == 0:
        return Response.not_found("未找到该反馈")
    
    # 插入历史记录
    history_data = {
        "feedback_id": feedback_id,
        "operator": admin_id,
        "action_type": "reply",
        "details": json.dumps({"reply": reply_content})
    }
    await insert_record("wxapp_feedback_history", history_data)

    return Response.success(message="回复成功")

@router.post("/delete", summary="删除反馈 (管理员)")
async def delete_feedback(
    body: Dict[str, Any] = Body(...)
):
    """管理员删除反馈"""
    feedback_id = body.get("feedback_id")
    admin_id = body.get("admin_id") # 从请求体获取操作员信息
    if not feedback_id or not admin_id:
        return Response.bad_request("缺少'feedback_id'或'admin_id'参数")

    feedback_sql = "SELECT * FROM wxapp_feedback WHERE id = %s"
    feedback = await execute_custom_query(feedback_sql, [feedback_id], fetch='one')
    if not feedback:
        return Response.error(message="反馈不存在")
    
    # 实际项目中可能需要权限校验
    
    delete_sql = "DELETE FROM wxapp_feedback WHERE id = %s"
    await execute_custom_query(delete_sql, [feedback_id], fetch=False)
    
    # 可选：也删除相关的处理记录
    await execute_custom_query("DELETE FROM wxapp_feedback_history WHERE feedback_id = %s", [feedback_id], fetch=False)
    
    return Response.success(message="反馈删除成功") 