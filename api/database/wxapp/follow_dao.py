"""
用户关注关系数据访问对象
提供用户关注、取消关注、查询关注关系等功能
"""
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
import os
from loguru import logger

# 直接使用数据库核心模块
from etl.load import db_core

# 表名常量
FOLLOW_TABLE = "wxapp_user_follows"
USER_TABLE = "wxapp_users"

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
        # 查询是否已存在关注关系
        sql = f"SELECT id, status FROM {FOLLOW_TABLE} WHERE follower_id = %s AND followed_id = %s"
        result = await db_core.async_query(sql, [follower_id, followed_id])
        
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if result:
            # 已存在关系，检查状态
            if result[0]['status'] == 1:
                # 已经是关注状态
                logger.debug(f"已经关注过该用户 (follower: {follower_id[:8]}..., followed: {followed_id[:8]}...)")
                return True
            else:
                # 更新状态为关注
                sql = f"UPDATE {FOLLOW_TABLE} SET status = 1, update_time = %s, is_deleted = 0 WHERE id = %s"
                await db_core.async_query(sql, [current_time, result[0]['id']])
        else:
            # 新增关注关系
            follow_data = {
                'follower_id': follower_id,
                'followed_id': followed_id,
                'create_time': current_time,
                'update_time': current_time,
                'status': 1,
                'is_deleted': 0
            }
            await db_core.async_insert(FOLLOW_TABLE, follow_data)
        
        # 更新用户的关注计数
        await update_following_count(follower_id)
        await update_followers_count(followed_id)
        
        logger.debug(f"关注用户成功 (follower: {follower_id[:8]}..., followed: {followed_id[:8]}...)")
        return True
    except Exception as e:
        logger.error(f"关注用户失败: {str(e)}")
        return False

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
        # 查询是否存在关注关系
        sql = f"SELECT id, status FROM {FOLLOW_TABLE} WHERE follower_id = %s AND followed_id = %s"
        result = await db_core.async_query(sql, [follower_id, followed_id])
        
        if not result or result[0]['status'] == 0:
            # 不存在关注关系或已经是取消状态
            logger.debug(f"未关注该用户 (follower: {follower_id[:8]}..., followed: {followed_id[:8]}...)")
            return True
        
        # 更新为取消关注状态
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sql = f"UPDATE {FOLLOW_TABLE} SET status = 0, update_time = %s WHERE id = %s"
        await db_core.async_query(sql, [current_time, result[0]['id']])
        
        # 更新用户的关注计数
        await update_following_count(follower_id)
        await update_followers_count(followed_id)
        
        logger.debug(f"取消关注用户成功 (follower: {follower_id[:8]}..., followed: {followed_id[:8]}...)")
        return True
    except Exception as e:
        logger.error(f"取消关注用户失败: {str(e)}")
        return False

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
        sql = f"SELECT id FROM {FOLLOW_TABLE} WHERE follower_id = %s AND followed_id = %s AND status = 1 AND is_deleted = 0"
        result = await db_core.async_query(sql, [follower_id, followed_id])
        return len(result) > 0
    except Exception as e:
        logger.error(f"检查关注状态失败: {str(e)}")
        return False

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
        # 查询总数
        total_sql = f"""
        SELECT COUNT(*) as total 
        FROM {FOLLOW_TABLE} f 
        WHERE f.follower_id = %s AND f.status = 1 AND f.is_deleted = 0
        """
        total_result = await db_core.async_query(total_sql, [openid])
        total = total_result[0]['total'] if total_result else 0
        
        # 查询关注用户列表
        users_sql = f"""
        SELECT u.* 
        FROM {USER_TABLE} u
        JOIN {FOLLOW_TABLE} f ON u.openid = f.followed_id
        WHERE f.follower_id = %s AND f.status = 1 AND f.is_deleted = 0 AND u.is_deleted = 0
        ORDER BY f.create_time DESC
        LIMIT %s OFFSET %s
        """
        users = await db_core.async_query(users_sql, [openid, limit, offset])
        
        # 处理日期时间字段
        for user in users:
            for field in ['create_time', 'update_time', 'last_login']:
                if field in user and isinstance(user[field], datetime):
                    user[field] = user[field].strftime("%Y-%m-%d %H:%M:%S")
        
        return users, total
    except Exception as e:
        logger.error(f"获取关注用户列表失败: {str(e)}")
        return [], 0

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
        # 查询总数
        total_sql = f"""
        SELECT COUNT(*) as total 
        FROM {FOLLOW_TABLE} f 
        WHERE f.followed_id = %s AND f.status = 1 AND f.is_deleted = 0
        """
        total_result = await db_core.async_query(total_sql, [openid])
        total = total_result[0]['total'] if total_result else 0
        
        # 查询粉丝列表
        users_sql = f"""
        SELECT u.* 
        FROM {USER_TABLE} u
        JOIN {FOLLOW_TABLE} f ON u.openid = f.follower_id
        WHERE f.followed_id = %s AND f.status = 1 AND f.is_deleted = 0 AND u.is_deleted = 0
        ORDER BY f.create_time DESC
        LIMIT %s OFFSET %s
        """
        users = await db_core.async_query(users_sql, [openid, limit, offset])
        
        # 处理日期时间字段
        for user in users:
            for field in ['create_time', 'update_time', 'last_login']:
                if field in user and isinstance(user[field], datetime):
                    user[field] = user[field].strftime("%Y-%m-%d %H:%M:%S")
        
        return users, total
    except Exception as e:
        logger.error(f"获取粉丝列表失败: {str(e)}")
        return [], 0

async def update_following_count(openid: str) -> bool:
    """更新用户的关注数量"""
    try:
        sql = f"""
        UPDATE {USER_TABLE} SET following_count = (
            SELECT COUNT(*) FROM {FOLLOW_TABLE} 
            WHERE follower_id = %s AND status = 1 AND is_deleted = 0
        )
        WHERE openid = %s
        """
        result = await db_core.async_query(sql, [openid, openid])
        return result > 0
    except Exception as e:
        logger.error(f"更新用户关注数量失败: {str(e)}")
        return False

async def update_followers_count(openid: str) -> bool:
    """更新用户的粉丝数量"""
    try:
        sql = f"""
        UPDATE {USER_TABLE} SET followers_count = (
            SELECT COUNT(*) FROM {FOLLOW_TABLE} 
            WHERE followed_id = %s AND status = 1 AND is_deleted = 0
        )
        WHERE openid = %s
        """
        result = await db_core.async_query(sql, [openid, openid])
        return result > 0
    except Exception as e:
        logger.error(f"更新用户粉丝数量失败: {str(e)}")
        return False

async def init_follow_table() -> bool:
    """
    初始化用户关注关系表
    
    如果表不存在，则创建表
    """
    try:
        # 获取表结构SQL文件
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        sql_file_path = os.path.join(base_dir, "etl", "load", "mysql_tables", "wxapp_user_follows.sql")
        
        # 读取SQL文件内容
        with open(sql_file_path, 'r', encoding='utf-8') as f:
            sql = f.read()
        
        # 执行SQL创建表
        await db_core.async_query(sql)
        
        logger.debug("初始化用户关注关系表成功")
        return True
    except Exception as e:
        logger.error(f"初始化用户关注关系表失败: {str(e)}")
        return False 