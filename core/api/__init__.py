"""
API模块
集中管理所有API路由并提供统一的注册入口
"""
from fastapi import FastAPI, APIRouter
from loguru import logger
from core.api.common.exceptions import setup_exception_handlers

# 预先创建所有路由器
wxapp_router = APIRouter(prefix="/wxapp")
mysql_router = APIRouter(prefix="/mysql")
agent_router = APIRouter(prefix="/agent")

def register_routers(app: FastAPI):
    """
    注册所有API路由到FastAPI应用
    
    Args:
        app: FastAPI应用实例
    """
    # 注册全局异常处理器
    setup_exception_handlers(app)
    
    # 注册微信小程序路由
    try:
        # 导入所有API模块，确保路由注册
        import traceback
        try:
            import core.api.wxapp.user_api
            logger.debug("成功导入user_api")
        except Exception as e:
            logger.error(f"导入user_api失败: {str(e)}")
            logger.error(traceback.format_exc())
        
        try:
            import core.api.wxapp.post_api
            logger.debug("成功导入post_api")
        except Exception as e:
            logger.error(f"导入post_api失败: {str(e)}")
            logger.error(traceback.format_exc())
            
        try:
            import core.api.wxapp.comment_api
            logger.debug("成功导入comment_api")
        except Exception as e:
            logger.error(f"导入comment_api失败: {str(e)}")
            logger.error(traceback.format_exc())
            
        try:
            import core.api.wxapp.search_api
            logger.debug("成功导入search_api")
        except Exception as e:
            logger.error(f"导入search_api失败: {str(e)}")
            logger.error(traceback.format_exc())
            
        try:
            import core.api.wxapp.notification_api
            logger.debug("成功导入notification_api")
        except Exception as e:
            logger.error(f"导入notification_api失败: {str(e)}")
            logger.error(traceback.format_exc())
            
        try:
            import core.api.wxapp.feedback_api
            logger.debug("成功导入feedback_api")
        except Exception as e:
            logger.error(f"导入feedback_api失败: {str(e)}")
            logger.error(traceback.format_exc())
            
        try:
            import core.api.wxapp.about_api
            logger.debug("成功导入about_api")
        except Exception as e:
            logger.error(f"导入about_api失败: {str(e)}")
            logger.error(traceback.format_exc())
        
        # 注册路由器
        app.include_router(wxapp_router)
        
        # 记录路由信息
        logger.info(f"微信小程序API路由已注册 - 前缀: {wxapp_router.prefix}")
        for route in sorted([f"{', '.join(route.methods)} {route.path}" for route in wxapp_router.routes]):
            logger.info(f"  路由: {route}")
    except Exception as e:
        logger.error(f"微信小程序API路由注册失败: {str(e)}")
    
    # 注册MySQL API路由
    try:
        # 导入MySQL API模块
        import core.api.mysql.mysql_api
        
        # 注册路由器
        app.include_router(mysql_router)
        logger.info(f"MySQL API路由已注册 - 前缀: {mysql_router.prefix}")
    except Exception as e:
        logger.error(f"MySQL API路由注册失败: {str(e)}")
    
    # 注册Agent API路由
    try:
        # 导入Agent API模块
        import core.api.agent.agent_api
        
        # 注册路由器
        app.include_router(agent_router)
        logger.info(f"Agent API路由已注册 - 前缀: {agent_router.prefix}")
    except Exception as e:
        logger.error(f"Agent API路由注册失败: {str(e)}")
        
    # 记录所有已注册的应用路由
    logger.info("所有已注册的API路由:")
    for route in app.routes:
        if hasattr(route, "methods") and hasattr(route, "path"):
            methods = ", ".join(getattr(route, "methods", ["UNKNOWN"]))
            logger.info(f"  {methods} {route.path}")

    logger.info("API路由注册完成") 