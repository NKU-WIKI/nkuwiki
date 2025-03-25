"""
用户数据访问对象
提供用户信息的CRUD操作
"""
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from loguru import logger

# 使用新的数据库核心模块替代原有的py_mysql
from etl.load import db_core

# 表名常量
TABLE_NAME = "wxapp_users"

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
        users = await db_core.async_query_records(TABLE_NAME, {"openid": openid, "is_deleted": 0}, limit=1)
        return users[0] if users else None
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
        # 查询用户列表
        users = await db_core.async_query_records(
            TABLE_NAME, 
            {"is_deleted": 0}, 
            order_by={"id": "DESC"}, 
            limit=limit, 
            offset=offset
        )
        
        # 查询总数
        sql = f"SELECT COUNT(*) as total FROM {TABLE_NAME} WHERE is_deleted = 0"
        count_result = await db_core.async_query(sql)
        total = count_result[0]['total'] if count_result and count_result[0] else 0
        
        return users, total
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
        # 确保有更新时间
        if 'update_time' not in update_data:
            update_data['update_time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 直接使用nick_name字段，确保不将nickname迁移到extra中
        if 'nickname' in update_data:
            # 将nickname复制到nick_name字段，然后删除原nickname字段
            update_data['nick_name'] = update_data.pop('nickname')
        
        logger.debug(f"更新用户 - 处理后的更新数据: {update_data}")
        
        # 查询用户ID
        users = await db_core.async_query_records(TABLE_NAME, {"openid": openid, "is_deleted": 0}, limit=1)
        if not users:
            raise ValueError(f"用户不存在: {openid}")
        
        user_id = users[0]['id']
        
        # 执行更新
        success = await db_core.async_update(TABLE_NAME, user_id, update_data)
        if not success:
            raise ValueError(f"更新用户失败: {openid}")
        
        # 查询更新后的用户
        updated_user = await db_core.async_get_by_id(TABLE_NAME, user_id)
        
        return updated_user
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
        # 直接使用nick_name字段，确保不将nickname迁移到extra中
        if 'nickname' in user_data:
            # 将nickname复制到nick_name字段，然后删除原nickname字段 
            user_data['nick_name'] = user_data.pop('nickname')
        
        # 查询用户是否存在
        users = await db_core.async_query_records(TABLE_NAME, {"openid": openid, "is_deleted": 0}, limit=1)
        
        if users:
            # 更新用户
            user_id = users[0]['id']
            update_data = {k: v for k, v in user_data.items() if k != 'openid'}
            if update_data:
                logger.debug(f"更新用户 (openid: {openid[:8]}...)")
                
                # 确保有更新时间和登录时间
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                if 'update_time' not in update_data:
                    update_data['update_time'] = now
                update_data['last_login'] = now
                
                # 执行更新
                await db_core.async_update(TABLE_NAME, user_id, update_data)
            else:
                # 只更新登录时间
                logger.debug(f"更新用户登录时间 (openid: {openid[:8]}...)")
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                await db_core.async_update(TABLE_NAME, user_id, {"last_login": now, "update_time": now})
            
            # 获取更新后的用户信息
            user_result = await db_core.async_get_by_id(TABLE_NAME, user_id)
        else:
            # 创建新用户
            logger.debug(f"创建新用户 (openid: {openid[:8]}...)")
            
            # 设置默认值
            if 'create_time' not in user_data:
                user_data['create_time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            if 'update_time' not in user_data:
                user_data['update_time'] = user_data['create_time']
            if 'last_login' not in user_data:
                user_data['last_login'] = user_data['create_time']
            if 'platform' not in user_data:
                user_data['platform'] = 'wxapp'
            if 'status' not in user_data:
                user_data['status'] = 1
            if 'is_deleted' not in user_data:
                user_data['is_deleted'] = 0
            
            # 执行插入
            inserted_id = await db_core.async_insert(TABLE_NAME, user_data)
            
            # 获取插入后的用户信息
            user_result = await db_core.async_get_by_id(TABLE_NAME, inserted_id)
        
        return user_result
    except Exception as e:
        logger.error(f"用户信息操作失败: {str(e)}")
        raise

async def insert_user_if_not_exists(openid: str) -> Dict[str, Any]:
    """
    只有在用户不存在时才插入基本的用户信息
    
    Args:
        openid: 用户的openid
        
    Returns:
        Dict[str, Any]: 用户信息，不会更新已存在用户的数据
    """
    if not openid:
        raise ValueError("openid不能为空")
    
    try:
        # 查询用户是否存在
        users = await db_core.async_query_records(TABLE_NAME, {"openid": openid, "is_deleted": 0}, limit=1)
        
        if users:
            # 用户已存在，直接返回现有用户信息
            logger.debug(f"用户已存在，不更新任何信息 (openid: {openid[:8]}...)")
            return users[0]
        else:
            # 创建新用户，只保存openid和必要的字段
            logger.debug(f"创建新用户，仅保存openid (openid: {openid[:8]}...)")
            
            # 准备最小的用户数据
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            user_data = {
                'openid': openid,
                'create_time': now,
                'update_time': now,
                'last_login': now,
                'platform': 'wxapp',
                'status': 1,
                'is_deleted': 0
            }
            
            # 执行插入
            inserted_id = await db_core.async_insert(TABLE_NAME, user_data)
            
            # 获取插入后的用户信息
            user_result = await db_core.async_get_by_id(TABLE_NAME, inserted_id)
            return user_result
            
    except Exception as e:
        logger.error(f"插入用户信息失败: {str(e)}")
        raise

async def update_user_counter(openid: str, field: str, increment: bool = True) -> bool:
    """
    更新用户计数器字段
    
    Args:
        openid: 用户的openid
        field: 要更新的计数器字段名
        increment: 是否是增加操作
        
    Returns:
        bool: 操作是否成功
    """
    logger.debug(f"{'增加' if increment else '减少'}用户{field} (openid: {openid[:8]}...)")
    try:
        # 构造SQL语句，如果是减少操作，则使用GREATEST确保不会小于0
        if increment:
            sql = f"UPDATE {TABLE_NAME} SET {field} = {field} + 1, update_time = NOW() WHERE openid = %s"
        else:
            sql = f"UPDATE {TABLE_NAME} SET {field} = GREATEST({field} - 1, 0), update_time = NOW() WHERE openid = %s"
        
        # 执行更新
        result = await db_core.async_query(sql, [openid], fetch=False)
        return result > 0
    except Exception as e:
        logger.error(f"更新用户{field}失败: {str(e)}")
        return False

async def increment_user_likes_count(openid: str) -> bool:
    """
    增加用户收到的点赞数
    
    Args:
        openid: 帖子作者的openid
        
    Returns:
        bool: 操作是否成功
    """
    return await update_user_counter(openid, 'likes_count', True)

async def decrement_user_likes_count(openid: str) -> bool:
    """
    减少用户收到的点赞数
    
    Args:
        openid: 帖子作者的openid
        
    Returns:
        bool: 操作是否成功
    """
    return await update_user_counter(openid, 'likes_count', False)

async def increment_user_favorites_count(openid: str) -> bool:
    """
    增加用户收到的收藏数
    
    Args:
        openid: 帖子作者的openid
        
    Returns:
        bool: 操作是否成功
    """
    return await update_user_counter(openid, 'favorites_count', True)

async def decrement_user_favorites_count(openid: str) -> bool:
    """
    减少用户收到的收藏数
    
    Args:
        openid: 帖子作者的openid
        
    Returns:
        bool: 操作是否成功
    """
    return await update_user_counter(openid, 'favorites_count', False)

async def increment_user_posts_count(openid: str) -> bool:
    """
    增加用户发帖数
    
    Args:
        openid: 发帖用户的openid
        
    Returns:
        bool: 操作是否成功
    """
    return await update_user_counter(openid, 'posts_count', True)

async def decrement_user_posts_count(openid: str) -> bool:
    """
    减少用户发帖数
    
    Args:
        openid: 发帖用户的openid
        
    Returns:
        bool: 操作是否成功
    """
    return await update_user_counter(openid, 'posts_count', False) 