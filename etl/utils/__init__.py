"""
工具模块，提供各种辅助功能
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))
from etl import *

import random
import base64

api_key = config.get("core.agent.coze.api_key")
base_url = config.get("core.agent.coze.base_url")
nkucs_dataset_id = config.get("core.agent.coze.nkucs_dataset_id")

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

__all__ = [
    'requests','random','time','os','json','datetime','logger','sys','Path','base64',

    'safe_json_loads', 'safe_file_write', 'safe_file_read', 'get_timestamp', 'get_datetime_str', 'random_sleep', 'api_key', 'base_url', 'nkucs_dataset_id'

]
