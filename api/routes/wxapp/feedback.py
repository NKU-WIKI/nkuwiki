"""
反馈相关API接口
处理反馈的创建、查询、更新和删除等功能
"""
from typing import Dict, Any, Optional, List
from fastapi import Depends, HTTPException, Query, Path
import json

from api import wxapp_router
from api.common import handle_api_errors, get_api_logger_dep
from api.models.common import SimpleOperationResponse
from api.models.wxapp.feedback import (
    FeedbackModel, 
    FeedbackCreateRequest, 
    FeedbackUpdateRequest,
    FeedbackListResponse
)

@wxapp_router.post("/feedback", response_model=FeedbackModel)
@handle_api_errors("提交反馈")
async def create_feedback(
    request: FeedbackCreateRequest,
    openid: str = Query(..., description="用户openid"),
    api_logger=Depends(get_api_logger_dep)
):
    """
    提交新反馈
    
    用户提交问题反馈、建议或其他类型的反馈
    """
    from api.database.wxapp import feedback_dao
    
    api_logger.debug(f"创建新反馈 (用户: {openid[:8]}...)")
    
    # 构建反馈数据
    feedback_data = {
        "openid": openid,
        "content": request.content,
        "type": request.type,
        "contact": request.contact,
        "images": request.images or [],
        "status": 0,  # 默认为待处理状态(0)
    }
    
    # 处理设备信息
    if request.device_info:
        feedback_data["device_info"] = request.device_info.dict()
    
    # 创建反馈
    feedback_id = await feedback_dao.create_feedback(feedback_data)
    
    if not feedback_id:
        raise HTTPException(status_code=500, detail="反馈创建失败")
    
    # 获取创建的反馈
    feedback = await feedback_dao.get_feedback_by_id(feedback_id)
    
    # 处理datetime类型字段
    if feedback and "create_time" in feedback and feedback["create_time"]:
        feedback["create_time"] = feedback["create_time"].strftime("%Y-%m-%d %H:%M:%S")
    if feedback and "update_time" in feedback and feedback["update_time"]:
        feedback["update_time"] = feedback["update_time"].strftime("%Y-%m-%d %H:%M:%S")
    if feedback and "resolve_time" in feedback and feedback["resolve_time"]:
        feedback["resolve_time"] = feedback["resolve_time"].strftime("%Y-%m-%d %H:%M:%S")
    
    # 处理图片和设备信息的JSON解析
    if feedback and "images" in feedback and isinstance(feedback["images"], str):
        try:
            feedback["images"] = json.loads(feedback["images"])
        except:
            feedback["images"] = []
    
    if feedback and "device_info" in feedback and isinstance(feedback["device_info"], str):
        try:
            feedback["device_info"] = json.loads(feedback["device_info"])
        except:
            feedback["device_info"] = {}
    
    return feedback

@wxapp_router.get("/users/{openid}/feedback", response_model=FeedbackListResponse)
@handle_api_errors("获取用户反馈列表")
async def get_user_feedback(
    openid: str = Path(..., description="用户openid"),
    type: Optional[str] = Query(None, description="反馈类型：bug-问题反馈, suggestion-建议, other-其他"),
    status: Optional[str] = Query(None, description="反馈状态：pending-待处理, processing-处理中, resolved-已解决, rejected-已拒绝"),
    limit: int = Query(20, description="返回记录数量限制", ge=1, le=100),
    offset: int = Query(0, description="分页偏移量", ge=0),
    api_logger=Depends(get_api_logger_dep)
):
    """
    获取用户的反馈列表
    
    支持按类型和状态筛选，分页获取
    """
    from api.database.wxapp import feedback_dao
    
    api_logger.debug(f"获取用户反馈列表 (用户: {openid[:8]}..., 类型: {type}, 状态: {status})")
    
    # 获取反馈列表
    feedback_list, total = await feedback_dao.get_user_feedback(
        openid=openid,
        feedback_type=type,
        status=status,
        limit=limit,
        offset=offset
    )
    
    # 处理datetime类型字段和JSON字段
    for feedback in feedback_list:
        if "create_time" in feedback and feedback["create_time"]:
            feedback["create_time"] = feedback["create_time"].strftime("%Y-%m-%d %H:%M:%S")
        if "update_time" in feedback and feedback["update_time"]:
            feedback["update_time"] = feedback["update_time"].strftime("%Y-%m-%d %H:%M:%S")
        if "resolve_time" in feedback and feedback["resolve_time"]:
            feedback["resolve_time"] = feedback["resolve_time"].strftime("%Y-%m-%d %H:%M:%S")
        
        # 处理图片和设备信息的JSON解析
        if "images" in feedback and isinstance(feedback["images"], str):
            try:
                feedback["images"] = json.loads(feedback["images"])
            except:
                feedback["images"] = []
        
        if "device_info" in feedback and isinstance(feedback["device_info"], str):
            try:
                feedback["device_info"] = json.loads(feedback["device_info"])
            except:
                feedback["device_info"] = {}
    
    return {
        "feedback_list": feedback_list,
        "total": total,
        "limit": limit,
        "offset": offset
    }

