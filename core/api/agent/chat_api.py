"""
Agent聊天API
提供AI智能体的聊天和知识检索功能
"""
import re
import json
from fastapi import Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, validator
from typing import List, Dict, Any, Optional
from loguru import logger

# 导入通用组件
from core.api.common import get_api_logger, handle_api_errors, create_standard_response
from core.api.agent import router

# 导入必要的Agent组件
from core import config
from core.bridge.reply import ReplyType

# 请求和响应模型
class ChatRequest(BaseModel):
    query: str = Field(..., description="用户输入的问题")
    history: Optional[List[Dict[str, str]]] = Field(default=[], description="对话历史")
    stream: bool = Field(default=False, description="是否使用流式响应")
    format: Optional[str] = Field(default="markdown", description="返回格式，支持 'markdown', 'text', 'html'")
    user_id: Optional[str] = Field(default="default_user", description="用户唯一标识")
    
    @validator('query')
    def validate_query(cls, v):
        if not v.strip():
            raise ValueError("问题不能为空")
        return v.strip()
    
    @validator('format')
    def validate_format(cls, v):
        valid_formats = ['markdown', 'text', 'html']
        if v.lower() not in valid_formats:
            raise ValueError(f"格式必须是以下之一: {', '.join(valid_formats)}")
        return v.lower()
    
    @validator('user_id')
    def validate_user_id(cls, v):
        if not v.strip():
            return "default_user"
        return v.strip()

class ChatResponse(BaseModel):
    response: str = Field(..., description="Agent的回答")
    sources: List[Dict[str, Any]] = Field(default=[], description="引用的知识来源") 
    format: str = Field(default="markdown", description="返回的格式类型")

class SearchRequest(BaseModel):
    keyword: str = Field(..., description="搜索关键词")
    limit: int = Field(default=10, ge=1, le=50, description="返回结果数量上限")
    
    @validator('keyword')
    def validate_keyword(cls, v):
        if not v.strip():
            raise ValueError("关键词不能为空")
        return v.strip()

# 格式化函数
def format_response_content(content, format_type):
    """格式化响应内容"""
    if format_type == "markdown":
        # 已经是Markdown格式，不需要特殊处理
        return content
    elif format_type == "text":
        # 移除Markdown标记
        text = content
        # 移除标题标记
        text = re.sub(r'#+\s+', '', text)
        # 移除粗体和斜体
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
        text = re.sub(r'\*(.*?)\*', r'\1', text)
        # 移除链接，保留文本
        text = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', text)
        # 移除代码块
        text = re.sub(r'```.*?\n(.*?)```', r'\1', text, flags=re.DOTALL)
        # 移除行内代码
        text = re.sub(r'`(.*?)`', r'\1', text)
        return text
    elif format_type == "html":
        # 将Markdown转换为HTML（简化转换）
        html = content
        # 标题转换
        html = re.sub(r'### (.*?)(\n|$)', r'<h3>\1</h3>\2', html)
        html = re.sub(r'## (.*?)(\n|$)', r'<h2>\1</h2>\2', html)
        html = re.sub(r'# (.*?)(\n|$)', r'<h1>\1</h1>\2', html)
        # 粗体和斜体
        html = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', html)
        html = re.sub(r'\*(.*?)\*', r'<em>\1</em>', html)
        # 链接
        html = re.sub(r'\[(.*?)\]\((.*?)\)', r'<a href="\2">\1</a>', html)
        # 代码块
        html = re.sub(r'```(.*?)\n(.*?)```', r'<pre><code>\2</code></pre>', html, flags=re.DOTALL)
        # 行内代码
        html = re.sub(r'`(.*?)`', r'<code>\1</code>', html)
        # 段落
        html = re.sub(r'([^\n])\n([^\n])', r'\1<br>\2', html)
        return html
    
    return content

async def stream_response(generator, format_type="markdown"):
    """生成流式响应"""
    try:
        for chunk in generator:
            # 格式化每个块
            formatted_chunk = format_response_content(chunk, format_type)
            yield f"data: {json.dumps({'content': formatted_chunk})}\n\n"
    except Exception as e:
        logger.error(f"Stream response error: {str(e)}")
        yield f"data: {json.dumps({'error': str(e)})}\n\n"

# API端点
@router.post("/chat")
@handle_api_errors("Agent对话")
async def chat_with_agent(
    request: ChatRequest,
    api_logger=Depends(get_api_logger)
):
    """与Agent进行对话"""
    # 延迟导入CozeAgent，避免循环导入
    from core.agent.coze.coze_agent import CozeAgent
    from core.bridge.context import Context, ContextType
    
    # 创建CozeAgent实例
    agent = CozeAgent()
    
    # 创建上下文对象
    context = Context()
    context.type = ContextType.TEXT
    context["session_id"] = "api_session_" + str(hash(request.query))
    context["stream"] = request.stream  # 添加stream参数
    context["format"] = request.format  # 添加format参数
    context["user_id"] = request.user_id  # 添加user_id参数
    
    api_logger.debug(f"处理聊天请求：query={request.query}, user_id={request.user_id}")
    
    # 发送请求并获取回复
    reply = agent.reply(request.query, context)
    
    if reply is None:
        raise HTTPException(status_code=500, detail="Agent响应失败")
    
    # 如果是流式响应
    if request.stream and reply.type == ReplyType.STREAM:
        return StreamingResponse(
            stream_response(reply.content, request.format),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
    
    # 非流式响应
    if reply.type != ReplyType.TEXT:
        raise HTTPException(status_code=500, detail="Agent响应类型错误")
    
    # 格式化内容    
    formatted_content = format_response_content(reply.content, request.format)
    
    return {
        "response": formatted_content,
        "sources": [],  # 目前CozeAgent不提供知识来源
        "format": request.format
    }

@router.post("/search", response_model=List[Dict[str, Any]])
@handle_api_errors("知识搜索")
async def search_knowledge(
    request: SearchRequest,
    api_logger=Depends(get_api_logger)
):
    """搜索知识库"""
    # TODO: 实现知识搜索逻辑
    results = []
    return results

@router.get("/status")
@handle_api_errors("获取Agent状态")
async def get_agent_status(
    api_logger=Depends(get_api_logger)
):
    """获取Agent状态"""
    return {
        "status": "running",
        "version": "1.0.0",
        "capabilities": ["chat", "search"],
        "formats": ["markdown", "text", "html"]
    } 