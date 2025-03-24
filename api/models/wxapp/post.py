"""
微信小程序帖子相关模型
"""
from typing import List, Dict, Any, Optional
from pydantic import Field
from api.models.base import BaseAPIModel, BaseTimeStampModel

class LocationInfo(BaseAPIModel):
    """位置信息模型"""
    latitude: float = Field(..., description="纬度")
    longitude: float = Field(..., description="经度")
    name: Optional[str] = Field(None, description="位置名称")
    address: Optional[str] = Field(None, description="详细地址")
    
class PostModel(BaseTimeStampModel):
    """帖子模型"""
    id: int = Field(..., description="帖子ID")
    openid: str = Field(..., description="发布者openid")
    nick_name: str = Field(..., description="发布者昵称")
    avatar: str = Field("", description="发布者头像")
    title: str = Field(..., description="帖子标题")
    content: str = Field(..., description="帖子内容")
    images: List[str] = Field(default_factory=list, description="帖子图片列表")
    tags: List[str] = Field(default_factory=list, description="帖子标签")
    category_id: int = Field(0, description="分类ID")
    location: Optional[Dict[str, Any]] = Field(None, description="位置信息")
    view_count: int = Field(0, description="浏览次数")
    like_count: int = Field(0, description="点赞次数")
    comment_count: int = Field(0, description="评论次数")
    favorite_count: int = Field(0, description="收藏次数")
    status: int = Field(1, description="状态：0-草稿，1-已发布，2-审核中，3-已删除")
    is_liked: Optional[bool] = Field(False, description="当前用户是否已点赞")
    is_favorited: Optional[bool] = Field(False, description="当前用户是否已收藏")
    
class PostCreateRequest(BaseAPIModel):
    """创建帖子请求"""
    title: str = Field(..., description="帖子标题")
    content: str = Field(..., description="帖子内容")
    images: Optional[List[str]] = Field(None, description="帖子图片列表")
    tags: Optional[List[str]] = Field(None, description="帖子标签")
    category_id: int = Field(0, description="分类ID")
    location: Optional[Dict[str, Any]] = Field(None, description="位置信息")
    
class PostUpdateRequest(BaseAPIModel):
    """更新帖子请求"""
    title: Optional[str] = Field(None, description="帖子标题")
    content: Optional[str] = Field(None, description="帖子内容")
    images: Optional[List[str]] = Field(None, description="帖子图片列表")
    tags: Optional[List[str]] = Field(None, description="帖子标签")
    category_id: Optional[int] = Field(None, description="分类ID")
    status: Optional[int] = Field(None, description="状态：0-草稿，1-已发布，2-审核中，3-已删除")
    
class PostQueryParams(BaseAPIModel):
    """帖子查询参数"""
    openid: Optional[str] = Field(None, description="作者openid")
    category_id: Optional[int] = Field(None, description="分类ID")
    tags: Optional[List[str]] = Field(None, description="标签列表")
    status: Optional[int] = Field(1, description="状态：0-草稿，1-已发布，2-审核中，3-已删除")
    keyword: Optional[str] = Field(None, description="关键词搜索")
    order_by: Optional[str] = Field("create_time DESC", description="排序方式")
    limit: int = Field(20, description="返回数量限制", ge=1, le=100)
    offset: int = Field(0, description="偏移量", ge=0)

class PostListResponse(BaseAPIModel):
    """帖子列表响应"""
    posts: List[PostModel] = Field(default_factory=list, description="帖子列表")
    total: int = Field(0, description="总数量")
    limit: int = Field(20, description="每页数量")
    offset: int = Field(0, description="偏移量")

class BatchOperationResponse(BaseAPIModel):
    """批量操作响应"""
    success: bool = Field(True, description="操作是否成功")
    message: str = Field("操作成功", description="操作消息")
    count: int = Field(0, description="受影响的记录数")
    
class PostActionResponse(BaseAPIModel):
    """帖子操作响应（点赞、收藏等）"""
    post_id: int = Field(..., description="帖子ID")
    success: bool = Field(True, description="操作是否成功")
    action: str = Field(..., description="操作类型，如like, unlike, favorite, unfavorite")
    count: int = Field(0, description="当前计数（如点赞数、收藏数）") 