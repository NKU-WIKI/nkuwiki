"""
core模块，负责核心功能
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
from loguru import logger
from typing import Dict, List, Any, Set, Union, Optional
sys.path.append(str(Path(__file__).resolve().parent.parent))
from config import Config
# 导入配置
config = Config()
config.load_config()

# ---------- 全局共享配置项 ----------
# 基础路径配置
LOG_PATH = Path(__file__).resolve().parent / "logs"
# 创建必要的目录
for path in [LOG_PATH]:
    path.mkdir(parents=True, exist_ok=True)

# 设置日志目录
LOG_PATH.mkdir(exist_ok=True, parents=True)
logger.add(LOG_PATH / "core.log", rotation="1 day", retention="3 months", level="INFO")
# 版本信息
__version__ = "1.0.0"

# 定义导出的符号列表 
__all__ = [
    # 基础库和工具
    'os', 'sys', 'Path', 'logger', 'config','re','json','time','datetime','Dict', 'List', 'Optional', 'Any', 'Set', 'datetime', 'timedelta','Union','requests','asyncio',
    # 路径配置
    'LOG_PATH'    
]

# core模块的公用配置和包
# 该模块负责核心功能，提供了全局共享的配置项和工具函数。
# 包含子模块：agent, bridge, context, reply, session, utils
# 提供的全局配置包括路径配置、环境变量配置和数据库配置。
