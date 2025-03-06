"""
工具模块，提供各种辅助功能
"""
import os
import sys
import json
import re
import time
import random
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Tuple
from loguru import logger
from datetime import datetime
import torch
import numpy as np

from config import Config

# 导入配置
config = Config()
config.load_config()

# 常用工具函数
def safe_json_loads(json_str, default=None):
    """安全加载JSON字符串"""
    try:
        return json.loads(json_str)
    except Exception as e:
        logger.error(f"JSON解析错误: {str(e)}")
        return default if default is not None else {}

def safe_file_write(path, content, mode='w', encoding='utf-8'):
    """安全写入文件"""
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, mode, encoding=encoding) as f:
            f.write(content)
        return True
    except Exception as e:
        logger.error(f"文件写入错误: {str(e)}")
        return False

def safe_file_read(path, default='', mode='r', encoding='utf-8'):
    """安全读取文件"""
    try:
        with open(path, mode, encoding=encoding) as f:
            return f.read()
    except Exception as e:
        logger.error(f"文件读取错误: {str(e)}")
        return default

def get_timestamp():
    """获取当前时间戳"""
    return int(time.time())

def get_datetime_str(format='%Y-%m-%d %H:%M:%S'):
    """获取当前时间字符串"""
    return datetime.now().strftime(format)

def random_sleep(min_seconds=1, max_seconds=3):
    """随机休眠一段时间"""
    sleep_time = random.uniform(min_seconds, max_seconds)
    time.sleep(sleep_time)
    return sleep_time
