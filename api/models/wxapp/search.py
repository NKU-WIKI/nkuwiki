"""
微信小程序搜索模型
"""
from typing import List
from pydantic import Field
from api.models.base import BaseAPIModel
from api.models.search import SearchResult

class WxappSearchResponse(BaseAPIModel):
    """微信小程序搜索响应模型"""
    results: List[SearchResult] = Field(default_factory=list, description="搜索结果列表")
    total: int = Field(0, description="结果总数")
    keyword: str = Field(..., description="搜索关键词") 