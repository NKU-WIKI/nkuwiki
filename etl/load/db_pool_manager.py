"""
数据库连接池管理模块
提供多实例环境下的动态负载均衡连接池管理
"""
import threading
import mysql.connector
from mysql.connector import pooling
import time
import atexit
import os
import uuid
import socket
import json
import fcntl
import subprocess
import psutil
import redis
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from contextlib import contextmanager

from config import Config
from etl.load import logger

config = Config()

# Redis可用性标志
REDIS_AVAILABLE = True

# 全局连接池
CONNECTION_POOL = None
# 连接池创建时间
POOL_CREATED_TIME = None
# 连接监控信息
CONNECTION_STATS = {
    "created": 0,
    "closed": 0, 
    "active": 0,
    "errors": 0,
    "max_active": 0,
    "rejected": 0
}
# 连接池锁，防止并发创建多个连接池
POOL_LOCK = threading.RLock()

# 创建MySQL连接池 - 使用线程本地存储保证线程安全
_thread_local = threading.local()

# 进程信息
PROCESS_ID = os.getpid()
HOSTNAME = socket.gethostname()
INSTANCE_ID = f"{HOSTNAME}-{PROCESS_ID}-{uuid.uuid4().hex[:8]}"

# 共享锁和信息文件路径
LOCK_FILE = "/tmp/nkuwiki_db_lock"
POOL_INFO_FILE = "/tmp/nkuwiki_pool_info.json"
POOL_METRICS_FILE = "/tmp/nkuwiki_pool_metrics.json"

# Redis键名前缀 (用于跨实例协调)
REDIS_KEY_PREFIX = "nkuwiki:db_pool:"

# 上次池大小调整时间
LAST_POOL_RESIZE_TIME = 0
# 调整间隔(秒)
POOL_RESIZE_INTERVAL = config.get('etl.data.mysql.db_pool.resize_interval', 60)

def get_mysql_config():
    """获取MySQL配置"""
    return {
        'host': config.get('etl.data.mysql.host', 'localhost'),
        'port': config.get('etl.data.mysql.port', 3306),
        'user': config.get('etl.data.mysql.user', 'nkuwiki'),
        'password': config.get('etl.data.mysql.password', ''),
        'database': config.get('etl.data.mysql.name', 'nkuwiki'),
        'charset': 'utf8mb4',
        'use_unicode': True,
        'get_warnings': True,
        'autocommit': True
    }

def get_redis_client():
    """获取Redis客户端连接"""
    try:
        redis_host = config.get('etl.data.redis.host', 'localhost')
        redis_port = config.get('etl.data.redis.port', 6379)
        redis_db = config.get('etl.data.redis.db', 0)
        redis_password = config.get('etl.data.redis.password', None)
        
        return redis.Redis(
            host=redis_host,
            port=redis_port,
            db=redis_db,
            password=redis_password,
            socket_timeout=5,
            socket_connect_timeout=5,
            decode_responses=True
        )
    except Exception as e:
        logger.error(f"获取Redis客户端失败: {str(e)}")
        return None

