"""
搜索模型
"""
from enum import Enum
from typing import List, Dict, Any, Optional, Union
from pydantic import Field, HttpUrl, field_validator
from datetime import datetime
from api.models.common import BaseAPI, BaseTimeStamp

class SearchType(str, Enum):
    """搜索内容类型"""
    WXAPP = Field("wxapp", description="微信小程序内容（合并帖子和评论）")
    WEBSITE = Field("website", description="普通网站内容")
    WECHAT = Field("wechat", description="微信公众号文章")
    MARKET = Field("market", description="电商平台商品")
    VIDEO = Field("video", description="视频内容")

class SortOrder(str, Enum):
    """排序方式枚举"""
    TIME_DESC = "time_desc"  # 时间降序
    TIME_ASC = "time_asc"  # 时间升序
    RELEVANCE = "relevance"  # 相关度

class FilterType(str, Enum):
    """过滤条件类型"""
    TAG = Field("tag", description="按标签过滤")
    AUTHOR = Field("author", description="按作者过滤")
    DATE_RANGE = Field("date", description="按日期范围过滤")
    PLATFORM = Field("platform", description="按来源平台过滤")
    WX_TYPE = Field("wx_type", description="微信内容类型过滤(post/comment)")
    CONTENT_TYPE = Field("content_type", description="按内容类型过滤")
    STATUS = Field("status", description="按状态过滤")

class Filter(BaseAPI):
    """搜索过滤条件"""
    type: FilterType = Field(..., description="过滤类型")
    values: List[str] = Field(..., min_items=1, description="过滤值列表")
    operator: str = Field("AND", pattern=r"^(AND|OR)$", 
                        description="逻辑运算符：AND-与, OR-或")

class SearchRequest(BaseAPI):
    """搜索请求参数"""
    keyword: str = Field(..., min_length=1, description="搜索关键词")
    page: int = Field(1, ge=1, description="当前页码，从1开始")
    page_size: int = Field(20, ge=1, le=100, description="每页结果数量，最大100")
    filters: List[Filter] = Field(default_factory=list, 
                                description="过滤条件组合")
    sort: str = Field("time_desc", 
                    description="排序方式，可选值：time_desc(时间降序)/time_asc(时间升序)/relevance(相关度)")

class SearchItem(BaseAPI):
    """搜索结果项"""
    id: int = Field(..., description="唯一标识ID")
    type: SearchType = Field(..., description="内容类型")
    content: str = Field(..., min_length=1, description="主要内容/摘要")
    time: datetime = Field(..., description="发布时间/更新时间")
    stats: Dict[str, int] = Field(default_factory=dict,
                                description="统计信息，包含：views-浏览数, likes-点赞数, comments-评论数")
    meta: Dict[str, Any] = Field(default_factory=dict,
                               description="扩展元数据，包含："
                                           "author-作者, platform-来源平台, "
                                           "url-原始链接, wxapp_type-微信内容类型(post/comment), "
                                           "parent_id-关联父ID")

class SearchResponse(BaseAPI):
    """搜索响应结果"""
    total: int = Field(..., ge=0, description="总结果数量")
    results: List[SearchItem] = Field(default_factory=list, 
                                    description="搜索结果列表")
    suggest: List[str] = Field(default_factory=list,
                             description="搜索建议关键词列表")

# 更新导出列表
__all__ = [
    "SearchType",
    "SortOrder",
    "FilterType",
    "Filter",
    "SearchRequest",
    "SearchItem",
    "SearchResponse"
] 