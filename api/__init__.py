"""
API模块，负责提供HTTP API接口

此模块提供了项目的所有 HTTP API 接口，支持各类客户端进行交互。
主要包括微信小程序接口、知识库检索接口和管理接口。

子模块:
- models: 数据模型定义
- common: 通用工具函数
- routes: 路由定义
  - wxapp: 微信小程序接口
  - knowledge: 知识库接口
  - agent: 智能体接口
"""
from api.routes import router
from core.utils.logger import register_logger

# 创建API模块专用日志器
api_logger = register_logger("api")

# 版本信息
__version__ = "1.0.0"

# 定义导出的符号列表
__all__ = [
    "router",
    "api_logger",
    "__version__"
]