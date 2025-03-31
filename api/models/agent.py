"""
智能体聊天相关模型
"""
from typing import List, Dict, Any, Optional
from pydantic import Field
from api.models.common import BaseAPI

class Source(BaseAPI):
    """内容来源模型"""
    original_url: HttpUrl = Field(..., description="原始URL")
    title: str = Field(..., description="标题")
    content: str = Field(..., description="内容")
    author: str = Field(..., description="作者")
    view_count: int = Field(0, description="阅读数")
    like_count: int = Field(0, description="点赞数")
    platform: str = Field(..., description="平台")
    tags: List[str] = Field(default_factory=list, description="标签")
    publish_time: Optional[datetime] = Field(None, description="发布时间")
    scrape_time: Optional[datetime] = Field(None, description="爬取时间")
    meta: Dict[str, Any] = Field(default_factory=dict, description="扩展元数据")