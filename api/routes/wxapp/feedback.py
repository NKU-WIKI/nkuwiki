"""
用户反馈相关API接口
"""
import json
from fastapi import APIRouter, Depends, Body
from typing import Dict, Any, Optional

from api.models.common import Response, validate_params, PaginationInfo
from etl.load import insert_record, query_records
from core.utils.logger import register_logger
from api.common.dependencies import get_current_active_user_optional, get_current_active_user

router = APIRouter()
logger = register_logger('api.routes.wxapp.feedback')


@router.post("/create", summary="创建用户反馈")
async def create_feedback(
    payload: Dict[str, Any] = Body(...),
    current_user: Optional[Dict[str, Any]] = Depends(get_current_active_user_optional)
):
    """
    创建一条新的用户反馈。
    - 如果用户已登录，将自动记录 user_id。
    - 如果用户未登录，则作为匿名反馈提交。
    """
    # 验证必要参数
    required_params = ['content']
    missing_params_response = validate_params(payload, required_params)
    if missing_params_response:
        return missing_params_response

    feedback_data = {
        "content": payload.get("content"),
        "title": payload.get("title"),
        "category": payload.get("category"),
        "contact": payload.get("contact"),
        "version": payload.get("version"),
        "status": "pending"  # 初始状态为待处理
    }
    
    # 如果存在image字段且是列表，则转换为JSON字符串
    if 'image' in payload and isinstance(payload['image'], list):
        feedback_data['image'] = json.dumps(payload['image'], ensure_ascii=False)
     
    # 如果存在device_info字段且是字典，则转换为JSON字符串
    if 'device_info' in payload and isinstance(payload['device_info'], dict):
        feedback_data['device_info'] = json.dumps(payload['device_info'], ensure_ascii=False)

    # 如果用户已登录，则记录 user_id
    if current_user:
        feedback_data["user_id"] = current_user.get("id")

    try:
        feedback_id = await insert_record("wxapp_feedback", feedback_data)
        if not feedback_id or feedback_id == -1:
            logger.error("插入反馈数据失败")
            return Response.db_error(details={"message": "创建反馈失败"})
        
        logger.info(f"成功创建反馈，ID: {feedback_id} | User: {feedback_data.get('user_id', 'anonymous')}")
        return Response.success(data={"id": feedback_id}, message="反馈提交成功！")
        
    except Exception as e:
        logger.error(f"创建反馈时发生异常: {e}")
        return Response.error(details=f"服务器内部错误: {e}")

@router.get("/my/list", summary="获取我的反馈列表")
async def get_my_feedback_list(
    page: int = 1,
    page_size: int = 10,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """获取当前登录用户的反馈列表"""
    user_id = current_user["id"]
    
    try:
        # 查询反馈记录
        result = await query_records(
            "wxapp_feedback",
            conditions={"user_id": user_id},
            order_by={"create_time": "DESC"},
            limit=page_size,
            offset=(page - 1) * page_size
        )
        
        feedbacks = result.get('data', [])
        total = result.get('total', 0)

        # 反序列化JSON字段
        for item in feedbacks:
            if isinstance(item.get('image'), str):
                try:
                    item['image'] = json.loads(item['image'])
                except json.JSONDecodeError:
                    item['image'] = None
            if isinstance(item.get('device_info'), str):
                try:
                    item['device_info'] = json.loads(item['device_info'])
                except json.JSONDecodeError:
                    item['device_info'] = None

        pagination = PaginationInfo(total=total, page=page, page_size=page_size)
        
        return Response.paged(data=feedbacks, pagination=pagination)
    except Exception as e:
        logger.error(f"获取我的反馈列表时发生异常: {e}")
        return Response.error(details=f"服务器内部错误: {e}")