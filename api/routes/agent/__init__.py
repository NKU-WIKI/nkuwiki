"""
智能体API模块
处理智能体相关的交互，包括RAG、聊天等功能

主要使用rag模块提供知识检索增强生成功能
搜索和聊天功能作为辅助接口保留
"""
from fastapi import APIRouter
from . import rag, chat

router = APIRouter()

router.include_router(rag.router)
router.include_router(chat.router)

__all__ = ['router']
