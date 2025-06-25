"""
数据库核心操作模块
提供所有与MySQL数据库的异步交互功能
"""
import asyncio
from typing import List, Dict, Any, Optional, Tuple, Union

import aiomysql
from etl.load.db_pool_manager import get_db_connection
from core.utils.logger import register_logger

logger = register_logger('etl.load.db_core')

async def _execute_query(query: str, params: Optional[Union[List, Tuple]] = None, fetch: Optional[str] = None) -> Any:
    """
    通用的异步查询执行函数。

    Args:
        query (str): 要执行的SQL查询语句。
        params (Optional[Union[List, Tuple]]): SQL查询的参数。
        fetch (Optional[str]): 获取结果的方式 ('one', 'all', None)。

    Returns:
        Any: 查询结果，根据fetch参数决定。
    """
    async with get_db_connection() as conn:
        try:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute(query, params)
                if fetch == 'one':
                    return await cursor.fetchone()
                elif fetch == 'all':
                    return await cursor.fetchall()
                else:
                    await conn.commit()
                    return cursor.lastrowid or cursor.rowcount
        except Exception as e:
            logger.error(f"数据库查询失败，正在回滚: {query} | 参数: {params}", exc_info=True)
            await conn.rollback()
            raise e


async def execute_custom_query(query: str, params: Optional[Union[List, Tuple]] = None, fetch: str = 'all') -> Any:
    """执行自定义SQL查询"""
    return await _execute_query(query, params, fetch=fetch)


async def insert_record(table_name: str, data: Dict[str, Any]) -> int:
    """插入单条记录"""
    cols = ", ".join(f"`{k}`" for k in data.keys())
    placeholders = ", ".join(["%s"] * len(data))
    query = f"INSERT INTO {table_name} ({cols}) VALUES ({placeholders})"
    return await _execute_query(query, list(data.values()), fetch=None)


async def batch_insert(table_name: str, records: List[Dict[str, Any]], batch_size: int = 500) -> int:
    """高效批量插入记录"""
    if not records:
        return 0

    total_inserted = 0
    cols = list(records[0].keys())
    cols_sql = ", ".join(f"`{k}`" for k in cols)
    placeholders = ", ".join(["%s"] * len(cols))
    query = f"INSERT INTO {table_name} ({cols_sql}) VALUES ({placeholders})"
    
    try:
        async with get_db_connection() as conn:
            async with conn.cursor() as cursor:
                for i in range(0, len(records), batch_size):
                    batch = records[i:i+batch_size]
                    data_to_insert = [tuple(r[c] for c in cols) for r in batch]
                    try:
                        await cursor.executemany(query, data_to_insert)
                        total_inserted += cursor.rowcount
                    except Exception as e:
                        logger.error(f"批量插入的子批次失败 (起始索引 {i}): {e}", exc_info=True)
                        # 如果一个批次失败，可以选择回滚并中断，或者记录日志并继续
                        # 这里选择中断
                        await conn.rollback()
                        raise e
                await conn.commit() # 所有批次成功后提交事务
    except Exception as e:
        logger.error(f"批量插入事务整体失败: {e}", exc_info=True)
        # 异常会由 get_db_connection 上下文管理器自动处理回滚
        total_inserted = 0 # 事务失败，重置计数
        # 根据需要可以重新抛出异常
        # raise e
    
    logger.info(f"批量插入 {total_inserted} 条记录到表 {table_name}")
    return total_inserted


async def update_record(table_name: str, conditions: Dict[str, Any], data: Dict[str, Any]) -> int:
    """根据条件更新记录"""
    set_clause = ", ".join([f"`{k}`=%s" for k in data.keys()])
    where_clause = " AND ".join([f"`{k}`=%s" for k in conditions.keys()])
    query = f"UPDATE {table_name} SET {set_clause} WHERE {where_clause}"
    params = list(data.values()) + list(conditions.values())
    return await _execute_query(query, params, fetch=None)


