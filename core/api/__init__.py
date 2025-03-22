"""
API模块
集中管理所有API路由并提供统一的注册入口
"""
from fastapi import FastAPI
from core.api.common.exceptions import setup_exception_handlers

def register_routers(app: FastAPI):
    """
    注册所有API路由到FastAPI应用
    
    Args:
        app: FastAPI应用实例
    """
    # 注册全局异常处理器
    setup_exception_handlers(app)
    
    # 导入并注册各模块路由器
    try:
        from core.api.wxapp import router as wxapp_router
        app.include_router(wxapp_router)
    except ImportError:
        pass
    
    try:
        from core.api.mysql import router as mysql_router
        app.include_router(mysql_router)
    except ImportError:
        pass
    
    try:
        from core.api.agent import router as agent_router
        app.include_router(agent_router)
    except ImportError:
        pass 