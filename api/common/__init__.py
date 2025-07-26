"""
API通用模块
提供API相关的通用功能，包括响应格式、装饰器、中间件等
"""

from .utils import (
    request_id_var,
    APIError,
    get_schema_api_router,
    stream_response
)

__all__ = [
    'request_id_var',
    'APIError',
    'get_schema_api_router',
    'stream_response'
]
