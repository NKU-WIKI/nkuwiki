"""
微信小程序API模块
处理微信小程序的前后端交互
"""

from fastapi import APIRouter
from . import user, post, notification, feedback, about, action, banwords, comment

router = APIRouter()

# 为每个子模块的路由统一添加前缀
router.include_router(user.router, prefix="/user", tags=["wxapp-user"])
router.include_router(post.router, prefix="/post", tags=["wxapp-post"])
router.include_router(notification.router, prefix="/notification", tags=["wxapp-notification"])
router.include_router(feedback.router, prefix="/feedback", tags=["wxapp-feedback"])
router.include_router(about.router, prefix="/about", tags=["wxapp-about"])
router.include_router(action.router, prefix="/action", tags=["wxapp-action"])
router.include_router(banwords.router, prefix="/banwords", tags=["wxapp-banwords"])
router.include_router(comment.router, prefix="/comment", tags=["wxapp-comment"])

# 导出子模块，供外部使用
__all__ = [
    'router'
]
