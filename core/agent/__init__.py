"""
agent模块，负责与大模型进行交互
"""
# 从根模块导入共享配置
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from core import *
from core.agent.agent import Agent
# 创建agent模块专用logger
agent_logger = logger.bind(module="agent")
log_path = LOG_PATH / 'agent.log'
log_format = "{time:YYYY-MM-DD HH:mm:ss} | {level} | {module} | {message}"
logger.configure(
    handlers=[
        {"sink": sys.stdout, "format": log_format},
        {"sink": log_path, "format": log_format, "rotation": "1 day", "retention": "3 months", "level": "INFO"},
    ]
)

__all__ = ['agent_logger','config','Agent','requests','json','time','datetime','Path','logger','sys'] 