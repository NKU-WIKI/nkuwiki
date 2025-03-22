"""
API通用组件模块
提供API开发使用的通用工具和组件
"""
from functools import wraps
import traceback
from typing import Any, Dict, Callable, Optional

from fastapi import FastAPI, APIRouter, HTTPException, Request, Depends
from fastapi_responseschema.routing import SchemaAPIRoute
from fastapi_responseschema import AbstractResponseSchema, wrap_app_responses
from fastapi.responses import JSONResponse
from loguru import logger
from contextvars import ContextVar
from core.api.common.response import create_standard_response, StandardResponse
from core.api.common.exceptions import setup_exception_handlers
from core.api.common.decorators import handle_api_errors
from core.api.common.dependencies import get_api_logger_dep as get_api_logger

__all__ = [
    'create_standard_response',
    'StandardResponse',
    'setup_exception_handlers',
    'get_api_logger',
    'handle_api_errors',
    'get_schema_api_router'
]

# 请求ID上下文变量
request_id_var: ContextVar[str] = ContextVar('request_id', default='')

# API日志获取函数
def get_api_logger():
    """获取API日志器，包含当前请求ID"""
    return logger.bind(request_id=request_id_var.get(), name='core.api')

# 获取不同模块的日志器
def get_mysql_logger():
    """获取MySQL日志器"""
    return logger.bind(request_id=request_id_var.get(), name='core.api.mysql')

def get_wxapp_logger():
    """获取微信小程序日志器"""
    return logger.bind(request_id=request_id_var.get(), name='core.api.wxapp')

def get_agent_logger():
    """获取智能体日志器"""
    return logger.bind(request_id=request_id_var.get(), name='core.api.agent')

# 标准响应创建函数
def create_standard_response(data: Any = None, code: int = 200, message: str = "success") -> Dict[str, Any]:
    """
    创建标准API响应格式
    
    Args:
        data: 响应数据
        code: 状态码
        message: 响应消息
        
    Returns:
        标准格式的响应字典
    """
    return {
        "code": code,
        "message": message,
        "data": data
    }

# 增强错误处理装饰器
def handle_api_errors(operation_name: str = "API操作"):
    """API异常处理装饰器，捕获异常并返回标准错误响应"""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            api_logger = kwargs.get('api_logger') or get_api_logger()
            try:
                return await func(*args, **kwargs)
            except HTTPException as e:
                # FastAPI的HTTP异常，直接传递
                api_logger.warning(f"{operation_name}失败: HTTP {e.status_code} - {e.detail}")
                return JSONResponse(
                    status_code=e.status_code,
                    content=create_standard_response(None, e.status_code, e.detail)
                )
            except Exception as e:
                # 记录详细的错误信息
                error_detail = str(e)
                error_trace = traceback.format_exc()
                api_logger.error(f"{operation_name}发生未处理异常: {error_detail}\n{error_trace}")
                
                # 返回500错误
                return JSONResponse(
                    status_code=500,
                    content=create_standard_response(None, 500, f"{operation_name}失败: {error_detail}")
                )
        return wrapper
    return decorator

# API请求处理中间件
async def api_request_handler(request: Request):
    """API请求处理中间件，设置请求ID等通用处理"""
    # 获取或生成请求ID
    request_id = request.headers.get("X-Request-ID", f"req-{id(request)}")
    # 设置上下文变量
    request_id_var.set(request_id)
    return request_id

def get_schema_api_router(**kwargs):
    """
    获取增强的API路由器（支持标准响应格式）
    
    Args:
        **kwargs: 路由器参数
        
    Returns:
        增强的APIRouter实例
    """
    try:
        # 创建标准APIRouter，但设置自定义的路由类
        router = APIRouter(route_class=SchemaAPIRoute, **kwargs)
        # 这里可以添加路由级别的中间件或依赖
        router.dependencies.append(Depends(api_request_handler))
        return router
    except Exception as e:
        # 异常情况下使用标准APIRouter
        from fastapi import APIRouter
        logger.error(f"创建API路由器失败: {e}")
        return APIRouter(**kwargs)

def get_client_ip(request: Request) -> str:
    """
    获取客户端IP地址，支持代理服务器
    
    Args:
        request: FastAPI请求对象
        
    Returns:
        客户端IP地址
    """
    # 尝试从X-Forwarded-For获取
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # 取第一个IP地址
        return forwarded_for.split(",")[0].strip()
    
    # 尝试从X-Real-IP获取
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    # 使用客户端直连IP
    return request.client.host if request.client else "unknown"

def log_request_info(request: Request, api_logger: Optional[logger] = None) -> None:
    """
    记录请求信息
    
    Args:
        request: FastAPI请求对象
        api_logger: 日志记录器，如果为None则使用默认记录器
    """
    if api_logger is None:
        api_logger = get_api_logger()
    
    # 记录请求信息
    client_ip = get_client_ip(request)
    user_agent = request.headers.get("User-Agent", "unknown")
    
    api_logger.debug(
        f"请求: {request.method} {request.url.path} | "
        f"客户端: {client_ip} | "
        f"UA: {user_agent}"
    ) 