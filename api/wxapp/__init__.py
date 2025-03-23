"""
微信小程序API模块
初始化文件
"""

from fastapi import APIRouter
from core.utils.logger import register_logger

# 注册模块专用日志记录器
logger = register_logger("api.wxapp")

# 记录模块初始化信息
logger.debug("api.wxapp模块初始化")

__all__ = []

# 导入所有API定义，使其注册到wxapp_router上
# 使用明确的导入代替通配符导入
import api.wxapp.user_api
import api.wxapp.post_api
import api.wxapp.comment_api
import api.wxapp.notification_api
import api.wxapp.search_api
import api.wxapp.feedback_api
import api.wxapp.about_api

# 空的__init__.py文件，避免任何循环导入问题
# 所有路由器和导入都在api/__init__.py中统一管理 