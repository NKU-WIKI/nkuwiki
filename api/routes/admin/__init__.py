"""
管理员API路由模块
"""
from fastapi import APIRouter
from . import system

router = APIRouter()
router.include_router(system.router)

__all__ = ["router"]