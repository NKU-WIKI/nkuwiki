"""
API模块
包含所有对外提供的HTTP接口
"""
from fastapi import APIRouter

# 创建各模块的路由器
wxapp_router = APIRouter(prefix="/wxapp", tags=["wxapp"])
mysql_router = APIRouter(prefix="/mysql", tags=["mysql"])
agent_router = APIRouter(prefix="/agent", tags=["agent"])

# 将这些路由器暴露给外部
__all__ = [
    "wxapp_router",
    "mysql_router",
    "agent_router",
    "register_routers",
]

# 定义注册路由器的函数
def register_routers(app):
    """
    将所有API路由器注册到FastAPI应用
    
    Args:
        app: FastAPI应用实例
    """
    app.include_router(wxapp_router)
    app.include_router(mysql_router)
    app.include_router(agent_router)

# 导入各子模块的路由
from api.wxapp import *
from api.mysql import *
from api.agent import * 