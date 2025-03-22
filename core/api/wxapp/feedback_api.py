"""
微信小程序意见反馈API
提供意见反馈相关的API接口
"""
from datetime import datetime
from fastapi import HTTPException, Path as PathParam, Depends, Query, Body
from pydantic import BaseModel, Field, validator
from typing import Dict, Any, Optional, List

# 导入通用组件
from core.api.common import get_api_logger, handle_api_errors, create_standard_response
from core.api import wxapp_router as router
from core.api.wxapp.common_utils import format_datetime, prepare_db_data, process_json_fields

# 导入数据库操作函数
from etl.load.py_mysql import (
    insert_record, update_record, delete_record, 
    query_records, count_records, get_record_by_id
)

# 反馈基础模型
class FeedbackBase(BaseModel):
    """反馈基础信息"""
    user_id: str = Field(..., description="用户ID")
    content: str = Field(..., description="反馈内容")
    type: str = Field(..., description="反馈类型: bug-功能异常, feature-功能建议, content-内容问题, other-其他")
    contact: Optional[str] = Field(None, description="联系方式，如邮箱、微信等")
    images: Optional[List[str]] = Field([], description="反馈图片列表")
    device_info: Optional[Dict[str, Any]] = Field(None, description="设备信息")
    
    @validator('type')
    def validate_type(cls, v):
        valid_types = ['bug', 'feature', 'content', 'other']
        if v not in valid_types:
            raise ValueError(f"反馈类型必须是以下之一: {', '.join(valid_types)}")
        return v
    
    @validator('content')
    def validate_content(cls, v):
        if not v or len(v.strip()) < 5:
            raise ValueError("反馈内容必须至少5个字符")
        return v.strip()

class FeedbackCreate(FeedbackBase):
    """创建反馈请求"""
    pass

class FeedbackUpdate(BaseModel):
    """更新反馈请求"""
    status: Optional[int] = Field(None, description="处理状态: 0-待处理, 1-处理中, 2-已处理, 3-已关闭")
    admin_reply: Optional[str] = Field(None, description="管理员回复")

class FeedbackResponse(FeedbackBase):
    """反馈响应"""
    id: int
    create_time: datetime
    update_time: Optional[datetime] = None
    status: int = 0  # 处理状态: 0-待处理, 1-处理中, 2-已处理, 3-已关闭
    admin_reply: Optional[str] = None

# API端点
@router.post("/feedback", response_model=Dict[str, Any], summary="提交反馈")
@handle_api_errors("提交反馈")
async def create_feedback(
    feedback: FeedbackCreate,
    api_logger=Depends(get_api_logger)
):
    """创建新反馈"""
    api_logger.debug(f"创建反馈: {feedback}")
    
    # 准备数据
    feedback_data = prepare_db_data(feedback.dict(), is_create=True)
    
    # 处理JSON字段
    if 'images' in feedback_data and isinstance(feedback_data['images'], list):
        feedback_data['images'] = process_json_fields(feedback_data['images'])
    
    if 'device_info' in feedback_data and isinstance(feedback_data['device_info'], dict):
        feedback_data['device_info'] = process_json_fields(feedback_data['device_info'])
    
    # 插入记录
    feedback_id = insert_record('wxapp_feedback', feedback_data)
    if not feedback_id:
        raise HTTPException(status_code=500, detail="创建反馈失败")
    
    # 获取创建的反馈
    created_feedback = get_record_by_id('wxapp_feedback', feedback_id)
    if not created_feedback:
        raise HTTPException(status_code=404, detail="找不到创建的反馈")
    
    # 处理日期格式
    if 'create_time' in created_feedback:
        created_feedback['create_time'] = str(created_feedback['create_time'])
    if 'update_time' in created_feedback:
        created_feedback['update_time'] = str(created_feedback['update_time'])
    
    # 处理JSON字段
    if 'images' in created_feedback and isinstance(created_feedback['images'], str):
        try:
            created_feedback['images'] = eval(created_feedback['images'])
        except:
            created_feedback['images'] = []
    
    if 'device_info' in created_feedback and isinstance(created_feedback['device_info'], str):
        try:
            created_feedback['device_info'] = eval(created_feedback['device_info'])
        except:
            created_feedback['device_info'] = {}
    
    return create_standard_response(
        code=200,
        message="提交反馈成功",
        data=created_feedback
    )

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
    
    # 处理日期格式
    if 'create_time' in feedback:
        feedback['create_time'] = str(feedback['create_time'])
    if 'update_time' in feedback:
        feedback['update_time'] = str(feedback['update_time'])
    
    # 处理JSON字段
    if 'images' in feedback and isinstance(feedback['images'], str):
        try:
            feedback['images'] = eval(feedback['images'])
        except:
            feedback['images'] = []
    
    if 'device_info' in feedback and isinstance(feedback['device_info'], str):
        try:
            feedback['device_info'] = eval(feedback['device_info'])
        except:
            feedback['device_info'] = {}
    
    return create_standard_response(
        code=200,
        message="获取反馈详情成功",
        data=feedback
    )

