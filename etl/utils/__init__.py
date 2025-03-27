"""
工具模块，提供各种辅助功能
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))
from etl import *
from core.utils import (
    safe_json_loads, safe_file_read, safe_file_write,
    get_timestamp, get_datetime_str, random_sleep
)

import random
import base64

api_key = config.get("core.agent.coze.api_key")
base_url = config.get("core.agent.coze.base_url")
nkucs_dataset_id = config.get("core.agent.coze.nkucs_dataset_id")

# 定义导出的变量和函数
__all__ = [
    'requests','random','time','os','json','datetime','logger','sys','Path','base64',

    'safe_json_loads', 'safe_file_write', 'safe_file_read', 'get_timestamp', 'get_datetime_str', 'random_sleep', 'api_key', 'base_url', 'nkucs_dataset_id'
]
