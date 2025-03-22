"""
API模块
集中管理所有API路由并提供统一的注册入口
"""
from fastapi import FastAPI
from loguru import logger
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
        
        # 记录注册的所有路由及其前缀
        routes = []
        for route in wxapp_router.routes:
            full_path = f"{wxapp_router.prefix}{route.path}"
            methods = ", ".join(route.methods)
            routes.append(f"{methods} {full_path}")
        
        logger.info(f"微信小程序API路由已注册 - 前缀: {wxapp_router.prefix}")
        for route in sorted(routes):
            logger.info(f"  路由: {route}")
    except ImportError as e:
        logger.error(f"微信小程序API路由注册失败: {str(e)}")
    except Exception as e:
        logger.error(f"微信小程序API路由注册时发生异常: {str(e)}")
    
    try:
        from core.api.mysql import router as mysql_router
        app.include_router(mysql_router)
        logger.info(f"MySQL API路由已注册 - 前缀: {getattr(mysql_router, 'prefix', '')}")
    except ImportError:
        logger.warning("MySQL API模块不可用，已跳过")
    except Exception as e:
        logger.error(f"MySQL API路由注册时发生异常: {str(e)}")
    
    try:
        from core.api.agent import router as agent_router
        app.include_router(agent_router)
        logger.info(f"Agent API路由已注册 - 前缀: {getattr(agent_router, 'prefix', '')}")
    except ImportError:
        logger.warning("Agent API模块不可用，已跳过")
    except Exception as e:
        logger.error(f"Agent API路由注册时发生异常: {str(e)}")
        
    # 记录所有已注册的应用路由
    logger.info("所有已注册的API路由:")
    for route in app.routes:
        if hasattr(route, "methods") and hasattr(route, "path"):
            methods = ", ".join(getattr(route, "methods", ["UNKNOWN"]))
            logger.info(f"  {methods} {route.path}")

    logger.info("API路由注册完成") 