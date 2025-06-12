"""
知识库API模块
处理知识库相关的交互，包括搜索等功能

主要使用knowledge模块提供知识检索功能
"""
from . import search  # 知识库接口
# 导出子模块，供外部使用
__all__ = ['search']