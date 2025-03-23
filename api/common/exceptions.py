"""
API异常处理模块
提供通用异常处理器
"""
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from pydantic import ValidationError
from loguru import logger
import traceback
from typing import Any, Dict, List

from api.common.decorators import create_standard_response, format_validation_errors

def setup_exception_handlers(app: FastAPI) -> None:
    """
    为FastAPI应用设置全局异常处理器
    
    Args:
        app: FastAPI应用实例
    """
    # 处理请求验证错误
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """全局请求参数验证错误处理器"""
        # 格式化错误信息
        error_details = format_validation_errors(exc.errors())
        error_msg = f"参数验证错误: {error_details}"
        
        # 记录日志
        logger.warning(
            f"请求验证错误 [{request.method} {request.url.path}]: {error_details}"
        )
        
        # 返回标准格式响应
        return JSONResponse(
            status_code=422,
            content=create_standard_response(
                data={"errors": exc.errors()},
                code=422,
                message=error_msg
            )
        )
    
    # 处理Pydantic验证错误
    @app.exception_handler(ValidationError)
    async def pydantic_validation_exception_handler(request: Request, exc: ValidationError):
        """全局Pydantic验证错误处理器"""
        # 格式化错误信息
        error_details = format_validation_errors(exc.errors())
        error_msg = f"数据验证错误: {error_details}"
        
        # 记录日志
        logger.warning(
            f"数据验证错误 [{request.method} {request.url.path}]: {error_details}"
        )
        
        # 返回标准格式响应
        return JSONResponse(
            status_code=422,
            content=create_standard_response(
                data={"errors": exc.errors()},
                code=422,
                message=error_msg
            )
        )
    
    # 处理HTTP异常
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        """全局HTTP异常处理器"""
        # 特别处理404错误
        if exc.status_code == 404:
            logger.warning(
                f"404未找到: {request.method} {request.url.path} | "
                f"客户端: {request.client.host if request.client else 'unknown'}"
            )
        else:
            logger.warning(
                f"HTTP异常 [{request.method} {request.url.path}]: "
                f"状态码={exc.status_code}, 详情='{exc.detail}'"
            )
        
        # 返回标准格式响应
        return JSONResponse(
            status_code=exc.status_code,
            content=create_standard_response(
                data=None,
                code=exc.status_code,
                message=str(exc.detail)
            )
        )
    
    # 处理所有其他异常
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """全局通用异常处理器"""
        # 记录详细的错误信息
        error_detail = str(exc)
        error_trace = traceback.format_exc()
        
        logger.error(
            f"未捕获异常 [{request.method} {request.url.path}]: {error_detail}\n{error_trace}"
        )
        
        # 返回标准格式响应
        return JSONResponse(
            status_code=500,
            content=create_standard_response(
                data=None,
                code=500,
                message=f"服务器内部错误: {error_detail}"
            )
        ) 