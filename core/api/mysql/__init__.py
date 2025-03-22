"""
MySQL查询API模块
提供MySQL数据库访问的API接口
"""
from fastapi import APIRouter
from core.api.common import get_schema_api_router

# 创建路由器
router = get_schema_api_router(
    prefix="/mysql",
    tags=["MySQL查询"],
    responses={404: {"description": "Not found"}}
)

# 导入子模块以注册路由
from core.api.mysql import query_api 