# 重试函数装饰器
def with_redis_retry(max_retries=3, delay=1.0, default_return=False):
    """Redis操作重试装饰器"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except (redis.exceptions.ConnectionError, redis.exceptions.TimeoutError) as e:
                    last_error = e
                    if attempt < max_retries - 1:
                        logger.warning(f"Redis操作失败，{delay}秒后重试 ({attempt+1}/{max_retries}): {str(e)}")
                        time.sleep(delay)
                    else:
                        logger.error(f"Redis操作失败，已达到最大重试次数: {str(e)}")
                except Exception as e:
                    logger.error(f"Redis操作失败，未知错误: {str(e)}")
                    last_error = e
                    break
            
            # 所有重试都失败，返回默认值
            return default_return
        return wrapper
    return decorator

@with_redis_retry(max_retries=2)
def register_instance():
    """注册当前实例到Redis"""
    try:
        r = get_redis_client()
        if not r:
            return False
        
        # 实例信息
        instance_info = {
            'hostname': HOSTNAME,
            'pid': PROCESS_ID,
            'instance_id': INSTANCE_ID,
            'start_time': time.time(),
            'pool_size': 0,
            'active_connections': 0,
            'cpu_usage': 0,
            'memory_usage': 0,
            'last_heartbeat': time.time()
        }
        
        # 注册实例信息
        r.hset(f"{REDIS_KEY_PREFIX}instances", INSTANCE_ID, json.dumps(instance_info))
        logger.debug(f"实例 {INSTANCE_ID} 已注册到Redis")
        return True
    except Exception as e:
        logger.error(f"注册实例到Redis失败: {str(e)}")
        return False

@with_redis_retry(max_retries=2)
def unregister_instance():
    """从Redis中注销当前实例"""
    try:
        r = get_redis_client()
        if not r:
            return False
        
        # 删除实例信息
        r.hdel(f"{REDIS_KEY_PREFIX}instances", INSTANCE_ID)
        logger.debug(f"实例 {INSTANCE_ID} 已从Redis注销")
        return True
    except Exception as e:
        logger.error(f"从Redis注销实例失败: {str(e)}")
        return False

@with_redis_retry(max_retries=2)
def update_instance_metrics():
    """更新实例指标到Redis"""
    try:
        r = get_redis_client()
        if not r:
            return False
        
        # 获取CPU和内存使用率
        try:
            process = psutil.Process(PROCESS_ID)
            cpu_usage = process.cpu_percent(interval=0.1)
            memory_usage = process.memory_percent()
        except:
            cpu_usage = 0
            memory_usage = 0
        
        # 更新指标
        instance_info = json.loads(r.hget(f"{REDIS_KEY_PREFIX}instances", INSTANCE_ID) or '{}')
        instance_info.update({
            'pool_size': getattr(CONNECTION_POOL, 'pool_size', 0),
            'active_connections': CONNECTION_STATS['active'],
            'cpu_usage': cpu_usage,
            'memory_usage': memory_usage,
            'last_heartbeat': time.time()
        })
        
        # 保存到Redis
        r.hset(f"{REDIS_KEY_PREFIX}instances", INSTANCE_ID, json.dumps(instance_info))
        
        # 更新全局连接池指标
        metrics = {
            'timestamp': time.time(),
            'instances': r.hlen(f"{REDIS_KEY_PREFIX}instances"),
            'total_connections': 0,
            'active_connections': 0,
            'max_mysql_connections': get_max_mysql_connections()
        }
        
        # 保存到Redis
        r.set(f"{REDIS_KEY_PREFIX}metrics", json.dumps(metrics))
        
        return True
    except Exception as e:
        logger.error(f"更新实例指标失败: {str(e)}")
        return False

@with_redis_retry(max_retries=2, default_return=[])
def get_active_instances():
    """获取活跃实例列表"""
    try:
        r = get_redis_client()
        if not r:
            return []
        
        # 获取所有实例信息
        instances_data = r.hgetall(f"{REDIS_KEY_PREFIX}instances")
        active_instances = []
        
        # 当前时间
        current_time = time.time()
        
        # 过滤出活跃实例 (最近3分钟有心跳)
        for instance_id, instance_info_json in instances_data.items():
            try:
                instance_info = json.loads(instance_info_json)
                last_heartbeat = instance_info.get('last_heartbeat', 0)
                
                # 如果最近3分钟有心跳，认为实例活跃
                if current_time - last_heartbeat < 180:
                    active_instances.append(instance_info)
            except:
                continue
        
        return active_instances
    except Exception as e:
        logger.error(f"获取活跃实例列表失败: {str(e)}")
        return []

def get_max_mysql_connections():
    """获取MySQL最大连接数"""
    try:
        result = subprocess.run(
            "mysql -e \"SHOW VARIABLES LIKE 'max_connections';\" | grep -oP '\\d+'", 
            shell=True, 
            capture_output=True, 
            text=True
        )
        max_connections = int(result.stdout.strip())
        return max_connections
    except Exception as e:
        logger.warning(f"无法获取MySQL最大连接数，使用默认值150: {str(e)}")
        return 150

def get_mysql_current_connections():
    """获取MySQL当前连接数"""
    try:
        result = subprocess.run(
            "mysql -e \"SHOW STATUS LIKE 'Threads_connected';\" | grep -oP '\\d+'", 
            shell=True, 
            capture_output=True, 
            text=True
        )
        current_connections = int(result.stdout.strip())
        return current_connections
    except Exception as e:
        logger.warning(f"无法获取当前连接数，使用默认值0: {str(e)}")
        return 0

def calculate_optimal_pool_size():
    """计算最优连接池大小"""
    global LAST_POOL_RESIZE_TIME
    
    # 检查是否需要调整池大小
    current_time = time.time()
    if current_time - LAST_POOL_RESIZE_TIME < POOL_RESIZE_INTERVAL:
        # 如果上次调整时间距现在小于间隔时间，则不调整
        if hasattr(CONNECTION_POOL, 'pool_size'):
            return CONNECTION_POOL.pool_size
        return 8  # 默认值
    
    try:
        # 如果Redis不可用，使用固定大小
        if not REDIS_AVAILABLE:
            min_pool_size = config.get('etl.data.mysql.db_pool.min_pool_size', 4)
            max_pool_size = config.get('etl.data.mysql.db_pool.max_pool_size', 32)
            default_size = min(16, max(min_pool_size, max_pool_size // 2))
            logger.debug(f"Redis不可用，使用默认连接池大小: {default_size}")
            return default_size
            
        # 获取MySQL最大连接数和当前连接数
        max_mysql_connections = get_max_mysql_connections()
        current_connections = get_mysql_current_connections()
        
        # 计算可用连接数
        available_connections = max(0, max_mysql_connections - current_connections)
        
        # 获取活跃实例数
        active_instances = get_active_instances()
        instance_count = len(active_instances) or 1
        
        # 计算每个实例应该分配的连接数，保留20%做为安全边界
        safe_connections = int(available_connections * 0.8)
        
        # 基于负载因子分配连接 - 根据实例CPU和连接使用比例分配
        # 获取当前实例的负载信息
        this_instance = None
        total_load_factor = 0
        load_factors = {}
        
        for instance in active_instances:
            # 计算负载因子 (结合CPU使用率和活跃连接数)
            instance_id = instance.get('instance_id')
            cpu_usage = instance.get('cpu_usage', 0)
            active_conn = instance.get('active_connections', 0)
            pool_size = instance.get('pool_size', 1)
            
            # 计算连接使用率 (0-1之间)
            conn_usage_ratio = min(1.0, active_conn / max(1, pool_size)) 
            
            # 负载因子 = (CPU使用率 + 连接使用率) / 2
            load_factor = (cpu_usage/100 + conn_usage_ratio) / 2
            load_factors[instance_id] = max(0.1, load_factor)  # 最小0.1保证有分配
            total_load_factor += load_factors[instance_id]
            
            if instance_id == INSTANCE_ID:
                this_instance = instance
        
        # 如果找不到当前实例，使用默认分配
        if not this_instance or total_load_factor == 0:
            return max(4, min(32, safe_connections // instance_count))
        
        # 基于负载的动态分配
        inverse_load = 1.0 - (load_factors[INSTANCE_ID] / total_load_factor)
        adjusted_factor = 0.5 + (inverse_load / 2.0)  # 将范围调整到0.5-1.0
        
        # 计算最终连接池大小
        base_size = safe_connections // instance_count
        pool_size = int(base_size * adjusted_factor)
        
        # 最小/最大池大小限制
        min_pool_size = config.get('etl.data.mysql.db_pool.min_pool_size', 4)
        max_pool_size = config.get('etl.data.mysql.db_pool.max_pool_size', 32)
        final_size = max(min_pool_size, min(max_pool_size, pool_size))
        
        # 更新调整时间
        LAST_POOL_RESIZE_TIME = current_time
        
        logger.info(f"动态连接池配置 - MySQL最大连接: {max_mysql_connections}, "
                       f"当前连接: {current_connections}, 实例数: {instance_count}, "
                       f"负载因子: {load_factors.get(INSTANCE_ID, 0):.2f}, 分配大小: {final_size}")
        
        return final_size
    except Exception as e:
        logger.error(f"计算最优连接池大小失败: {str(e)}")
        # 使用保守的默认值
        return 8

def initialize_pool():
    """初始化连接池"""
    global CONNECTION_POOL, POOL_CREATED_TIME
    
    try:
        # 初始检查Redis可用性
        redis_ok = check_redis_available()
        
        # 尝试注册实例到Redis
        if redis_ok:
            register_instance()
        
        # 计算最优连接池大小
        pool_size = calculate_optimal_pool_size()
        
        # 从配置中获取数据库连接信息
        db_config = get_mysql_config()
        # 添加连接池特有配置
        db_config.update({
            'pool_name': f'nkuwiki_pool_{INSTANCE_ID}',
            'pool_size': pool_size,
            'pool_reset_session': True,
            'connection_timeout': 30,
        })
        
        # 创建连接池
        CONNECTION_POOL = mysql.connector.pooling.MySQLConnectionPool(**db_config)
        POOL_CREATED_TIME = time.time()
        
        # 记录日志
        logger.info(f"MySQL连接池创建成功: {db_config['host']}:{db_config['port']}/{db_config['database']}, "
                       f"连接池大小: {pool_size}, 实例ID: {INSTANCE_ID}")
        
        # 更新实例指标
        if redis_ok:
            update_instance_metrics()
        
        # 注册退出时的清理函数
        atexit.register(cleanup_pool)
        
        return True
    except Exception as e:
        logger.error(f"初始化连接池失败: {str(e)}")
        return False

def resize_pool_if_needed(force_size=None):
    """
    根据负载情况调整连接池大小
    参数:
        force_size: 强制设置的连接池大小，不受计算影响
    """
    global CONNECTION_POOL, LAST_POOL_RESIZE_TIME
    
    # 如果连接池不存在，不进行操作
    if CONNECTION_POOL is None:
        return None
    
    try:
        # 获取当前池大小
        current_size = getattr(CONNECTION_POOL, 'pool_size', 4)
        
        # 如果指定了大小，直接设置
        if force_size is not None:
            new_size = force_size
            logger.info(f"强制调整连接池大小: {current_size} -> {new_size}")
        else:
            # 检查Redis是否可用
            if not check_redis_available() and not force_size:
                logger.debug("Redis不可用，跳过自动调整连接池大小")
                return None
                
            # 检查是否需要调整
            if time.time() - LAST_POOL_RESIZE_TIME > POOL_RESIZE_INTERVAL:
                # 计算最优池大小
                optimal_size = calculate_optimal_pool_size()
                
                # 判断是否需要调整 - 只有变化超过一定比例才调整
                if abs(optimal_size - current_size) >= 2:
                    new_size = optimal_size
                    logger.info(f"动态调整连接池大小: {current_size} -> {new_size}")
                else:
                    return None  # 不需要调整
            else:
                return None  # 未到调整时间
        
        # 获取最小和最大池大小配置
        min_pool_size = config.get('etl.data.mysql.db_pool.min_pool_size', 4)
        max_pool_size = config.get('etl.data.mysql.db_pool.max_pool_size', 32)
        
        # 限制在配置范围内
        new_size = max(min_pool_size, min(new_size, max_pool_size))
        
        # 记录调整时间
        LAST_POOL_RESIZE_TIME = time.time()
        
        # 如果新大小与当前大小相同，不操作
        if new_size == current_size:
            return None
        
        # 重新创建连接池
        with POOL_LOCK:
            # 创建新连接池
            try:
                mysql_config = get_mysql_config()
                CONNECTION_POOL = mysql.connector.pooling.MySQLConnectionPool(
                    pool_name="nkuwiki_pool", 
                    pool_size=new_size,
                    **mysql_config
                )
                
                # 更新指标
                if REDIS_AVAILABLE:
                    update_instance_metrics()
                
                # 记录日志
                logger.info(f"连接池大小调整成功: {current_size} -> {new_size}")
                return new_size
            except Exception as e:
                logger.error(f"调整连接池大小失败: {str(e)}")
                return None
    except Exception as e:
        logger.error(f"调整连接池大小过程中发生错误: {str(e)}")
        return None

def get_connection(max_retries=3, retry_interval=0.5):
    """获取数据库连接，带重试机制"""
    global CONNECTION_POOL, CONNECTION_STATS
    
    # 懒加载模式创建连接池
    with POOL_LOCK:
        if CONNECTION_POOL is None:
            if not initialize_pool():
                raise Exception("无法初始化数据库连接池")
    
    # 定期检查Redis可用性（每10次获取连接检查一次）
    if 'redis_check_count' not in globals():
        globals()['redis_check_count'] = 0
    globals()['redis_check_count'] += 1
    
    if globals()['redis_check_count'] % 10 == 0:
        # 使用线程安全的方式进行检查
        threading.Thread(target=check_redis_available).start()
    
    # 定期检查是否需要调整连接池大小
    # 使用线程安全的方式调整，不会影响现有连接
    if time.time() - LAST_POOL_RESIZE_TIME > POOL_RESIZE_INTERVAL:
        threading.Thread(target=resize_pool_if_needed).start()
    
    # 获取或创建线程局部连接
    if hasattr(_thread_local, 'connection') and _thread_local.connection is not None:
        return _thread_local.connection
    
    # 尝试获取新连接，带重试机制
    last_error = None
    for attempt in range(max_retries):
        try:
            _thread_local.connection = CONNECTION_POOL.get_connection()
            CONNECTION_STATS["created"] += 1
            CONNECTION_STATS["active"] += 1
            
            # 更新最大活跃连接数统计
            if CONNECTION_STATS["active"] > CONNECTION_STATS["max_active"]:
                CONNECTION_STATS["max_active"] = CONNECTION_STATS["active"]
            
            logger.debug(f"从连接池获取新连接成功，当前活跃连接: {CONNECTION_STATS['active']}")
            
            # 异步更新实例指标
            if REDIS_AVAILABLE:
                threading.Thread(target=update_instance_metrics).start()
            
            return _thread_local.connection
        except Exception as e:
            last_error = e
            # 记录错误统计
            CONNECTION_STATS["errors"] += 1
            
            # 如果连接池已满并且还有重试次数，等待后重试
            if "queue is full" in str(e) and attempt < max_retries - 1:
                CONNECTION_STATS["rejected"] += 1
                logger.warning(f"连接池已满，等待重试 ({attempt+1}/{max_retries})...")
                time.sleep(retry_interval)
            else:
                # 其他错误或者重试次数用尽，直接失败
                break
    
    # 所有重试都失败
    logger.error(f"无法从连接池获取连接: {str(last_error)}")
    
    # 尝试直接创建独立连接作为应急措施
    try:
        logger.warning("尝试创建独立连接作为应急措施...")
        
        # 获取数据库配置
        db_config = get_mysql_config()
        
        # 创建独立连接
        _thread_local.connection = mysql.connector.connect(**db_config)
        _thread_local.is_standalone = True  # 标记为独立连接
        
        CONNECTION_STATS["created"] += 1
        CONNECTION_STATS["active"] += 1
        
        logger.warning("成功创建独立连接作为应急措施")
        return _thread_local.connection
    except Exception as e:
        logger.error(f"创建独立连接失败: {str(e)}")
        raise Exception(f"无法获取数据库连接: {str(last_error)}")

def release_connection():
    """释放当前线程的数据库连接"""
    global CONNECTION_STATS
    
    if not hasattr(_thread_local, 'connection') or _thread_local.connection is None:
        return
    
    # 检查是否是独立连接
    is_standalone = getattr(_thread_local, 'is_standalone', False)
    
    try:
        if is_standalone:
            # 直接关闭独立连接
            _thread_local.connection.close()
        else:
            # 尝试归还连接池连接
            try:
                _thread_local.connection.close()
            except mysql.connector.errors.PoolError as e:
                if "queue is full" in str(e):
                    logger.debug(f"连接池已满，连接可能已自动归还: {str(e)}")
                else:
                    # 其他PoolError错误仍然需要记录
                    raise
        
        # 无论如何，都清理线程本地存储
        _thread_local.connection = None
        if is_standalone:
            _thread_local.is_standalone = False
        
        CONNECTION_STATS["closed"] += 1
        CONNECTION_STATS["active"] -= 1
        
        logger.debug(f"释放MySQL连接成功，当前活跃连接: {CONNECTION_STATS['active']}")
    except Exception as e:
        logger.warning(f"释放MySQL连接失败: {str(e)}")
        CONNECTION_STATS["errors"] += 1

def close_all_connections():
    """关闭所有连接"""
    for thread in threading.enumerate():
        if hasattr(thread, '_thread_local') and hasattr(thread._thread_local, 'connection'):
            try:
                thread._thread_local.connection.close()
                thread._thread_local.connection = None
            except:
                pass

def cleanup_pool():
    """清理连接池资源"""
    global CONNECTION_POOL
    
    try:
        # 关闭所有连接
        close_all_connections()
        
        # 释放当前线程的连接
        release_connection()
        
        # 尝试注销实例，只在Redis可用时执行
        if REDIS_AVAILABLE:
            try:
                unregister_instance()
            except Exception as e:
                logger.warning(f"从Redis注销实例失败: {str(e)}")
        
        # 重置连接池
        CONNECTION_POOL = None
        
        logger.info(f"MySQL连接池已清理，实例ID: {INSTANCE_ID}, 统计: {CONNECTION_STATS}")
    except Exception as e:
        logger.warning(f"清理连接池资源失败: {str(e)}")

@contextmanager
def get_db_connection():
    """获取数据库连接的上下文管理器"""
    conn = None
    try:
        conn = get_connection()
        yield conn
    finally:
        if conn:
            release_connection()

def get_pool_stats():
    """获取连接池统计信息"""
    stats = {
        "instance_id": INSTANCE_ID,
        "hostname": HOSTNAME,
        "process_id": PROCESS_ID,
        "pool_created_time": POOL_CREATED_TIME,
        "uptime": time.time() - POOL_CREATED_TIME if POOL_CREATED_TIME else 0,
        "pool_size": getattr(CONNECTION_POOL, 'pool_size', 0),
        "connection_stats": CONNECTION_STATS.copy(),
        "pool_exists": CONNECTION_POOL is not None,
        "redis_available": REDIS_AVAILABLE,
        "timestamp": time.time()
    }
    
    # 如果Redis可用，尝试获取全局统计信息
    if REDIS_AVAILABLE:
        try:
            r = get_redis_client()
            if r:
                stats["active_instances"] = len(get_active_instances())
                metrics_json = r.get(f"{REDIS_KEY_PREFIX}metrics")
                if metrics_json:
                    metrics = json.loads(metrics_json)
                    stats["global_metrics"] = metrics
        except:
            pass
    
    return stats

def check_redis_available():
    """检查Redis是否可用"""
    global REDIS_AVAILABLE
    try:
        redis_client = get_redis_client()
        if redis_client and redis_client.ping():
            if not REDIS_AVAILABLE:
                logger.info("Redis服务恢复连接")
                REDIS_AVAILABLE = True
            return True
        else:
            if REDIS_AVAILABLE:
                logger.warning("无法连接到Redis服务，将采用本地模式")
                REDIS_AVAILABLE = False
            return False
    except Exception as e:
        if REDIS_AVAILABLE:
            logger.warning(f"Redis连接检查失败: {str(e)}，将采用本地模式")
            REDIS_AVAILABLE = False
        return False 