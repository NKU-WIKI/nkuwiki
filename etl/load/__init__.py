"""
加载模块，负责数据加载和索引构建
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from etl import *
from core.utils.logger import get_module_logger

import mysql.connector
from mysql.connector import pooling

# 连接池对象
conn_pool = None

# 创建加载模块专用logger
load_logger = get_module_logger("etl.load")

def get_conn(use_database=True) -> mysql.connector.MySQLConnection:
    """获取MySQL数据库连接
    
    Args:
        use_database: 是否连接到特定数据库，False仅连接MySQL服务器
        
    Returns:
        数据库连接对象
    """
    global conn_pool
    
    params = {
        'host': DB_HOST,
        'port': DB_PORT,
        'user': DB_USER,  # 使用配置文件中的用户
        'password': DB_PASSWORD,
        'charset': 'utf8mb4',
        'autocommit': True,
        'use_pure': True,  # 使用纯Python实现
        'connection_timeout': 10,  # 连接超时时间
        'pool_size': 20,  # 增加连接池大小
        'pool_name': 'nkuwiki_pool'
    }
    
    if use_database:
        params["database"] = DB_NAME  # 使用配置的数据库名
        
    # 尝试使用连接池
    try:
        if conn_pool is None:
            # 创建连接池 
            conn_pool = pooling.MySQLConnectionPool(**params)
            load_logger.debug("MySQL连接池已创建")
        
        # 从连接池获取连接
        return conn_pool.get_connection()
    except Exception as e:
        load_logger.warning(f"连接池获取连接失败: {str(e)}, 尝试直接连接")
        # 如果连接池失败，直接创建连接
        return mysql.connector.connect(**params)

def close_conn_pool():
    """关闭MySQL连接池
    
    在应用程序退出前调用，确保所有数据库连接被正确释放
    """
    global conn_pool
    
    if conn_pool is not None:
        try:
            # MySQL Connector/Python的连接池没有直接关闭的方法
            # 将连接池设为None，让Python的垃圾回收机制处理
            conn_pool = None
            load_logger.debug("MySQL连接池已释放")
        except Exception as e:
            load_logger.error(f"关闭MySQL连接池时出错: {str(e)}")

# 定义导出的变量和函数
__all__ = [
    'os', 'sys', 'json', 'time', 'asyncio', 'Path', 'Dict', 'List','Tuple','tqdm',
    'Optional', 'Any', 'Union', 'load_logger', 'datetime',
    'defaultdict', 'get_conn', 'close_conn_pool', 'mysql','re','json','time',
    # 路径配置
    'BASE_PATH', 'RAW_PATH', 'INDEX_PATH', 'CACHE_PATH', 'QDRANT_PATH', 'LOG_PATH',
    
    'DB_HOST', 'DB_PORT', 'DB_USER', 'DB_PASSWORD', 'DB_NAME'
]