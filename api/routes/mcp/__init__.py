"""
MCP (Model Context Protocol) API模块
提供数据库查询工具供Cursor Claude 访问
"""

# 导入子模块，触发路由注册
from . import db_mcp

# 导出子模块，供外部使用
__all__ = ['db_mcp'] 