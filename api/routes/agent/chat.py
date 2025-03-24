"""
智能体聊天API接口
处理与智能体的对话、RAG查询等功能
"""
import time
from fastapi import Depends
from api import agent_router
from api.common import handle_api_errors, get_api_logger_dep
from api.models.agent.chat import ChatResponse, AgentStatusModel, ChatRequest, ChatMessage, MessageRole

@agent_router.post("/chat", response_model=ChatResponse)
@handle_api_errors("智能体对话")
async def chat_with_agent(
    request: ChatRequest,
    api_logger=Depends(get_api_logger_dep)
):
    """
    与AI智能体进行对话
    
    支持普通对话和流式返回
    """
    api_logger.debug(f"处理对话请求: query={request.query}")
    
    # 获取智能体实例
    from core.agent.agent_factory import get_agent
    agent_instance = get_agent("coze")
    
    # 构建消息历史
    messages = []
    if request.messages:
        messages.extend(request.messages)
    
    # 添加用户问题
    messages.append(ChatMessage(
        role=MessageRole.USER,
        content=request.query
    ))
    
    start_time = time.time()
    
    # 生成回答
    if request.stream:
        # 流式生成
        return await agent_instance.chat_stream(
            messages=messages,
            format=request.format
        )
    else:
        # 普通生成
        response = await agent_instance.chat(
            messages=messages,
            format=request.format
        )
        
        # 获取知识来源
        sources = []
        if isinstance(response, dict) and "sources" in response:
            sources = response["sources"]
        
        # 生成推荐问题
        suggested_questions = []
        if isinstance(response, dict) and "suggested_questions" in response:
            suggested_questions = response["suggested_questions"]
        
        return {
            "response": response["content"] if isinstance(response, dict) and "content" in response else str(response),
            "sources": sources,
            "suggested_questions": suggested_questions,
            "format": request.format
        }

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