"""
全局异常处理模块
提供统一的API异常处理
"""
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from loguru import logger
from core.api.common.response import create_standard_response

def setup_exception_handlers(app: FastAPI):
    """
    设置全局异常处理器
    
    Args:
        app: FastAPI应用实例
    """
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """HTTP异常处理器"""
        return JSONResponse(
            status_code=exc.status_code,
            content=create_standard_response(
                data=None,
                code=exc.status_code,
                message=str(exc.detail)
            )
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """通用异常处理器"""
        logger.error(f"未捕获的异常: {str(exc)}")
        return JSONResponse(
            status_code=500,
            content=create_standard_response(
                data=None,
                code=500,
                message=f"服务器内部错误: {str(exc)}"
            )
        ) 