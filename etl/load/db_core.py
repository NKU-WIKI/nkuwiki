"""
数据库核心操作模块
提供简洁、安全、高效的MySQL数据库访问接口
"""
import re
import json
import time
import asyncio
import os
import multiprocessing
from typing import Dict, List, Any, Optional, Union, Tuple, Callable
from contextlib import contextmanager
from functools import wraps
import pymysql
from pymysql.cursors import DictCursor
import concurrent.futures
import atexit
import queue

from etl import config
from core.utils.logger import register_logger
from etl.load.db_pool_manager import get_db_connection

# 创建模块专用日志记录器
db_logger = register_logger("etl.load.db_core")

# 根据CPU核心数动态设置线程池大小
# 数据库IO密集型操作通常设置为CPU核心数的2-4倍，但这里我们减少数量以避免线程耗尽
CPU_COUNT = multiprocessing.cpu_count()
MAX_WORKERS = max(10, CPU_COUNT * 2)  # 至少10个线程，最多CPU核心数的2倍
THREAD_TIMEOUT = 60  # 空闲线程的超时时间（秒）

# 添加环境变量检查，确保只有一个进程创建线程池
thread_pool_key = os.environ.get('NKUWIKI_THREAD_POOL_PID', '')
current_pid = str(os.getpid())

# 如果是第一个进程或者线程池未初始化，则创建线程池
if not thread_pool_key or current_pid == thread_pool_key:
    os.environ['NKUWIKI_THREAD_POOL_PID'] = current_pid
    db_logger.info(f"初始化数据库线程池 - 进程ID: {current_pid}, CPU核心数: {CPU_COUNT}, 最大工作线程: {MAX_WORKERS}")
    
    # 创建全局线程池，设置线程保持活跃的时间
    THREAD_POOL = concurrent.futures.ThreadPoolExecutor(
        max_workers=MAX_WORKERS,
        thread_name_prefix="db_worker",
    )
else:
    db_logger.info(f"使用现有线程池 - 当前进程ID: {current_pid}, 线程池进程ID: {thread_pool_key}")
    # 使用已有的线程池或创建一个较小的备用线程池
    THREAD_POOL = concurrent.futures.ThreadPoolExecutor(
        max_workers=5,  # 极小的线程池，仅用于必要操作
        thread_name_prefix=f"db_worker_sub_{current_pid}"
    )

# 创建任务队列，用于批量处理数据库操作
TASK_QUEUE = queue.Queue()
MAX_BATCH_SIZE = 50  # 最大批处理数量
BATCH_TIMEOUT = 0.1  # 批处理等待超时时间（秒）

# 注册程序退出时关闭线程池
@atexit.register
def close_thread_pool():
    db_logger.info("关闭数据库线程池")
    THREAD_POOL.shutdown(wait=True)

# 连接池状态监控
class DBPoolMonitor:
    """数据库连接池状态监控"""
    def __init__(self):
        self.active_tasks = 0
        self.completed_tasks = 0
        self.failed_tasks = 0
        self.last_reset_time = time.time()
    
    def task_started(self):
        """记录任务开始"""
        self.active_tasks += 1
    
    def task_completed(self):
        """记录任务完成"""
        self.active_tasks -= 1
        self.completed_tasks += 1
    
    def task_failed(self):
        """记录任务失败"""
        self.active_tasks -= 1
        self.failed_tasks += 1
    
    def get_stats(self):
        """获取统计信息"""
        return {
            "active_tasks": self.active_tasks,
            "completed_tasks": self.completed_tasks,
            "failed_tasks": self.failed_tasks,
            "uptime": int(time.time() - self.last_reset_time)
        }
    
    def reset_stats(self):
        """重置统计信息"""
        self.completed_tasks = 0
        self.failed_tasks = 0
        self.last_reset_time = time.time()

# 创建监控实例
db_monitor = DBPoolMonitor()

