"""
微信小程序API模块
提供微信小程序相关功能的API接口
"""
from core.api.common import get_schema_api_router

# 创建路由器
router = get_schema_api_router(
    prefix="/wxapp",
    tags=["微信小程序"],
    responses={404: {"description": "Not found"}}
)

# 导入子模块以注册路由
from core.api.wxapp import user_api
from core.api.wxapp import post_api
from core.api.wxapp import comment_api 