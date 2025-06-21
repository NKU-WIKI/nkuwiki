"""
API路由模块
包含所有API路由的定义
"""
from fastapi import APIRouter
from api.routes.agent import chat, rag
from api.routes.wxapp import about, comment, feedback, notification, post, user, action, banwords
from api.routes.admin import system
from api.routes.knowledge import search, insight
from api.routes.wxapp import router as wxapp_router  # 导入 wxapp 的主路由器

router = APIRouter()

# 统一添加 /api 前缀
api_router = APIRouter(prefix="/api")

# 包含知识库路由
api_router.include_router(search.router, prefix="/knowledge", tags=["knowledge"])
api_router.include_router(insight.router, prefix="/knowledge", tags=["knowledge"])

# 包含 Agent 路由
api_router.include_router(chat.router, prefix="/agent", tags=["agent"])
api_router.include_router(rag.router, prefix="/agent", tags=["agent"])

# 包含小程序路由
api_router.include_router(wxapp_router, prefix="/wxapp", tags=["wxapp"])

# 包含管理后台路由
api_router.include_router(system.router, prefix="/admin", tags=["admin"])

# 将带有 /api 前缀的总路由赋值给 router
router.include_router(api_router)

__all__ = ['router']