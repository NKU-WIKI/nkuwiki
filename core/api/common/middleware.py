"""
API中间件模块
提供API请求处理中间件
"""
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from loguru import logger
import time
import traceback
from typing import Callable
from core.api.common import create_standard_response

class NotFoundMiddleware(BaseHTTPMiddleware):
    """
    404错误处理中间件
    捕获所有不匹配路由的请求并返回标准格式的404响应
    """
    
    async def dispatch(self, request: Request, call_next: Callable):
        """
        处理请求，捕获404错误
        """
        # 获取日志记录器
        api_logger = logger.bind(name="core.api.middleware")
        path = request.url.path
        
        # 记录请求开始
        client_host = request.client.host if request.client else "unknown"
        api_logger.debug(f"开始处理请求: {request.method} {path} (客户端: {client_host})")
        
        # 处理请求
        response = await call_next(request)
        
        # 检查是否为404错误
        if response.status_code == 404:
            api_logger.warning(
                f"404未找到: {request.method} {path} | "
                f"客户端: {client_host} | "
                f"UA: {request.headers.get('User-Agent', 'unknown')}"
            )
            
            # 返回标准格式的404响应
            return JSONResponse(
                status_code=404,
                content=create_standard_response(
                    data=None,
                    code=404,
                    message=f"未找到资源: {path}"
                )
            )
        
        return response

class APILoggingMiddleware(BaseHTTPMiddleware):
    """
    API日志中间件
    记录所有API请求和响应
    """
    
    async def dispatch(self, request: Request, call_next: Callable):
        """
        处理请求并记录日志
        """
        # 跳过静态文件请求
        if request.url.path.startswith("/static"):
            return await call_next(request)
        
        # 获取日志记录器
        api_logger = logger.bind(name="core.api.middleware")
        
        # 记录请求开始时间
        start_time = time.time()
        
        # 记录请求信息
        client_host = request.client.host if request.client else "unknown"
        request_id = request.headers.get("X-Request-ID", "")
        user_agent = request.headers.get("User-Agent", "")
        
        # 记录请求体（对于POST/PUT请求）
        request_body = ""
        if request.method in ["POST", "PUT"]:
            try:
                # 由于请求体只能被读取一次，我们需要克隆请求体
                body = await request.body()
                request_body = body.decode()
                # 重新设置请求体供后续处理
                request._body = body
            except Exception as e:
                api_logger.warning(f"无法读取请求体: {e}")
        
        # 打印请求信息
        request_log = (
            f"Request: {request.method} {request.url.path}?{request.url.query} | "
            f"ClientIP: {client_host} | "
            f"ReqID: {request_id} | "
            f"UA: {user_agent}"
        )
        if request_body:
            # 限制请求体长度以避免日志过大
            if len(request_body) > 500:
                request_body = request_body[:500] + "... [截断]"
            request_log += f" | Body: {request_body}"
        
        api_logger.info(request_log)
        
        # 处理请求
        try:
            response = await call_next(request)
            
            # 计算处理时间
            process_time = time.time() - start_time
            
            # 记录响应信息
            api_logger.info(
                f"Response: {request.method} {request.url.path} | "
                f"Status: {response.status_code} | "
                f"Time: {process_time:.4f}s | "
                f"ReqID: {request_id}"
            )
            
            # 添加处理时间到响应头
            response.headers["X-Process-Time"] = str(process_time)
            
            return response
        except Exception as e:
            # 记录异常信息
            error_detail = str(e)
            error_trace = traceback.format_exc()
            
            api_logger.error(
                f"Error: {request.method} {request.url.path} | "
                f"Exception: {error_detail} | "
                f"ReqID: {request_id} | "
                f"Traceback: {error_trace}"
            )
            
            # 返回标准格式的500响应
            return JSONResponse(
                status_code=500,
                content=create_standard_response(
                    data=None,
                    code=500,
                    message=f"服务器内部错误: {error_detail}"
                )
            ) 