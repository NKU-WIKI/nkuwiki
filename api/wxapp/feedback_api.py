"""
微信小程序用户反馈API
提供用户反馈相关的API接口
"""
from datetime import datetime
from fastapi import FastAPI, HTTPException, Path as PathParam, Depends, Query, Body
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

# 反馈基础模型
class FeedbackBase(BaseModel):
    """反馈基础信息"""
    openid: str = Field(..., description="用户openid")
    content: str = Field(..., description="反馈内容")
    type: str = Field(..., description="反馈类型: bug-问题反馈, suggestion-建议, other-其他")
    contact: Optional[str] = Field(None, description="联系方式")
    images: List[str] = Field([], description="图片URL列表")
    device_info: Dict[str, Any] = Field({}, description="设备信息")
    
    @validator('type')
    def validate_type(cls, v):
        valid_types = ['bug', 'suggestion', 'other']
        if v not in valid_types:
            raise ValueError(f"反馈类型必须是以下之一: {', '.join(valid_types)}")
        return v

class FeedbackCreate(FeedbackBase):
    """创建反馈请求"""
    pass

class FeedbackUpdate(BaseModel):
    """更新反馈请求"""
    content: Optional[str] = None
    status: Optional[str] = None
    admin_reply: Optional[str] = None
    extra: Optional[Dict[str, Any]] = None

class FeedbackResponse(FeedbackBase):
    """反馈响应"""
    id: int
    create_time: datetime
    update_time: datetime
    status: str = "pending"
    admin_reply: Optional[str] = None
    platform: str = "wxapp"
    is_deleted: int = 0
    extra: Optional[Dict[str, Any]] = None

# API端点
@router.post("/feedback", response_model=Dict[str, Any], summary="提交反馈")
@handle_api_errors("提交反馈")
async def create_feedback(
    feedback: FeedbackCreate,
    api_logger=Depends(get_api_logger)
):
    """提交用户反馈"""
    # 准备数据
    feedback_data = feedback.dict()
    
    # 添加默认值
    feedback_data['status'] = 'pending'
    feedback_data['platform'] = 'wxapp'
    feedback_data['is_deleted'] = 0
    feedback_data['extra'] = json.dumps({})
    
    # 转换List和Dict为JSON字符串
    if 'images' in feedback_data:
        feedback_data['images'] = json.dumps(feedback_data['images'])
    if 'device_info' in feedback_data:
        feedback_data['device_info'] = json.dumps(feedback_data['device_info'])
    
    feedback_data = prepare_db_data(feedback_data, is_create=True)
    
    # 插入记录
    api_logger.debug(f"创建反馈: {feedback_data}")
    feedback_id = insert_record('wxapp_feedback', feedback_data)
    if not feedback_id:
        raise HTTPException(status_code=500, detail="提交反馈失败")
    
    # 获取创建的反馈
    created_feedback = get_record_by_id('wxapp_feedback', feedback_id)
    if not created_feedback:
        raise HTTPException(status_code=404, detail="找不到创建的反馈")
    
    # 处理JSON字段
    created_feedback = process_json_fields(created_feedback)
    
    return create_standard_response(created_feedback)

@router.get("/feedback/{feedback_id}", response_model=Dict[str, Any], summary="获取反馈详情")
@handle_api_errors("获取反馈")
async def get_feedback(
    feedback_id: int = PathParam(..., description="反馈ID"),
    api_logger=Depends(get_api_logger)
):
    """获取指定反馈详情"""
    feedback = get_record_by_id('wxapp_feedback', feedback_id)
    if not feedback:
        raise HTTPException(status_code=404, detail="反馈不存在")
    
    # 处理JSON字段
    feedback = process_json_fields(feedback)
    
    return create_standard_response(feedback)

