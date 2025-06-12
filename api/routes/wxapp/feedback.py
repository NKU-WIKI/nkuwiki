"""
微信小程序用户反馈API
"""
from typing import List, Dict, Any, Optional
from fastapi import Query, APIRouter
from api.models.common import Response, Request, validate_params
from etl.load.db_core import async_execute_custom_query, async_insert
from core.utils.logger import register_logger
import json

router = APIRouter()
logger = register_logger('api.routes.wxapp.feedback')

@router.get("/feedback/detail")
async def get_feedback_detail(
    feedback_id: str = Query(..., description="反馈ID")
):
    """获取用户反馈详情"""
    if(not feedback_id):
        return Response.bad_request(details={"message": "缺少feedback_id参数"})
    try:
        # 使用直接SQL查询获取反馈详情
        sql = "SELECT * FROM wxapp_feedback WHERE id = %s"
        feedback = await async_execute_custom_query(sql, [feedback_id])
        
        if not feedback:
            return Response.not_found(resource="反馈")
            
        return Response.success(data=feedback[0])
    except Exception as e:
        logger.error(f"获取反馈详情失败: {e}")
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
        # 构建查询条件
        conditions = ["openid = %s"]
        params = [openid]
        
        if type:
            conditions.append("type = %s")
            params.append(type)
            
        if status:
            conditions.append("status = %s")
            params.append(status)
            
        # 构建SQL
        where_clause = " AND ".join(conditions)
        sql = f"""
            SELECT * FROM wxapp_feedback 
            WHERE {where_clause} 
            ORDER BY create_time DESC
        """
        
        # 执行查询
        feedbacks = await async_execute_custom_query(sql, params)
        
        return Response.success(data={"feedbacks": feedbacks or []})
    except Exception as e:
        logger.error(f"获取用户反馈列表失败: {e}")
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
        type = req_data.get("type", "")
        image = req_data.get("image", [])
        contact = req_data.get("contact", "")

        # 使用直接SQL插入反馈
        sql = """
            INSERT INTO wxapp_feedback 
            (openid, content, type, image, contact, create_time, update_time) 
            VALUES (%s, %s, %s, %s, %s, NOW(), NOW())
        """
        
        # 执行插入并返回ID
        result = await async_execute_custom_query(
            sql, 
            [openid, content, type, json.dumps(image) if isinstance(image, list) else image, contact],
            fetch=True
        )
        
        feedback_id = result[0]["id"] if result and "id" in result[0] else None
        if not feedback_id:
            # 回退到原始插入方法
            feedback_data = {
                "openid": openid,
                "content": content,
                "type": type,
                "image": image,
                "contact": contact
            }
            
            feedback_id = await async_insert("wxapp_feedback", feedback_data)

        logger.debug(f"创建反馈成功: {feedback_id}")
        return Response.success(details={"feedback_id": feedback_id, "message": "反馈创建成功"})
    except Exception as e:
        logger.error(f"创建反馈失败: {e}")
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

        # 检查反馈是否存在
        feedback_sql = "SELECT * FROM wxapp_feedback WHERE id = %s"
        feedback = await async_execute_custom_query(feedback_sql, [feedback_id])
        
        if not feedback:
            return Response.not_found(resource="反馈")

        # 提取可更新字段
        allowed_fields = ["content", "type", "image", "contact", "status", "reply"]
        update_fields = []
        update_params = []
        
        for field in allowed_fields:
            if field in req_data:
                update_fields.append(f"{field} = %s")
                # 特殊处理image字段
                if field == "image" and isinstance(req_data[field], list):
                    update_params.append(json.dumps(req_data[field]))
                else:
                    update_params.append(req_data[field])
        
        if not update_fields:
            return Response.bad_request(details={"message": "没有提供可更新的字段"})
            
        update_fields.append("update_time = NOW()")
        
        # 构建更新SQL
        set_clause = ", ".join(update_fields)
        update_sql = f"""
            UPDATE wxapp_feedback 
            SET {set_clause} 
            WHERE id = %s
        """
        update_params.append(feedback_id)
        
        # 执行更新
        await async_execute_custom_query(update_sql, update_params, fetch=False)

        return Response.success(details={"message": "反馈更新成功"})
    except Exception as e:
        logger.error(f"更新反馈失败: {e}")
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

        # 检查反馈是否存在
        feedback_sql = "SELECT * FROM wxapp_feedback WHERE id = %s"
        feedback = await async_execute_custom_query(feedback_sql, [feedback_id])
        
        if not feedback:
            return Response.not_found(resource="反馈")

        # 删除反馈
        delete_sql = "DELETE FROM wxapp_feedback WHERE id = %s"
        await async_execute_custom_query(delete_sql, [feedback_id], fetch=False)

        return Response.success(details={"message": "反馈删除成功"})
    except Exception as e:
        logger.error(f"删除反馈失败: {e}")
        return Response.error(details={"message": f"删除反馈失败: {str(e)}"}) 