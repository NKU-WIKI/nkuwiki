"""
时间工具模块
提供时间戳、格式化时间等基础时间操作函数
"""
import time
import random
from datetime import datetime
from typing import Optional

def get_timestamp() -> int:
    """
    获取当前时间戳（秒级）
    
    Returns:
        int: 当前时间戳
    """
    return int(time.time())

def get_datetime_str(format: str = '%Y-%m-%d %H:%M:%S') -> str:
    """
    获取当前时间的格式化字符串
    
    Args:
        format: 时间格式字符串，默认'%Y-%m-%d %H:%M:%S'
        
    Returns:
        str: 格式化的时间字符串
    """
    return datetime.now().strftime(format)

def random_sleep(min_seconds: float = 1, max_seconds: float = 3) -> float:
    """
    随机休眠一段时间
    
    Args:
        min_seconds: 最小休眠时间（秒）
        max_seconds: 最大休眠时间（秒）
        
    Returns:
        float: 实际休眠时间
    """
    sleep_time = random.uniform(min_seconds, max_seconds)
    time.sleep(sleep_time)
    return sleep_time

def parse_datetime(date_str: str, formats: list = None) -> Optional[datetime]:
    """
    尝试多种格式解析日期时间字符串
    
    Args:
        date_str: 日期时间字符串
        formats: 尝试的格式列表，如为None则使用默认格式列表
        
    Returns:
        datetime: 解析成功返回datetime对象，失败返回None
    """
    if formats is None:
        formats = [
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%d',
            '%Y/%m/%d %H:%M:%S',
            '%Y/%m/%d',
            '%Y年%m月%d日 %H:%M:%S',
            '%Y年%m月%d日'
        ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    
    return None 