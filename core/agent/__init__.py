"""
agent模块，负责与大模型进行交互
"""
# 从根模块导入共享配置
import sys
import json
import time
import requests
from datetime import datetime
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from config import Config

# 导入 Agent 类
from core.agent.agent import Agent
from core.utils.logger import register_logger

# 配置引用
config = Config()

# 创建agent模块专用logger
logger = register_logger("core.agent")
logger.debug("core.agent模块初始化")

__all__ = ['logger', 'config', 'Agent', 'requests', 'json', 'time', 'datetime', 'Path', 'sys'] 