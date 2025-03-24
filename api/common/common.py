"""
API通用模块
提供API相关的通用功能，包括响应格式、装饰器、中间件等
"""
# 标准库导入
from contextvars import ContextVar
from typing import Any, Callable, Optional, Dict, List, Union
from datetime import datetime

# 第三方库导入
from fastapi import APIRouter, Request, Depends, FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from starlette.status import HTTP_422_UNPROCESSABLE_ENTITY

# 本地导入
from core.utils.logger import register_logger
from api.models.common import create_response, StatusCode, StandardResponseModel

# 初始化API通用日志记录器
api_logger = register_logger("api")

# 请求ID上下文变量
request_id_var: ContextVar[str] = ContextVar('request_id', default='')

# API错误基类
class APIError(Exception):
    """API错误基类"""
    def __init__(self, message: str, code: int = 500, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(message)

# 格式化工具
def format_response_content(content: Any) -> Any:
    """格式化响应内容，处理特殊类型"""
    if isinstance(content, (dict, list)):
        return process_json_fields(content)
    elif isinstance(content, datetime):
        return content.isoformat()
    return content

def process_json_fields(data: Union[Dict, List]) -> Union[Dict, List]:
    """处理JSON字段，格式化特殊类型"""
    if isinstance(data, dict):
        return {k: process_json_fields(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [process_json_fields(item) for item in data]
    elif isinstance(data, datetime):
        return data.isoformat()
    return data

# API请求处理中间件
async def api_request_handler(request: Request):
    """API请求处理中间件，设置请求ID等通用处理"""
    # 获取或生成请求ID
    request_id = request.headers.get("X-Request-ID", f"req-{id(request)}")
    # 设置上下文变量
    request_id_var.set(request_id)
    return request_id

def get_schema_api_router(**kwargs):
    """获取增强的API路由器（支持标准响应格式）"""
    router = APIRouter(**kwargs)
    # 添加路由级别的中间件或依赖
    router.dependencies.append(Depends(api_request_handler))
    return router 