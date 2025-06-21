"""
通用数据模型
"""
from typing import Dict, List, Any, Optional, TypeVar, Generic, Annotated
from pydantic import BaseModel, Field, ConfigDict, model_validator
from enum import Enum, IntEnum
from datetime import datetime, date
import json
from fastapi import status, Request as FastAPIRequest
from fastapi.responses import JSONResponse

# 定义泛型类型变量
T = TypeVar('T')

class StatusCode(IntEnum):
    """状态码枚举"""
    SUCCESS = status.HTTP_200_OK
    CREATED = status.HTTP_201_CREATED
    ACCEPTED = status.HTTP_202_ACCEPTED
    NO_CONTENT = status.HTTP_204_NO_CONTENT
    BAD_REQUEST = status.HTTP_400_BAD_REQUEST
    UNAUTHORIZED = status.HTTP_401_UNAUTHORIZED
    FORBIDDEN = status.HTTP_403_FORBIDDEN
    NOT_FOUND = status.HTTP_404_NOT_FOUND
    METHOD_NOT_ALLOWED = status.HTTP_405_METHOD_NOT_ALLOWED
    CONFLICT = status.HTTP_409_CONFLICT
    UNPROCESSABLE_ENTITY = status.HTTP_422_UNPROCESSABLE_ENTITY
    TOO_MANY_REQUESTS = status.HTTP_429_TOO_MANY_REQUESTS
    INTERNAL_ERROR = status.HTTP_500_INTERNAL_SERVER_ERROR
    SERVICE_UNAVAILABLE = status.HTTP_503_SERVICE_UNAVAILABLE

# 自定义JSON编码器，处理特殊类型如datetime
class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, date):
            return obj.isoformat()
        return super().default(obj)

