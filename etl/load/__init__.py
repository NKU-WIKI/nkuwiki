"""
加载模块，负责数据库操作和配置加载
"""
import threading
import mysql.connector
from mysql.connector import pooling
import sys
import time
import atexit
import os
import uuid
import socket
import json
import fcntl
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
# 明确导入etl模块中需要的内容，而不是使用*
from etl import etl_logger, config, DATA_PATH

from core.utils.logger import register_logger

# 创建模块专用日志记录器
load_logger = register_logger("etl.load")

# 全局连接池
CONNECTION_POOL = None
# 连接池创建时间
POOL_CREATED_TIME = None
# 连接监控信息
CONNECTION_STATS = {
    "created": 0,
    "closed": 0,
    "active": 0,
    "errors": 0
}
# 连接池锁，防止并发创建多个连接池
POOL_LOCK = threading.RLock()

# 创建MySQL连接池 - 使用线程本地存储保证线程安全
_thread_local = threading.local()

# 进程信息
PROCESS_ID = os.getpid()
HOSTNAME = socket.gethostname()
INSTANCE_ID = f"{HOSTNAME}-{PROCESS_ID}-{uuid.uuid4().hex[:8]}"

# 共享锁文件路径
LOCK_FILE = "/tmp/nkuwiki_db_lock"
POOL_INFO_FILE = "/tmp/nkuwiki_pool_info.json"

# 获取实例数量 - 查看有多少个nkuwiki服务在运行
def get_instance_count():
    """估计当前运行的nkuwiki实例数量"""
    try:
        # 使用systemctl命令获取nkuwiki服务数量
        import subprocess
        result = subprocess.run(
            "systemctl list-units --all | grep -c 'nkuwiki.*\.service'", 
            shell=True, 
            capture_output=True, 
            text=True
        )
        count = int(result.stdout.strip())
        return max(count, 1)  # 至少返回1
    except Exception as e:
        load_logger.warning(f"无法获取实例数量，默认为8: {str(e)}")
        return 8  # 默认值

