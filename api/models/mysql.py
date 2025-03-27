"""
MySQL查询相关数据模型
"""
from typing import Dict, List, Optional, Any, Union
from pydantic import Field, validator
from . import BaseAPIModel

class TableField(BaseAPIModel):
    """表字段信息"""
    Field: str = Field(..., description="字段名")
    Type: str = Field(..., description="字段类型")
    Null: str = Field(..., description="是否可为空")
    Key: str = Field(..., description="键类型")
    Default: Optional[str] = Field(None, description="默认值")
    Extra: str = Field(..., description="额外信息")

class QueryRequest(BaseAPIModel):
    """查询请求"""
    table_name: str = Field(..., min_length=1, description="表名")
    conditions: Dict[str, Any] = Field(default_factory=dict, description="查询条件")
    order_by: Optional[str] = Field(None, description="排序方式")
    limit: int = Field(20, ge=1, le=100, description="返回记录数量限制")
    offset: int = Field(0, ge=0, description="分页偏移量")

    @validator("table_name")
    def validate_table_name(cls, v):
        """验证表名"""
        if not v.strip():
            raise ValueError("表名不能为空")
        return v.strip()

class CountRequest(BaseAPIModel):
    """统计请求"""
    table_name: str = Field(..., min_length=1, description="表名")
    conditions: Dict[str, Any] = Field(default_factory=dict, description="统计条件")

    @validator("table_name")
    def validate_table_name(cls, v):
        """验证表名"""
        if not v.strip():
            raise ValueError("表名不能为空")
        return v.strip()

class CustomQueryRequest(BaseAPIModel):
    """自定义查询请求"""
    query: str = Field(..., min_length=1, description="SQL查询语句")
    params: List[Any] = Field(default_factory=list, description="查询参数")
    fetch: bool = Field(True, description="是否返回查询结果")

    @validator("query")
    def validate_query(cls, v):
        """验证SQL查询语句"""
        if not v.strip():
            raise ValueError("SQL查询语句不能为空")
        return v.strip()

# 导出所有模型
__all__ = [
    "TableField",
    "QueryRequest",
    "CountRequest",
    "CustomQueryRequest"
] 