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
    logger.warning("无法导入db_pool_manager模块，连接池功能将不可用")
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

# 导入异步数据库核心函数 (所有函数现在都是异步的)
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
    # 兼容性别名
    async_query,
    async_insert,
    async_update,
    async_delete,
    async_get_by_id,
    async_query_records,
    async_count_records,            
    async_execute_custom_query
)

# 导入统一表管理器
from etl.load.table_manager import TableManager

# 创建全局表管理器实例
_table_manager = None

def get_table_manager() -> TableManager:
    """获取表管理器实例"""
    global _table_manager
    if _table_manager is None:
        _table_manager = TableManager()
    return _table_manager

# 提供便捷的表管理函数
async def recreate_tables(table_names=None, force=False, apply_defaults=True):
    """重新创建表的便捷函数"""
    manager = get_table_manager()
    return await manager.recreate_tables(table_names, force, apply_defaults)

async def recreate_wxapp_tables(force=False):
    """重新创建微信小程序表的便捷函数"""
    manager = get_table_manager()
    available_tables = manager.get_available_table_definitions()
    wxapp_tables = [t for t in available_tables if t.startswith('wxapp_')]
    return await manager.recreate_tables(wxapp_tables, force, True)

async def export_table_structure(output_file=None):
    """导出表结构的便捷函数"""
    manager = get_table_manager()
    return await manager.export_table_structure(output_file)

async def check_table_health():
    """检查表健康状况的便捷函数"""
    manager = get_table_manager()
    return await manager.check_table_health()

async def list_tables_with_info():
    """列出所有表及其信息的便捷函数"""
    manager = get_table_manager()
    await manager.print_table_summary()

# 版本信息
__version__ = "2.0.0"

# 导出模块API
__all__ = [
    # 连接管理
    'logger',
    'close_conn_pool', 'get_connection_stats',
    'resize_pool_if_needed',
    
    # 异步数据库操作 (主要接口)
    'execute_query', 'insert_record', 'update_record', 'delete_record',
    'get_record_by_id', 'query_records', 'count_records', 'execute_custom_query',
    'batch_insert', 'get_all_tables',
    
    # 兼容性别名
    'async_query', 'async_insert', 'async_update', 'async_delete', 'async_get_by_id',
    'async_query_records', 'async_count_records', 'async_execute_custom_query',
    
    # 表管理
    'TableManager', 'get_table_manager',
    'recreate_tables', 'recreate_wxapp_tables', 'export_table_structure',
    'check_table_health', 'list_tables_with_info',
    
    # 核心模块
    'db_core'
]