# 添加性能监控装饰器
def monitor_execution(func):
    """监控数据库操作执行时间的装饰器"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        db_monitor.task_started()
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            if execution_time > 0.5:  # 记录超过0.5秒的慢查询
                # 尝试从参数中获取SQL语句
                sql = args[0] if args and isinstance(args[0], str) else "未知SQL"
                db_logger.warning(f"慢查询 [{execution_time:.2f}秒]: {sql[:200]}...")
            db_monitor.task_completed()
            return result
        except Exception as e:
            db_monitor.task_failed()
            raise
    return wrapper

def get_mysql_config() -> Dict[str, Any]:
    """获取MySQL配置"""
    return {
        'host': config.get('etl.data.mysql.host', 'localhost'),
        'port': config.get('etl.data.mysql.port', 3306),
        'user': config.get('etl.data.mysql.user', 'nkuwiki'),
        'password': config.get('etl.data.mysql.password', ''),
        'database': config.get('etl.data.mysql.name', 'nkuwiki'),
        'charset': 'utf8mb4',
        'autocommit': True,
        'cursorclass': DictCursor
    }

@contextmanager
def get_connection():
    """获取数据库连接，使用普通的pymysql连接，用于较小的独立操作"""
    conn = None
    try:
        conn = pymysql.connect(**get_mysql_config())
        yield conn
    except Exception as e:
        db_logger.error(f"数据库连接错误: {str(e)}")
        raise
    finally:
        if conn:
            try:
                conn.close()
            except:
                pass

def validate_table_name(table_name: str) -> bool:
    """验证表名是否合法，防止SQL注入"""
    return bool(re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', table_name))

@monitor_execution
def execute_query(sql: str, params: Any = None, fetch: bool = True) -> Union[List[Dict[str, Any]], int]:
    """
    执行SQL查询，返回结果或受影响的行数
    
    Args:
        sql: SQL语句
        params: 查询参数
        fetch: 是否获取结果集
        
    Returns:
        查询结果列表或插入操作的ID或影响的行数
    """
    db_logger.debug(f"执行SQL: {sql[:100]}{'...' if len(sql) > 100 else ''}")
    with get_connection() as conn:
        with conn.cursor() as cursor:
            try:
                cursor.execute(sql, params)
                if fetch:
                    return cursor.fetchall()
                return cursor.lastrowid or cursor.rowcount
            except Exception as e:
                db_logger.error(f"SQL执行错误: {str(e)}")
                raise

def insert_record(table_name: str, data: Dict[str, Any]) -> int:
    """
    向指定表插入单条记录
    
    Args:
        table_name: 表名
        data: 字段和值的字典
        
    Returns:
        int: 插入记录的ID，失败返回-1
    """
    if not validate_table_name(table_name):
        db_logger.error(f"非法表名: {table_name}")
        return -1
        
    if not data:
        db_logger.error("数据不能为空")
        return -1
    
    try:
        # 处理JSON类型字段
        processed_data = {}
        for k, v in data.items():
            if isinstance(v, (dict, list)):
                processed_data[k] = json.dumps(v, ensure_ascii=False)
            else:
                processed_data[k] = v
        
        columns = ', '.join(processed_data.keys())
        placeholders = ', '.join(['%s'] * len(processed_data))
        values = list(processed_data.values())
        
        sql = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
        
        return execute_query(sql, values, fetch=False)
    except Exception as e:
        db_logger.error(f"插入记录失败: {str(e)}")
        return -1

def update_record(table_name: str, record_id: int, data: Dict[str, Any]) -> bool:
    """
    更新指定表的指定记录
    
    Args:
        table_name: 表名
        record_id: 记录ID
        data: 要更新的字段和值的字典
        
    Returns:
        bool: 更新是否成功
    """
    if not validate_table_name(table_name):
        db_logger.error(f"非法表名: {table_name}")
        return False
        
    if not data:
        db_logger.warning(f"更新记录数据为空，跳过更新")
        return True  # 没有数据要更新，视为成功
    
    try:
        # 处理JSON类型字段
        processed_data = {}
        for k, v in data.items():
            if isinstance(v, (dict, list)):
                processed_data[k] = json.dumps(v, ensure_ascii=False)
            else:
                processed_data[k] = v
        
        set_clause = ', '.join([f"{k} = %s" for k in processed_data.keys()])
        values = list(processed_data.values())
        values.append(record_id)  # WHERE id = %s 的参数
        
        sql = f"UPDATE {table_name} SET {set_clause} WHERE id = %s"
        
        rows_affected = execute_query(sql, values, fetch=False)
        return rows_affected > 0
    except Exception as e:
        db_logger.error(f"更新记录失败: {str(e)}")
        return False

def delete_record(table_name: str, record_id: int, logical: bool = True) -> bool:
    """
    删除指定表中的指定记录
    
    Args:
        table_name: 表名
        record_id: 记录ID
        logical: 是否使用逻辑删除（默认True）
        
    Returns:
        bool: 删除是否成功
    """
    if not validate_table_name(table_name):
        db_logger.error(f"非法表名: {table_name}")
        return False
        
    try:
        if logical:
            # 逻辑删除，设置is_deleted=1
            sql = f"UPDATE {table_name} SET is_deleted = 1, update_time = NOW() WHERE id = %s"
        else:
            # 物理删除
            sql = f"DELETE FROM {table_name} WHERE id = %s"
        
        rows_affected = execute_query(sql, [record_id], fetch=False)
        return rows_affected > 0
    except Exception as e:
        db_logger.error(f"删除记录失败: {str(e)}")
        return False

def get_record_by_id(table_name: str, record_id: int) -> Optional[Dict[str, Any]]:
    """
    获取指定表中的指定ID记录
    
    Args:
        table_name: 表名
        record_id: 记录ID
        
    Returns:
        Dict[str, Any]: 记录数据，未找到则返回None
    """
    if not validate_table_name(table_name):
        db_logger.error(f"非法表名: {table_name}")
        return None
        
    try:
        sql = f"SELECT * FROM {table_name} WHERE id = %s"
        results = execute_query(sql, [record_id])
        return results[0] if results else None
    except Exception as e:
        db_logger.error(f"查询记录失败: {str(e)}")
        return None

def query_records(table_name: str,
                  conditions: Dict[str, Any] = None,
                  fields: List[str] = None,
                  order_by: Union[str, Dict[str, str]] = None,
                  limit: int = 1000,
                  offset: int = 0) -> Dict[str, Any]:
    """
    条件查询记录，并返回分页信息
    
    Args:
        table_name: 表名
        conditions: 条件字典，格式为 {字段名: 值} 或特殊格式
        fields: 要返回的字段列表，默认为所有字段(*)
        order_by: 排序字段，格式为 "字段名 ASC/DESC" 或 {"字段名": "ASC/DESC"}
        limit: 返回结果最大条数
        offset: 分页起始位置
        
    Returns:
        Dict[str, Any]: 查询结果字典，包含 'data' 和 'pagination' 键
    """
    if not validate_table_name(table_name):
        db_logger.error(f"非法表名: {table_name}")
        return {"data": [], "pagination": None}

    try:
        where_clause = ""
        values = []

        if conditions:
            # 处理特殊条件格式
            if 'where_condition' in conditions and 'params' in conditions:
                where_clause = f"WHERE {conditions['where_condition']}"
                values = conditions['params'] if isinstance(conditions['params'], list) else [conditions['params']]
            else:
                # 处理普通条件字典
                where_parts = []
                for key, value in conditions.items():
                    if key not in ['where_condition', 'params']:
                        if isinstance(value, list) and len(value) > 0 and value[0] == "IN":
                            # 处理IN条件
                            if isinstance(value[1], (list, tuple)):
                                placeholders = ', '.join(['%s'] * len(value[1]))
                                where_parts.append(f"{key} IN ({placeholders})")
                                values.extend(value[1])
                            else:
                                where_parts.append(f"{key} IN (%s)")
                                values.append(value[1])
                        else:
                            where_parts.append(f"{key} = %s")
                            values.append(value)
                where_clause = f"WHERE {' AND '.join(where_parts)}" if where_parts else ""

        # 处理选择的字段
        select_fields = "*"
        if fields and isinstance(fields, list) and len(fields) > 0:
            select_fields = ", ".join(fields)

        # 处理排序
        order_clause = ""
        if order_by:
            if isinstance(order_by, dict):
                # 处理排序字典
                order_parts = []
                for field, direction in order_by.items():
                    order_parts.append(f"{field} {direction}")
                order_clause = f"ORDER BY {', '.join(order_parts)}"
            elif isinstance(order_by, str):
                # 处理排序字符串
                if ":" in order_by:
                    # 格式类似 "field:desc"
                    field, direction = order_by.split(":", 1)
                    direction = "DESC" if direction.lower() == "desc" else "ASC"
                    order_clause = f"ORDER BY {field} {direction}"
                else:
                    order_clause = f"ORDER BY {order_by}"

        limit_clause = f"LIMIT {limit} OFFSET {offset}" if limit else ""

        # 构建查询总数的SQL
        count_sql = f"SELECT COUNT(*) as total FROM {table_name} {where_clause}"
        db_logger.debug(f"查询总数SQL: {count_sql}, 参数: {values}")
        total_count_result = execute_query(count_sql, values)
        total_count = total_count_result[0]['total'] if total_count_result else 0
        db_logger.debug(f"查询总数结果: {total_count}")

        # 构建并执行数据查询SQL
        sql = f"SELECT {select_fields} FROM {table_name} {where_clause} {order_clause} {limit_clause}"
        db_logger.debug(f"查询数据SQL: {sql}, 参数: {values}")
        query_results = execute_query(sql, values)
        db_logger.debug(f"查询结果条数: {len(query_results)}")

        # 构建分页信息
        pagination_info = {
            "total": total_count,
            "page": (offset // limit) + 1 if limit != 0 else 1,
            "page_size": limit,
            "total_pages": (total_count + limit - 1) // limit if limit != 0 else 1
        }

        return {"data": query_results, "pagination": pagination_info}
    except Exception as e:
        db_logger.error(f"查询记录失败: {str(e)}")
        return {"data": [], "pagination": None}

def count_records(table_name: str, conditions: Dict[str, Any] = None) -> int:
    """
    统计记录数量
    
    Args:
        table_name: 表名
        conditions: 条件字典，格式为 {字段名: 值}
        
    Returns:
        int: 记录数量，失败返回-1
    """
    if not validate_table_name(table_name):
        db_logger.error(f"非法表名: {table_name}")
        return -1
        
    try:
        where_clause = ""
        values = []
        
        if conditions:
            # 处理特殊条件格式
            if 'where_condition' in conditions and 'params' in conditions:
                where_clause = f"WHERE {conditions['where_condition']}"
                values = conditions['params'] if isinstance(conditions['params'], list) else [conditions['params']]
            else:
                # 处理普通条件字典
                where_parts = []
                for key, value in conditions.items():
                    if key not in ['where_condition', 'params']:
                        if isinstance(value, list) and len(value) > 0 and value[0] == "IN":
                            # 处理IN条件
                            if isinstance(value[1], (list, tuple)):
                                placeholders = ', '.join(['%s'] * len(value[1]))
                                where_parts.append(f"{key} IN ({placeholders})")
                                values.extend(value[1])
                            else:
                                where_parts.append(f"{key} IN (%s)")
                                values.append(value[1])
                        else:
                            where_parts.append(f"{key} = %s")
                            values.append(value)
                where_clause = f"WHERE {' AND '.join(where_parts)}" if where_parts else ""
        
        sql = f"SELECT COUNT(*) as total FROM {table_name} {where_clause}"
        results = execute_query(sql, values)
        return results[0]['total'] if results else 0
    except Exception as e:
        db_logger.error(f"统计记录数失败: {str(e)}")
        return -1

def batch_insert(table_name: str, records: List[Dict[str, Any]], batch_size: int = 100) -> int:
    """
    批量插入记录
    
    Args:
        table_name: 表名
        records: 记录列表，每个记录是一个字典
        batch_size: 每批插入的记录数量
        
    Returns:
        int: 成功插入的记录数量
    """
    if not records:
        return 0
        
    if not validate_table_name(table_name):
        db_logger.error(f"非法表名: {table_name}")
        return 0
    
    # 使用第一条记录的键作为列名
    columns = list(records[0].keys())
    
    # 构建SQL的VALUES部分的占位符，每条记录一组括号
    placeholders = ', '.join(['%s'] * len(columns))
    
    # 构建最终的INSERT语句
    sql = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"
    
    total_inserted = 0
    
    # 分批处理
    for i in range(0, len(records), batch_size):
        batch = records[i:i+batch_size]
        batch_values = []
        
        # 为每条记录准备参数
        for record in batch:
            # 确保按列名顺序提取值
            row_values = []
            for col in columns:
                value = record.get(col)
                # 处理JSON类型
                if isinstance(value, (dict, list)):
                    value = json.dumps(value, ensure_ascii=False)
                row_values.append(value)
            batch_values.append(row_values)
        
        try:
            with get_connection() as conn:
                with conn.cursor() as cursor:
                    # 使用executemany批量执行
                    row_count = cursor.executemany(sql, batch_values)
                    total_inserted += row_count
        except Exception as e:
            db_logger.error(f"批量插入失败: {str(e)}")
            # 继续处理下一批
    
    return total_inserted

def execute_custom_query(query: str, params: Any = None, fetch: bool = True) -> Union[List[Dict[str, Any]], int, None]:
    """
    执行自定义SQL查询
    
    Args:
        query: SQL查询语句
        params: 查询参数
        fetch: 是否获取结果
        
    Returns:
        查询结果列表，每个结果是一个字典，或者影响的行数，或者None
    """
    try:
        return execute_query(query, params, fetch)
    except Exception as e:
        db_logger.error(f"自定义查询执行失败: {str(e)}")
        return [] if fetch else 0

def get_all_tables() -> List[str]:
    """获取所有表名"""
    try:
        sql = "SHOW TABLES"
        results = execute_query(sql)
        return [list(row.values())[0] for row in results]
    except Exception as e:
        db_logger.error(f"获取表名失败: {str(e)}")
        return []

# 异步数据库操作方法
async def async_query(sql: str, params: Any = None) -> List[Dict[str, Any]]:
    """
    异步执行SQL查询
    
    Args:
        sql: SQL语句
        params: 查询参数
        
    Returns:
        List[Dict]: 查询结果列表
    """
    return await asyncio.to_thread(execute_query, sql, params)

async def async_insert(table_name: str, data: Dict[str, Any]) -> int:
    """
    异步插入记录
    
    Args:
        table_name: 表名
        data: 要插入的数据
        
    Returns:
        int: 插入记录的ID
    """
    try:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            THREAD_POOL,
            lambda: insert_record(table_name, data)
        )
    except Exception as e:
        db_logger.error(f"异步插入记录失败: {str(e)}")
        return -1

async def async_update(table_name: str, record_id: int, data: Dict[str, Any]) -> bool:
    """
    异步更新记录
    
    Args:
        table_name: 表名
        record_id: 记录ID
        data: 要更新的数据
        
    Returns:
        bool: 更新是否成功
    """
    try:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            THREAD_POOL,
            lambda: update_record(table_name, record_id, data)
        )
    except Exception as e:
        db_logger.error(f"异步更新记录失败: {str(e)}")
        return False

async def async_get_by_id(table_name: str, record_id: int) -> Optional[Dict[str, Any]]:
    """异步获取指定ID的记录"""
    return await asyncio.to_thread(get_record_by_id, table_name, record_id)

async def async_query_records(table_name: str, 
                              conditions: Dict[str, Any] = None,
                              fields: List[str] = None,
                              order_by: Union[str, Dict[str, str]] = None,
                              limit: int = 1000, 
                              offset: int = 0) -> Dict[str, Any]:
    """异步条件查询记录，并返回分页信息"""
    try:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            THREAD_POOL, 
            lambda: query_records(
                table_name=table_name,
                conditions=conditions,
                fields=fields,
                order_by=order_by,
                limit=limit,
                offset=offset
            )
        )
    except Exception as e:
        db_logger.error(f"异步查询记录失败: {str(e)}")
        return {"data": [], "pagination": None}

async def async_count_records(table_name: str, conditions: Dict[str, Any] = None) -> int:
    """异步计算记录数量
    
    Args:
        table_name: 表名称
        conditions: 查询条件
        
    Returns:
        记录数量
    """
    try:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            THREAD_POOL,
            lambda: count_records(table_name, conditions)
        )
    except Exception as e:
        db_logger.error(f"异步计数记录失败: {str(e)}")
        return 0

async def async_execute_custom_query(query: str, params: Any = None, fetch: bool = True) -> Union[List[Dict[str, Any]], int, None]:
    """
    异步执行自定义SQL查询
    
    Args:
        query: SQL查询语句
        params: 查询参数
        fetch: 是否获取结果
        
    Returns:
        查询结果列表，每个结果是一个字典，或者影响的行数，或者None
    """
    try:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            THREAD_POOL,
            lambda: execute_query(query, params, fetch)
        )
    except Exception as e:
        db_logger.error(f"异步自定义查询执行失败: {str(e)}")
        return [] if fetch else 0

async def async_delete(table_name: str, record_id: int, logical: bool = True) -> bool:
    """
    异步删除记录
    
    Args:
        table_name: 表名
        record_id: 记录ID
        logical: 是否逻辑删除
        
    Returns:
        bool: 删除是否成功
    """
    try:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            THREAD_POOL,
            lambda: delete_record(table_name, record_id, logical)
        )
    except Exception as e:
        db_logger.error(f"异步删除记录失败: {str(e)}")
        return False 