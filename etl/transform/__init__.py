"""
转换模块，负责数据格式转换和处理
"""
import os
import sys
import json
import re
import time
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from loguru import logger
from datetime import datetime
import mysql.connector
from collections import defaultdict

# 从根模块导入共享配置
from .. import (
    # 路径配置
    BASE_PATH, RAW_PATH, CACHE_PATH, LOG_PATH,
    # 配置工具
    config
)

# 数据库配置
DB_HOST = config.get('mysql.host', '127.0.0.1')
DB_PORT = config.get('mysql.port', 3306)
DB_USER = config.get('mysql.user', 'root')
DB_PASSWORD = config.get('mysql.password', '')
DB_NAME = config.get('mysql.name', 'mysql')

# 转换配置
HTML_TAGS_PATTERN = r'<.*?>'
SPECIAL_CHARS_PATTERN = r'[^\w\s\u4e00-\u9fff]'
MAX_TEXT_LENGTH = config.get('etl.transform.max_text_length', 1000000)
MIN_TEXT_LENGTH = config.get('etl.transform.min_text_length', 10)

# 创建转换模块专用logger
transform_logger = logger.bind(module="transform")
log_path = LOG_PATH / "transform.log"
log_format = "{time:YYYY-MM-DD HH:mm:ss} | {level} | {module} | {message}"
logger.configure(
    handlers=[
        {"sink": sys.stdout, "format": log_format},
        {"sink": log_path, "format": log_format, "rotation": "1 day", "retention": "3 months", "level": "INFO"},
    ]
)

# 数据库连接函数
def get_conn(use_database=True):
    """带容错机制的数据库连接"""
    params = {
        'host': DB_HOST,
        'port': DB_PORT,
        'user': DB_USER,
        'password': DB_PASSWORD,
        'charset': 'utf8mb4',
        'autocommit': True
    }
    
    if use_database:
        params['database'] = DB_NAME
    
    transform_logger.debug(f"尝试连接数据库：host={DB_HOST} user={DB_USER}")
    try:
        conn = mysql.connector.connect(**params)
        return conn
    except Exception as e:
        transform_logger.error(f"数据库连接失败: {str(e)}")
        raise

# 导入转换模块
from etl.transform.transformation import CustomFilePathExtractor, CustomTitleExtractor

# 定义导出的变量和函数
__all__ = [
    'os', 'sys', 'json', 're', 'time', 'Path', 'Dict', 'List', 'Optional', 'Any', 'Union',
    'transform_logger', 'datetime', 'mysql', 'defaultdict', 'get_conn',
    'CustomFilePathExtractor', 'CustomTitleExtractor',
    
    # 路径配置
    'BASE_PATH', 'RAW_PATH', 'CACHE_PATH', 'LOG_PATH',
    
    # 数据库配置
    'DB_HOST', 'DB_PORT', 'DB_USER', 'DB_PASSWORD', 'DB_NAME',
    
    # 转换配置
    'HTML_TAGS_PATTERN', 'SPECIAL_CHARS_PATTERN', 'MAX_TEXT_LENGTH', 'MIN_TEXT_LENGTH'
]

from etl.transform import config, transform_logger, get_conn
