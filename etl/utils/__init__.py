"""
基础工具模块

提供各种基础辅助功能：
- 文件操作、日期处理、文本工具
- 常量定义和扫描工具
- 基础配置
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))
from etl import config
from core.utils import (
    safe_json_loads, safe_file_read, safe_file_write,
    get_timestamp, get_datetime_str, random_sleep
)

from .file import *
from .date import *
from .text import *
from .const import *
from .scan import *

api_key = config.get("core.agent.coze.api_key")
base_url = config.get("core.agent.coze.base_url")
nkucs_dataset_id = config.get("core.agent.coze.nkucs_dataset_id")

# 定义导出的变量和函数
__all__ = [
    'safe_json_loads', 'safe_file_write', 'safe_file_read', 
    'get_timestamp', 'get_datetime_str', 'random_sleep', 
    'api_key', 'base_url', 'nkucs_dataset_id'
]

__all__ += file.__all__ if hasattr(file, '__all__') else []
__all__ += date.__all__ if hasattr(date, '__all__') else []
__all__ += text.__all__ if hasattr(text, '__all__') else []
__all__ += const.__all__ if hasattr(const, '__all__') else []
__all__ += scan.__all__ if hasattr(scan, '__all__') else []
