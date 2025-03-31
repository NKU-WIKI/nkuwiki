"""
微信小程序用户反馈API
"""
from typing import List, Dict, Any, Optional
from fastapi import Query, APIRouter
from api.models.common import Response, Request, validate_params

from etl.load.db_core import (
    async_query_records, async_get_by_id, async_insert, async_update
)

router = APIRouter()

@router.get("/feedback/detail")
async def get_feedback_detail(
    feedback_id: str = Query(..., description="反馈ID")
):
    """获取用户反馈详情"""
    if(not feedback_id):
        return Response.bad_request(details={"message": "缺少feedback_id参数"})
    try:
        feedback = await async_get_by_id("wxapp_feedback", feedback_id)
        if not feedback:
            return Response.not_found(resource="反馈")
        return Response.success(data=feedback)
    except Exception as e:
        return Response.error(details={"message": f"获取反馈详情失败: {str(e)}"})

@router.get("/feedback/list")
async def get_feedback_list(
    openid: str = Query(..., description="用户OpenID"),
    type: Optional[str] = Query(None, description="反馈类型"),
    status: Optional[str] = Query(None, description="反馈状态")
):
    """获取用户反馈列表"""
    if(not openid):
        return Response.bad_request(details={"message": "缺少openid参数"})
    try:
        conditions = {"openid": openid}
        if type:
            conditions["type"] = type
        if status:
            conditions["status"] = status

        feedbacks = await async_query_records(
            table_name="wxapp_feedback",
            conditions=conditions,
            order_by="create_time DESC"
        )

        feedback_list = feedbacks

        return Response.success(data={"feedbacks": feedback_list})
    except Exception as e:
        return Response.error(details={"message": f"获取用户反馈列表失败: {str(e)}"})

@router.post("/feedback")
async def create_feedback(request: Request):
    """创建用户反馈"""
    try:
        req_data = await request.json()
        required_params = ["content"]
        error_response = validate_params(req_data, required_params)
        if(error_response):
            return error_response

        openid = req_data.get("openid")
        content = req_data.get("content")
        type = req_data.get("type","")
        image = req_data.get("image", [])
        contact = req_data.get("contact","")

        feedback_data = {
            "openid":openid,
            "content":content,
            "type":type,
            "image":image,
            "contact":contact
        }

        feedback_id = await async_insert("wxapp_feedback", feedback_data)

        return Response.success(details={"feedback_id": feedback_id,"message":"反馈创建成功"})
    except Exception as e:
        return Response.error(details={"message": f"创建反馈失败: {str(e)}"})

@router.post("/feedback/update")
async def update_feedback(request: Request):
    """更新用户反馈"""
    try:
        req_data = await request.json()
        required_params = ["feedback_id"]
        error_response = validate_params(req_data, required_params)
        if(error_response):
            return error_response

        openid = req_data.get("openid")
        feedback_id = req_data.get("feedback_id")

        feedback = await async_get_by_id("wxapp_feedback", feedback_id)
        if not feedback:
            return Response.not_found(resource="反馈")

        update_data = req_data

        await async_update(
            table_name="wxapp_feedback",
            record_id=feedback_id,
            update_data=update_data
        )

        return Response.success(details={"message":"反馈更新成功"})
    except Exception as e:
        return Response.error(details={"message": f"更新反馈失败: {str(e)}"})

@router.post("/feedback/delete")
async def delete_feedback(request: Request):
    """删除反馈"""
    try:
        req_data = await request.json()
        required_params = ["feedback_id"]
        error_response = validate_params(req_data, required_params)
        if(error_response):
            return error_response

        feedback_id = req_data.get("feedback_id")

        feedback = await async_get_by_id("wxapp_feedback", feedback_id)
        if not feedback:
            return Response.not_found(resource="反馈")

        await delete_record("wxapp_feedback", feedback_id)

        return Response.success(details={"message":"反馈删除成功"})
    except Exception as e:
        return Response.error(details={"message": f"删除反馈失败: {str(e)}"}) 