@wxapp_router.get("/feedback/{feedback_id}", response_model=FeedbackModel)
@handle_api_errors("获取反馈详情")
async def get_feedback_detail(
    feedback_id: int = Path(..., description="反馈ID"),
    api_logger=Depends(get_api_logger_dep)
):
    """
    获取反馈详情
    
    根据ID获取反馈的详细信息
    """
    from api.database.wxapp import feedback_dao
    
    api_logger.debug(f"获取反馈详情 (ID: {feedback_id})")
    
    # 获取反馈信息
    feedback = await feedback_dao.get_feedback_by_id(feedback_id)
    
    if not feedback:
        raise HTTPException(status_code=404, detail="反馈不存在")
    
    # 处理datetime类型字段
    if "create_time" in feedback and feedback["create_time"]:
        feedback["create_time"] = feedback["create_time"].strftime("%Y-%m-%d %H:%M:%S")
    if "update_time" in feedback and feedback["update_time"]:
        feedback["update_time"] = feedback["update_time"].strftime("%Y-%m-%d %H:%M:%S")
    if "resolve_time" in feedback and feedback["resolve_time"]:
        feedback["resolve_time"] = feedback["resolve_time"].strftime("%Y-%m-%d %H:%M:%S")
    
    # 处理图片和设备信息的JSON解析
    if "images" in feedback and isinstance(feedback["images"], str):
        try:
            feedback["images"] = json.loads(feedback["images"])
        except:
            feedback["images"] = []
    
    if "device_info" in feedback and isinstance(feedback["device_info"], str):
        try:
            feedback["device_info"] = json.loads(feedback["device_info"])
        except:
            feedback["device_info"] = {}
    
    return feedback

@wxapp_router.put("/feedback/{feedback_id}", response_model=FeedbackModel)
@handle_api_errors("更新反馈")
async def update_feedback(
    request: FeedbackUpdateRequest,
    feedback_id: int = Path(..., description="反馈ID"),
    api_logger=Depends(get_api_logger_dep)
):
    """
    更新反馈
    
    更新反馈内容、状态和管理员回复
    """
    from api.database.wxapp import feedback_dao
    import json
    
    api_logger.debug(f"更新反馈 (ID: {feedback_id})")
    
    # 检查反馈是否存在
    feedback = await feedback_dao.get_feedback_by_id(feedback_id)
    
    if not feedback:
        raise HTTPException(status_code=404, detail="反馈不存在")
    
    # 更新反馈
    update_data = request.dict(exclude_unset=True)
    
    # 处理列表和字典类型
    if "images" in update_data and update_data["images"] is not None:
        update_data["images"] = json.dumps(update_data["images"])
    if "device_info" in update_data and update_data["device_info"] is not None:
        update_data["device_info"] = json.dumps(update_data["device_info"])
    
    if update_data:
        await feedback_dao.update_feedback(feedback_id, update_data)
        
    # 获取更新后的反馈
    updated_feedback = await feedback_dao.get_feedback_by_id(feedback_id)
    
    # 处理datetime类型字段
    if "create_time" in updated_feedback and updated_feedback["create_time"]:
        updated_feedback["create_time"] = updated_feedback["create_time"].strftime("%Y-%m-%d %H:%M:%S")
    if "update_time" in updated_feedback and updated_feedback["update_time"]:
        updated_feedback["update_time"] = updated_feedback["update_time"].strftime("%Y-%m-%d %H:%M:%S")
    
    return updated_feedback

@wxapp_router.delete("/feedback/{feedback_id}", response_model=SimpleOperationResponse)
@handle_api_errors("删除反馈")
async def delete_feedback(
    feedback_id: int = Path(..., description="反馈ID"),
    api_logger=Depends(get_api_logger_dep)
):
    """
    删除反馈
    
    标记删除指定反馈
    """
    from api.database.wxapp import feedback_dao
    
    api_logger.debug(f"删除反馈 (ID: {feedback_id})")
    
    # 检查反馈是否存在
    feedback = await feedback_dao.get_feedback_by_id(feedback_id)
    
    if not feedback:
        raise HTTPException(status_code=404, detail="反馈不存在")
    
    # 标记删除
    await feedback_dao.mark_feedback_deleted(feedback_id)
    
    return SimpleOperationResponse(
        success=True,
        message="反馈已删除",
        affected_items=1
    ) 