@router.get("/users/{user_id}/feedback", response_model=Dict[str, Any], summary="获取用户反馈列表")
@handle_api_errors("获取用户反馈列表")
async def list_user_feedback(
    user_id: str = PathParam(..., description="用户openid"),
    type: Optional[str] = Query(None, description="反馈类型: bug-问题反馈, suggestion-建议, other-其他"),
    status: Optional[str] = Query(None, description="反馈状态: pending-待处理, processing-处理中, resolved-已解决, rejected-已拒绝"),
    limit: int = Query(20, description="返回记录数量限制", ge=1, le=100),
    offset: int = Query(0, description="分页偏移量", ge=0),
    api_logger=Depends(get_api_logger)
):
    """获取用户反馈列表"""
    api_logger.debug(f"获取用户ID={user_id}的反馈列表, 类型={type}, 状态={status}")
    
    # 构建查询条件
    conditions = {"openid": user_id, "is_deleted": 0}
    if type:
        conditions["type"] = type
    if status:
        conditions["status"] = status
    
    # 查询反馈
    try:
        feedback_list = query_records(
            'wxapp_feedback',
            conditions=conditions,
            order_by='create_time DESC',
            limit=limit,
            offset=offset
        )
        
        # 查询总反馈数量
        total_count = count_records('wxapp_feedback', conditions)
        
        # 处理反馈数据
        for feedback in feedback_list:
            # 处理JSON字段
            feedback = process_json_fields(feedback)
        
        return create_standard_response({
            'feedback_list': feedback_list,
            'total': total_count,
            'limit': limit,
            'offset': offset
        })
    except Exception as e:
        api_logger.error(f"获取反馈列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取反馈列表失败: {str(e)}")

@router.put("/feedback/{feedback_id}", response_model=Dict[str, Any], summary="更新反馈")
@handle_api_errors("更新反馈")
async def update_feedback(
    feedback_update: FeedbackUpdate,
    feedback_id: int = PathParam(..., description="反馈ID"),
    api_logger=Depends(get_api_logger)
):
    """更新反馈信息"""
    # 检查反馈是否存在
    feedback = get_record_by_id('wxapp_feedback', feedback_id)
    if not feedback:
        raise HTTPException(status_code=404, detail="反馈不存在")
    
    # 过滤掉None值
    update_data = {k: v for k, v in feedback_update.dict().items() if v is not None}
    if not update_data:
        # 没有需要更新的字段，返回原反馈
        return create_standard_response(process_json_fields(feedback))
    
    # 验证status字段
    if 'status' in update_data:
        valid_statuses = ['pending', 'processing', 'resolved', 'rejected']
        if update_data['status'] not in valid_statuses:
            raise HTTPException(status_code=400, detail=f"反馈状态必须是以下之一: {', '.join(valid_statuses)}")
    
    # 处理extra字段
    if 'extra' in update_data:
        update_data['extra'] = json.dumps(update_data['extra'])
    
    # 添加更新时间
    update_data = prepare_db_data(update_data, is_create=False)
    
    # 更新记录
    success = update_record('wxapp_feedback', feedback_id, update_data)
    if not success:
        raise HTTPException(status_code=500, detail="更新反馈失败")
    
    # 获取更新后的反馈
    updated_feedback = get_record_by_id('wxapp_feedback', feedback_id)
    
    # 处理JSON字段
    updated_feedback = process_json_fields(updated_feedback)
    
    return create_standard_response(updated_feedback)

@router.delete("/feedback/{feedback_id}", response_model=Dict[str, Any], summary="删除反馈")
@handle_api_errors("删除反馈")
async def delete_feedback(
    feedback_id: int = PathParam(..., description="反馈ID"),
    api_logger=Depends(get_api_logger)
):
    """删除反馈（标记删除）"""
    # 检查反馈是否存在
    feedback = get_record_by_id('wxapp_feedback', feedback_id)
    if not feedback:
        raise HTTPException(status_code=404, detail="反馈不存在")
    
    # 标记删除
    success = update_record('wxapp_feedback', feedback_id, {
        'is_deleted': 1,
        'update_time': format_datetime(None)
    })
    
    if not success:
        raise HTTPException(status_code=500, detail="删除反馈失败")
    
    return create_standard_response({
        'success': True,
        'message': '反馈已删除'
    }) 