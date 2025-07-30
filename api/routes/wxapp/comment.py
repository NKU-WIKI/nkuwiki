# This file will manage all comment-related API endpoints.

"""
微信小程序评论相关API接口
处理评论创建、查询、更新、删除和点赞等功能
"""
from fastapi import APIRouter, Query, Body, Depends, BackgroundTasks
from api.models.common import Response, Request, validate_params, PaginationInfo
from etl.load import (
    query_records, 
    insert_record, 
    update_record, 
    execute_custom_query
)
from etl.load.db_pool_manager import get_db_connection as _get_db_connection
import json
import logging
import asyncio
import aiomysql
from typing import Dict, Any, Optional, List
from pydantic import BaseModel

from ._utils import _update_count, create_notification
from api.common.dependencies import get_current_active_user, get_current_active_user_optional

# 配置日志
logger = logging.getLogger("wxapp.comment")
router = APIRouter()


async def _enrich_comments(comments: List[Dict[str, Any]], current_user: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """高效地为评论列表批量补充作者信息、父评论信息和当前用户的点赞状态"""
    if not comments:
        return []

    author_ids = {c.get("user_id") for c in comments if c.get("user_id")}
    comment_ids = [c.get("id") for c in comments if c.get("id")]
    parent_ids = {c.get("parent_id") for c in comments if c.get("parent_id")}

    # 批量获取用户信息
    users_info_map = {}
    if author_ids:
        placeholders = ', '.join(['%s'] * len(author_ids))
        user_sql = f"SELECT id, nickname, avatar, bio FROM wxapp_user WHERE id IN ({placeholders})"
        user_results = await execute_custom_query(user_sql, list(author_ids))
        users_info_map = {user['id']: user for user in user_results}

    # 批量获取父评论信息
    parent_comments_map = {}
    if parent_ids:
        placeholders = ', '.join(['%s'] * len(parent_ids))
        parent_sql = f"""
        SELECT 
            c.id, c.content, c.user_id, c.create_time,
            u.nickname as parent_author_nickname
        FROM wxapp_comment c
        LEFT JOIN wxapp_user u ON c.user_id = u.id
        WHERE c.id IN ({placeholders})
        """
        parent_results = await execute_custom_query(parent_sql, list(parent_ids))
        parent_comments_map = {parent['id']: parent for parent in parent_results}

    # 批量获取点赞状态
    liked_comment_ids = set()
    if current_user and comment_ids:
        current_user_id = current_user['id']
        placeholders = ', '.join(['%s'] * len(comment_ids))
        like_sql = f"SELECT target_id FROM wxapp_action WHERE action_type = 'like' AND target_type = 'comment' AND user_id = %s AND target_id IN ({placeholders})"
        # 将comment_ids转换为字符串，因为wxapp_action.target_id是VARCHAR类型
        like_params = [current_user_id] + [str(cid) for cid in comment_ids]
        like_results = await execute_custom_query(like_sql, like_params)
        # 将target_id转换为整数进行比较，确保类型一致
        liked_comment_ids = {int(res['target_id']) for res in like_results}
    
    # 注入信息到评论中
    for comment in comments:
        # 注入作者信息
        author_id = comment.get("user_id")
        user_info = users_info_map.get(author_id, {})
        
        # 避免用户信息中的id字段覆盖评论的id，但保留用户ID作为author_id
        if 'id' in user_info:
            user_info = user_info.copy()  # 创建副本避免修改原数据
            comment["author_id"] = user_info['id']  # 保存用户ID为author_id
            del user_info['id']  # 删除用户的id字段以避免冲突
        
        comment.update(user_info)
        comment["is_liked"] = comment.get("id") in liked_comment_ids
        
        # 注入父评论信息
        parent_id = comment.get("parent_id")
        if parent_id and parent_id in parent_comments_map:
            parent_info = parent_comments_map[parent_id]
            comment["parent_comment"] = {
                "id": parent_info.get("id"),
                "content": parent_info.get("content", "")[:50] + ("..." if len(parent_info.get("content", "")) > 50 else ""),  # 截取前50字符
                "author_nickname": parent_info.get("parent_author_nickname", "未知用户"),
                "create_time": str(parent_info.get("create_time", ""))
            }
        else:
            comment["parent_comment"] = None
        
        if 'openid' in comment: # 保留，以防万一
            del comment['openid']

    return comments

# 递归获取子评论的函数
async def get_child_comments(comment_id: int, current_user: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """递归获取评论的所有子评论，使用批量查询优化性能"""
    replies_sql = """
    SELECT 
        id, resource_id, resource_type, parent_id, user_id, 
        content, image, like_count, reply_count, status, is_deleted, 
        create_time, update_time
    FROM wxapp_comment 
    WHERE parent_id = %s AND status = 1 AND is_deleted = 0
    ORDER BY create_time DESC
    """
    try:
        replies = await execute_custom_query(replies_sql, [comment_id])
    except Exception as e:
        logger.error(f"查询子评论失败 (parent_id={comment_id}): {e}")
        return []

    if not replies:
        return []
    
    # 高效地为当前层级的回复补充信息
    enriched_replies = await _enrich_comments(replies, current_user)
    
    # 递归处理更深层级的子评论
    for i, reply in enumerate(enriched_replies):
        # "parent_comment_count" 实际上是该评论在同级回复中的位置索引
        reply["parent_comment_count"] = i
        
        children = await get_child_comments(reply.get("id"), current_user)
        if children:
            reply["children"] = children
    
    return enriched_replies

async def _send_comment_notification(
    resource_type: str, 
    resource: Dict, 
    parent_id: Optional[int], 
    current_user: Dict[str, Any]
):
    """发送评论相关的通知。"""
    try:
        # 检查 resource 是否为空
        if not resource:
            logger.warning("resource 为空，跳过发送评论通知")
            return
            
        user_id = current_user['id']
        sender_info = current_user # 直接使用传入的用户对象
        sender_payload = {
            "user_id": user_id, 
            "avatar": sender_info.get("avatar", ""), 
            "nickname": sender_info.get("nickname", "")
        }

        # 回复通知
        if parent_id:
            parent_result = await execute_custom_query(
                "SELECT user_id FROM wxapp_comment WHERE id = %s", (parent_id,)
            )
            parent_comment = parent_result[0] if parent_result else None
            if parent_comment and parent_comment.get("user_id") != user_id:
                await create_notification(
                    openid=parent_comment["user_id"],
                    title="收到新回复",
                    content="用户回复了你的评论",
                    target_id=parent_id,
                    target_type="comment",
                    sender_payload=sender_payload
                )
        # 资源评论通知
        elif resource.get("user_id") != user_id:
            safe_title = resource.get('title', '无标题')
            resource_name = '帖子' if resource_type == 'post' else '知识'
            await create_notification(
                user_id=resource["user_id"],
                title="收到新评论",
                content=f"用户评论了你的{resource_name}「{safe_title}」",
                target_id=resource.get("id"),
                target_type=resource_type,
                sender_payload=sender_payload
            )
    except Exception as e:
        logger.exception(f"发送评论通知时出错: {e}")


@router.get("/detail", summary="获取单条评论详情")
async def get_comment_detail(
    comment_id: str,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """获取评论详情"""
    if not comment_id:
        return Response.bad_request(details={"message": "缺少comment_id参数"})
    
    try:
        # 确保comment_id是整数
        try:
            # 移除可能存在的括号，只保留数字部分
            comment_id_clean = comment_id.strip('()').strip()
            comment_id_int = int(comment_id_clean)
            logger.debug(f"处理comment_id参数: 原值={comment_id}, 清理后={comment_id_clean}, 转换为整数={comment_id_int}")
        except ValueError:
            logger.warning(f"comment_id参数格式错误: {comment_id}")
            return Response.bad_request(details={"message": "comment_id必须是整数"})
        
        # 使用单一SQL查询获取评论详情
        comment_sql = """
        SELECT * FROM wxapp_comment 
        WHERE id = %s
        """
        comment_result = await execute_custom_query(comment_sql, [comment_id_int], fetch='one')

        if not comment_result:
            return Response.not_found(resource="评论")
            
        comment = dict(comment_result)

        # 使用单一查询获取点赞状态
        user_id = current_user['id']
        like_query_coro = execute_custom_query(
            """
            SELECT 1 FROM wxapp_action 
            WHERE user_id = %s AND action_type = 'like' AND target_id = %s AND target_type = 'comment' 
            LIMIT 1
            """, 
            [user_id, comment_id_int],
            fetch='one'
        )
        
        # 获取用户信息
        user_query_coro = execute_custom_query(
            """
            SELECT nickname, avatar, bio FROM wxapp_user 
            WHERE id = %s 
            LIMIT 1
            """, 
            [comment.get("user_id")],
            fetch='one'
        )
        
        # 并行执行查询
        like_record, user_info = await asyncio.gather(like_query_coro, user_query_coro)
        
        # 判断是否已点赞
        liked = bool(like_record)
        
        # 添加用户信息
        if user_info:
            comment["nickname"] = user_info.get("nickname")
            comment["avatar"] = user_info.get("avatar")
            comment["bio"] = user_info.get("bio")
        
        # 递归获取所有子评论
        children = await get_child_comments(comment_id_int, current_user)

        # 移除 openid 
        if 'openid' in comment:
            del comment['openid']

        result = {
            **comment,
            "liked": liked,
            "like_count": comment.get("like_count", 0),
            "children": children
        }

        return Response.success(data=result)
    except Exception as e:
        return Response.error(details={"message": f"获取评论详情失败: {str(e)}"})


@router.get("/status")
async def get_comment_status(
    comment_id: str = Query(..., description="评论ID列表，用逗号分隔"),
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """获取评论状态"""
    if not comment_id:
        return Response.bad_request(details={"message": "缺少comment_id参数"})
    
    try:
        # 分割评论ID列表并转换为整数
        raw_ids = comment_id.split(',')
        if not raw_ids:
            return Response.bad_request(details={"message": "评论ID列表格式错误"})
        
        # 处理每个ID，确保为整数
        ids = []
        for id_str in raw_ids:
            try:
                # 移除可能存在的括号，只保留数字部分
                clean_id = id_str.strip('()').strip()
                ids.append(int(clean_id))
            except ValueError:
                logger.warning(f"评论ID格式错误: {id_str}")
                # 跳过无效ID
                continue
        
        if not ids:
            return Response.bad_request(details={"message": "未提供有效的评论ID"})
        
        # 使用单一SQL查询获取所有点赞状态
        user_id = current_user['id']
        placeholders = ','.join(['%s'] * len(ids))
        sql = f"""
        SELECT target_id, 1 as is_liked 
        FROM wxapp_action 
        WHERE user_id = %s AND action_type = 'like' AND target_type = 'comment' AND target_id IN ({placeholders})
        """
        
        # 执行查询，将ids转换为字符串因为wxapp_action.target_id是VARCHAR类型
        comments = await execute_custom_query(sql, [user_id] + [str(cid) for cid in ids])
        
        # 转换点赞结果为集合，将target_id转为整数方便快速查找
        liked_ids = {int(record['target_id']) for record in comments} if comments else set()
        
        # 为每个请求的评论ID构建状态信息
        result = {}
        comment_dict = {int(comment['target_id']): comment for comment in comments} if comments else {}
        
        for cid in ids:
            comment = comment_dict.get(cid)
            if comment:
                result[str(cid)] = {
                    "exists": True,
                    "liked": cid in liked_ids,
                    "reply_count": int(comment.get('reply_count', 0))
                }
            else:
                result[str(cid)] = {
                    "exists": False,
                    "liked": False,
                    "reply_count": 0
                }
        
        return Response.success(data=result)
    except Exception as e:
        logger.error(f"获取评论状态失败: {e}")
        return Response.error(details={"message": f"获取评论状态失败: {str(e)}"})


@router.get("/replies", summary="获取单条评论的回复列表")
async def get_replies(
    comment_id: str,
    page: int = 1,
    page_size: int = 5,
    current_user: Optional[Dict[str, Any]] = Depends(get_current_active_user_optional)
):
    """获取单条评论的回复列表，分页展示"""
    try:
        comment_id_int = int(comment_id)
    except (ValueError, TypeError):
        return Response.bad_request(details={"message": "comment_id必须是整数"})
        
    offset = (page - 1) * page_size
    
    # 查询子评论
    replies_sql = """
    SELECT * FROM wxapp_comment 
    WHERE parent_id = %s AND status = 1 AND is_deleted = 0
    ORDER BY create_time ASC
    LIMIT %s OFFSET %s
    """
    replies = await execute_custom_query(replies_sql, [comment_id_int, page_size, offset])
    
    # 丰富评论信息
    enriched_replies = await _enrich_comments(replies, current_user)
    
    # 查询总数以进行分页
    total_count_sql = "SELECT COUNT(*) as total FROM wxapp_comment WHERE parent_id = %s AND status = 1 AND is_deleted = 0"
    total_result = await execute_custom_query(total_count_sql, [comment_id_int], fetch='one')
    total = total_result.get('total', 0)
    
    pagination = PaginationInfo(total=total, page=page, page_size=page_size)
    
    return Response.paged(data=enriched_replies, pagination=pagination)


@router.post("/delete", summary="删除评论")
async def delete_comment(
    body: Dict[str, Any] = Body(...),
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """删除评论"""
    comment_id = body.get("id")
    if not comment_id:
        return Response.bad_request(details={"message": "缺少id参数"})

    try:
        # 验证评论是否存在且属于当前用户
        comment_result = await execute_custom_query(
            "SELECT user_id, parent_id, resource_id, resource_type FROM wxapp_comment WHERE id = %s", (comment_id,)
        )
        if not comment_result:
            return Response.not_found(resource="评论")
        comment = comment_result[0]
        if not comment:
            return Response.not_found(resource="评论")
        
        if comment['user_id'] != current_user['id']:
            return Response.forbidden(details={"message": "只能删除自己的评论"})

        async with _get_db_connection() as conn:
            async with conn.cursor() as cursor:
                await conn.begin()
                try:
                    # 执行删除 (逻辑删除)
                    await update_record("wxapp_comment", {"id": comment_id}, {"is_deleted": 1}, cursor=cursor)
                    
                    # 更新相关计数
                    if comment.get("parent_id"):
                        # 是回复，更新父评论的回复数
                        await _update_count("wxapp_comment", comment["parent_id"], "reply_count", -1, cursor=cursor)
                    else:
                        # 是顶级评论，更新资源的评论数
                        resource_table_name = f"wxapp_{comment['resource_type']}"
                        await _update_count(resource_table_name, comment["resource_id"], "comment_count", -1, cursor=cursor)
                    
                    await conn.commit()
                except Exception as e:
                    await conn.rollback()
                    logger.error(f"删除评论事务失败: {e}")
                    raise e

        return Response.success(details={"message": "删除成功"})
    except Exception as e:
        logger.error(f"删除评论失败: {e}")
        return Response.error(details={"message": "删除评论失败"})


class UpdateCommentRequest(BaseModel):
    id: int
    content: str


@router.post("/update")
async def update_comment(
    request_data: UpdateCommentRequest,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    更新评论
    """
    comment_id = request_data.id
    content = request_data.content

    # 检查评论是否存在以及用户是否有权编辑
    comment_result = await execute_custom_query(
        "SELECT user_id FROM wxapp_comment WHERE id = %s", (comment_id,)
    )
    if not comment_result:
        return Response.not_found(resource="评论")
    comment = comment_result[0]
    if not comment:
        return Response.not_found(resource="评论")

    user_id = current_user['id']
    if comment.get("user_id") != user_id:
        return Response.forbidden(details={"message": "无权编辑此评论"})

    # 使用事务更新评论内容
    async with _get_db_connection() as conn:
        async with conn.cursor() as cursor:
            await conn.begin()
            try:
                # 更新评论内容和更新时间
                from datetime import datetime
                update_data = {
                    "content": content,
                    "update_time": datetime.now()
                }
                await update_record("wxapp_comment", {"id": comment_id}, update_data, cursor=cursor)
                await conn.commit()
            except Exception as e:
                await conn.rollback()
                logger.error(f"更新评论事务失败: {e}")
                raise e
    
    return Response.success(details={"message": "更新成功"})


@router.get("/list", summary="获取评论列表")
async def get_comments(
    resource_id: int = Query(..., description="资源ID (例如帖子ID)"),
    resource_type: str = Query("post", description="资源类型"),
    page: int = 1,
    page_size: int = 10,
    current_user: Optional[Dict[str, Any]] = Depends(get_current_active_user_optional)
):
    """获取指定资源的评论列表，分页展示，并包含每个评论的点赞状态"""
    offset = (page - 1) * page_size
    
    # 先获取顶层评论
    comments_sql = """
    SELECT * FROM wxapp_comment 
    WHERE resource_id = %s AND resource_type = %s AND parent_id IS NULL AND is_deleted = 0
    ORDER BY create_time DESC 
    LIMIT %s OFFSET %s
    """
    comments = await execute_custom_query(comments_sql, [resource_id, resource_type, page_size, offset])
    
    # 丰富评论信息（作者、点赞状态）
    enriched_comments = await _enrich_comments(comments, current_user)

    # 递归获取子评论
    for comment in enriched_comments:
        comment["children"] = await get_child_comments(comment.get("id"), current_user)
    
    # 获取总数用于分页
    total_sql = "SELECT COUNT(*) as total FROM wxapp_comment WHERE resource_id = %s AND resource_type = %s AND parent_id IS NULL AND is_deleted = 0"
    total_result = await execute_custom_query(total_sql, [resource_id, resource_type], fetch='one')
    total = total_result.get('total', 0)
    
    pagination = PaginationInfo(total=total, page=page, page_size=page_size)
    
    return Response.paged(data=enriched_comments, pagination=pagination)


@router.get("/user", summary="获取用户的评论列表")
async def get_user_comments(
    user_id: int = Query(..., description="目标用户的ID"),
    page: int = 1,
    page_size: int = 10,
    current_user: Optional[Dict[str, Any]] = Depends(get_current_active_user_optional)
):
    """获取指定用户发表的所有评论，并附带当前用户的点赞状态"""
    try:
        # 1. 计算分页
        offset = (page - 1) * page_size

        # 2. 构建查询
        query_sql = """
            SELECT 
                c.id, c.resource_id, c.resource_type, c.parent_id, c.user_id, 
                c.content, c.image, c.like_count, c.reply_count, c.status, 
                c.is_deleted, c.create_time, c.update_time,
                p.title AS resource_title, p.content AS resource_abstract
            FROM 
                wxapp_comment c
            LEFT JOIN 
                wxapp_post p ON c.resource_id = p.id AND c.resource_type = 'post'
            WHERE 
                c.user_id = %s AND c.status = 1 AND c.is_deleted = 0
            ORDER BY 
                c.create_time DESC
            LIMIT %s OFFSET %s
        """
        count_sql = "SELECT COUNT(*) as total FROM wxapp_comment WHERE user_id = %s AND status = 1 AND is_deleted = 0"

        # 3. 并行执行数据查询和总数查询
        comments_task = execute_custom_query(query_sql, [user_id, page_size, offset])
        total_task = execute_custom_query(count_sql, [user_id], fetch='one')
        
        comments_data, total_result = await asyncio.gather(comments_task, total_task)

        # 4. 丰富评论信息（作者、点赞状态）
        enriched_comments = await _enrich_comments(comments_data, current_user)

        # 5. 构建分页信息
        total_records = total_result.get('total', 0)
        pagination = PaginationInfo(total=total_records, page=page, page_size=page_size)
        
        return Response.paged(data=enriched_comments, pagination=pagination)

    except Exception as e:
        logger.exception(f"获取用户评论列表失败 (target_user_id={user_id}): {e}")
        return Response.error(message="服务器内部错误")


@router.post("/create", summary="发布评论")
async def create_comment(
    body: Dict[str, Any] = Body(...),
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    发布评论或回复。
    - 如果`parent_id`为空，则为对资源的直接评论。
    - 如果`parent_id`不为空，则为对另一条评论的回复。
    """
    # 验证必要参数
    required_params = ['resource_id', 'resource_type', 'content']
    error_resp = validate_params(body, required_params)
    if error_resp:
        return error_resp

    # 提取参数
    resource_id = body.get("resource_id")
    resource_type = body.get("resource_type")
    content = body.get("content")
    parent_id = body.get("parent_id")
    image = body.get("image", [])
    
    user_id = current_user['id']

    async with _get_db_connection() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            await conn.begin()
            try:
                # 在事务中验证资源是否存在
                table_map = {"post": "wxapp_post", "knowledge": "wxapp_knowledge"}
                table_name = table_map.get(resource_type)
                if not table_name:
                    await conn.rollback()
                    return Response.bad_request(details={"message": f"不支持的资源类型: {resource_type}"})
                
                await cursor.execute(f"SELECT * FROM {table_name} WHERE id = %s FOR UPDATE", (resource_id,))
                resource = await cursor.fetchone()
                if not resource:
                    await conn.rollback()
                    return Response.not_found(resource=f"目标资源 {resource_type}")

                # 准备插入数据
                comment_data = {
                    "user_id": user_id,
                    "resource_id": resource_id,
                    "resource_type": resource_type,
                    "content": content,
                    "image": json.dumps(image, ensure_ascii=False) if image else None,
                    "parent_id": parent_id
                }

                # 直接使用cursor插入评论数据
                cols = ", ".join(f"`{k}`" for k in comment_data.keys())
                placeholders = ", ".join(["%s"] * len(comment_data))
                insert_query = f"INSERT INTO wxapp_comment ({cols}) VALUES ({placeholders})"
                
                await cursor.execute(insert_query, list(comment_data.values()))
                comment_id = cursor.lastrowid
                if not comment_id:
                    raise Exception("插入评论记录失败，未能获取 lastrowid")

                # 更新相关计数
                await _update_count(table_name, resource_id, "comment_count", 1, cursor=cursor)
                if parent_id:
                    await _update_count("wxapp_comment", parent_id, "reply_count", 1, cursor=cursor)
                await _update_count("wxapp_user", user_id, "comment_count", 1, cursor=cursor)
                
                await conn.commit()
            except Exception as e:
                await conn.rollback()
                logger.error(f"创建评论事务失败: {e}", exc_info=True)
                return Response.db_error(details={"message": "发布评论失败"})

    # 使用事务中获取的 resource 对象发送通知
    asyncio.create_task(_send_comment_notification(resource_type, resource, parent_id, current_user))

    return Response.success(data={"id": comment_id}, details={"message": "发布成功"})