# 动态计算连接池大小
def calculate_pool_size():
    """根据运行实例数量动态计算合适的连接池大小"""
    # 获取MySQL最大连接数
    try:
        import subprocess
        result = subprocess.run(
            "mysql -e \"SHOW VARIABLES LIKE 'max_connections';\" | grep -oP '\\d+'", 
            shell=True, 
            capture_output=True, 
            text=True
        )
        max_mysql_connections = int(result.stdout.strip())
    except Exception as e:
        load_logger.warning(f"无法获取MySQL最大连接数，使用默认值150: {str(e)}")
        max_mysql_connections = 150  # 默认MySQL最大连接数
    
    # 读取当前已连接数
    try:
        result = subprocess.run(
            "mysql -e \"SHOW STATUS LIKE 'Threads_connected';\" | grep -oP '\\d+'", 
            shell=True, 
            capture_output=True, 
            text=True
        )
        current_connections = int(result.stdout.strip())
    except Exception as e:
        load_logger.warning(f"无法获取当前连接数，使用默认值0: {str(e)}")
        current_connections = 0
    
    # 计算剩余可用连接数
    available_connections = max_mysql_connections - current_connections
    
    # 获取实例数量
    instance_count = get_instance_count()
    
    # 计算每个实例应该分配的连接数，保留20%做为安全边界
    safe_connections = int(available_connections * 0.8)
    
    # 每个实例至少有3个连接，最多16个连接(mysql-connector限制)
    min_connections = 3
    max_connections = 16
    
    # 平均分配连接
    connections_per_instance = max(min_connections, min(max_connections, safe_connections // instance_count))
    
    load_logger.info(f"动态连接池配置 - MySQL最大连接: {max_mysql_connections}, 当前连接: {current_connections}, "
                   f"实例数: {instance_count}, 每实例分配: {connections_per_instance}")
    
    return connections_per_instance

def get_conn():
    """获取数据库连接，如果连接池不存在则创建"""
    global CONNECTION_POOL, POOL_CREATED_TIME, CONNECTION_STATS
    
    # 懒加载模式创建连接池
    with POOL_LOCK:
        if CONNECTION_POOL is None:
            try:
                # 动态计算合适的连接池大小
                pool_size = calculate_pool_size()
                
                # 从配置中获取数据库连接信息
                db_config = {
                    'host': config.get('etl.data.mysql.host', 'localhost'),
                    'port': config.get('etl.data.mysql.port', 3306),
                    'user': config.get('etl.data.mysql.user', 'nkuwiki'),
                    'password': config.get('etl.data.mysql.password', ''),
                    'database': config.get('etl.data.mysql.name', 'nkuwiki'),
                    'charset': 'utf8mb4',
                    'use_unicode': True,
                    'get_warnings': True,
                    'autocommit': True,
                    'pool_name': f'nkuwiki_pool_{INSTANCE_ID}',
                    'pool_size': pool_size,  # 动态计算的连接池大小
                    'pool_reset_session': True,  # 重置会话状态
                    'connection_timeout': 30,  # 连接超时时间
                }
                
                # 创建连接池
                CONNECTION_POOL = mysql.connector.pooling.MySQLConnectionPool(**db_config)
                POOL_CREATED_TIME = time.time()
                
                # 记录连接池信息到文件，用于监控
                try:
                    with open(LOCK_FILE, 'w+') as f:
                        fcntl.flock(f, fcntl.LOCK_EX)
                        try:
                            pool_info = {}
                            if os.path.exists(POOL_INFO_FILE):
                                with open(POOL_INFO_FILE, 'r') as pf:
                                    pool_info = json.load(pf)
                            
                            # 添加/更新当前实例信息
                            pool_info[INSTANCE_ID] = {
                                'pid': PROCESS_ID,
                                'hostname': HOSTNAME,
                                'created_time': POOL_CREATED_TIME,
                                'pool_size': pool_size,
                                'last_updated': time.time()
                            }
                            
                            # 写回文件
                            with open(POOL_INFO_FILE, 'w') as pf:
                                json.dump(pool_info, pf)
                        finally:
                            fcntl.flock(f, fcntl.LOCK_UN)
                except Exception as e:
                    load_logger.warning(f"无法记录连接池信息: {str(e)}")
                
                load_logger.info(f"MySQL连接池创建成功: {db_config['host']}:{db_config['port']}/{db_config['database']}, "
                               f"连接池大小: {db_config['pool_size']}, 实例ID: {INSTANCE_ID}")
                
                # 注册模块级别的退出清理函数
                atexit.register(close_conn_pool)
            except Exception as e:
                load_logger.error(f"创建MySQL连接池失败: {str(e)}")
                CONNECTION_STATS["errors"] += 1
                raise
    
    # 获取或创建线程局部连接
    if not hasattr(_thread_local, 'connection') or _thread_local.connection is None:
        try:
            _thread_local.connection = CONNECTION_POOL.get_connection()
            CONNECTION_STATS["created"] += 1
            CONNECTION_STATS["active"] += 1
            load_logger.debug(f"从连接池获取新连接成功，当前活跃连接: {CONNECTION_STATS['active']}")
        except Exception as e:
            load_logger.error(f"从连接池获取连接失败: {str(e)}")
            CONNECTION_STATS["errors"] += 1
            raise
    
    return _thread_local.connection

def close_conn():
    """关闭当前线程的数据库连接"""
    global CONNECTION_STATS
    
    if hasattr(_thread_local, 'connection') and _thread_local.connection is not None:
        try:
            # 尝试关闭连接，但忽略"queue is full"错误，因为这表示连接池已满，连接已归还
            try:
                _thread_local.connection.close()
            except mysql.connector.errors.PoolError as e:
                if "queue is full" in str(e):
                    load_logger.debug(f"连接池已满，连接可能已自动归还: {str(e)}")
                else:
                    # 其他PoolError错误仍然需要记录
                    raise
            
            # 无论如何，都将连接设为None，更新统计信息
            _thread_local.connection = None
            CONNECTION_STATS["closed"] += 1
            CONNECTION_STATS["active"] -= 1
            load_logger.debug(f"关闭MySQL连接，当前活跃连接: {CONNECTION_STATS['active']}")
        except Exception as e:
            load_logger.warning(f"关闭MySQL连接失败: {str(e)}")
            CONNECTION_STATS["errors"] += 1

def close_conn_pool():
    """关闭连接池，应用退出时调用"""
    global CONNECTION_POOL, CONNECTION_STATS
    
    with POOL_LOCK:
        if CONNECTION_POOL is not None:
            # 关闭所有连接
            try:
                # 强制关闭当前所有线程的连接
                for thread in threading.enumerate():
                    if hasattr(thread, '_thread_local') and hasattr(thread._thread_local, 'connection'):
                        try:
                            thread._thread_local.connection.close()
                        except:
                            pass
                
                # 关闭当前线程的连接
                close_conn()
                
                # 从池信息文件中移除此实例的信息
                try:
                    with open(LOCK_FILE, 'w+') as f:
                        fcntl.flock(f, fcntl.LOCK_EX)
                        try:
                            if os.path.exists(POOL_INFO_FILE):
                                with open(POOL_INFO_FILE, 'r') as pf:
                                    pool_info = json.load(pf)
                                
                                # 移除当前实例信息
                                if INSTANCE_ID in pool_info:
                                    del pool_info[INSTANCE_ID]
                                
                                # 写回文件
                                with open(POOL_INFO_FILE, 'w') as pf:
                                    json.dump(pool_info, pf)
                        finally:
                            fcntl.flock(f, fcntl.LOCK_UN)
                except Exception as e:
                    load_logger.warning(f"无法更新连接池信息: {str(e)}")
                
                # 重置连接池
                CONNECTION_POOL = None
                uptime = time.time() - POOL_CREATED_TIME if POOL_CREATED_TIME else 0
                load_logger.info(f"MySQL连接池已关闭，实例ID: {INSTANCE_ID}, 运行时间: {uptime:.2f}秒，统计: {CONNECTION_STATS}")
            except Exception as e:
                load_logger.warning(f"关闭MySQL连接池失败: {str(e)}")
                CONNECTION_STATS["errors"] += 1

def get_connection_stats():
    """获取连接统计信息"""
    # 本实例的连接池信息
    local_stats = {
        "instance_id": INSTANCE_ID,
        "hostname": HOSTNAME,
        "process_id": PROCESS_ID,
        "pool_created_time": POOL_CREATED_TIME,
        "uptime": time.time() - POOL_CREATED_TIME if POOL_CREATED_TIME else 0,
        "stats": CONNECTION_STATS.copy(),
        "pool_exists": CONNECTION_POOL is not None
    }
    
    # 尝试读取全局连接池信息
    all_instances = {}
    try:
        if os.path.exists(POOL_INFO_FILE):
            with open(POOL_INFO_FILE, 'r') as pf:
                all_instances = json.load(pf)
    except Exception as e:
        load_logger.warning(f"无法读取全局连接池信息: {str(e)}")
    
    # 合并信息
    return {
        "local": local_stats,
        "all_instances": all_instances,
        "total_instances": len(all_instances),
        "timestamp": time.time()
    }
            
# 导出模块API
__all__ = ['get_conn', 'close_conn', 'close_conn_pool', 'get_connection_stats']