"""
用户关注关系数据访问对象
提供用户关注、取消关注、查询关注关系等功能
"""
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from core.utils.logger import register_logger
import pymysql
import asyncio
from config import Config
import os

# 初始化日志
logger = register_logger("wxapp_follow_dao")

# 表名常量
FOLLOW_TABLE = "wxapp_user_follows"
USER_TABLE = "wxapp_users"

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

async def follow_user(follower_id: str, followed_id: str) -> bool:
    """
    关注用户
    
    Args:
        follower_id: 关注者的openid
        followed_id: 被关注者的openid
        
    Returns:
        bool: 操作是否成功
    """
    if follower_id == followed_id:
        logger.warning(f"不能关注自己 (openid: {follower_id[:8]}...)")
        return False
    
    try:
        conn = pymysql.connect(**get_mysql_config())
        
        try:
            with conn.cursor() as cursor:
                # 查询是否已存在关注关系
                sql = f"SELECT id, status FROM {FOLLOW_TABLE} WHERE follower_id = %s AND followed_id = %s"
                cursor.execute(sql, [follower_id, followed_id])
                result = cursor.fetchone()
                
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                if result:
                    # 已存在关系，检查状态
                    if result['status'] == 1:
                        # 已经是关注状态
                        logger.debug(f"已经关注过该用户 (follower: {follower_id[:8]}..., followed: {followed_id[:8]}...)")
                        return True
                    else:
                        # 更新状态为关注
                        sql = f"UPDATE {FOLLOW_TABLE} SET status = 1, update_time = %s, is_deleted = 0 WHERE id = %s"
                        cursor.execute(sql, [current_time, result['id']])
                else:
                    # 新增关注关系
                    sql = f"INSERT INTO {FOLLOW_TABLE} (follower_id, followed_id, create_time, update_time) VALUES (%s, %s, %s, %s)"
                    cursor.execute(sql, [follower_id, followed_id, current_time, current_time])
                
                # 更新用户的关注计数
                update_following_count(cursor, follower_id)
                update_followers_count(cursor, followed_id)
                
                conn.commit()
                logger.debug(f"关注用户成功 (follower: {follower_id[:8]}..., followed: {followed_id[:8]}...)")
                return True
        except Exception as e:
            conn.rollback()
            logger.error(f"关注用户失败: {str(e)}")
            raise
        finally:
            conn.close()
    except Exception as e:
        logger.error(f"数据库连接失败: {str(e)}")
        raise

async def unfollow_user(follower_id: str, followed_id: str) -> bool:
    """
    取消关注用户
    
    Args:
        follower_id: 关注者的openid
        followed_id: 被关注者的openid
        
    Returns:
        bool: 操作是否成功
    """
    try:
        conn = pymysql.connect(**get_mysql_config())
        
        try:
            with conn.cursor() as cursor:
                # 查询是否存在关注关系
                sql = f"SELECT id, status FROM {FOLLOW_TABLE} WHERE follower_id = %s AND followed_id = %s"
                cursor.execute(sql, [follower_id, followed_id])
                result = cursor.fetchone()
                
                if not result or result['status'] == 0:
                    # 不存在关注关系或已经是取消状态
                    logger.debug(f"未关注该用户 (follower: {follower_id[:8]}..., followed: {followed_id[:8]}...)")
                    return True
                
                # 更新为取消关注状态
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                sql = f"UPDATE {FOLLOW_TABLE} SET status = 0, update_time = %s WHERE id = %s"
                cursor.execute(sql, [current_time, result['id']])
                
                # 更新用户的关注计数
                update_following_count(cursor, follower_id)
                update_followers_count(cursor, followed_id)
                
                conn.commit()
                logger.debug(f"取消关注用户成功 (follower: {follower_id[:8]}..., followed: {followed_id[:8]}...)")
                return True
        except Exception as e:
            conn.rollback()
            logger.error(f"取消关注用户失败: {str(e)}")
            raise
        finally:
            conn.close()
    except Exception as e:
        logger.error(f"数据库连接失败: {str(e)}")
        raise

async def check_follow_status(follower_id: str, followed_id: str) -> bool:
    """
    检查用户是否已关注某用户
    
    Args:
        follower_id: 关注者的openid
        followed_id: 被关注者的openid
        
    Returns:
        bool: 是否已关注
    """
    try:
        conn = pymysql.connect(**get_mysql_config())
        
        try:
            with conn.cursor() as cursor:
                sql = f"SELECT id FROM {FOLLOW_TABLE} WHERE follower_id = %s AND followed_id = %s AND status = 1 AND is_deleted = 0"
                cursor.execute(sql, [follower_id, followed_id])
                result = cursor.fetchone()
                
                return result is not None
        finally:
            conn.close()
    except Exception as e:
        logger.error(f"检查关注状态失败: {str(e)}")
        raise

