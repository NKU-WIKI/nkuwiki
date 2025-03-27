"""
Coze RAG模型定义
定义与RAG系统相关的请求和响应模型
"""
from typing import List, Dict, Any, Optional
from pydantic import Field, BaseModel

from api.models.common import BaseAPIModel, BaseFullModel


class WxappRAGRequest(BaseAPIModel):
    """
    微信小程序RAG请求模型
    简化版的RAG请求，面向微信小程序前端
    """
    query: str = Field(..., description="用户问题", min_length=1)
    openid: Optional[str] = Field(None, description="用户openid")


class CozeRAGRequest(BaseAPIModel):
    """
    Coze RAG请求模型
    用于内部RAG处理
    """
    query: str = Field(..., min_length=1, description="用户查询问题")
    tables: List[str] = Field(default=["wxapp_posts"], description="要检索的表名列表")
    max_results: int = Field(5, ge=1, le=20, description="每个表返回的最大结果数")
    stream: bool = Field(False, description="是否流式返回")
    format: str = Field("markdown", description="回复格式: markdown")
    openid: Optional[str] = Field(None, description="用户唯一标识")
    rewrite_bot_id: Optional[str] = Field(None, description="查询改写bot ID，不填则使用配置默认值")
    knowledge_bot_id: Optional[str] = Field(None, description="回答生成bot ID，不填则使用配置默认值")


class Source(BaseModel):
    """
    RAG结果来源
    """
    type: str = Field(..., description="来源类型")
    title: str = Field(..., description="标题")
    content: str = Field(..., description="内容")
    author: Optional[str] = Field(None, description="作者")
    url: Optional[str] = Field(None, description="URL")


class CozeRAGResponse(BaseAPIModel):
    """
    Coze RAG响应模型
    """
    original_query: str = Field(..., description="原始查询")
    rewritten_query: str = Field(..., description="改写后的查询")
    response: str = Field(..., description="回答内容")
    sources: List[Source] = Field(default_factory=list, description="来源列表")
    suggested_questions: List[str] = Field(default_factory=list, description="推荐问题") 

class KnowledgeBase(BaseFullModel):
    """知识库"""
    id: str = Field(..., description="知识库ID")
    name: str = Field(..., description="知识库名称")
    description: Optional[str] = Field(None, description="知识库描述")
    document_count: int = Field(0, ge=0, description="文档数量")
    owner: str = Field(..., description="所有者openid")
    is_public: bool = Field(False, description="是否公开")
    embedding_model: str = Field("default", description="嵌入模型")
    tags: List[str] = Field(default_factory=list, description="标签")

class SearchResult(BaseAPIModel):
    """搜索结果"""
    title: str = Field(..., description="标题")
    url: str = Field(..., description="URL")
    snippet: str = Field(..., description="内容片段")
    score: float = Field(..., ge=0, le=1, description="相关度得分")

class SearchRequest(BaseAPIModel):
    """搜索请求"""
    keyword: str = Field(..., min_length=1, description="搜索关键词")
    limit: int = Field(10, ge=1, le=100, description="返回结果数量限制")

class Source(BaseAPIModel):
    """来源信息"""
    type: str = Field(..., description="来源类型")
    title: str = Field(..., description="标题")
    content: str = Field(..., description="内容")
    author: Optional[str] = Field(None, description="作者")

class RAGRequest(BaseAPIModel):
    """RAG请求"""
    query: str = Field(..., min_length=1, description="用户查询问题")
    tables: List[str] = Field(default=["wxapp_posts"], description="要检索的表名列表")
    max_results: int = Field(5, ge=1, le=20, description="每个表返回的最大结果数")
    stream: bool = Field(False, description="是否流式返回")
    format: str = Field("markdown", description="回复格式: markdown")
    openid: Optional[str] = Field(None, description="用户唯一标识")
    rewrite_bot_id: Optional[str] = Field(None, description="查询改写bot ID，不填则使用配置默认值")
    knowledge_bot_id: Optional[str] = Field(None, description="回答生成bot ID，不填则使用配置默认值")

class RAGResponse(BaseAPIModel):
    """RAG响应"""
    original_query: str = Field(..., description="原始查询")
    rewritten_query: str = Field(..., description="改写后的查询")
    response: str = Field(..., description="生成的回答")
    sources: List[Source] = Field(..., description="来源列表")
    suggested_questions: List[str] = Field(default_factory=list, description="建议问题列表")

class SourceInfo(BaseAPIModel):
    """知识来源信息模型"""
    title: str = Field("未知标题", description="来源标题")
    url: str = Field("", description="来源URL")
    snippet: str = Field("", description="内容摘要")

class KnowledgeSearchResult(BaseAPIModel):
    """知识搜索结果模型"""
    id: int = Field(..., description="ID")
    title: str = Field("", description="标题")
    content_preview: str = Field("", description="内容预览")
    author: str = Field("", description="作者")
    create_time: str = Field("", description="创建时间")
    type: str = Field("文章", description="类型")
    view_count: int = Field(0, description="浏览次数")
    like_count: int = Field(0, description="点赞次数")
    comment_count: int = Field(0, description="评论数量")
    relevance: float = Field(0.0, description="相关度得分")

class KnowledgeSearchResponse(BaseAPIModel):
    """知识搜索响应模型"""
    results: List[KnowledgeSearchResult] = Field(default_factory=list, description="搜索结果列表")
    keyword: str = Field("", description="搜索关键词")
    total: int = Field(0, description="结果总数") 