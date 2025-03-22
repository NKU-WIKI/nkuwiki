"""
API通用组件模块
提供API开发使用的通用工具和组件
"""
from functools import wraps
import traceback
from typing import Any, Dict, Callable

from fastapi import FastAPI, APIRouter, HTTPException, Request, Depends
from fastapi_responseschema.routing import SchemaAPIRoute
from fastapi_responseschema import AbstractResponseSchema, wrap_app_responses
from fastapi.responses import JSONResponse
from loguru import logger
from contextvars import ContextVar
from core.api.common.response import create_standard_response, StandardResponse
from core.api.common.exceptions import setup_exception_handlers
from core.api.common.decorators import handle_api_errors

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
    """创建标准响应格式"""
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