"""
API路由模块
包含所有API路由的定义
"""
from fastapi import APIRouter
from api.routes.agent import router as agent_router
from api.routes.wxapp import router as wxapp_router
from api.routes.admin import router as admin_router
from api.routes.knowledge import router as knowledge_router

router = APIRouter()

# 统一添加 /api 前缀
api_router = APIRouter(prefix="/api")

# 包含知识库路由
api_router.include_router(knowledge_router, prefix="/knowledge", tags=["knowledge"])

# 包含 Agent 路由
api_router.include_router(agent_router, prefix="/agent", tags=["agent"])

# 包含小程序路由
api_router.include_router(wxapp_router, prefix="/wxapp", tags=["wxapp"])

# 包含管理后台路由
api_router.include_router(admin_router, prefix="/admin", tags=["admin"])

# 将带有 /api 前缀的总路由赋值给 router
router.include_router(api_router)

__all__ = ['router']