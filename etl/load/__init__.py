"""
加载模块，负责数据加载和索引构建
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from etl import *
import mysql.connector
# 创建加载模块专用logger
load_logger = logger.bind(module="load")
log_path = LOG_PATH / "load.log"
log_format = "{time:YYYY-MM-DD HH:mm:ss} | {level} | {module} | {message}"
logger.configure(
    handlers=[
        {"sink": sys.stdout, "format": log_format},
        {"sink": log_path, "format": log_format, "rotation": "1 day", "retention": "3 months", "level": "INFO"},
    ]
)


def get_conn(use_database=True) -> mysql.connector.MySQLConnection:
    """获取MySQL数据库连接
    
    Args:
        use_database: 是否连接到特定数据库，False仅连接MySQL服务器
        
    Returns:
        数据库连接对象
    """
    params = {
        'host': DB_HOST,
        'port': DB_PORT,
        'user': 'nkuwiki',  # 强制使用nkuwiki用户
        'password': DB_PASSWORD,
        'charset': 'utf8mb4',
        'autocommit': True
    }
    if use_database:
        params["database"] = "nkuwiki"  # 默认连接到nkuwiki数据库
    return mysql.connector.connect(**params)

# 定义导出的变量和函数
__all__ = [
    'os', 'sys', 'json', 'time', 'asyncio', 'Path', 'Dict', 'List','Tuple',
    'Optional', 'Any', 'Union', 'load_logger', 'datetime',
    'defaultdict', 'get_conn', 'mysql','re','json','time',
    # 路径配置
    'BASE_PATH', 'RAW_PATH', 'INDEX_PATH', 'CACHE_PATH', 'QDRANT_PATH', 'LOG_PATH',
    
    'DB_HOST', 'DB_PORT', 'DB_USER', 'DB_PASSWORD', 'DB_NAME'
]