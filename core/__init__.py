"""
Core模块，负责核心功能

此模块实现了智能体对话、贡献激励、平台治理等核心算法应用。
提供智能体管理、会话处理、身份验证等功能。

子模块:
- agent: 智能体应用，支持多种类型的AI引擎
- api: 提供API接口，包括对话和知识搜索
- auth: 处理认证和授权
- bridge: 桥接服务与智能体
- utils: 通用工具函数和类
"""
import os
import re
import sys
import json
import time
import requests
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Set, Union, Optional
sys.path.append(str(Path(__file__).resolve().parent.parent))

# ---------- 全局共享配置项 ----------
# 基础路径配置
LOG_PATH = Path(__file__).resolve().parent / "logs"
# 创建必要的目录
for path in [LOG_PATH]:
    path.mkdir(parents=True, exist_ok=True)

# 初始化核心日志
from core.utils.logger import register_logger, logger
# 注册core模块的日志记录器 - 使用DEBUG级别
core_logger = register_logger("core")
core_logger.debug("Core模块日志初始化完成")

# 在初始化日志后再导入Config，避免循环导入
from config import Config
# 导入配置
config = Config()

# 版本信息
__version__ = "1.0.0"

# 定义导出的符号列表 
__all__ = [
    # 基础库和工具
    'os', 'sys', 'Path', 'logger', 'core_logger', 'config', 're', 'json', 'time', 'datetime', 
    'Dict', 'List', 'Optional', 'Any', 'Set', 'datetime', 'timedelta', 'Union', 'requests', 'asyncio',
    # 路径配置
    'LOG_PATH'    
]

# core模块的公用配置和包
# 该模块负责核心功能，提供了全局共享的配置项和工具函数。
# 包含子模块：agent, bridge, auth, api, utils
# 提供的主要功能包括：
# 1. 智能体对话：通过agent子模块实现
# 2. 认证授权：通过auth子模块实现
# 3. 桥接服务：通过bridge子模块实现
# 4. API接口：通过api子模块实现
# 5. 工具函数：通过utils子模块实现
