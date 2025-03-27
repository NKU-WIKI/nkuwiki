"""
API中间件和异常处理模块
提供API请求处理中间件和全局异常处理
"""
import time
import traceback
import json
from typing import Callable, Dict, List, Any, Optional

from fastapi import Request, FastAPI
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from pydantic import ValidationError
from starlette.status import HTTP_422_UNPROCESSABLE_ENTITY

from core.utils.logger import register_logger
from api.models.common import StandardResponseModel, StatusCode
from .common import APIError

logger = register_logger("api")

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """API请求日志中间件，记录请求和响应信息"""
    
    async def dispatch(self, request: Request, call_next: Callable):
        """处理请求并记录日志"""
        # 跳过静态文件请求
        if request.url.path.startswith("/static"):
            return await call_next(request)
        
        # 记录请求开始时间
        start_time = time.time()
        
        # 获取请求信息
        client_host = request.client.host if request.client else "unknown"
        request_id = request.headers.get("X-Request-ID", "")
        
        # 记录请求信息
        logger.debug(
            f"Request: {request.method} {request.url.path} | "
            f"ClientIP: {client_host} | "
            f"ReqID: {request_id}"
        )
        
        # 处理请求
        try:
            response = await call_next(request)
            
            # 计算处理时间
            process_time = time.time() - start_time
            
            # 记录响应信息
            logger.debug(
                f"Response: {request.method} {request.url.path} | "
                f"Status: {response.status_code} | "
                f"Time: {process_time:.4f}s"
            )
            
            # 添加处理时间到响应头
            response.headers["X-Process-Time"] = str(process_time)
            
            return response
        except Exception as e:
            # 记录异常信息
            error_detail = str(e)
            error_trace = traceback.format_exc()
            
            logger.error(
                f"Error: {request.method} {request.url.path} | "
                f"Exception: {error_detail} | "
                f"Traceback: {error_trace}"
            )
            
            # 返回标准格式的500响应
            return JSONResponse(
                status_code=500,
                content=StandardResponseModel(
                    data=None,
                    code=StatusCode.INTERNAL_ERROR,
                    message=f"服务器内部错误: {error_detail}"
                ).dict()
            )

def format_validation_errors(error: ValidationError) -> List[Dict[str, Any]]:
    """格式化验证错误"""
    return [
        {
            "loc": e.get("loc", []),
            "msg": e.get("msg", ""),
            "type": e.get("type", "")
        }
        for e in error.errors()
    ]

def setup_exception_handlers(app: FastAPI):
    """设置全局异常处理器"""
    @app.exception_handler(APIError)
    async def api_error_handler(request: Request, exc: APIError):
        """处理APIError异常"""
        logger.error(f"API错误: {exc.message}")
        return JSONResponse(
            status_code=exc.code,
            content=StandardResponseModel.error(
                code=exc.code,
                message=exc.message,
                details=exc.details
            ).dict()
        )
    
    @app.exception_handler(ValidationError)
    async def validation_error_handler(request: Request, exc: ValidationError):
        """处理验证错误"""
        errors = format_validation_errors(exc)
        logger.error(f"验证错误: {errors}")
        return JSONResponse(
            status_code=HTTP_422_UNPROCESSABLE_ENTITY,
            content=StandardResponseModel.error(
                code=HTTP_422_UNPROCESSABLE_ENTITY,
                message="请求参数验证失败",
                details={"errors": errors}
            ).dict()
        ) 