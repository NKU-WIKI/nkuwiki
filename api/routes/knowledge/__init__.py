"""
知识库API模块
处理知识库相关的交互，包括搜索等功能

主要使用knowledge模块提供知识检索功能
"""
from . import search  # 知识库接口
from . import insights
from fastapi import APIRouter

from .search import router as search_router
from .insights import router as insights_router

router = APIRouter()
router.include_router(search_router)
router.include_router(insights_router)

# 导出子模块，供外部使用
__all__ = ['search']