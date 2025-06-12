"""
API路由模块
包含所有API路由的定义
"""
from fastapi import APIRouter
from api.routes.agent import chat, rag
from api.routes.wxapp import about, comment, feedback, notification, post, user, action, banwords
from api.routes.admin import system
from api.routes.knowledge import search
router = APIRouter()

router.include_router(search.router, prefix="/knowledge", tags=["knowledge"])
router.include_router(chat.router, prefix="/agent", tags=["agent"])
router.include_router(rag.router, prefix="/agent", tags=["agent"])
router.include_router(about.router, prefix="/wxapp", tags=["wxapp"])
router.include_router(action.router, prefix="/wxapp", tags=["wxapp"])
router.include_router(comment.router, prefix="/wxapp", tags=["wxapp"])
router.include_router(feedback.router, prefix="/wxapp", tags=["wxapp"])
router.include_router(notification.router, prefix="/wxapp", tags=["wxapp"])
router.include_router(post.router, prefix="/wxapp", tags=["wxapp"])
router.include_router(user.router, prefix="/wxapp", tags=["wxapp"])
router.include_router(banwords.router, prefix="/wxapp", tags=["wxapp"])
router.include_router(system.router, prefix="/admin", tags=["admin"])

__all__ = ['router']