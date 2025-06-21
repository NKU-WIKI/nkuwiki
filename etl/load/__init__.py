"""
加载模块，负责数据库操作和配置加载
"""
# 导入新的数据库核心模块
from etl.load import db_core
from core.utils.logger import register_logger

# 相对导入，避免循环依赖问题
from . import db_pool_manager

logger = register_logger('etl.load')

# 定义要导出的连接池相关函数
init_db_pool = db_pool_manager.init_db_pool
close_db_pool = db_pool_manager.close_db_pool
get_pool_stats = lambda: None # get_pool_stats 尚未在 db_pool_manager 中实现

# 导入异步数据库核心函数 (所有函数现在都是异步的)
from etl.load.db_core import (
    execute_custom_query,
    insert_record,
    update_record,
    query_records,
    count_records,
    batch_insert,
    get_all_tables,
    get_by_id
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
    'close_conn_pool', 'get_connection_stats',
    'resize_pool_if_needed',
    
    # 异步数据库操作 (主要接口)
    'execute_custom_query', 'insert_record', 'update_record',
    'query_records', 'count_records', 'batch_insert', 
    'get_all_tables', 'get_by_id',
    
    # 表管理
    'TableManager', 'get_table_manager',
    'recreate_tables', 'recreate_wxapp_tables', 'export_table_structure',
    'check_table_health', 'list_tables_with_info',
    
    # 核心模块
    'db_core', 'db_pool_manager',
    'init_db_pool', 'close_db_pool', 'get_pool_stats',
]