async def get_user_followings(openid: str, limit: int = 20, offset: int = 0) -> Tuple[List[Dict[str, Any]], int]:
    """
    获取用户关注的用户列表
    
    Args:
        openid: 用户openid
        limit: 每页数量
        offset: 偏移量
        
    Returns:
        Tuple[List[Dict[str, Any]], int]: 关注用户列表和总数
    """
    try:
        conn = pymysql.connect(**get_mysql_config())
        
        try:
            with conn.cursor() as cursor:
                # 查询总数
                sql = f"""
                SELECT COUNT(*) as total 
                FROM {FOLLOW_TABLE} f 
                WHERE f.follower_id = %s AND f.status = 1 AND f.is_deleted = 0
                """
                cursor.execute(sql, [openid])
                total = cursor.fetchone()['total']
                
                # 查询关注用户列表
                sql = f"""
                SELECT u.* 
                FROM {USER_TABLE} u
                JOIN {FOLLOW_TABLE} f ON u.openid = f.followed_id
                WHERE f.follower_id = %s AND f.status = 1 AND f.is_deleted = 0 AND u.is_deleted = 0
                ORDER BY f.create_time DESC
                LIMIT %s OFFSET %s
                """
                cursor.execute(sql, [openid, limit, offset])
                users = cursor.fetchall()
                
                # 处理日期时间字段
                for user in users:
                    for field in ['create_time', 'update_time', 'last_login']:
                        if field in user and isinstance(user[field], datetime):
                            user[field] = user[field].strftime("%Y-%m-%d %H:%M:%S")
                
                return users, total
        finally:
            conn.close()
    except Exception as e:
        logger.error(f"获取关注用户列表失败: {str(e)}")
        raise

async def get_user_followers(openid: str, limit: int = 20, offset: int = 0) -> Tuple[List[Dict[str, Any]], int]:
    """
    获取关注用户的用户列表（粉丝列表）
    
    Args:
        openid: 用户openid
        limit: 每页数量
        offset: 偏移量
        
    Returns:
        Tuple[List[Dict[str, Any]], int]: 粉丝列表和总数
    """
    try:
        conn = pymysql.connect(**get_mysql_config())
        
        try:
            with conn.cursor() as cursor:
                # 查询总数
                sql = f"""
                SELECT COUNT(*) as total 
                FROM {FOLLOW_TABLE} f 
                WHERE f.followed_id = %s AND f.status = 1 AND f.is_deleted = 0
                """
                cursor.execute(sql, [openid])
                total = cursor.fetchone()['total']
                
                # 查询粉丝列表
                sql = f"""
                SELECT u.* 
                FROM {USER_TABLE} u
                JOIN {FOLLOW_TABLE} f ON u.openid = f.follower_id
                WHERE f.followed_id = %s AND f.status = 1 AND f.is_deleted = 0 AND u.is_deleted = 0
                ORDER BY f.create_time DESC
                LIMIT %s OFFSET %s
                """
                cursor.execute(sql, [openid, limit, offset])
                users = cursor.fetchall()
                
                # 处理日期时间字段
                for user in users:
                    for field in ['create_time', 'update_time', 'last_login']:
                        if field in user and isinstance(user[field], datetime):
                            user[field] = user[field].strftime("%Y-%m-%d %H:%M:%S")
                
                return users, total
        finally:
            conn.close()
    except Exception as e:
        logger.error(f"获取粉丝列表失败: {str(e)}")
        raise

def update_following_count(cursor, openid: str):
    """更新用户的关注数量"""
    sql = f"""
    UPDATE {USER_TABLE} SET following_count = (
        SELECT COUNT(*) FROM {FOLLOW_TABLE} 
        WHERE follower_id = %s AND status = 1 AND is_deleted = 0
    )
    WHERE openid = %s
    """
    cursor.execute(sql, [openid, openid])

def update_followers_count(cursor, openid: str):
    """更新用户的粉丝数量"""
    sql = f"""
    UPDATE {USER_TABLE} SET followers_count = (
        SELECT COUNT(*) FROM {FOLLOW_TABLE} 
        WHERE followed_id = %s AND status = 1 AND is_deleted = 0
    )
    WHERE openid = %s
    """
    cursor.execute(sql, [openid, openid])

async def init_follow_table():
    """
    初始化用户关注关系表
    
    如果表不存在，则创建表
    """
    try:
        conn = pymysql.connect(**get_mysql_config())
        
        try:
            with conn.cursor() as cursor:
                # 获取表结构SQL文件
                base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
                sql_file_path = os.path.join(base_dir, "etl", "load", "mysql_tables", "wxapp_user_follows.sql")
                
                # 读取SQL文件内容
                with open(sql_file_path, 'r', encoding='utf-8') as f:
                    sql = f.read()
                
                # 执行SQL创建表
                cursor.execute(sql)
                conn.commit()
                
                logger.debug(f"初始化用户关注关系表成功")
                return True
        except Exception as e:
            conn.rollback()
            logger.error(f"初始化用户关注关系表失败: {str(e)}")
            raise
        finally:
            conn.close()
    except Exception as e:
        logger.error(f"数据库连接失败: {str(e)}")
        raise 