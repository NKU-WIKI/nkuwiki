"""
搜索模型
"""
from typing import List, Optional
from pydantic import Field
from datetime import datetime
from api.models.common import BaseTimeStamp

class Source(BaseTimeStamp):
    """来源"""
    author: str = Field(description="作者")
    platform: str = Field(description="平台")
    original_url: str = Field(description="原始URL")
    tag: Optional[List[str]] = Field(description="标签")
    title: str = Field(description="标题")
    content: str = Field(description="内容")
    image: Optional[List[str]] = Field(description="图片URL列表")
    publish_time: Optional[datetime] = Field(description="发布时间")
    scrape_time: Optional[datetime] = Field(description="爬取时间")
    is_truncated: Optional[bool] = Field(default=False, description="内容是否被截断")
    relevance: Optional[float] = Field(description="相关性")

# 更新导出列表
__all__ = [
    "Source",
] 