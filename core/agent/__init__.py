"""
agent模块，负责与大模型进行交互
"""
# 从根模块导入共享配置
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from core import *
from core.agent.agent import Agent
from core.utils.logger import get_module_logger

# 创建agent模块专用logger
agent_logger = get_module_logger("core.agent")

__all__ = ['agent_logger', 'config', 'Agent', 'requests', 'json', 'time', 'datetime', 'Path', 'sys'] 