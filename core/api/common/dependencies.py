"""
API通用依赖项模块
提供API路由使用的常用依赖注入函数
"""
from fastapi import Depends
from loguru import logger
from contextvars import ContextVar

# 请求ID上下文变量
request_id_var: ContextVar[str] = ContextVar("request_id", default="")

def get_api_logger(module: str = "api"):
    """
    提供API日志记录器
    
    Args:
        module: 模块名称
    
    Returns:
        带有请求ID和模块信息的日志记录器
    """
    return logger.bind(
        request_id=request_id_var.get(),
        module=module
    )

def get_mysql_logger():
    """MySQL API专用日志记录器"""
    return get_api_logger(module="mysql_api")

def get_wxapp_logger():
    """微信小程序API专用日志记录器"""
    return get_api_logger(module="wxapp_api")

def get_agent_logger():
    """Agent API专用日志记录器"""
    return get_api_logger(module="agent_api") 