"""
转换模块，负责数据格式转换和处理
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from etl import *

import mysql.connector
from collections import defaultdict

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

# 定义导出的变量和函数
__all__ = [
    'os', 'sys', 'json', 're', 'time', 'Path','requests','Dict', 'List', 'Optional', 'Any', 'Union',
    'transform_logger', 'datetime', 'mysql', 'defaultdict', 'get_conn',
    'config',
    
    # 路径配置
    'BASE_PATH', 'RAW_PATH', 'CACHE_PATH', 'LOG_PATH',
    
    # 数据库配置
    'DB_HOST', 'DB_PORT', 'DB_USER', 'DB_PASSWORD', 'DB_NAME',
    
    # 转换配置
    'HTML_TAGS_PATTERN', 'SPECIAL_CHARS_PATTERN', 'MAX_TEXT_LENGTH', 'MIN_TEXT_LENGTH'
]