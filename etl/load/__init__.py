"""
加载模块，负责数据库操作和配置加载
"""
import os
from etl import config, DATA_PATH
from core.utils.logger import register_logger

# 创建模块专用日志记录器
logger = register_logger("etl.load")

# 导入新的数据库核心模块
from etl.load import db_core

# 从新的连接池管理模块导入所需功能
try:
    from etl.load.db_pool_manager import (
        get_pool_stats as _get_pool_stats,
        get_db_connection as _get_db_connection,
        resize_pool_if_needed,
        cleanup_pool as _cleanup_pool
    )
except ImportError:
    load_logger.warning("无法导入db_pool_manager模块，连接池功能将不可用")
    _get_pool_stats = lambda: {"error": "连接池管理模块未加载"}
    _get_db_connection = None
    resize_pool_if_needed = lambda force_size=None: None
    _cleanup_pool = lambda: None

def close_conn_pool():
    """关闭连接池，应用退出时调用"""
    _cleanup_pool()

def get_connection_stats():
    """获取连接统计信息"""
    return _get_pool_stats()

# 重要：添加对db_core的导出和引用
from etl.load.db_core import (
    execute_query,
    insert_record,
    update_record,
    delete_record,
    get_record_by_id,
    query_records,
    count_records,
    execute_custom_query,
    batch_insert,
    get_all_tables,
    # 异步函数
    async_query,
    async_insert,
    async_update,
    async_get_by_id,
    async_query_records,
    async_count_records,            
    async_execute_custom_query
)

# 版本信息
__version__ = "2.0.0"

# 导出模块API
__all__ = [
    # 连接管理
    'logger',
    'close_conn_pool', 'get_connection_stats',
    'resize_pool_if_needed',
    
    # 基本数据库操作
    'execute_query', 'insert_record', 'update_record', 'delete_record',
    'get_record_by_id', 'query_records', 'count_records', 'execute_custom_query',
    'batch_insert', 'get_all_tables',
    
    # 异步函数
    'async_query', 'async_insert', 'async_update', 'async_get_by_id',
    'async_query_records', 'async_count_records', 'async_execute_custom_query',
    
    # 核心模块
    'db_core'
]