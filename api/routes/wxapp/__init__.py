"""
微信小程序API模块
处理微信小程序的前后端交互
"""

from fastapi import APIRouter

# 导入子模块，触发路由注册
from . import user
from . import post
from . import comment
from . import notification
from . import feedback
from . import about
from . import search
from . import action

# 导出子模块，供外部使用
__all__ = [
    'user', 'post', 'comment', 'notification', 
    'feedback', 'about', 'search', 'action'
]