# 递归处理对象，使其可JSON序列化
def process_json_data(obj):
    if isinstance(obj, dict):
        return {k: process_json_data(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [process_json_data(i) for i in obj]
    elif isinstance(obj, (datetime, date)):
        return obj.isoformat()
    elif hasattr(obj, 'model_dump'):
        # 支持Pydantic v2模型
        return process_json_data(obj.model_dump())
    elif hasattr(obj, 'dict'):
        # 支持Pydantic v1模型
        return process_json_data(obj.dict())
    return obj

# 基础模型类
class BaseAPI(BaseModel):
    """API基础模型"""
    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={datetime: lambda dt: dt.isoformat()}
    )

# 带有时间戳的基础模型类
class BaseTimeStamp(BaseAPI):
    """带有创建和更新时间的基础模型类"""
    create_time: Optional[datetime] = Field(None, description="创建时间")
    update_time: Optional[datetime] = Field(None, description="更新时间")

class PaginationInfo(BaseAPI):
    """分页信息"""
    total: int = Field(description="总记录数")
    page: int = Field(description="当前页码")
    page_size: int = Field(description="每页数量")
    total_pages: Optional[int] = Field(None, description="总页数")
    has_more: Optional[bool] = Field(None, description="是否还有更多")

    @model_validator(mode='after')
    def calculate_pagination_fields(self) -> 'PaginationInfo':
        if self.page_size > 0:
            self.total_pages = (self.total + self.page_size - 1) // self.page_size
        else:
            self.total_pages = 0
        
        self.has_more = self.page * self.page_size < self.total
        return self

class Request(FastAPIRequest):
    """请求基类，包装FastAPIRequest并添加openid属性"""
    openid: Optional[str] = None
    pagination: Optional[PaginationInfo] = Field(None, description="分页信息")
    async def json(self):
        """重写json方法获取请求体数据"""
        body = await super().json()
        # 如果请求体中有openid，自动提取并设置到实例属性
        if isinstance(body, dict) and "openid" in body:
            self.openid = body["openid"]
        return body

class RequestData(BaseAPI):
    """请求数据模型，用于验证请求数据"""
    openid: Optional[str] = Field(None, description="用户openid")
    pagination: Optional[PaginationInfo] = Field(None, description="分页信息")

class Response(JSONResponse):
    """自定义响应类，兼容Pydantic V2"""
    
    media_type = "application/json"
    
    def __init__(
        self,
        content: Any = None,
        code: int = StatusCode.SUCCESS,
        message: str = "success",
        data: Any = None,
        details: Optional[Dict[str, Any]] = None,
        timestamp: Optional[datetime] = None,
        pagination: Optional[PaginationInfo] = None,
        status_code: int = 200,
        headers: Optional[Dict[str, str]] = None,
        **kwargs
    ):
        """
        初始化Response对象
        
        注意: 构造函数支持两种调用方式:
        1. 标准方式: Response(data=数据, message=消息)
        2. 直接传递content: Response(content=完整响应字典)
        """
        if content is not None and isinstance(content, dict):
            # 如果直接传递了完整内容，则使用它
            response_content = content
        else:
            # 处理数据，确保可以JSON序列化
            processed_data = process_json_data(data)
            processed_details = process_json_data(details)
            processed_pagination = process_json_data(pagination)
            
            # 构造标准响应格式
            response_content = {
                "code": code,
                "message": message,
                "data": processed_data,
                "details": processed_details,
                "timestamp": timestamp.isoformat() if timestamp else datetime.now().isoformat(),
                "pagination": processed_pagination
            }
        
        # 使用自定义JSON编码器
        kwargs["content"] = response_content
        kwargs["status_code"] = status_code
        kwargs["headers"] = headers
        
        # 使用自定义JSON编码器
        super().__init__(**kwargs)
        
    def render(self, content: Any) -> bytes:
        """重写渲染方法，使用自定义JSON编码器"""
        return json.dumps(
            content,
            ensure_ascii=False,
            allow_nan=False,
            indent=None,
            separators=(",", ":"),
            cls=CustomJSONEncoder
        ).encode("utf-8")
    
    # 以下为标准响应工厂方法
    @classmethod
    def success(cls, data: Any = None, message: str = "success", details: Dict[str, Any] = None):
        """成功响应"""
        return cls(
            code=StatusCode.SUCCESS,
            message=message,
            data=data,
            details=details,
            status_code=StatusCode.SUCCESS
        )
    
    @classmethod
    def error(cls, code: int = StatusCode.INTERNAL_ERROR, message: str = "未捕获的错误", 
             details: Dict[str, Any] = None):
        """错误响应"""
        return cls(
            code=code,
            message=message,
            details=details,
            status_code=code
        )
    
    @classmethod
    def internal_error(cls, message: str = "Internal server error", details: Dict[str, Any] = None):
        """内部服务器错误响应"""
        return cls(
            code=StatusCode.INTERNAL_ERROR,
            message=message,
            details=details,
            status_code=StatusCode.INTERNAL_ERROR
        )
    
    @classmethod
    def created(cls, data: Any = None, message: str = "Created successfully", details: Dict[str, Any] = None):
        """创建成功响应"""
        return cls(
            data=data,
            message=message, 
            code=StatusCode.CREATED, 
            details=details,
            status_code=StatusCode.CREATED
        )
    
    @classmethod
    def not_found(cls, resource: str = "Resource", message: Optional[str] = None):
        """资源未找到响应"""
        return cls(
            message=message or f"{resource} not found", 
            code=StatusCode.NOT_FOUND,
            status_code=StatusCode.NOT_FOUND
        )
    
    @classmethod
    def bad_request(cls, message: str = "Bad request", details: Dict[str, Any] = None):
        """请求参数错误响应"""
        return cls(
            message=message, 
            code=StatusCode.BAD_REQUEST, 
            details=details,
            status_code=StatusCode.BAD_REQUEST
        )
    
    @classmethod
    def forbidden(cls, message: str = "Permission denied", details: Dict[str, Any] = None):
        """权限错误响应"""
        return cls(
            message=message, 
            code=StatusCode.FORBIDDEN, 
            details=details,
            status_code=StatusCode.FORBIDDEN
        )
    
    @classmethod
    def unauthorized(cls, message: str = "Unauthorized access", details: Dict[str, Any] = None):
        """未授权响应"""
        return cls(
            message=message, 
            code=StatusCode.UNAUTHORIZED, 
            details=details,
            status_code=StatusCode.UNAUTHORIZED
        )
    
    @classmethod
    def conflict(cls, message: str = "Resource conflict", details: Dict[str, Any] = None):
        """资源冲突响应"""
        return cls(
            message=message, 
            code=StatusCode.CONFLICT, 
            details=details,
            status_code=StatusCode.CONFLICT
        )
    
    @classmethod
    def service_unavailable(cls, message: str = "Service temporarily unavailable", 
                          details: Dict[str, Any] = None):
        """服务不可用响应"""
        return cls(
            message=message, 
            code=StatusCode.SERVICE_UNAVAILABLE, 
            details=details,
            status_code=StatusCode.SERVICE_UNAVAILABLE
        )
    
    @classmethod
    def too_many_requests(cls, message: str = "Too many requests", details: Dict[str, Any] = None):
        """请求过多响应"""
        return cls(
            message=message, 
            code=StatusCode.TOO_MANY_REQUESTS, 
            details=details,
            status_code=StatusCode.TOO_MANY_REQUESTS
        )
    
    @classmethod
    def method_not_allowed(cls, message: str = "Method not allowed", details: Dict[str, Any] = None):
        """方法不允许响应"""
        return cls(
            message=message, 
            code=StatusCode.METHOD_NOT_ALLOWED, 
            details=details,
            status_code=StatusCode.METHOD_NOT_ALLOWED
        )
    
    @classmethod
    def validation_error(cls, errors: List[Dict[str, Any]], 
                       message: str = "Validation error"):
        """验证错误响应"""
        return cls(
            message=message, 
            code=StatusCode.BAD_REQUEST, 
            details={"errors": errors},
            status_code=StatusCode.BAD_REQUEST
        )
    
    @classmethod
    def db_error(cls, message: str = "Database operation failed", details: Dict[str, Any] = None):
        """数据库错误响应"""
        return cls(
            message=message, 
            code=StatusCode.INTERNAL_ERROR, 
            details=details,
            status_code=StatusCode.INTERNAL_ERROR
        )
    
    @classmethod
    def no_content(cls):
        """无内容响应"""
        return cls(
            code=StatusCode.NO_CONTENT, 
            message="No content",
            status_code=StatusCode.NO_CONTENT
        )
    
    @classmethod
    def accepted(cls, message: str = "Request accepted"):
        """请求已接受响应"""
        return cls(
            code=StatusCode.ACCEPTED, 
            message=message,
            status_code=StatusCode.ACCEPTED
        )
    
    @classmethod
    def paged(cls, data: Any = None, pagination: Any = None, 
             message: str = "success", details: Dict[str, Any] = None):
        """分页响应"""
        # 确保pagination是字典类型
        if pagination and hasattr(pagination, 'model_dump'):
            pagination = pagination.model_dump()
        elif pagination and hasattr(pagination, 'dict'):
            pagination = pagination.dict()
        
        return cls(
            code=StatusCode.SUCCESS,
            message=message,
            data=data,
            pagination=pagination,
            details=details,
            status_code=StatusCode.SUCCESS
        )
        
def validate_params(req_data: Dict, required_params: List[str]) -> Optional[JSONResponse]:
    """
    通用参数验证函数 (同步)

    Args:
        req_data (Dict): 请求数据字典
        required_params (List[str]): 必需参数列表

    Returns:
        Optional[JSONResponse]: 错误响应，如果验证通过则返回 None
    """
    required_params = list(required_params)  # 创建副本，避免修改原参数
    required_params.append("openid")  # 添加openid作为必需参数
    missing_params = [param for param in required_params if param not in req_data]
    if missing_params:
        return Response.bad_request(message=f"缺少必要参数: {', '.join(missing_params)}")
    return None

