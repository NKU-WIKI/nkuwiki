"""
API路由模块
包含所有API路由的定义
"""

# 导入子模块，触发路由注册
# 注意导入顺序，避免循环导入
from api.routes import agent    # 智能体相关路由
from api.routes import wxapp    # 微信小程序相关路由
from api.routes import admin    # 管理员相关路由

# 确保子模块能被导入
__all__ = ["wxapp", "agent", "admin"] 