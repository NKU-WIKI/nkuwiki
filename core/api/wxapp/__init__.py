"""
微信小程序API模块
初始化文件，导入所有相关API接口
"""

from fastapi import APIRouter

# 创建路由器
router = APIRouter(prefix="/wxapp")

# 导入所有API接口
from core.api.wxapp import (
    user_api,
    post_api,
    comment_api,
    search_api,
    agent_api,
    notification_api,
    feedback_api,
    about_api
)

__all__ = [
    "router",
    "user_api",
    "post_api",
    "comment_api",
    "search_api",
    "agent_api",
    "notification_api",
    "feedback_api",
    "about_api"
]

# 自动导入其他已存在的API模块
# 这些导入语句已存在，不需要修改 