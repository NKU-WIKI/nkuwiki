"""
评论数据访问对象
提供评论相关的数据库操作方法
"""
from typing import Dict, Any, List, Optional, Tuple
from loguru import logger
import json

# 直接从etl模块导入方法
from etl.load.py_mysql import (
    insert_record,
    update_record,
    delete_record,
    query_records,
    count_records,
    get_record_by_id,
    execute_raw_query,
    execute_custom_query
)

# 评论表名
TABLE_NAME = "wxapp_comments"

async def create_comment(comment_data: Dict[str, Any]) -> int:
    """
    创建新评论
    
    Args:
        comment_data: 评论数据
        
    Returns:
        int: 评论ID
    """
    logger.debug(f"创建新评论: {comment_data}")
    
    # 复制评论数据，避免修改原始数据
    processed_data = comment_data.copy()
    
    # 将列表和字典类型转换为JSON字符串
    if "images" in processed_data and processed_data["images"] is not None:
        processed_data["images"] = json.dumps(processed_data["images"])
    
    # 创建评论
    comment_id = insert_record(TABLE_NAME, processed_data)
    
    # 更新帖子评论数
    if comment_id and processed_data.get("post_id"):
        execute_raw_query(
            "UPDATE wxapp_posts SET comment_count = comment_count + 1 WHERE id = %s",
            [processed_data["post_id"]]
        )
    
    return comment_id

async def get_comment_by_id(comment_id: int) -> Optional[Dict[str, Any]]:
    """
    根据ID获取评论
    
    Args:
        comment_id: 评论ID
        
    Returns:
        Optional[Dict[str, Any]]: 评论数据，不存在则返回None
    """
    logger.debug(f"获取评论 (ID: {comment_id})")
    return get_record_by_id(TABLE_NAME, comment_id)

async def get_post_comments(
    post_id: int,
    parent_id: Optional[int] = None,
    limit: int = 20,
    offset: int = 0,
    sort_by: str = "create_time DESC"
) -> Tuple[List[Dict[str, Any]], int]:
    """
    获取帖子的评论列表
    
    Args:
        post_id: 帖子ID
        parent_id: 父评论ID，为None时获取一级评论
        limit: 返回数量限制
        offset: 起始偏移量
        sort_by: 排序方式
        
    Returns:
        Tuple[List[Dict[str, Any]], int]: (评论列表, 总数)
    """
    logger.debug(f"获取帖子评论列表: post_id={post_id}, parent_id={parent_id}, limit={limit}, offset={offset}")
    
    # 处理父评论为NULL的情况
    if parent_id is None:
        # 避免使用execute_custom_query，直接使用query_records
        # 通过sql语句手动实现NULL的比较
        query = f"""
            SELECT * FROM {TABLE_NAME} 
            WHERE post_id = %s AND is_deleted = 0 AND parent_id IS NULL 
            ORDER BY {sort_by} 
            LIMIT {limit} OFFSET {offset}
        """
        count_query = f"""
            SELECT COUNT(*) as count FROM {TABLE_NAME} 
            WHERE post_id = %s AND is_deleted = 0 AND parent_id IS NULL
        """
        
        logger.debug(f"执行SQL查询: {query} 参数: {[post_id]}")
        
        try:
            # 使用execute_raw_query
            result = execute_raw_query(query, [post_id])
            comments = result if result else []
            logger.debug(f"查询结果: {comments}")
            
            count_result = execute_raw_query(count_query, [post_id])
            total = count_result[0]['count'] if count_result else 0
            logger.debug(f"查询总数: {total}")
        except Exception as e:
            logger.error(f"获取评论列表错误: {e}")
            return [], 0
    else:
        # 有父评论的情况，使用conditions参数
        conditions = {
            "post_id": post_id,
            "is_deleted": 0,
            "parent_id": parent_id
        }
        
        logger.debug(f"查询条件: {conditions}")
        
        try:
            # 查询评论列表
            comments = query_records(
                TABLE_NAME,
                conditions=conditions,
                order_by=sort_by,
                limit=limit,
                offset=offset
            )
            logger.debug(f"查询结果: {comments}")
            
            # 获取总数
            total = count_records(TABLE_NAME, conditions=conditions)
            logger.debug(f"查询总数: {total}")
        except Exception as e:
            logger.error(f"获取评论列表错误: {e}")
            return [], 0
    
    # 如果是一级评论，获取每个评论的回复预览
    if parent_id is None and comments:
        for comment in comments:
            try:
                # 获取最新的2条回复
                reply_conditions = {
                    "parent_id": comment["id"],
                    "is_deleted": 0
                }
                
                replies = query_records(
                    TABLE_NAME,
                    conditions=reply_conditions,
                    order_by="create_time DESC",
                    limit=2
                )
                
                # 获取回复总数
                reply_count = count_records(
                    TABLE_NAME,
                    conditions=reply_conditions
                )
                
                comment["reply_count"] = reply_count
                comment["reply_preview"] = replies
            except Exception as e:
                logger.error(f"获取评论回复预览错误: {e}")
                comment["reply_count"] = 0
                comment["reply_preview"] = []
    
    logger.debug(f"返回评论列表: {len(comments)}条, 总数: {total}")
    return comments, total

async def update_comment(comment_id: int, update_data: Dict[str, Any]) -> bool:
    """
    更新评论
    
    Args:
        comment_id: 评论ID
        update_data: 更新数据
        
    Returns:
        bool: 更新是否成功
    """
    logger.debug(f"更新评论 (ID: {comment_id}): {update_data}")
    return update_record(TABLE_NAME, comment_id, update_data)

async def mark_comment_deleted(comment_id: int) -> bool:
    """
    标记评论为已删除
    
    Args:
        comment_id: 评论ID
        
    Returns:
        bool: 操作是否成功
    """
    logger.debug(f"标记评论删除 (ID: {comment_id})")
    
    # 获取评论信息
    comment = get_record_by_id(TABLE_NAME, comment_id)
    if not comment:
        return False
    
    # 标记删除
    success = update_record(TABLE_NAME, comment_id, {"is_deleted": 1})
    
    if success and comment.get("post_id"):
        # 更新帖子评论数
        execute_raw_query(
            "UPDATE wxapp_posts SET comment_count = GREATEST(comment_count - 1, 0) WHERE id = %s",
            [comment["post_id"]]
        )
    
    return success

async def like_comment(comment_id: int, openid: str) -> bool:
    """
    点赞评论
    
    Args:
        comment_id: 评论ID
        openid: 用户openid
        
    Returns:
        bool: 操作是否成功
    """
    logger.debug(f"点赞评论 (ID: {comment_id}, 用户: {openid})")
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
    execute_raw_query(sql, [openid, comment_id])
    return True

async def unlike_comment(comment_id: int, openid: str) -> bool:
    """
    取消点赞评论
    
    Args:
        comment_id: 评论ID
        openid: 用户openid
        
    Returns:
        bool: 操作是否成功
    """
    logger.debug(f"取消点赞评论 (ID: {comment_id}, 用户: {openid})")
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
    execute_raw_query(sql, [openid, comment_id])
    return True 