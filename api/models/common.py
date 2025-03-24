"""
通用数据模型
定义所有API共用的数据结构
"""
from typing import Dict, List, Any, Optional, TypeVar, Generic, Annotated
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum, IntEnum
from datetime import datetime
from fastapi.responses import JSONResponse
from fastapi import status, Query, Depends

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

class SortOrder(str, Enum):
    """排序顺序"""
    ASC = "asc"  # 升序
    DESC = "desc"  # 降序

# 基础模型类
class BaseFullModel(BaseModel):
    """基础模型类"""
    model_config = ConfigDict(from_attributes=True)

class BaseAPIModel(BaseFullModel):
    """基础API模型类"""
    model_config = ConfigDict(from_attributes=True)

# 带有时间戳的基础模型类
class BaseTimeStampModel(BaseAPIModel):
    """带有创建和更新时间的基础模型类"""
    create_time: Optional[datetime] = Field(None, description="创建时间")
    update_time: Optional[datetime] = Field(None, description="更新时间")

# 简单操作响应模型
class SimpleOperationResponse(BaseAPIModel):
    """简单操作响应模型"""
    success: bool = Field(True, description="操作是否成功")
    message: str = Field("success", description="操作消息")
    operation_id: Optional[str] = Field(None, description="操作ID，用于追踪操作")
    affected_items: Optional[int] = Field(None, description="受影响的记录数")

# ID响应模型
class IDResponse(BaseAPIModel):
    """ID响应模型"""
    id: Any = Field(..., description="记录ID")
    success: bool = Field(True, description="操作是否成功")
    message: str = Field("success", description="操作消息")

# 计数响应模型
class CountResponse(BaseAPIModel):
    """计数响应模型"""
    count: int = Field(..., description="记录数量")
    success: bool = Field(True, description="操作是否成功")
    message: str = Field("success", description="操作消息")

# 分页参数模型
class PaginationParams(BaseAPIModel):
    """分页参数模型"""
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(20, ge=1, le=100, description="每页数量")

# 分页参数依赖项
def pagination_params(
    page: Annotated[int, Query(ge=1, description="页码")] = 1,
    page_size: Annotated[int, Query(ge=1, le=100, description="每页数量")] = 20
) -> dict:
    """分页参数依赖项"""
    return {"page": page, "page_size": page_size}

# 排序参数模型
class SortParams(BaseAPIModel):
    """排序参数模型"""
    sort_by: Optional[str] = Field(None, description="排序字段名称")
    sort_order: SortOrder = Field(SortOrder.DESC, description="排序顺序")

# 排序参数依赖项
def sort_params(
    sort_by: Annotated[Optional[str], Query(description="排序字段名称")] = None,
    sort_order: Annotated[SortOrder, Query(description="排序顺序")] = SortOrder.DESC
) -> dict:
    """排序参数依赖项"""
    return {"sort_by": sort_by, "sort_order": sort_order}

# 组合分页和排序参数依赖项
def page_sort_params(
    pagination: dict = Depends(pagination_params),
    sort: dict = Depends(sort_params)
) -> dict:
    """组合分页和排序参数"""
    return {**pagination, **sort}

class PaginationInfo(BaseModel):
    """分页信息"""
    total: int = Field(description="总记录数")
    page: int = Field(description="当前页码")
    page_size: int = Field(description="每页数量")
    total_pages: int = Field(description="总页数")

class StandardResponseModel(BaseModel, Generic[T]):
    """标准响应模型"""
    model_config = ConfigDict(from_attributes=True)
    
    code: int = Field(StatusCode.SUCCESS, description="状态码")
    message: str = Field("success", description="响应消息")
    data: Optional[T] = Field(None, description="响应数据")
    details: Optional[Dict[str, Any]] = Field(None, description="额外详情")
    timestamp: datetime = Field(default_factory=datetime.now, description="响应时间戳")

class PagedResponseModel(StandardResponseModel[List[T]]):
    """分页响应模型"""
    data: Optional[List[T]] = Field(None, description="分页数据")
    pagination: Optional[PaginationInfo] = Field(None, description="分页信息")

def create_response(
    data: Any = None,
    message: str = "success",
    code: int = StatusCode.SUCCESS,
    details: Dict[str, Any] = None,
    headers: Dict[str, str] = None,
) -> JSONResponse:
    """创建标准响应"""
    response_model = StandardResponseModel(
        code=code,
        message=message,
        data=data,
        details=details,
        timestamp=datetime.now()
    )
    
    # 使用model_dump并手动处理datetime
    content = response_model.model_dump()
    
    # 手动处理timestamp
    if "timestamp" in content and isinstance(content["timestamp"], datetime):
        content["timestamp"] = content["timestamp"].strftime("%Y-%m-%d %H:%M:%S")
    
    return JSONResponse(
        content=content,
        status_code=code,
        headers=headers,
    )

def create_paged_response(
    items: List[Any],
    total: int,
    page: int,
    page_size: int,
    message: str = "success",
    details: Dict[str, Any] = None,
) -> JSONResponse:
    """创建分页响应"""
    pagination = PaginationInfo(
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size
    )
    
    response_model = PagedResponseModel(
        code=StatusCode.SUCCESS,
        message=message,
        data=items,
        pagination=pagination,
        details=details,
        timestamp=datetime.now()
    )
    
    # 使用model_dump并手动处理datetime
    content = response_model.model_dump()
    
    # 手动处理timestamp
    if "timestamp" in content and isinstance(content["timestamp"], datetime):
        content["timestamp"] = content["timestamp"].strftime("%Y-%m-%d %H:%M:%S")
    
    return JSONResponse(content=content)

# 响应工厂函数
def success(data: Any = None, message: str = "success", details: Dict[str, Any] = None) -> JSONResponse:
    """成功响应"""
    return create_response(data=data, message=message, details=details)

def error(code: int = StatusCode.INTERNAL_ERROR, message: str = "Internal server error", 
          details: Dict[str, Any] = None) -> JSONResponse:
    """错误响应"""
    return create_response(code=code, message=message, details=details)

def created(data: Any = None, message: str = "Created successfully") -> JSONResponse:
    """创建成功响应"""
    return create_response(data=data, message=message, code=StatusCode.CREATED)

def no_content(message: str = "Operation successful") -> JSONResponse:
    """无内容响应"""
    return create_response(message=message, code=StatusCode.NO_CONTENT)

def not_found(resource: str = "Resource", message: str = None) -> JSONResponse:
    """资源未找到响应"""
    return create_response(message=message or f"{resource} not found", code=StatusCode.NOT_FOUND)

def unauthorized(message: str = "Unauthorized") -> JSONResponse:
    """未认证响应"""
    return create_response(message=message, code=StatusCode.UNAUTHORIZED)

def forbidden(message: str = "Forbidden") -> JSONResponse:
    """权限不足响应"""
    return create_response(message=message, code=StatusCode.FORBIDDEN)

def bad_request(message: str = "Bad request", details: Dict[str, Any] = None) -> JSONResponse:
    """请求参数错误响应"""
    return create_response(message=message, code=StatusCode.BAD_REQUEST, details=details)

def conflict(message: str = "Resource conflict", details: Dict[str, Any] = None) -> JSONResponse:
    """资源冲突响应"""
    return create_response(message=message, code=StatusCode.CONFLICT, details=details)

def too_many_requests(message: str = "Too many requests", retry_after: int = None) -> JSONResponse:
    """请求频率限制响应"""
    headers = {"Retry-After": str(retry_after)} if retry_after else None
    return create_response(message=message, code=StatusCode.TOO_MANY_REQUESTS, headers=headers)
