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
    update_time: Optional[datetime] = Field(description="更新时间")
    create_time: Optional[datetime] = Field(description="发布时间")
    scrape_time: Optional[datetime] = Field(description="爬取时间")
    is_truncated: Optional[bool] = Field(default=False, description="内容是否被截断")
    is_official: Optional[bool] = Field(default=False, description="是否为官方信息")
    relevance: Optional[float] = Field(description="相关性")

class Insight(BaseTimeStamp):
    """洞察信息模型"""
    id: int
    title: str = Field(description="洞察标题")
    content: str = Field(description="洞察主体内容")
    category: Optional[str] = Field(description="洞察分类")
    insight_date: datetime = Field(description="洞察相关的日期")

# 更新导出列表
__all__ = [
    "Source",
    "Insight",
] 