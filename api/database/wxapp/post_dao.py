"""
帖子数据访问对象
提供帖子相关的数据库操作方法
"""
from typing import Dict, Any, List, Optional, Tuple
from loguru import logger
import json

# 使用新的数据库核心模块
from etl.load import db_core

# 帖子表名
TABLE_NAME = "wxapp_posts"

async def create_post(post_data: Dict[str, Any]) -> int:
    """
    创建新帖子
    
    Args:
        post_data: 帖子数据
        
    Returns:
        int: 帖子ID
    """
    logger.debug(f"创建新帖子: {post_data}")
    
    # 处理列表和字典类型
    processed_data = post_data.copy()
    
    if "images" in processed_data and processed_data["images"] is not None:
        processed_data["images"] = json.dumps(processed_data["images"])
    
    if "tags" in processed_data and processed_data["tags"] is not None:
        processed_data["tags"] = json.dumps(processed_data["tags"])
    
    if "location" in processed_data and processed_data["location"] is not None:
        processed_data["location"] = json.dumps(processed_data["location"])
    
    return await db_core.async_insert(TABLE_NAME, processed_data)

async def get_post_by_id(post_id: int) -> Optional[Dict[str, Any]]:
    """
    根据ID获取帖子
    
    Args:
        post_id: 帖子ID
        
    Returns:
        Optional[Dict[str, Any]]: 帖子数据，不存在则返回None
    """
    logger.debug(f"获取帖子 (ID: {post_id})")
    return await db_core.async_get_by_id(TABLE_NAME, post_id)

async def get_posts(
    conditions: Dict[str, Any],
    tag: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    order_by: str = "update_time DESC"
) -> Tuple[List[Dict[str, Any]], int]:
    """
    获取帖子列表
    
    Args:
        conditions: 查询条件
        tag: 标签筛选
        limit: 返回数量限制
        offset: 起始偏移量
        order_by: 排序方式
        
    Returns:
        Tuple[List[Dict[str, Any]], int]: (帖子列表, 总数)
    """
    logger.debug(f"获取帖子列表: conditions={conditions}, tag={tag}, limit={limit}, offset={offset}, order_by={order_by}")
    
    # 构建WHERE子句
    where_conditions = {}
    extra_conditions = []
    params = []
    
    # 添加基本条件
    for key, value in conditions.items():
        where_conditions[key] = value
    
    # 添加标签筛选
    if tag:
        extra_conditions.append("JSON_CONTAINS(tags, %s)")
        params.append(f'"{tag}"')  # JSON字符串格式
    
    # 处理排序字段映射
    if order_by:
        # 处理字段名映射
        field_mapping = {
            'created_at': 'create_time',
            'updated_at': 'update_time'
        }
        
        for old_field, new_field in field_mapping.items():
            order_by = order_by.replace(old_field, new_field)
    
    # 查询帖子列表
    posts = await db_core.async_query_records(
        TABLE_NAME,
        conditions=where_conditions,
        order_by=order_by,
        limit=limit,
        offset=offset
    )
    
    # 获取总数
    total_count = await db_core.async_count_records(TABLE_NAME, conditions=where_conditions)
    
    return posts, total_count

async def update_post(post_id: int, update_data: Dict[str, Any]) -> bool:
    """
    更新帖子
    
    Args:
        post_id: 帖子ID
        update_data: 更新数据
        
    Returns:
        bool: 更新是否成功
    """
    logger.debug(f"更新帖子 (ID: {post_id}): {update_data}")
    return await db_core.async_update(TABLE_NAME, post_id, update_data)

async def mark_post_deleted(post_id: int) -> bool:
    """
    标记帖子为已删除
    
    Args:
        post_id: 帖子ID
        
    Returns:
        bool: 操作是否成功
    """
    logger.debug(f"标记帖子删除 (ID: {post_id})")
    return await db_core.async_update(TABLE_NAME, post_id, {"is_deleted": 1})

async def increment_view_count(post_id: int) -> bool:
    """
    增加帖子浏览量
    
    Args:
        post_id: 帖子ID
        
    Returns:
        bool: 操作是否成功
    """
    logger.debug(f"更新帖子浏览量 (ID: {post_id})")
    sql = f"UPDATE {TABLE_NAME} SET view_count = view_count + 1 WHERE id = %s"
    result = await db_core.async_query(sql, [post_id])
    return True

async def like_post(post_id: int, openid: str) -> bool:
    """
    点赞帖子
    
    Args:
        post_id: 帖子ID
        openid: 用户openid
        
    Returns:
        bool: 操作是否成功
    """
    logger.debug(f"点赞帖子 (ID: {post_id}, 用户: {openid})")
    sql = f"""
        UPDATE {TABLE_NAME} 
        SET 
            like_count = like_count + 1,
            liked_users = JSON_ARRAY_APPEND(
                COALESCE(liked_users, JSON_ARRAY()),
                '$',
                %s
            )
        WHERE id = %s
    """
    await db_core.async_query(sql, [openid, post_id])
    return True

async def unlike_post(post_id: int, openid: str) -> bool:
    """
    取消点赞帖子
    
    Args:
        post_id: 帖子ID
        openid: 用户openid
        
    Returns:
        bool: 操作是否成功
    """
    logger.debug(f"取消点赞帖子 (ID: {post_id}, 用户: {openid})")
    sql = f"""
        UPDATE {TABLE_NAME} 
        SET 
            like_count = GREATEST(like_count - 1, 0),
            liked_users = JSON_REMOVE(
                liked_users,
                JSON_UNQUOTE(JSON_SEARCH(liked_users, 'one', %s))
            )
        WHERE id = %s
    """
    await db_core.async_query(sql, [openid, post_id])
    return True

async def favorite_post(post_id: int, openid: str) -> bool:
    """
    收藏帖子
    
    Args:
        post_id: 帖子ID
        openid: 用户openid
        
    Returns:
        bool: 操作是否成功
    """
    logger.debug(f"收藏帖子 (ID: {post_id}, 用户: {openid})")
    sql = f"""
        UPDATE {TABLE_NAME} 
        SET 
            favorite_count = favorite_count + 1,
            favorite_users = JSON_ARRAY_APPEND(
                COALESCE(favorite_users, JSON_ARRAY()),
                '$',
                %s
            )
        WHERE id = %s
    """
    await db_core.async_query(sql, [openid, post_id])
    return True

async def unfavorite_post(post_id: int, openid: str) -> bool:
    """
    取消收藏帖子
    
    Args:
        post_id: 帖子ID
        openid: 用户openid
        
    Returns:
        bool: 操作是否成功
    """
    logger.debug(f"取消收藏帖子 (ID: {post_id}, 用户: {openid})")
    sql = f"""
        UPDATE {TABLE_NAME} 
        SET 
            favorite_count = GREATEST(favorite_count - 1, 0),
            favorite_users = JSON_REMOVE(
                favorite_users,
                JSON_UNQUOTE(JSON_SEARCH(favorite_users, 'one', %s))
            )
        WHERE id = %s
    """
    await db_core.async_query(sql, [openid, post_id])
    return True 