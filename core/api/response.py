"""
API标准响应模块
定义API通用的标准响应格式和工具函数，使用fastapi-responseschema库
"""
from typing import Optional, Dict, Any, List, Union, TypeVar, Generic
from pydantic import BaseModel, Field

# 定义泛型类型变量
T = TypeVar('T')

# 这里导入fastapi-responseschema的组件 (实际使用时需要安装该库)
# from fastapi_responseschema import ResponseSchema, SchemaAPIRouter

# 通用响应结构（与fastapi-responseschema兼容）
class StandardResponse(BaseModel, Generic[T]):
    """
    标准API响应格式
    
    属性:
        code: 状态码，默认200表示成功
        message: 响应消息，默认"成功"
        data: 响应数据，类型为泛型T
    """
    code: int = Field(200, description="状态码")
    message: str = Field("成功", description="响应消息")
    data: Optional[T] = Field(None, description="响应数据")
    
    @classmethod
    def success(cls, data: T = None, message: str = "成功") -> "StandardResponse":
        """
        创建成功响应
        
        Args:
            data: 响应数据
            message: 响应消息
            
        Returns:
            StandardResponse: 成功的标准响应对象
        """
        return cls(code=200, message=message, data=data)
    
    @classmethod
    def error(cls, code: int = 500, message: str = "服务器内部错误", data: T = None) -> "StandardResponse":
        """
        创建错误响应
        
        Args:
            code: 错误状态码
            message: 错误消息
            data: 错误相关数据
            
        Returns:
            StandardResponse: 错误的标准响应对象
        """
        return cls(code=code, message=message, data=data)
    
    def dict(self, *args, **kwargs):
        """重写dict方法，确保None值也被包含在结果中"""
        result = super().dict(*args, **kwargs)
        return result

def create_standard_response(data, code=200, message="成功") -> Dict[str, Any]:
    """
    创建标准化的API响应格式（函数形式，便于简单使用）
    
    Args:
        data: 响应数据
        code: 状态码
        message: 响应消息
        
    Returns:
        dict: 标准化的响应字典
    """
    return StandardResponse(code=code, message=message, data=data).dict()

# 常用响应
SUCCESS = create_standard_response(None, 200, "成功")
BAD_REQUEST = create_standard_response(None, 400, "请求参数错误")
UNAUTHORIZED = create_standard_response(None, 401, "未授权的访问")
FORBIDDEN = create_standard_response(None, 403, "权限不足")
NOT_FOUND = create_standard_response(None, 404, "资源不存在")
SERVER_ERROR = create_standard_response(None, 500, "服务器内部错误")

# 分页响应
class PageInfo(BaseModel):
    """分页信息"""
    total: int = Field(0, description="总记录数")
    page: int = Field(1, description="当前页码")
    page_size: int = Field(20, description="每页记录数")
    total_pages: int = Field(0, description="总页数")

class PagedData(BaseModel, Generic[T]):
    """分页数据"""
    items: List[T] = Field([], description="数据列表")
    page_info: PageInfo = Field(..., description="分页信息")

def create_paged_response(items: List[Any], total: int, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
    """
    创建分页响应
    
    Args:
        items: 当前页的数据项列表
        total: 总记录数
        page: 当前页码
        page_size: 每页记录数
        
    Returns:
        dict: 标准分页响应
    """
    total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0
    page_info = PageInfo(
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )
    paged_data = PagedData(items=items, page_info=page_info)
    return create_standard_response(paged_data)

# 创建与fastapi-responseschema兼容的类和函数
# 这些功能在实际部署时由安装的库提供
class ResponseSchema(StandardResponse):
    """与fastapi-responseschema兼容的响应架构"""
    pass

# 创建适配器函数，便于后续切换到真正的库实现
def get_schema_api_router(*args, **kwargs):
    """
    获取SchemaAPIRouter的适配器函数
    
    使用说明:
    - 开发测试阶段：返回标准FastAPI路由器，不执行实际包装
    - 部署时：调整为使用实际的fastapi-responseschema.SchemaAPIRouter
    """
    from fastapi import APIRouter
    try:
        # 尝试导入fastapi-responseschema
        from fastapi_responseschema import SchemaAPIRouter
        return SchemaAPIRouter(*args, **kwargs)
    except ImportError:
        # 如果未安装，返回普通的APIRouter
        return APIRouter(*args, **kwargs)