"""
Agent功能API模块
提供对AI智能体的操作接口
"""
from core.api.common import get_schema_api_router

# 创建路由器
router = get_schema_api_router(
    prefix="/agent",
    tags=["Agent功能"],
    responses={404: {"description": "Not found"}}
)

# 导入子模块以注册路由
from core.api.agent import chat_api 