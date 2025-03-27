"""
智能体聊天API接口
处理与智能体的对话、RAG查询等功能
"""
from fastapi import Depends,HTTPException
from api import agent_router
from api.common import handle_api_errors, get_api_logger_dep
from api.models.agent.chat import AgentStatusModel, ChatRequest, ChatResponse
from fastapi.responses import StreamingResponse
from typing import Callable
from api.common import format_response_content
from core.bridge.reply import ReplyType
from core.utils.logger import register_logger
import json

# 请求和响应模型
logger = register_logger("api.agent")
# 错误处理函数

# def handle_agent_error(func: Callable) -> Callable:
#     """装饰器：统一处理Agent操作异常"""
#     import functools
    
#     @functools.wraps(func)
#     async def wrapper(*args, api_logger=Depends(get_api_logger_dep), **kwargs):
#         try:
#             return await func(*args, api_logger=api_logger, **kwargs)
#         except ValueError as e:
#             api_logger.warning(f"输入验证错误: {str(e)}")
#             raise HTTPException(status_code=400, detail=str(e))
#         except HTTPException:
#             raise
#         except Exception as e:
#             api_logger.error(f"Agent操作失败: {str(e)}")
#             raise HTTPException(status_code=500, detail=f"操作失败: {str(e)}")
    
#     return wrapper



# API端点
@agent_router.post("/chat",response_model=ChatResponse)
@handle_api_errors("与Agent进行对话")
async def chat_with_agent(
    request: ChatRequest,
    api_logger=Depends(get_api_logger_dep)
):
    """与Agent进行对话"""
    # 延迟导入CozeAgent，避免循环导入
    from core.agent.coze.coze_agent import CozeAgent
    from core.bridge.context import Context, ContextType
    
    # 获取bot_tag参数，默认使用"default"
    bot_tag = request.bot_tag if hasattr(request, "bot_tag") and request.bot_tag else "default"
    
    # 创建CozeAgent实例，传入bot_tag
    agent = CozeAgent(tag=bot_tag)
    
    # 创建上下文对象
    context = Context()
    context.type = ContextType.TEXT
    context["session_id"] = "api_session_" + str(hash(request.query))
    context["stream"] = request.stream  # 添加stream参数
    context["format"] = request.format  # 添加format参数
    context["openid"] = request.openid  # 添加openid参数
    
    api_logger.debug(f"处理聊天请求：query={request.query}, openid={request.openid}, bot_tag={bot_tag}")
    
    # 发送请求并获取回复
    reply = agent.reply(request.query, context)
    
    if reply is None:
        raise HTTPException(status_code=500, detail="Agent响应失败")
    
    # 如果是流式响应
    if request.stream and reply.type == ReplyType.STREAM:
        async def sse_generator():
            """生成SSE格式的流式响应"""
            try:
                for chunk in reply.content:
                    if chunk:
                        # 简单格式化文本
                        if request.format != 'text':
                            yield f"data: {json.dumps({'content': chunk})}\n\n"
                        else:
                            yield f"data: {json.dumps({'content': chunk})}\n\n"
            except Exception as e:
                api_logger.error(f"流式响应生成失败: {str(e)}")
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
                
        return StreamingResponse(
            sse_generator(),
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
    
    return ChatResponse(
        message=formatted_content,
        sources=[],  # 目前CozeAgent不提供知识来源
        format=request.format
    )

@agent_router.get("/status", response_model=AgentStatusModel)
@handle_api_errors("获取智能体状态")
async def get_agent_status(
    api_logger=Depends(get_api_logger_dep)
):
    """
    获取Agent系统状态
    """
    api_logger.debug("获取智能体状态")
    
    # 获取智能体实例
    from core.agent.agent_factory import get_agent
    agent_instance = get_agent("coze")
    
    # 由于基础Agent类可能没有get_status方法，提供一个默认状态
    try:
        status = await agent_instance.get_status()
    except AttributeError:
        # 如果智能体没有get_status方法，返回默认状态
        status = {
            "status": "running",
            "version": "1.0.0",
            "capabilities": ["chat", "search"],
            "formats": ["markdown", "text", "html"]
        }
    
    return {
        "status": status.get("status", "running"),
        "version": status.get("version", "1.0.0"),
        "capabilities": status.get("capabilities", ["chat", "search"]),
        "formats": status.get("formats", ["markdown", "text", "html"])
    } 