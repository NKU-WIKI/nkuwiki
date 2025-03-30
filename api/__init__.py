"""
API模块
包含所有对外提供的HTTP接口

提供以下主要路由器:
- wxapp_router: 微信小程序接口
- agent_router: 智能体接口
- admin_router: 管理员接口
"""
from api.routes import router
__all__ = [
    "router"
]