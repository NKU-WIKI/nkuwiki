"""
API装饰器模块
提供API错误处理等常用装饰器和工具函数
"""
from functools import wraps
import traceback
import json
from typing import Any, Dict, Callable, List, TypeVar, Optional, Union
from fastapi import HTTPException, Request
from core.utils.logger import register_logger
from pydantic import ValidationError
from api.models.common import create_response, StatusCode

logger = register_logger("api")
T = TypeVar('T')

def format_validation_errors(error: ValidationError) -> List[Dict[str, Any]]:
    """格式化Pydantic验证错误"""
    return [{
        "loc": e.get("loc", []),
        "msg": e.get("msg", ""),
        "type": e.get("type", "")
    } for e in error.errors()]

def handle_api_errors(operation_name: str = "API操作"):
    """
    装饰器：确保API接口返回标准响应格式，并处理异常
    如果路由定义了response_model，还会验证返回数据是否符合模型
    
    Args:
        operation_name: 操作名称，用于日志记录
    """
    def decorator(func: Callable[..., T]):
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            try:
                result = await func(*args, **kwargs)
                
                # 如果结果已经是JSONResponse实例，直接返回
                if hasattr(result, "status_code"):
                    return result
                
                # 获取路由的response_model（如果有）
                response_model = None
                # 尝试从函数对象中获取FastAPI设置的路由信息
                if hasattr(func, "__fastapi_route__"):
                    route_info = getattr(func, "__fastapi_route__")
                    response_model = getattr(route_info, "response_model", None)
                
                # 如果有response_model且不是None，验证返回数据
                if response_model is not None:
                    try:
                        # 如果返回的不是字典，转换为字典
                        if not isinstance(result, dict) and hasattr(result, "dict"):
                            result_dict = result.dict()
                        elif not isinstance(result, dict) and hasattr(result, "model_dump"):
                            result_dict = result.model_dump()
                        else:
                            result_dict = result
                        
                        # 使用response_model验证数据
                        validated_data = response_model(**result_dict)
                        # 使用验证后的数据
                        result = validated_data
                        
                    except ValidationError as e:
                        # 记录验证错误但不抛出异常，仍然返回原始数据
                        logger.warning(
                            f"{operation_name}响应不符合response_model要求: {str(e)}"
                        )
                
                # 包装为标准响应格式
                return create_response(data=result)
                
            except HTTPException as e:
                # FastAPI的HTTP异常
                logger.warning(f"{operation_name}失败: HTTP {e.status_code} - {e.detail}")
                return create_response(
                    message=e.detail,
                    code=e.status_code
                )
                    
            except ValidationError as e:
                # Pydantic验证错误
                errors = format_validation_errors(e)
                error_message = "请求参数验证失败"
                
                # 添加更详细的错误日志
                logger.warning(
                    f"{operation_name}失败: 验证错误 - {error_message}\n"
                    f"详细错误: {json.dumps(errors, ensure_ascii=False)}\n"
                    f"原始错误: {str(e)}\n"
                    f"错误字段: {['.'.join(map(str, err.get('loc', []))) for err in errors]}"
                )
                
                return create_response(
                    message=error_message,
                    code=StatusCode.BAD_REQUEST,
                    details={"errors": errors}
                )
                
            except Exception as e:
                # 其他异常
                error_detail = str(e)
                error_trace = traceback.format_exc()
                
                logger.error(
                    f"{operation_name}发生未处理异常: {error_detail}\n{error_trace}"
                )
                
                return create_response(
                    message=f"{operation_name}失败: {error_detail}",
                    code=StatusCode.INTERNAL_ERROR
                )
        
        return wrapper
    return decorator

def require_permissions(permissions: List[str] = None):
    """
    装饰器：要求接口具有特定权限
    
    Args:
        permissions: 需要的权限列表
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            # 这里需要实现权限验证逻辑
            return await func(request, *args, **kwargs)
        return wrapper
    return decorator

__all__ = [
    "handle_api_errors",
    "require_permissions"
] 