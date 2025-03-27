"""
微信小程序评论相关模型
"""
from typing import List, Dict, Any, Optional
from pydantic import Field

from api.models.base import BaseAPIModel, BaseTimeStampModel

class CommentModel(BaseTimeStampModel):
    """评论模型"""
    id: int = Field(..., description="评论ID")
    post_id: int = Field(..., description="帖子ID")
    openid: str = Field(..., description="评论用户openid")
    nick_name: str = Field(..., description="用户昵称")
    avatar: str = Field("", description="用户头像URL")
    content: str = Field(..., description="评论内容")
    parent_id: Optional[int] = Field(None, description="父评论ID（回复）")
    images: List[str] = Field(default_factory=list, description="图片列表")
    like_count: int = Field(0, description="点赞数")
    is_liked: Optional[bool] = Field(False, description="当前用户是否已点赞")
    reply_count: Optional[int] = Field(0, description="回复数量")

class CommentCreateRequest(BaseAPIModel):
    """创建评论请求"""
    post_id: int = Field(..., description="帖子ID")
    content: str = Field(..., description="评论内容", min_length=1)
    parent_id: Optional[int] = Field(None, description="父评论ID")
    images: Optional[List[str]] = Field(None, description="图片列表")

class CommentUpdateRequest(BaseAPIModel):
    """更新评论请求"""
    content: Optional[str] = Field(None, description="评论内容", min_length=1)
    images: Optional[List[str]] = Field(None, description="图片列表")
    status: Optional[int] = Field(None, description="状态：1-正常, 0-禁用")

class CommentQueryParams(BaseAPIModel):
    """评论查询参数"""
    post_id: Optional[int] = Field(None, description="帖子ID")
    openid: Optional[str] = Field(None, description="用户openid")
    parent_id: Optional[int] = Field(None, description="父评论ID")
    status: Optional[int] = Field(1, description="状态筛选")
    order_by: Optional[str] = Field("create_time DESC", description="排序方式")
    limit: int = Field(20, description="返回数量限制", ge=1, le=100)
    offset: int = Field(0, description="偏移量", ge=0)

class CommentListResponse(BaseAPIModel):
    """评论列表响应"""
    comments: List[CommentModel] = Field(default_factory=list, description="评论列表")
    total: int = Field(0, description="总数量")
    limit: int = Field(20, description="每页数量")
    offset: int = Field(0, description="偏移量")

class CommentActionResponse(BaseAPIModel):
    """评论操作响应（点赞等）"""
    comment_id: int = Field(..., description="评论ID")
    success: bool = Field(True, description="操作是否成功")
    message: str = Field("操作成功", description="操作消息")
    action: str = Field(..., description="操作类型，如like, unlike")
    count: Optional[int] = Field(None, description="当前计数（如点赞数）")
    liked: Optional[bool] = Field(None, description="是否已点赞")
    like_count: Optional[int] = Field(None, description="当前点赞数") 