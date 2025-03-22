"""
MySQL查询API
提供对MySQL数据库的查询功能
"""
import re
from fastapi import HTTPException, Path as PathParam, Depends
from pydantic import BaseModel, Field, validator
from typing import List, Dict, Any, Optional

# 导入通用组件
from core.api.common import get_api_logger, handle_api_errors, create_standard_response
from core.api.mysql import router

# 数据库相关导入
from etl.load import get_conn
from etl.load.py_mysql import query_records, count_records, execute_custom_query, get_nkuwiki_tables

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

# API端点
@router.get("/tables", response_model=TablesResponse)
@handle_api_errors("获取数据库表")
async def get_tables(api_logger=Depends(get_api_logger)):
    """获取数据库中所有表"""
    tables = get_nkuwiki_tables()
    return {"tables": tables}

@router.get("/table/{table_name}/structure", response_model=TableStructureResponse)
@handle_api_errors("获取表结构")
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

@router.post("/query", response_model=List[Dict[str, Any]])
@handle_api_errors("查询数据")
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

@router.post("/count", response_model=CountResponse)
@handle_api_errors("统计记录")
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

@router.post("/custom_query")
@handle_api_errors("自定义查询")
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