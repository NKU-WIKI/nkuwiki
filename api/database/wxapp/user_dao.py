"""
用户数据访问对象
提供用户信息的CRUD操作
"""
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from loguru import logger
import pymysql
from config import Config
import json

# 表名常量
TABLE_NAME = "wxapp_users"

def get_mysql_config():
    """获取MySQL配置"""
    config = Config()
    mysql_config = {
        'host': config.get('etl.data.mysql.host', 'localhost'),
        'port': config.get('etl.data.mysql.port', 3306),
        'user': config.get('etl.data.mysql.user', 'nkuwiki'),
        'password': config.get('etl.data.mysql.password', ''),
        'db': config.get('etl.data.mysql.name', 'nkuwiki'),
        'charset': 'utf8mb4',
        'cursorclass': pymysql.cursors.DictCursor
    }
    return mysql_config

async def get_user_by_openid(openid: str) -> Optional[Dict[str, Any]]:
    """
    根据openid获取用户信息
    
    Args:
        openid: 用户openid
        
    Returns:
        Optional[Dict[str, Any]]: 用户信息，如果不存在则返回None
    """
    logger.debug(f"查询用户 (openid: {openid[:8]}...)")
    
    try:
        # 直接连接数据库
        conn = pymysql.connect(**get_mysql_config())
        
        try:
            with conn.cursor() as cursor:
                sql = f"SELECT * FROM {TABLE_NAME} WHERE openid = %s AND is_deleted = 0 LIMIT 1"
                cursor.execute(sql, [openid])
                result = cursor.fetchone()
                return result
        finally:
            conn.close()
    except Exception as e:
        logger.error(f"查询用户信息失败: {str(e)}")
        raise

async def get_users(limit: int = 10, offset: int = 0) -> Tuple[List[Dict[str, Any]], int]:
    """
    获取用户列表
    
    Args:
        limit: 每页数量
        offset: 偏移量
        
    Returns:
        Tuple[List[Dict[str, Any]], int]: 用户列表和总数
    """
    try:
        conn = pymysql.connect(**get_mysql_config())
        
        try:
            with conn.cursor() as cursor:
                # 查询总数
                cursor.execute(f"SELECT COUNT(*) as total FROM {TABLE_NAME} WHERE is_deleted = 0")
                total = cursor.fetchone()['total']
                
                # 查询用户列表
                sql = f"SELECT * FROM {TABLE_NAME} WHERE is_deleted = 0 ORDER BY id DESC LIMIT %s OFFSET %s"
                cursor.execute(sql, [limit, offset])
                users = cursor.fetchall()
                
                return users, total
        finally:
            conn.close()
    except Exception as e:
        logger.error(f"获取用户列表失败: {str(e)}")
        raise

