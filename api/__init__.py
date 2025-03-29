"""
API模块
包含所有对外提供的HTTP接口

提供以下主要路由器:
- wxapp_router: 微信小程序接口
- agent_router: 智能体接口
- health_router: 健康检查接口
- admin_router: 管理员接口
- mcp_router: MCP协议接口
"""
from fastapi import APIRouter

# 创建各种路由
health_router = APIRouter(tags=["health"])
wxapp_router = APIRouter(prefix="/wxapp", tags=["wxapp"])
agent_router = APIRouter(prefix="/agent", tags=["agent"])
mcp_router = APIRouter(prefix="/mcp", tags=["mcp"])

# 导入各子模块的路由，这会触发子模块中的路由注册
from api.routes import wxapp, agent, admin, mcp

# 导入admin_router以便将其注册
from api.routes.admin import admin_router

# 将这些路由器暴露给外部
__all__ = [
    "wxapp_router",
    "health_router", 
    "agent_router",
    "admin_router",
    "mcp_router",
    "register_routers",
]

def register_routers(app):
    """
    将所有API路由器注册到FastAPI应用
    
    Args:
        app: FastAPI应用实例
    """
    # 注意：健康检查端点(/api/health)已在app.py中通过api_router注册
    # 这里只注册各个子路由器的路由
    
    # 注册各路由器
    app.include_router(health_router)
    app.include_router(wxapp_router)
    app.include_router(agent_router)
    app.include_router(admin_router)
    app.include_router(mcp_router)