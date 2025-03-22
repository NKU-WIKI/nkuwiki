"""
MySQL查询API接口
提供对MySQL数据库的查询功能
"""
import re
from fastapi import APIRouter, HTTPException, Path as PathParam, Depends
from pydantic import BaseModel, Field, validator
from typing import List, Dict, Any, Optional, Union, Callable
from loguru import logger
from fastapi.responses import JSONResponse

# 导入标准响应模块
from core.api.response import create_standard_response, StandardResponse, get_schema_api_router

# 数据库相关导入
from etl.load import get_conn
from etl.load.py_mysql import query_records, count_records, execute_custom_query, get_nkuwiki_tables

# 创建专用API路由
mysql_router = get_schema_api_router(
    prefix="/mysql",
    tags=["MySQL查询"],
    responses={404: {"description": "Not found"}},
)

# 添加异常处理中间件
# 注释掉路由器上的异常处理器，移动到全局异常处理
'''
@mysql_router.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """自定义HTTP异常处理器，确保异常也返回标准格式"""
    return JSONResponse(
        status_code=exc.status_code,
        content=create_standard_response(
            data=None,
            code=exc.status_code,
            message=str(exc.detail)
        )
    )

@mysql_router.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """通用异常处理器，确保所有异常都返回标准格式"""
    logger.error(f"未捕获的异常: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content=create_standard_response(
            data=None,
            code=500,
            message=f"服务器内部错误: {str(exc)}"
        )
    )
'''

# 请求和响应模型
class TablesResponse(BaseModel):
    tables: List[str] = Field(..., description="数据库中的表列表")

class TableStructureResponse(BaseModel):
    fields: List[Dict[str, Any]] = Field(..., description="表结构")

class QueryRequest(BaseModel):
    table_name: str = Field(..., description="要查询的表名")
    conditions: Optional[Dict[str, Any]] = Field(default={}, description="查询条件")
    order_by: Optional[str] = Field(default=None, description="排序字段")
    limit: int = Field(default=100, ge=1, le=1000, description="返回记录数量上限")
    offset: int = Field(default=0, ge=0, description="分页偏移量")
    
    @validator('table_name')
    def validate_table_name(cls, v):
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', v):
            raise ValueError(f"非法表名: {v}")
        return v

class CountRequest(BaseModel):
    table_name: str = Field(..., description="要统计的表名")
    conditions: Optional[Dict[str, Any]] = Field(default={}, description="统计条件")
    
    @validator('table_name')
    def validate_table_name(cls, v):
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', v):
            raise ValueError(f"非法表名: {v}")
        return v

class CountResponse(BaseModel):
    count: int = Field(..., description="记录数量")

class CustomQueryRequest(BaseModel):
    query: str = Field(..., description="自定义SQL查询语句")
    params: Optional[List[Any]] = Field(default=None, description="查询参数")
    fetch: bool = Field(default=True, description="是否获取结果")
    
    @validator('query')
    def validate_query(cls, v):
        # 简单防注入检查
        sql_lower = v.lower()
        if any(cmd in sql_lower for cmd in ["insert", "update", "delete", "drop", "alter", "truncate"]):
            raise ValueError("仅支持SELECT查询")
        return v

# 依赖项函数
def get_api_logger():
    """提供API日志记录器"""
    return logger.bind(module="mysql_api")

# 错误处理函数
def handle_db_error(func: Callable) -> Callable:
    """装饰器：统一处理数据库操作异常"""
    import functools
    
    @functools.wraps(func)
    async def wrapper(*args, api_logger=Depends(get_api_logger), **kwargs):
        try:
            return await func(*args, api_logger=api_logger, **kwargs)
        except ValueError as e:
            # 输入验证错误
            api_logger.warning(f"输入验证错误: {str(e)}")
            raise HTTPException(status_code=400, detail=str(e))
        except HTTPException:
            # 直接传递HTTP异常
            raise
        except Exception as e:
            # 其他服务器错误
            api_logger.error(f"数据库操作失败: {str(e)}")
            raise HTTPException(status_code=500, detail=f"操作失败: {str(e)}")
    
    return wrapper

# API端点
@mysql_router.get("/tables", response_model=TablesResponse)
@handle_db_error
async def get_tables(api_logger=Depends(get_api_logger)):
    """获取数据库中所有表"""
    tables = get_nkuwiki_tables()
    return {"tables": tables}

@mysql_router.get("/table/{table_name}/structure", response_model=TableStructureResponse)
@handle_db_error
async def get_table_structure(
    table_name: str = PathParam(..., description="表名"),
    api_logger=Depends(get_api_logger)
):
    """获取表结构"""
    # 验证表名
    if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', table_name):
        raise ValueError(f"非法表名: {table_name}")
        
    # 获取表结构
    structure = execute_custom_query(f"DESCRIBE {table_name}")
    if not structure:
        raise HTTPException(status_code=404, detail=f"表 {table_name} 不存在")
    return {"fields": structure}

@mysql_router.post("/query", response_model=List[Dict[str, Any]])
@handle_db_error
async def query_data(
    request: QueryRequest,
    api_logger=Depends(get_api_logger)
):
    """查询表数据"""
    records = query_records(
        table_name=request.table_name,
        conditions=request.conditions,
        order_by=request.order_by,
        limit=request.limit,
        offset=request.offset
    )
    return records

@mysql_router.post("/count", response_model=CountResponse)
@handle_db_error
async def count_data(
    request: CountRequest,
    api_logger=Depends(get_api_logger)
):
    """统计记录数量"""
    count = count_records(
        table_name=request.table_name,
        conditions=request.conditions
    )
    if count < 0:
        raise Exception("统计记录失败")
    return {"count": count}

@mysql_router.post("/custom_query")
@handle_db_error
async def custom_query(
    request: CustomQueryRequest,
    api_logger=Depends(get_api_logger)
):
    """执行自定义SQL查询"""
    result = execute_custom_query(
        query=request.query,
        params=tuple(request.params) if request.params else None,
        fetch=request.fetch
    )
    return {"result": result} 