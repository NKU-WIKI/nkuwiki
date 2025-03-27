"""
IO工具模块
提供文件读写、JSON处理等基础IO操作函数
"""
import os
import json
import logging
from typing import Any, Optional, Union
from core.utils.logger import logger

def safe_json_loads(json_str: str, default: Any = None) -> Any:
    """
    安全加载JSON字符串
    
    Args:
        json_str: JSON字符串
        default: 解析失败时返回的默认值
        
    Returns:
        解析后的对象，失败则返回默认值
    """
    try:
        return json.loads(json_str)
    except Exception as e:
        logger.error(f"JSON解析错误: {str(e)}")
        return default if default is not None else {}

def safe_file_write(path: str, content: Union[str, bytes], mode: str = 'w', encoding: str = 'utf-8') -> bool:
    """
    安全写入文件
    
    Args:
        path: 文件路径
        content: 文件内容
        mode: 写入模式，默认'w'
        encoding: 编码，默认'utf-8'
        
    Returns:
        是否写入成功
    """
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, mode, encoding=encoding) as f:
            f.write(content)
        return True
    except Exception as e:
        logger.error(f"文件写入错误: {str(e)}")
        return False

def safe_file_read(path: str, default: str = '', mode: str = 'r', encoding: str = 'utf-8') -> str:
    """
    安全读取文件
    
    Args:
        path: 文件路径
        default: 读取失败时返回的默认值
        mode: 读取模式，默认'r'
        encoding: 编码，默认'utf-8'
        
    Returns:
        文件内容，失败则返回默认值
    """
    try:
        with open(path, mode, encoding=encoding) as f:
            return f.read()
    except Exception as e:
        logger.error(f"文件读取错误: {str(e)}")
        return default 