async def query_records(
    table_name: str,
    conditions: Optional[Dict[str, Any]] = None,
    fields: Optional[List[str]] = None,
    order_by: Optional[Dict[str, str]] = None,
    limit: Optional[int] = None,
    offset: int = 0
) -> Dict[str, Any]:
    """通用查询函数，支持更复杂的排序和条件"""
    field_str = ", ".join(f"`{f}`" for f in fields) if fields else "*"
    query = f"SELECT {field_str} FROM `{table_name}`"
    count_query = f"SELECT COUNT(*) as total FROM `{table_name}`"
    
    params = []
    
    if conditions:
        where_clauses = []
        
        # 1. 处理常规的键值对条件
        for key, value in conditions.items():
            if key in ["where_condition", "params"]:
                continue  # 跳过特殊键，稍后处理
            
            if isinstance(value, list):
                if not value: continue
                placeholders = ', '.join(['%s'] * len(value))
                where_clauses.append(f"`{key}` IN ({placeholders})")
                params.extend(value)
            else:
                where_clauses.append(f"`{key}`=%s")
                params.append(value)
        
        # 2. 处理自定义的 where_condition
        if "where_condition" in conditions:
            where_clauses.append(conditions["where_condition"])
            if "params" in conditions:
                params.extend(conditions["params"])

        # 3. 组合所有条件
        if where_clauses:
            where_sql = " WHERE " + " AND ".join(where_clauses)
            query += where_sql
            count_query += where_sql

    # 为总数查询准备参数
    count_params = list(params)

    if order_by:
        order_by_clauses = [f"`{k}` {v.upper()}" for k, v in order_by.items()]
        query += " ORDER BY " + ", ".join(order_by_clauses)
    
    if limit is not None:
        query += f" LIMIT {limit}"
    
    if offset > 0:
        query += f" OFFSET {offset}"

    # 并发执行数据查询和总数查询
    data_task = _execute_query(query, params, fetch='all')
    total_task = _execute_query(count_query, count_params, fetch='one')
    
    results = await asyncio.gather(data_task, total_task)
    
    data = results[0]
    total_result = results[1]
    
    total = total_result['total'] if total_result else 0

    return {"data": data, "total": total}


async def get_all_tables() -> List[str]:
    """获取所有表名"""
    query = "SHOW TABLES"
    results = await _execute_query(query, fetch='all')
    return [list(row.values())[0] for row in results] if results else []


async def get_by_id(table_name: str, record_id: Union[int, str], id_column: str = 'id', fields: Optional[List[str]] = None) -> Optional[Dict[str, Any]]:
    """通过指定的列获取单条记录"""
    field_str = ", ".join(fields) if fields else "*"
    query = f"SELECT {field_str} FROM `{table_name}` WHERE `{id_column}` = %s"
    return await _execute_query(query, [record_id], fetch='one')


async def count_records(table_name: str, conditions: Optional[Dict[str, Any]] = None) -> int:
    """计算记录数"""
    query = f"SELECT COUNT(*) as total FROM `{table_name}`"
    params = []
    if conditions:
        where_clauses = []
        for key, value in conditions.items():
            if isinstance(value, list):
                if not value: continue
                placeholders = ', '.join(['%s'] * len(value))
                where_clauses.append(f"`{key}` IN ({placeholders})")
                params.extend(value)
            else:
                where_clauses.append(f"`{key}`=%s")
                params.append(value)
        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)
    
    result = await _execute_query(query, params, fetch='one')
    return result['total'] if result else 0


async def execute_sql_list_in_transaction(sql_list: List[Tuple[str, Optional[Union[List, Tuple]]]]) -> bool:
    """
    在单个事务中按顺序执行一系列SQL语句。
    如果任何语句失败，则回滚。
    """
    try:
        async with get_db_connection() as conn:
            async with conn.cursor() as cursor:
                for query, params in sql_list:
                    await cursor.execute(query, params)
                await conn.commit()
                return True
    except Exception as e:
        logger.error(f"事务执行失败: {e}", exc_info=True)
        # 已经在连接池层面处理了回滚
        return False 