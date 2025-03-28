"""
智能体API模块
处理智能体相关的交互，包括RAG、聊天等功能

主要使用coze_rag模块提供知识检索增强生成功能
搜索和聊天功能作为辅助接口保留
"""

# 导入子模块，触发路由注册
from . import coze_rag  # Coze智能体RAG实现，主要接口
from . import search    # 搜索接口
from . import chat      # 聊天接口

# 导出子模块，供外部使用
__all__ = ['coze_rag', 'search', 'chat'] 