async def update_user(openid: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    更新用户信息
    
    Args:
        openid: 用户openid
        update_data: 更新数据
        
    Returns:
        Dict[str, Any]: 更新后的用户信息
    """
    try:
        conn = pymysql.connect(**get_mysql_config())
        
        try:
            with conn.cursor() as cursor:
                # 确保有更新时间
                if 'update_time' not in update_data:
                    update_data['update_time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                # 检查表结构，提取标准字段和额外字段
                cursor.execute(f"SHOW COLUMNS FROM {TABLE_NAME}")
                columns = [column['Field'] for column in cursor.fetchall()]
                
                # 处理extra字段中的标准字段迁移
                if 'extra' in update_data and update_data['extra']:
                    extra_data = update_data['extra']
                    if isinstance(extra_data, str):
                        try:
                            extra_data = json.loads(extra_data)
                        except:
                            extra_data = {}
                    
                    # 从extra中提取标准字段
                    for field in ['birthday', 'wechatId', 'qqId']:
                        if field in extra_data and field in columns:
                            update_data[field] = extra_data.pop(field)
                    
                    # 更新extra字段
                    if extra_data:
                        update_data['extra'] = json.dumps(extra_data)
                    else:
                        update_data['extra'] = None
                
                # 将非标准字段放入extra字段，如果extra不存在则创建
                standard_fields = set(columns)
                extra_fields = {}
                
                for key in list(update_data.keys()):
                    if key not in standard_fields:
                        # 将非标准字段移到extra中
                        extra_fields[key] = update_data.pop(key)
                
                # 如果有扩展字段，则更新或创建extra字段
                if extra_fields:
                    # 先检查是否已存在extra字段
                    cursor.execute(f"SELECT extra FROM {TABLE_NAME} WHERE openid = %s", [openid])
                    existing_extra_row = cursor.fetchone()
                    existing_extra = {}
                    
                    if existing_extra_row and existing_extra_row.get('extra'):
                        try:
                            # 尝试解析现有的extra JSON
                            existing_extra = json.loads(existing_extra_row['extra'])
                        except:
                            pass
                    
                    # 合并现有extra和新的extra字段
                    if isinstance(existing_extra, dict):
                        existing_extra.update(extra_fields)
                        update_data['extra'] = json.dumps(existing_extra)
                    else:
                        update_data['extra'] = json.dumps(extra_fields)
                
                # 如果没有要更新的标准字段，确保至少更新时间被更新
                if not update_data:
                    update_data['update_time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                # 构建更新SQL
                set_clause = ", ".join(f"{k} = %s" for k in update_data.keys())
                params = list(update_data.values()) + [openid]
                
                # 执行更新
                cursor.execute(f"UPDATE {TABLE_NAME} SET {set_clause} WHERE openid = %s", params)
                conn.commit()
                
                # 查询更新后的用户
                cursor.execute(f"SELECT * FROM {TABLE_NAME} WHERE openid = %s", [openid])
                result = cursor.fetchone()
                
                # 如果存在extra字段且是JSON字符串，尝试解析并合并到结果中
                if result and 'extra' in result and result['extra']:
                    try:
                        extra_data = json.loads(result['extra'])
                        if isinstance(extra_data, dict):
                            for key, value in extra_data.items():
                                if key not in result:  # 避免覆盖已有字段
                                    result[key] = value
                    except:
                        logger.error("解析extra字段失败")
                
                return result
        finally:
            conn.close()
    except Exception as e:
        logger.error(f"更新用户信息失败: {str(e)}")
        raise

async def upsert_user(user_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    创建或更新用户信息
    
    Args:
        user_data: 用户数据，必须包含openid
        
    Returns:
        Dict[str, Any]: 用户信息
    """
    openid = user_data.get('openid')
    if not openid:
        raise ValueError("用户数据必须包含openid")
    
    try:
        conn = pymysql.connect(**get_mysql_config())
        
        try:
            with conn.cursor() as cursor:
                # 处理extra字段
                if 'extra' in user_data and user_data['extra']:
                    extra_data = user_data['extra']
                    if isinstance(extra_data, str):
                        try:
                            extra_data = json.loads(extra_data)
                        except:
                            extra_data = {}
                    
                    # 检查表结构
                    cursor.execute(f"SHOW COLUMNS FROM {TABLE_NAME}")
                    columns = [column['Field'] for column in cursor.fetchall()]
                    
                    # 从extra中提取标准字段
                    for field in ['birthday', 'wechatId', 'qqId']:
                        if field in extra_data and field in columns:
                            user_data[field] = extra_data.pop(field)
                    
                    # 更新extra字段
                    if extra_data:
                        user_data['extra'] = json.dumps(extra_data)
                    else:
                        user_data['extra'] = None
                
                # 查询用户是否存在
                sql = f"SELECT * FROM {TABLE_NAME} WHERE openid = %s AND is_deleted = 0 LIMIT 1"
                cursor.execute(sql, [openid])
                existing_user = cursor.fetchone()
                
                if existing_user:
                    # 更新用户信息
                    update_data = {k: v for k, v in user_data.items() if k != 'openid'}
                    if update_data:
                        logger.debug(f"更新用户信息 (openid: {openid[:8]}...)")
                        
                        # 确保有更新时间
                        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        if 'update_time' not in update_data:
                            update_data['update_time'] = now
                        
                        # 同时更新登录时间
                        update_data['last_login'] = now
                        
                        # 构建更新SQL
                        set_clause = ", ".join(f"{k} = %s" for k in update_data.keys())
                        params = list(update_data.values()) + [openid]
                        
                        # 执行更新
                        cursor.execute(f"UPDATE {TABLE_NAME} SET {set_clause} WHERE openid = %s", params)
                    else:
                        # 只更新登录时间
                        logger.debug(f"更新用户登录时间 (openid: {openid[:8]}...)")
                        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        cursor.execute(
                            f"UPDATE {TABLE_NAME} SET last_login = %s, update_time = %s WHERE openid = %s",
                            [now, now, openid]
                        )
                else:
                    # 创建新用户
                    logger.debug(f"创建新用户 (openid: {openid[:8]}...)")
                    
                    # 确保有创建时间
                    if 'create_time' not in user_data:
                        user_data['create_time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    
                    # 确保有更新时间
                    if 'update_time' not in user_data:
                        user_data['update_time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    
                    # 确保有最后登录时间
                    if 'last_login' not in user_data:
                        user_data['last_login'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    
                    # 构建插入SQL
                    fields = ', '.join(user_data.keys())
                    placeholders = ', '.join(['%s'] * len(user_data))
                    
                    # 执行插入
                    cursor.execute(
                        f"INSERT INTO {TABLE_NAME} ({fields}) VALUES ({placeholders})",
                        list(user_data.values())
                    )
                
                # 提交事务
                conn.commit()
                
                # 返回最新的用户信息
                cursor.execute(f"SELECT * FROM {TABLE_NAME} WHERE openid = %s AND is_deleted = 0 LIMIT 1", [openid])
                user_result = cursor.fetchone()
                
                # 如果存在extra字段且是JSON字符串，尝试解析并合并到结果中
                if user_result and 'extra' in user_result and user_result['extra']:
                    try:
                        extra_data = json.loads(user_result['extra'])
                        if isinstance(extra_data, dict):
                            for key, value in extra_data.items():
                                if key not in user_result:  # 避免覆盖已有字段
                                    user_result[key] = value
                    except:
                        logger.error("解析extra字段失败")
                
                return user_result
        finally:
            conn.close()
    except Exception as e:
        logger.error(f"用户信息操作失败: {str(e)}")
        raise 