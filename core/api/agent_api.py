"""
Agent查询API接口
提供对Agent功能的访问接口
"""
import re
from fastapi import APIRouter, HTTPException, Path as PathParam, Depends
from pydantic import BaseModel, Field, validator
from typing import List, Dict, Any, Optional, Union, Callable
from loguru import logger

from core.agent.coze.coze_agent_new import CozeAgentNew
from core import config

# 创建专用API路由
agent_router = APIRouter(
    prefix="/agent",
    tags=["Agent功能"],
    responses={404: {"description": "Not found"}}
)

# 请求和响应模型
class ChatRequest(BaseModel):
    query: str = Field(..., description="用户输入的问题")
    history: Optional[List[Dict[str, str]]] = Field(default=[], description="对话历史")
    
    @validator('query')
    def validate_query(cls, v):
        if not v.strip():
            raise ValueError("问题不能为空")
        return v.strip()

class ChatResponse(BaseModel):
    response: str = Field(..., description="Agent的回答")
    sources: List[Dict[str, Any]] = Field(default=[], description="引用的知识来源")

class SearchRequest(BaseModel):
    keyword: str = Field(..., description="搜索关键词")
    limit: int = Field(default=10, ge=1, le=50, description="返回结果数量上限")
    
    @validator('keyword')
    def validate_keyword(cls, v):
        if not v.strip():
            raise ValueError("关键词不能为空")
        return v.strip()

# 依赖项函数
def get_api_logger():
    """提供API日志记录器"""
    return logger.bind(module="agent_api")

# 错误处理函数
def handle_agent_error(func: Callable) -> Callable:
    """装饰器：统一处理Agent操作异常"""
    import functools
    
    @functools.wraps(func)
    async def wrapper(*args, api_logger=Depends(get_api_logger), **kwargs):
        try:
            return await func(*args, api_logger=api_logger, **kwargs)
        except ValueError as e:
            api_logger.warning(f"输入验证错误: {str(e)}")
            raise HTTPException(status_code=400, detail=str(e))
        except HTTPException:
            raise
        except Exception as e:
            api_logger.error(f"Agent操作失败: {str(e)}")
            raise HTTPException(status_code=500, detail=f"操作失败: {str(e)}")
    
    return wrapper

# API端点
@agent_router.post("/chat", response_model=ChatResponse)
@handle_agent_error
async def chat_with_agent(
    request: ChatRequest,
    api_logger=Depends(get_api_logger)
):
    """与Agent进行对话"""
    # 创建CozeAgent实例
    wx_bot_id = config.get("core.agent.coze.wx_bot_id")
    agent = CozeAgentNew(wx_bot_id)
    
    # 发送请求并获取回复
    response = agent.reply(request.query)
    
    if response is None:
        raise HTTPException(status_code=500, detail="Agent响应失败")
        
    return {
        "response": response,
        "sources": []  # 目前CozeAgent不提供知识来源
    }

@agent_router.post("/search", response_model=List[Dict[str, Any]])
@handle_agent_error
async def search_knowledge(
    request: SearchRequest,
    api_logger=Depends(get_api_logger)
):
    """搜索知识库"""
    # TODO: 实现知识搜索逻辑
    results = []
    return results

@agent_router.get("/status")
@handle_agent_error
async def get_agent_status(
    api_logger=Depends(get_api_logger)
):
    """获取Agent状态"""
    return {
        "status": "running",
        "version": "1.0.0",
        "capabilities": ["chat", "search"]
    } 