"""
微信小程序评论API
提供评论管理相关的API接口
"""
from fastapi import HTTPException, Path as PathParam, Depends, Query
from pydantic import BaseModel, Field, validator
from typing import Dict, Any, Optional, List
import json

# 导入通用组件
from core.api.common import get_api_logger, handle_api_errors, create_standard_response
from core.api.wxapp import router
from core.api.wxapp.common_utils import format_datetime, prepare_db_data, process_json_fields

# 导入数据库操作函数
from etl.load.py_mysql import (
    insert_record, update_record, delete_record, 
    query_records, count_records, get_record_by_id
)

# 评论模型
class CommentBase(BaseModel):
    """评论基础信息"""
    user_id: str = Field(..., description="评论用户ID")
    post_id: int = Field(..., description="帖子ID")
    content: str = Field(..., description="评论内容", min_length=1, max_length=1000)
    parent_id: Optional[int] = Field(None, description="父评论ID，用于回复")
    
    @validator('content')
    def validate_content(cls, v):
        if not v or not v.strip():
            raise ValueError("评论内容不能为空")
        return v.strip()

class CommentCreate(CommentBase):
    """创建评论请求"""
    pass

class CommentUpdate(BaseModel):
    """更新评论请求"""
    content: Optional[str] = None
    status: Optional[int] = None
    
    @validator('content')
    def validate_content(cls, v):
        if v is not None and not v.strip():
            raise ValueError("评论内容不能为空")
        return v.strip() if v else None

class CommentResponse(CommentBase):
    """评论响应"""
    id: int
    create_time: str
    update_time: str
    like_count: int = 0
    liked_users: List[int] = []
    status: int = 1

# API端点
@router.post("/comments", response_model=Dict[str, Any], summary="创建评论")
@handle_api_errors("创建评论")
async def create_comment(
    comment: CommentCreate,
    api_logger=Depends(get_api_logger)
):
    """创建新评论"""
    # 检查帖子是否存在
    post = get_record_by_id('wxapp_posts', comment.post_id)
    if not post:
        raise HTTPException(status_code=404, detail="帖子不存在")
    
    # 如果是回复，检查父评论是否存在
    if comment.parent_id:
        parent_comment = get_record_by_id('wxapp_comments', comment.parent_id)
        if not parent_comment:
            raise HTTPException(status_code=404, detail="父评论不存在")
    
    # 准备数据
    comment_data = comment.dict()
    
    # 初始化点赞用户
    comment_data['liked_users'] = json.dumps([])
    comment_data['like_count'] = 0
    comment_data['status'] = 1
    
    # 准备数据库数据
    comment_data = prepare_db_data(comment_data, is_create=True)
    
    # 插入记录
    comment_id = insert_record('wxapp_comments', comment_data)
    if not comment_id:
        raise HTTPException(status_code=500, detail="创建评论失败")
    
    # 更新帖子评论数
    post_data = process_json_fields(post)
    comment_count = post_data.get('comment_count', 0) + 1
    
    update_success = update_record('wxapp_posts', comment.post_id, {
        'comment_count': comment_count,
        'update_time': format_datetime(None)  # 使用当前时间
    })
    
    if not update_success:
        api_logger.warning(f"更新帖子评论数失败，帖子ID: {comment.post_id}")
    
    # 获取创建的评论
    created_comment = get_record_by_id('wxapp_comments', comment_id)
    if not created_comment:
        raise HTTPException(status_code=404, detail="找不到创建的评论")
    
    # 处理JSON字段
    created_comment = process_json_fields(created_comment)
    
    return create_standard_response(created_comment)

@router.get("/comments/{comment_id}", response_model=Dict[str, Any], summary="获取评论详情")
@handle_api_errors("获取评论")
async def get_comment(
    comment_id: int = PathParam(..., description="评论ID"),
    api_logger=Depends(get_api_logger)
):
    """获取指定评论详情"""
    comment = get_record_by_id('wxapp_comments', comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail="评论不存在")
    
    # 处理JSON字段
    comment = process_json_fields(comment)
    
    return create_standard_response(comment)

