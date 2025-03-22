"""
API装饰器模块
提供API错误处理和日志记录等通用装饰器
"""
import functools
from fastapi import HTTPException, Depends
from loguru import logger
from typing import Callable
from core.api.common.dependencies import get_api_logger

def handle_api_errors(operation_name: str = "API操作"):
    """
    装饰器：统一处理API操作异常
    
    Args:
        operation_name: 操作名称，用于日志记录
    
    Returns:
        装饰后的函数
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, api_logger=Depends(get_api_logger), **kwargs):
            try:
                return await func(*args, api_logger=api_logger, **kwargs)
            except ValueError as e:
                # 输入验证错误
                api_logger.warning(f"{operation_name}输入验证错误: {str(e)}")
                raise HTTPException(status_code=400, detail=str(e))
            except HTTPException:
                # 直接传递HTTP异常
                raise
            except Exception as e:
                # 其他服务器错误
                api_logger.error(f"{operation_name}失败: {str(e)}")
                raise HTTPException(status_code=500, detail=f"{operation_name}失败: {str(e)}")
                
        return wrapper
    return decorator 