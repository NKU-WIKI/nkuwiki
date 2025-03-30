"""
API路由模块
包含所有API路由的定义
"""

from fastapi import APIRouter

# 导入子模块，触发路由注册
from api.routes.agent import chat, coze_rag, search
from api.routes.wxapp import about, comment, feedback, notification, post, search, user, action

router = APIRouter()
router.include_router(chat.router, prefix="/agent", tags=["agent"])
router.include_router(coze_rag.router, prefix="/agent", tags=["agent"])
router.include_router(search.router, prefix="/agent", tags=["agent"])

router.include_router(about.router, prefix="/wxapp", tags=["wxapp"])
router.include_router(comment.router, prefix="/wxapp", tags=["wxapp"])
router.include_router(feedback.router, prefix="/wxapp", tags=["wxapp"])
router.include_router(notification.router, prefix="/wxapp", tags=["wxapp"])
router.include_router(post.router, prefix="/wxapp", tags=["wxapp"])
router.include_router(search.router, prefix="/wxapp", tags=["wxapp"])
router.include_router(user.router, prefix="/wxapp", tags=["wxapp"]) 
router.include_router(action.router, prefix="/wxapp", tags=["wxapp"])

__all__ = ['router']