@router.get("/comments", response_model=Dict[str, Any], summary="查询评论列表")
@handle_api_errors("查询评论列表")
async def list_comments(
    post_id: int = Query(..., description="帖子ID"),
    parent_id: Optional[int] = Query(None, description="父评论ID（回复）"),
    user_id: Optional[str] = Query(None, description="用户ID"),
    limit: int = Query(20, description="返回记录数量限制", ge=1, le=100),
    offset: int = Query(0, description="分页偏移量", ge=0),
    status: Optional[int] = Query(1, description="评论状态: 1-正常, 0-禁用"),
    order_by: str = Query("create_time ASC", description="排序方式"),
    api_logger=Depends(get_api_logger)
):
    """获取评论列表"""
    conditions = {}
    
    # 添加筛选条件
    if post_id is not None:
        conditions['post_id'] = post_id
        
    if user_id is not None:
        conditions['user_id'] = user_id
        
    if parent_id is not None:
        conditions['parent_id'] = parent_id
    
    if status is not None:
        conditions['status'] = status
    
    # 查询评论列表
    comments = query_records(
        'wxapp_comments',
        conditions=conditions,
        order_by=order_by,
        limit=limit,
        offset=offset
    )
    
    # 处理JSON字段
    comments = [process_json_fields(comment) for comment in comments]
    
    # 获取总数
    total_count = count_records('wxapp_comments', conditions)
    
    return create_standard_response({
        "comments": comments,
        "total": total_count,
        "limit": limit,
        "offset": offset
    })

@router.put("/comments/{comment_id}", response_model=Dict[str, Any], summary="更新评论")
@handle_api_errors("更新评论")
async def update_comment(
    comment_update: CommentUpdate,
    comment_id: int = PathParam(..., description="评论ID"),
    api_logger=Depends(get_api_logger)
):
    """更新评论信息"""
    # 检查评论是否存在
    comment = get_record_by_id('wxapp_comments', comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail="评论不存在")
    
    # 过滤掉None值
    update_data = {k: v for k, v in comment_update.dict().items() if v is not None}
    if not update_data:
        # 没有需要更新的字段，返回原评论
        return create_standard_response(process_json_fields(comment))
    
    # 添加更新时间
    update_data = prepare_db_data(update_data, is_create=False)
    
    # 更新记录
    success = update_record('wxapp_comments', comment_id, update_data)
    if not success:
        raise HTTPException(status_code=500, detail="更新评论失败")
    
    # 获取更新后的评论
    updated_comment = get_record_by_id('wxapp_comments', comment_id)
    
    # 处理JSON字段
    updated_comment = process_json_fields(updated_comment)
    
    return create_standard_response(updated_comment)

@router.delete("/comments/{comment_id}", response_model=Dict[str, Any], summary="删除评论")
@handle_api_errors("删除评论")
async def delete_comment(
    comment_id: int = PathParam(..., description="评论ID"),
    api_logger=Depends(get_api_logger)
):
    """删除评论（标记删除）"""
    # 检查评论是否存在
    comment = get_record_by_id('wxapp_comments', comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail="评论不存在")
    
    # 获取帖子信息，以便更新评论计数
    post_id = comment.get('post_id')
    post = None
    if post_id:
        post = get_record_by_id('wxapp_posts', post_id)
    
    # 标记删除
    success = update_record('wxapp_comments', comment_id, {
        'is_deleted': 1,
        'status': 0,
        'update_time': format_datetime(None)  # 使用当前时间
    })
    
    if not success:
        raise HTTPException(status_code=500, detail="删除评论失败")
    
    # 更新帖子评论数
    if post:
        post_data = process_json_fields(post)
        comment_count = max(0, post_data.get('comment_count', 0) - 1)
        
        update_success = update_record('wxapp_posts', post_id, {
            'comment_count': comment_count,
            'update_time': format_datetime(None)  # 使用当前时间
        })
        
        if not update_success:
            api_logger.warning(f"更新帖子评论数失败，帖子ID: {post_id}")
    
    return create_standard_response({
        "success": True,
        "message": "评论已删除"
    })

@router.post("/comments/{comment_id}/like", response_model=Dict[str, Any], summary="点赞/取消点赞评论")
@handle_api_errors("点赞评论")
async def like_comment(
    comment_id: int = PathParam(..., description="评论ID"),
    user_id: str = Query(..., description="用户ID"),
    api_logger=Depends(get_api_logger)
):
    """点赞或取消点赞评论"""
    # 检查评论是否存在
    comment = get_record_by_id('wxapp_comments', comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail="评论不存在")
    
    # 处理JSON字段
    comment = process_json_fields(comment)
    
    # 获取当前点赞用户列表
    liked_users = comment.get('liked_users', [])
    
    # 判断是点赞还是取消点赞
    if user_id in liked_users:
        # 取消点赞
        liked_users.remove(user_id)
        like_count = max(0, comment.get('like_count', 0) - 1)
        action = "取消点赞"
    else:
        # 点赞
        liked_users.append(user_id)
        like_count = comment.get('like_count', 0) + 1
        action = "点赞"
    
    # 更新评论
    success = update_record('wxapp_comments', comment_id, {
        'liked_users': json.dumps(liked_users),
        'like_count': like_count,
        'update_time': format_datetime(None)  # 使用当前时间
    })
    
    if not success:
        raise HTTPException(status_code=500, detail=f"{action}失败")
    
    return create_standard_response({
        "success": True,
        "message": f"{action}成功",
        "liked": user_id in liked_users,
        "like_count": like_count
    }) 