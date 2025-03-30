"""
智能体聊天相关模型
"""
from typing import List, Dict, Any, Optional
from pydantic import Field, field_validator
from enum import Enum
from api.models.common import Request, Response, BaseAPI, BaseTimeStamp

class MessageRole(str, Enum):
    """消息角色"""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    FUNCTION = "function"
    TOOL = "tool"

class ChatMessage(BaseAPI):
    """聊天消息"""
    role: MessageRole = Field(..., description="消息角色")
    content: str = Field(..., description="消息内容")
    name: Optional[str] = Field(None, description="名称，用于function调用")

    @field_validator("content")
    def validate_content(cls, v):
        """验证消息内容不为空"""
        if not v or not v.strip():
            raise ValueError("消息内容不能为空")
        return v.strip()

class ChatRequest(Request):
    """聊天请求"""
    query: str = Field(..., description="用户查询")
    stream: bool = Field(False, description="是否流式返回")
    format: str = Field("markdown", description="输出格式，如markdown、text或html")
    bot_tag: Optional[str] = Field("default", description="机器人tag，用于指定使用哪个机器人")

    @field_validator("query")
    def validate_query(cls, v):
        """验证query不为空"""
        if not v or not v.strip():
            raise ValueError("query不能为空")
        return v.strip()

    @field_validator("format")
    def validate_format(cls, v):
        """验证format是有效的格式"""
        valid_formats = ["markdown", "text", "html"]
        if v.lower() not in valid_formats:
            raise ValueError(f"无效的格式: {v}, 有效格式为: {', '.join(valid_formats)}")
        return v.lower()

class ChatResponse(Response):
    """聊天响应"""
    message: str = Field(..., description="生成的消息内容")
    format: str = Field("markdown", description="输出格式")
    usage: Optional[Dict[str, int]] = Field(default_factory=dict, description="token使用情况")
    finish_reason: Optional[str] = Field(None, description="完成原因")

class Source(BaseAPI):
    """RAG结果的数据来源"""
    type: str = Field(..., description="来源类型，如'微信公众号文章'")
    title: str = Field(..., description="标题")
    content: str = Field(..., description="内容")
    author: Optional[str] = Field(None, description="作者")

class RAGRequest(BaseAPI):
    """统一RAG请求模型"""
    # 公共字段
    query: str = Field(..., 
                     min_length=1,
                     description="用户查询内容，支持自然语言提问")
    openid: Optional[str] = Field(None,
                                description="用户身份标识，小程序场景必填")
    
    # 原CozeRAGRequest字段
    tables: List[str] = Field(["wxapp_posts"],
                            description="检索目标表: wxapp_posts-小程序内容, knowledge_base-知识库")
    max_results: int = Field(5,
                           ge=1, le=20,
                           description="每个数据源返回的最大结果数")
    stream: bool = Field(False,
                       description="是否启用流式响应，默认关闭")
    format: str = Field("markdown",
                      description="响应格式：markdown-带格式文本，raw-纯文本")
    
    # 高级参数
    min_score: float = Field(0.5,
                           ge=0, le=1,
                           description="相关性分数阈值，默认0.5")
    debug: bool = Field(False,
                      description="是否返回调试信息")
    
    # Agent特定参数
    rewrite_bot_id: Optional[str] = Field(None, description="用于查询改写的机器人ID")
    knowledge_bot_id: Optional[str] = Field(None, description="用于生成回答的机器人ID")

class RAGResponse(BaseAPI):
    """RAG响应模型"""
    original_query: str = Field(..., description="原始查询")
    rewritten_query: str = Field(..., description="改写后的查询")
    response: str = Field(..., description="回答内容")
    sources: List[Source] = Field(default_factory=list, description="结果来源")
    suggested_questions: List[str] = Field(default_factory=list, description="推荐问题")
    format: str = Field("markdown", description="输出格式")
    retrieved_count: int = Field(0, description="检索到的结果数量")
    response_time: float = Field(0.0, description="响应时间(秒)") 