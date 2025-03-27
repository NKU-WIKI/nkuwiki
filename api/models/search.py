"""
搜索模型定义
包含所有与搜索相关的请求和响应模型
"""
from typing import List, Dict, Any, Optional
from pydantic import Field, HttpUrl, field_validator
from datetime import datetime
from api.models.base import BaseAPIModel, BaseTimeStampModel

class SearchQuery(BaseAPIModel):
    """通用搜索查询"""
    query: str = Field(..., min_length=1, description="搜索查询词")
    limit: int = Field(10, ge=1, le=100, description="返回结果数量限制")
    offset: int = Field(0, ge=0, description="起始偏移量")
    filters: Dict[str, Any] = Field(default_factory=dict, description="过滤条件")

class SearchResult(BaseAPIModel):
    """通用搜索结果项"""
    id: str = Field(..., description="结果ID")
    title: str = Field(..., description="标题")
    content: str = Field(..., description="内容")
    score: float = Field(..., ge=0, le=1, description="相关度得分")
    source: str = Field(..., description="来源")
    url: Optional[HttpUrl] = Field(None, description="URL")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")

class SearchResponse(BaseAPIModel):
    """通用搜索响应"""
    results: List[SearchResult] = Field(..., description="搜索结果列表")
    total: int = Field(..., ge=0, description="总结果数")
    query: str = Field(..., description="搜索查询词")

class DocumentIndexRequest(BaseAPIModel):
    """文档索引请求"""
    file_id: str = Field(..., description="文件ID")
    file_name: str = Field(..., description="文件名称")
    openid: str = Field(..., description="用户openid")
    custom_metadata: Dict[str, Any] = Field(default_factory=dict, description="自定义元数据")

class DocumentIndexResponse(BaseAPIModel):
    """文档索引响应"""
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="响应消息")
    document_id: Optional[str] = Field(None, description="文档ID")
    suggested_keywords: List[str] = Field(default_factory=list, description="建议关键词")

class PostSearchRequest(BaseAPIModel):
    """帖子搜索请求"""
    keyword: Optional[str] = Field(None, description="关键词，搜索标题和内容")
    title: Optional[str] = Field(None, description="标题关键词")
    content: Optional[str] = Field(None, description="内容关键词")
    openid: Optional[str] = Field(None, description="按发帖用户openid筛选")
    nick_name: Optional[str] = Field(None, description="按用户昵称筛选")
    tags: List[str] = Field(default_factory=list, description="按标签筛选，支持多个标签")
    category_id: Optional[int] = Field(None, ge=0, description="按分类ID筛选")
    start_time: Optional[datetime] = Field(None, description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")
    status: int = Field(1, ge=0, le=1, description="帖子状态: 1-正常, 0-禁用")
    include_deleted: bool = Field(False, description="是否包含已删除的帖子")
    sort_by: str = Field("update_time DESC", description="排序方式")
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(20, ge=1, le=100, description="每页记录数")

    @field_validator("end_time")
    def validate_time_range(cls, v, info):
        """验证时间范围"""
        values = info.data
        if v and values.get("start_time") and v < values["start_time"]:
            raise ValueError("结束时间不能早于开始时间")
        return v

    @field_validator("keyword", "title", "content", "openid", "nick_name")
    def validate_search_params(cls, v, info):
        """验证搜索参数至少有一个不为空"""
        values = info.data
        if not any([
            values.get("keyword"), values.get("title"), 
            values.get("content"), values.get("openid"),
            values.get("nick_name"), values.get("tags"),
            values.get("category_id")
        ]):
            raise ValueError("至少需要一个搜索条件")
        return v

class AgentSearchRequest(BaseAPIModel):
    """智能体搜索请求"""
    keyword: str = Field(..., min_length=1, description="搜索关键词")
    limit: int = Field(10, ge=1, le=50, description="结果数量限制")
    include_content: bool = Field(False, description="是否包含完整内容")

class GenerateRequest(BaseAPIModel):
    """生成请求"""
    query: str = Field(..., min_length=1, description="用户查询")
    context: Optional[str] = Field(None, description="上下文信息")
    model: str = Field("default", description="使用的模型")
    max_tokens: Optional[int] = Field(None, gt=0, description="最大生成token数")
    temperature: float = Field(0.7, ge=0, le=2.0, description="温度参数")
    stream: bool = Field(False, description="是否流式返回")

class GenerateResponse(BaseAPIModel):
    """生成响应"""
    query: str = Field(..., description="用户查询")
    response: str = Field(..., description="生成的回答")
    usage: Dict[str, int] = Field(..., description="token使用情况")
    processing_time: float = Field(..., ge=0, description="处理时间(秒)")

class RagChatSessionRequest(BaseAPIModel):
    """RAG聊天会话请求"""
    session_id: Optional[str] = Field(None, description="会话ID，为空则创建新会话")
    openid: str = Field(..., description="用户openid")
    title: Optional[str] = Field(None, description="会话标题")

class RagChatSessionResponse(BaseTimeStampModel):
    """RAG聊天会话响应"""
    session_id: str = Field(..., description="会话ID")
    openid: str = Field(..., description="用户openid")
    title: str = Field(..., description="会话标题")
    message_count: int = Field(0, ge=0, description="消息数量")

# 导出所有模型
__all__ = [
    "SearchQuery",
    "SearchResult",
    "SearchResponse",
    "DocumentIndexRequest",
    "DocumentIndexResponse",
    "PostSearchRequest",
    "AgentSearchRequest",
    "GenerateRequest",
    "GenerateResponse",
    "RagChatSessionRequest",
    "RagChatSessionResponse"
] 