@router.get("/users/{user_id}/feedback", response_model=Dict[str, Any], summary="获取用户反馈列表")
@handle_api_errors("获取用户反馈列表")
async def list_user_feedback(
    user_id: str = PathParam(..., description="用户ID"),
    status: Optional[int] = Query(None, description="处理状态过滤: 0-待处理, 1-处理中, 2-已处理, 3-已关闭"),
    limit: int = Query(20, description="返回记录数量限制", ge=1, le=100),
    offset: int = Query(0, description="分页偏移量", ge=0),
    api_logger=Depends(get_api_logger)
):
    """获取用户反馈列表"""
    api_logger.debug(f"获取用户ID={user_id}的反馈列表, 状态={status}")
    
    try:
        # 构建查询条件
        conditions = {"user_id": user_id}
        if status is not None:
            conditions["status"] = status
        
        # 查询反馈
        feedbacks = query_records(
            'wxapp_feedback',
            conditions=conditions,
            order_by='create_time DESC',
            limit=limit,
            offset=offset
        )
        
        # 查询总反馈数量
        total_count = count_records('wxapp_feedback', {"user_id": user_id})
        
        # 处理反馈数据
        for feedback in feedbacks:
            # 处理日期格式
            if 'create_time' in feedback:
                feedback['create_time'] = str(feedback['create_time'])
            if 'update_time' in feedback:
                feedback['update_time'] = str(feedback['update_time'])
            
            # 处理JSON字段
            if 'images' in feedback and isinstance(feedback['images'], str):
                try:
                    feedback['images'] = eval(feedback['images'])
                except:
                    feedback['images'] = []
            
            if 'device_info' in feedback and isinstance(feedback['device_info'], str):
                try:
                    feedback['device_info'] = eval(feedback['device_info'])
                except:
                    feedback['device_info'] = {}
        
        return create_standard_response(
            code=200,
            message="获取反馈列表成功",
            data={
                "feedbacks": feedbacks,
                "total": total_count
            }
        )
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
    """更新反馈信息，主要用于管理员处理反馈"""
    # 检查反馈是否存在
    feedback = get_record_by_id('wxapp_feedback', feedback_id)
    if not feedback:
        raise HTTPException(status_code=404, detail="反馈不存在")
    
    # 过滤掉None值
    update_data = {k: v for k, v in feedback_update.dict().items() if v is not None}
    if not update_data:
        return create_standard_response(
            code=200,
            message="无需更新",
            data=feedback
        )
    
    # 添加更新时间
    update_data['update_time'] = format_datetime(datetime.now())
    
    # 更新记录
    api_logger.debug(f"更新反馈ID={feedback_id}: {update_data}")
    success = update_record('wxapp_feedback', feedback_id, update_data)
    if not success:
        raise HTTPException(status_code=500, detail="更新反馈失败")
    
    # 获取更新后的反馈
    updated_feedback = get_record_by_id('wxapp_feedback', feedback_id)
    
    # 处理日期格式
    if 'create_time' in updated_feedback:
        updated_feedback['create_time'] = str(updated_feedback['create_time'])
    if 'update_time' in updated_feedback:
        updated_feedback['update_time'] = str(updated_feedback['update_time'])
    
    # 处理JSON字段
    if 'images' in updated_feedback and isinstance(updated_feedback['images'], str):
        try:
            updated_feedback['images'] = eval(updated_feedback['images'])
        except:
            updated_feedback['images'] = []
    
    if 'device_info' in updated_feedback and isinstance(updated_feedback['device_info'], str):
        try:
            updated_feedback['device_info'] = eval(updated_feedback['device_info'])
        except:
            updated_feedback['device_info'] = {}
    
    return create_standard_response(
        code=200,
        message="更新反馈成功",
        data=updated_feedback
    ) 