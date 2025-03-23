"""
API依赖项模块
提供API常用的依赖注入函数
"""
from loguru import logger
from fastapi import Request, Depends
from core.utils.logger import register_logger

def get_module_name(request: Request) -> str:
    """
    从请求路径中获取模块名称
    例如 /wxapp/posts -> wxapp
    
    Args:
        request: FastAPI请求对象
        
    Returns:
        模块名称
    """
    path = request.url.path
    parts = path.strip('/').split('/')
    if parts:
        return parts[0]
    return "api"

def get_request_logger(request: Request):
    """
    获取绑定了请求信息的日志记录器
    
    Args:
        request: FastAPI请求对象
        
    Returns:
        日志记录器实例
    """
    module = get_module_name(request)
    client_ip = request.client.host if request.client else "unknown"
    path = request.url.path
    
    # 获取模块日志记录器并绑定请求上下文
    logger = register_logger(f"api.{module}")
    return logger.bind(
        client_ip=client_ip,
        path=path
    )

def get_api_logger_dep(request: Request):
    """
    提供API日志记录器的依赖注入函数
    
    Args:
        request: FastAPI请求对象
        
    Returns:
        日志记录器实例
    """
    return get_request_logger(request) 