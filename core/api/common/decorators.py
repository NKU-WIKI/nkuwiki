"""
API装饰器模块
提供API错误处理等通用装饰器
"""
import functools
import traceback
from typing import Callable, Dict, Any
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from loguru import logger

def handle_api_errors(operation_name: str):
    """
    API错误处理装饰器
    捕获并处理API执行过程中的异常，返回标准格式响应
    
    Args:
        operation_name: 操作名称，用于日志记录
        
    Returns:
        装饰器函数
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # 获取请求对象(如果有)
            request = next((arg for arg in args if isinstance(arg, Request)), None)
            client_ip = request.client.host if request and request.client else "unknown"
            path = request.url.path if request else "unknown"
            
            # 检查api_logger是否在kwargs中
            api_logger = kwargs.get('api_logger', logger)
            
            # 记录请求开始
            api_logger.info(f"开始执行 [{operation_name}] - 路径: {path}, 客户端: {client_ip}")
            
            try:
                # 执行API处理函数
                response = await func(*args, **kwargs)
                
                # 记录成功响应
                api_logger.info(f"成功完成 [{operation_name}]")
                
                return response
            except HTTPException as e:
                # 处理HTTP异常
                api_logger.warning(
                    f"HTTP异常 [{operation_name}]: "
                    f"状态码={e.status_code}, "
                    f"详情='{e.detail}'"
                )
                
                # 返回标准格式响应
                return JSONResponse(
                    status_code=e.status_code,
                    content=create_standard_response(None, e.status_code, str(e.detail))
                )
            except Exception as e:
                # 处理其他异常
                error_detail = str(e)
                error_trace = traceback.format_exc()
                
                # 记录异常详情
                api_logger.error(
                    f"未捕获异常 [{operation_name}]: {error_detail}\n{error_trace}"
                )
                
                # 返回标准格式响应
                return JSONResponse(
                    status_code=500,
                    content=create_standard_response(None, 500, f"{operation_name}失败: {error_detail}")
                )
                
        return wrapper
    return decorator

def create_standard_response(data: Any = None, code: int = 200, message: str = "success") -> Dict[str, Any]:
    """
    创建标准响应格式
    
    Args:
        data: 响应数据
        code: 响应状态码
        message: 响应消息
        
    Returns:
        标准格式的响应字典
    """
    return {
        "code": code,
        "message": message,
        "data": data
    } 