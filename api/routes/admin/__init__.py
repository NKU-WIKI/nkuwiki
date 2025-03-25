"""
管理员API路由模块
"""
from fastapi import APIRouter

# 创建管理员路由
admin_router = APIRouter(prefix="/admin", tags=["admin"])

# 导入子模块（放在最后避免循环导入）
from . import system

# 确保子模块能被导入
__all__ = ["admin_router", "system"] 