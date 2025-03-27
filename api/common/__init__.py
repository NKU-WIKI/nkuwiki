"""
API通用模块
提供API相关的通用功能，包括响应格式、装饰器、中间件等
"""
# 导入FastAPI相关类
from fastapi import APIRouter, Request, Depends

# 从common.py导入核心功能
from .common import (
    api_logger,
    request_id_var,
    APIError,
    format_response_content,
    process_json_fields,
    get_schema_api_router
)

# 从decorators.py导入装饰器
from .decorators import (
    handle_api_errors,
    require_permissions
)

# 从middleware.py导入中间件相关
from .middleware import (
    RequestLoggingMiddleware,
    setup_exception_handlers
)

# 模块公开的函数和类
__all__ = [
    # 核心功能
    'api_logger',
    'request_id_var',
    'APIError',
    'format_response_content',
    'process_json_fields',
    
    # 装饰器
    'handle_api_errors',
    'require_permissions',
    
    # 中间件
    'RequestLoggingMiddleware',
    'setup_exception_handlers',
    
    # 路由相关
    'get_schema_api_router',
    'get_api_logger_dep'
]

# API请求处理中间件
async def api_request_handler(request: Request):
    """API请求处理中间件，设置请求ID等通用处理"""
    # 获取或生成请求ID
    request_id = request.headers.get("X-Request-ID", f"req-{id(request)}")
    # 设置上下文变量
    request_id_var.set(request_id)
    return request_id

# API日志处理器依赖
def get_api_logger_dep():
    """获取API日志记录器依赖"""
    return api_logger 