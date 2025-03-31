"""
数据库核心操作模块
提供简洁、安全、高效的MySQL数据库访问接口
"""
import re
import json
import time
import asyncio
from typing import Dict, List, Any, Optional, Union, Tuple
from contextlib import contextmanager
import pymysql
from pymysql.cursors import DictCursor

from etl import config
from core.utils.logger import register_logger
from etl.load.db_pool_manager import get_db_connection

# 创建模块专用日志记录器
db_logger = register_logger("etl.load.db_core")

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
                  order_by: Union[str, Dict[str, str]] = None,
                  limit: int = 1000,
                  offset: int = 0) -> Dict[str, Any]:
    """
    条件查询记录，并返回分页信息
    
    Args:
        table_name: 表名
        conditions: 条件字典，格式为 {字段名: 值} 或特殊格式
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
                        where_parts.append(f"{key} = %s")
                        values.append(value)
                where_clause = f"WHERE {' AND '.join(where_parts)}" if where_parts else ""

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
        sql = f"SELECT * FROM {table_name} {where_clause} {order_clause} {limit_clause}"
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
        raise

def upsert_record(table_name: str, data: Dict[str, Any], unique_fields: List[str]) -> bool:
    """
    插入或更新记录（存在则更新，不存在则插入）
    
    Args:
        table_name: 表名
        data: 数据字典
        unique_fields: 用于判断记录存在与否的字段列表
        
    Returns:
        bool: 操作是否成功
    """
    if not validate_table_name(table_name):
        db_logger.error(f"非法表名: {table_name}")
        return False
        
    if not data or not unique_fields:
        db_logger.error("数据或唯一字段列表为空")
        return False
    
    try:
        # 构建查询条件
        where_parts = []
        where_values = []
        for field in unique_fields:
            if field in data:
                where_parts.append(f"{field} = %s")
                where_values.append(data[field])
            else:
                db_logger.error(f"唯一字段 {field} 不在数据中")
                return False
        
        # 检查记录是否已存在
        sql = f"SELECT id FROM {table_name} WHERE {' AND '.join(where_parts)}"
        existing = execute_query(sql, where_values)
        
        if existing:
            # 记录存在，执行更新
            return update_record(table_name, existing[0]['id'], data)
        else:
            # 记录不存在，执行插入
            return insert_record(table_name, data) > 0
    except Exception as e:
        db_logger.error(f"Upsert操作失败: {str(e)}")
        return False

def init_database(sql_scripts: List[str] = None):
    """
    初始化数据库：创建表、添加初始数据等
    
    Args:
        sql_scripts: 可选的SQL脚本列表
    
    Returns:
        bool: 是否成功完成初始化
    """
    if not sql_scripts:
        db_logger.warning("未提供SQL脚本，初始化操作将被跳过")
        return True
    
    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                for script in sql_scripts:
                    # 按分号分割SQL语句
                    statements = [s.strip() for s in script.split(';') if s.strip()]
                    for statement in statements:
                        try:
                            cursor.execute(statement)
                        except Exception as e:
                            db_logger.error(f"执行SQL语句失败: {str(e)}\n{statement}")
                            # 继续执行下一条语句
        return True
    except Exception as e:
        db_logger.error(f"初始化数据库失败: {str(e)}")
        return False

def get_all_tables() -> List[str]:
    """获取所有表名"""
    try:
        sql = "SHOW TABLES"
        results = execute_query(sql)
        return [list(row.values())[0] for row in results]
    except Exception as e:
        db_logger.error(f"获取表名失败: {str(e)}")
        return []

def get_table_structure(table_name: str) -> List[Dict[str, Any]]:
    """获取表结构"""
    if not validate_table_name(table_name):
        db_logger.error(f"非法表名: {table_name}")
        return []
        
    try:
        sql = f"DESCRIBE {table_name}"
        return execute_query(sql)
    except Exception as e:
        db_logger.error(f"获取表结构失败: {str(e)}")
        return []

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
    """异步插入记录"""
    return await asyncio.to_thread(insert_record, table_name, data)

async def async_update(table_name: str, record_id: int, data: Dict[str, Any]) -> bool:
    """异步更新记录"""
    return await asyncio.to_thread(update_record, table_name, record_id, data)

async def async_get_by_id(table_name: str, record_id: int) -> Optional[Dict[str, Any]]:
    """
    异步获取记录
    
    Args:
        table_name: 表名
        record_id: 记录ID
        
    Returns:
        记录数据字典，未找到则返回None
    """
    try:
        result = await async_query_records(
            table_name=table_name,
            conditions={"id": record_id},
            limit=1
        )
        return result['data'][0] if result and result['data'] else None
    except Exception as e:
        db_logger.error(f"通过ID查询记录失败: {str(e)}")
        return None

async def async_query_records(table_name: str, conditions: Dict[str, Any] = None,
                             order_by: Union[str, Dict[str, str]] = None,
                             limit: int = 1000, offset: int = 0) -> Dict[str, Any]:
    """异步条件查询记录，并返回分页信息"""
    return await asyncio.to_thread(
        query_records,
        table_name=table_name,
        conditions=conditions,
        order_by=order_by,
        limit=limit,
        offset=offset
    )

async def async_count_records(table_name: str, conditions: Dict[str, Any] = None) -> int:
    """异步计算记录数量
    
    Args:
        table_name: 表名称
        conditions: 查询条件
        
    Returns:
        记录数量
    """
    return await asyncio.to_thread(count_records, table_name, conditions)

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
        return await asyncio.to_thread(execute_query, query, params, fetch)
    except Exception as e:
        db_logger.error(f"异步自定义查询执行失败: {str(e)}")
        return [] if fetch else 0 