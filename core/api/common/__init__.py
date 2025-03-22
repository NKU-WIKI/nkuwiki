"""
API通用组件模块
提供API开发使用的通用工具和组件
"""
from fastapi import FastAPI, APIRouter
from fastapi_responseschema.routing import SchemaAPIRoute
from fastapi_responseschema import AbstractResponseSchema, wrap_app_responses
from core.api.common.response import create_standard_response, StandardResponse
from core.api.common.exceptions import setup_exception_handlers
from core.api.common.dependencies import get_api_logger
from core.api.common.decorators import handle_api_errors

__all__ = [
    'create_standard_response',
    'StandardResponse',
    'setup_exception_handlers',
    'get_api_logger',
    'handle_api_errors',
    'get_schema_api_router'
]

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
        return router
    except Exception as e:
        # 异常情况下使用标准APIRouter
        from fastapi import APIRouter
        return APIRouter(**kwargs) 