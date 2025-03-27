"""
智能体聊天相关模型
"""
from typing import List, Dict, Any, Optional
from pydantic import Field, field_validator
from enum import Enum
from api.models.base import BaseAPIModel, BaseTimeStampModel, BaseFullModel

class MessageRole(str, Enum):
    """消息角色"""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    FUNCTION = "function"
    TOOL = "tool"

# class ChatRequest(BaseModel):
#     query: str = Field(..., description="用户输入的问题")
#     history: Optional[List[Dict[str, str]]] = Field(default=[], description="对话历史")
#     stream: bool = Field(default=False, description="是否使用流式响应")
#     format: Optional[str] = Field(default="markdown", description="返回格式，支持 'markdown', 'text', 'html'")
#     user_id: Optional[str] = Field(default="default_user", description="用户唯一标识")
    
#     def validate_query(cls, v):
#         if not v.strip():
#             raise ValueError("问题不能为空")
#         return v.strip()
    
#     def validate_format(cls, v):
#         valid_formats = ['markdown', 'text', 'html']
#         if v.lower() not in valid_formats:
#             raise ValueError(f"格式必须是以下之一: {', '.join(valid_formats)}")
#         return v.lower()
    
#     def validate_user_id(cls, v):
#         if not v.strip():
#             return "default_user"
#         return v.strip()

class ChatMessage(BaseAPIModel):
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

class ChatRequest(BaseAPIModel):
    """聊天请求"""
    query: str = Field(..., description="用户查询")
    openid: str = Field(..., description="用户openid")
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

class ChatResponse(BaseAPIModel):
    """聊天响应"""
    message: str = Field(..., description="生成的消息内容")
    sources: List[str] = Field(default_factory=list, description="知识来源")
    format: str = Field("markdown", description="输出格式")
    usage: Optional[Dict[str, int]] = Field(default_factory=dict, description="token使用情况")
    finish_reason: Optional[str] = Field(None, description="完成原因")

class FunctionDefinition(BaseAPIModel):
    """函数定义"""
    name: str = Field(..., description="函数名称")
    description: Optional[str] = Field(None, description="函数描述")
    parameters: Dict[str, Any] = Field(..., description="函数参数")

class ToolCall(BaseAPIModel):
    """工具调用"""
    id: str = Field(..., description="调用ID")
    type: str = Field(..., description="工具类型")
    function: Dict[str, Any] = Field(..., description="函数调用信息")

class AgentConfig(BaseFullModel):
    """智能体配置"""
    name: str = Field(..., description="智能体名称")
    description: Optional[str] = Field(None, description="智能体描述")
    model: str = Field("gpt-3.5-turbo", description="使用的模型")
    system_prompt: Optional[str] = Field(None, description="系统提示词")
    functions: List[FunctionDefinition] = Field(default_factory=list, description="可用函数")
    plugins: List[str] = Field(default_factory=list, description="启用的插件")

class ChatSession(BaseTimeStampModel):
    """聊天会话"""
    session_id: str = Field(..., description="会话ID")
    messages: List[ChatMessage] = Field(default_factory=list, description="消息历史")
    title: Optional[str] = Field(None, description="会话标题")

class ChatSessionRequest(BaseAPIModel):
    """获取会话请求"""
    session_id: Optional[str] = Field(None, description="会话ID，为空则返回所有会话")
    limit: int = Field(10, ge=1, le=100, description="返回结果数量限制")

class AgentStatusModel(BaseAPIModel):
    """智能体状态模型"""
    status: str = Field("running", description="智能体状态")
    version: str = Field("1.0.0", description="版本号")
    capabilities: List[str] = Field(default_factory=list, description="支持的能力")
    formats: List[str] = Field(default_factory=list, description="支持的格式") 