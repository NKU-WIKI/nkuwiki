#!/usr/bin/env python3
"""
Redis连接测试脚本
"""
import sys
import redis
from pathlib import Path

# 添加项目根目录到Python路径
root_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(root_dir))

from etl import config
from core.utils.logger import register_logger

# 创建日志记录器
logger = register_logger('tools.test_redis')

def test_redis_connection():
    """测试Redis连接"""
    # 获取Redis配置
    redis_host = config.get('etl.data.redis.host', 'localhost')
    redis_port = config.get('etl.data.redis.port', 6379)
    redis_db = config.get('etl.data.redis.db', 0)
    redis_password = config.get('etl.data.redis.password')
    
    logger.info(f"正在连接Redis服务器: {redis_host}:{redis_port}")
    
    try:
        # 创建Redis客户端连接
        r = redis.Redis(
            host=redis_host,
            port=redis_port,
            db=redis_db,
            password=redis_password,
            socket_timeout=5,
            socket_connect_timeout=5,
            decode_responses=True
        )
        
        # 简单测试
        ping_result = r.ping()
        logger.info(f"Redis服务器PING结果: {ping_result}")
        
        # 测试写入读取
        test_key = "test_connection_key"
        test_value = "测试连接成功"
        r.set(test_key, test_value)
        logger.info(f"Redis写入测试: SET {test_key} {test_value}")
        
        read_value = r.get(test_key)
        logger.info(f"Redis读取测试: GET {test_key} = {read_value}")
        
        # 测试是否一致
        assert test_value == read_value, "写入和读取的值不一致"
        
        # 删除测试键
        r.delete(test_key)
        logger.info(f"Redis删除测试: DEL {test_key}")
        
        logger.info("Redis连接测试成功")
        return True
    except Exception as e:
        logger.error(f"Redis连接测试失败: {str(e)}")
        return False

if __name__ == '__main__':
    success = test_redis_connection()
    sys.exit(0 if success else 1) 