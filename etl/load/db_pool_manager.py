"""
数据库连接池管理模块 (基于aiomysql)
"""
import aiomysql
import asyncio
from contextlib import asynccontextmanager
from typing import Optional

from etl import (
    DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME,
    DB_POOL_MIN_SIZE, DB_POOL_MAX_SIZE
)
from core.utils.logger import register_logger

logger = register_logger('etl.load.db_pool_manager')

# 全局数据库连接池变量
db_pool: Optional[aiomysql.Pool] = None

async def init_db_pool():
    """
    初始化aiomysql数据库连接池。
    此函数应在应用启动时调用。
    """
    global db_pool
    if db_pool:
        logger.info("数据库连接池已存在，无需重复初始化。")
        return

    logger.info("正在初始化数据库连接池...")
    try:
        db_pool = await aiomysql.create_pool(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            db=DB_NAME,
            autocommit=False,  # 修改为False以支持事务
            minsize=DB_POOL_MIN_SIZE,
            maxsize=DB_POOL_MAX_SIZE,
            loop=asyncio.get_event_loop()
        )
        logger.info("数据库连接池初始化成功。")
    except Exception as e:
        logger.error(f"数据库连接池初始化失败: {e}", exc_info=True)
        db_pool = None
        raise

async def close_db_pool():
    """
    关闭数据库连接池。
    此函数应在应用关闭时调用。
    """
    global db_pool
    if db_pool:
        logger.info("正在关闭数据库连接池...")
        db_pool.close()
        await db_pool.wait_closed()
        db_pool = None
        logger.info("数据库连接池已成功关闭。")

@asynccontextmanager
async def get_db_connection():
    """
    从连接池获取一个数据库连接的异步上下文管理器。

    用法:
    async with get_db_connection() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute("SELECT 1")
            ...
    """
    if not db_pool:
        logger.error("数据库连接池未初始化或初始化失败。")
        raise ConnectionError("数据库连接池不可用。")

    conn = None
    try:
        conn = await db_pool.acquire()
        yield conn
    finally:
        if conn:
            await db_pool.release(conn) 