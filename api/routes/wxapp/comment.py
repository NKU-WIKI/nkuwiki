# This file will manage all comment-related API endpoints.

"""
微信小程序评论相关API接口
处理评论创建、查询、更新、删除和点赞等功能
"""
from fastapi import APIRouter, Query, Body, Depends
from api.models.common import Response, Request, validate_params, PaginationInfo
from etl.load import (
    query_records, 
    insert_record, 
    update_record, 
    execute_custom_query,
    get_by_id
)
from etl.load.db_pool_manager import get_db_connection as _get_db_connection
import json
import logging
import asyncio
from typing import Dict, Any, Optional, List

from ._utils import _update_count, create_notification

# 配置日志
logger = logging.getLogger("wxapp.comment")
router = APIRouter()


async def _enrich_comments(comments: List[Dict[str, Any]], current_openid: Optional[str] = None) -> List[Dict[str, Any]]:
    """高效地为评论列表批量补充作者信息和当前用户的点赞状态"""
    if not comments:
        return []

    author_openids = {c.get("openid") for c in comments if c.get("openid")}
    comment_ids = [c.get("id") for c in comments if c.get("id")]

    # 批量获取用户信息
    users_info_map = {}
    if author_openids:
        placeholders = ', '.join(['%s'] * len(author_openids))
        user_sql = f"SELECT openid, nickname, avatar, bio FROM wxapp_user WHERE openid IN ({placeholders})"
        user_results = await execute_custom_query(user_sql, list(author_openids))
        users_info_map = {user['openid']: user for user in user_results}

    # 批量获取点赞状态
    liked_comment_ids = set()
    if current_openid and comment_ids:
        placeholders = ', '.join(['%s'] * len(comment_ids))
        like_sql = f"SELECT target_id FROM wxapp_action WHERE action_type = 'like' AND target_type = 'comment' AND openid = %s AND target_id IN ({placeholders})"
        like_params = [current_openid] + comment_ids
        like_results = await execute_custom_query(like_sql, like_params)
        liked_comment_ids = {res['target_id'] for res in like_results}
    
    # 注入信息到评论中
    for comment in comments:
        author_openid = comment.get("openid")
        user_info = users_info_map.get(author_openid, {})
        comment.update(user_info)
        comment["is_liked"] = comment.get("id") in liked_comment_ids

    return comments

# 递归获取子评论的函数
async def get_child_comments(comment_id: int, openid: Optional[str] = None) -> List[Dict[str, Any]]:
    """递归获取评论的所有子评论，使用批量查询优化性能"""
    replies_sql = """
    SELECT 
        id, resource_id, resource_type, parent_id, openid, 
        content, image, like_count, reply_count, status, is_deleted, 
        create_time, update_time
    FROM wxapp_comment 
    WHERE parent_id = %s AND status = 1 AND is_deleted = 0
    ORDER BY create_time ASC
    """
    try:
        replies = await execute_custom_query(replies_sql, [comment_id])
    except Exception as e:
        logger.error(f"查询子评论失败 (parent_id={comment_id}): {e}")
        return []

    if not replies:
        return []
    
    # 高效地为当前层级的回复补充信息
    enriched_replies = await _enrich_comments(replies, openid)
    
    # 递归处理更深层级的子评论
    for i, reply in enumerate(enriched_replies):
        # "parent_comment_count" 实际上是该评论在同级回复中的位置索引
        reply["parent_comment_count"] = i
        
        children = await get_child_comments(reply.get("id"), openid)
        if children:
            reply["children"] = children
    
    return enriched_replies

async def _send_comment_notification(
    resource_type: str, 
    resource: Dict, 
    parent_id: Optional[int], 
    user_openid: str
):
    """发送评论相关的通知。"""
    try:
        sender_info = await get_by_id("wxapp_user", user_openid, id_column='openid', fields=['nickname', 'avatar'])
        sender_payload = {
            "openid": user_openid, 
            "avatar": sender_info.get("avatar", ""), 
            "nickname": sender_info.get("nickname", "")
        }

        # 回复通知
        if parent_id:
            parent_comment = await get_by_id("wxapp_comment", parent_id, fields=['openid'])
            if parent_comment and parent_comment.get("openid") != user_openid:
                await create_notification(
                    openid=parent_comment["openid"],
                    title="收到新回复",
                    content="用户回复了你的评论",
                    target_id=parent_id,
                    target_type="comment",
                    sender_payload=sender_payload
                )
        # 资源评论通知
        elif resource.get("openid") != user_openid:
            safe_title = resource.get('title', '无标题')
            resource_name = '帖子' if resource_type == 'post' else '知识'
            await create_notification(
                openid=resource["openid"],
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
    openid: Optional[str] = Query(None)
):
    """获取评论详情"""
    if not openid:
        return Response.bad_request(details={"message": "缺少openid参数"})
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
        like_query_coro = execute_custom_query(
            """
            SELECT 1 FROM wxapp_action 
            WHERE openid = %s AND action_type = 'like' AND target_id = %s AND target_type = 'comment' 
            LIMIT 1
            """, 
            [openid, comment_id_int],
            fetch='one'
        )
        
        # 获取用户信息
        user_query_coro = execute_custom_query(
            """
            SELECT nickname, avatar, bio FROM wxapp_user 
            WHERE openid = %s 
            LIMIT 1
            """, 
            [comment.get("openid")],
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
        children = await get_child_comments(comment_id_int, openid)

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
    openid: str = Query(..., description="用户OpenID"),
    comment_ids: str = Query(..., description="评论ID列表，用逗号分隔"),
):
    """获取评论状态"""
    if not openid:
        return Response.bad_request(details={"message": "缺少openid参数"})
    if not comment_ids:
        return Response.bad_request(details={"message": "缺少comment_ids参数"})
    
    try:
        # 分割评论ID列表并转换为整数
        raw_ids = comment_ids.split(',')
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
            return Response.bad_request(details={"message": "没有有效的评论ID"})
        
        # 构建IN查询的占位符
        placeholders = ','.join(['%s'] * len(ids))
        
        # 获取评论存在状态和回复数量
        comment_sql = f"""
        SELECT id, 
               (SELECT COUNT(*) FROM wxapp_comment WHERE parent_id = c.id AND status = 1) AS reply_count
        FROM wxapp_comment c
        WHERE id IN ({placeholders}) AND status = 1
        """
        
        # 获取用户点赞状态
        like_sql = f"""
        SELECT target_id
        FROM wxapp_action 
        WHERE openid = %s AND action_type = 'like' AND target_type = 'comment' AND target_id IN ({placeholders})
        """
        
        # 执行查询
        comments = await execute_custom_query(comment_sql, ids)
        like_params = [openid] + ids
        likes = await execute_custom_query(like_sql, like_params)
        
        # 转换点赞结果为集合，方便快速查找
        liked_ids = {record['target_id'] for record in likes} if likes else set()
        
        # 为每个请求的评论ID构建状态信息
        result = {}
        comment_dict = {comment['id']: comment for comment in comments} if comments else {}
        
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
    openid: Optional[str] = Query(None)
):
    """获取单条评论的回复列表"""
    try:
        # 获取所有子评论
        children = await get_child_comments(int(comment_id), openid)
        
        # 内存分页
        total = len(children)
        start = (page - 1) * page_size
        end = start + page_size
        paginated_children = children[start:end]
        
        # 构建分页信息
        pagination = PaginationInfo(
            total=total,
            page=page,
            page_size=page_size
        )
        
        return Response.paged(data=paginated_children, pagination=pagination)
    except Exception as e:
        logger.error(f"获取回复列表失败 (comment_id={comment_id}): {e}")
        return Response.error(details=f"获取回复失败: {e}")


@router.post("/delete", summary="删除评论")
async def delete_comment(
    body: Dict[str, Any] = Body(...)
):
    """删除用户自己的评论。"""
    try:
        comment_id = body.get('comment_id')
        openid = body.get('openid')
        if not comment_id or not openid:
            return Response.bad_request(details={"message": "缺少comment_id或openid参数"})

        comment = await get_by_id("wxapp_comment", comment_id)
        if not comment:
            return Response.error(message="评论不存在")

        if comment.get('openid') != openid:
            return Response.error(message="无权删除他人评论", code=403)

        # 逻辑删除
        await update_record("wxapp_comment", {"id": comment_id}, {"is_deleted": 1})
        
        # 如果是父评论，也需要处理子评论（暂不处理，前端隐藏即可）

        # 更新相关资源评论计数
        resource_type = comment.get('resource_type')
        resource_id = comment.get('resource_id')
        if resource_type and resource_id:
            resource = await get_by_id(f"wxapp_{resource_type}", resource_id)
            if resource and resource.get("comment_count", 0) > 0:
                 await update_record(
                    f"wxapp_{resource_type}",
                    {"id": resource_id},
                    {"comment_count": resource.get("comment_count") - 1}
                )

        return Response.success(message="删除成功")
    except Exception as e:
        logger.error(f"删除评论失败: {e}", exc_info=True)
        return Response.error(message="删除失败")

@router.post("/update")
async def update_comment(
    request: Request,
):
    """更新评论"""
    try:
        req_data = await request.json()
        required_params = ["comment_id", "openid"]
        error_response = validate_params(req_data, required_params)
        if(error_response):
            return error_response

        openid = req_data.get("openid")
        comment_id = req_data.get("comment_id")
        content = req_data.get("content")
        image = req_data.get("image")


        comment = await get_by_id(
            table_name="wxapp_comment",
            record_id=comment_id
        )

        if not comment:
            return Response.not_found(resource="评论")

        if comment["openid"] != openid:
            return Response.forbidden(details={"message": "只有评论作者才能更新评论"})

        allowed_fields = ["content", "image"]
        filtered_data = {k: v for k, v in req_data.items() if k in allowed_fields}

        if not filtered_data:
            return Response.bad_request(details={"message": "没有提供可更新的字段"})

        if 'image' in filtered_data and isinstance(filtered_data['image'], list):
            filtered_data['image'] = json.dumps(filtered_data['image'], ensure_ascii=False)

        try:
            await update_record(
                table_name="wxapp_comment",
                record_id=comment_id,
                data=filtered_data
            )

        except Exception as e:
            return Response.db_error(details={"message": f"评论更新失败: {str(e)}"})

        updated_comment = await get_by_id(
            table_name="wxapp_comment",
            record_id=comment_id
        )

        return Response.success(data=updated_comment)
    except Exception as e:
        return Response.error(details={"message": f"更新评论失败: {str(e)}"})

@router.get("/list", summary="获取评论列表")
async def get_comments(
    post_id: int = Query(..., description="帖子ID"),
    page: int = 1,
    page_size: int = 10,
    current_openid: Optional[str] = Query(None)
):
    """获取评论列表"""
    offset = (page - 1) * page_size
    
    # 首先计算总评论数
    count_sql = "SELECT COUNT(*) as total FROM wxapp_comment WHERE resource_id = %s AND resource_type = 'post' AND parent_id = 0 AND is_deleted = 0"
    total_result = await execute_custom_query(count_sql, [post_id], fetch='one')
    total_comments = total_result['total'] if total_result else 0
    
    if total_comments == 0:
        return Response.paged(data=[], pagination=PaginationInfo(total=0, page=page, page_size=page_size))
        
    # 获取顶层评论
    comments_sql = """
    SELECT * FROM wxapp_comment 
    WHERE resource_id = %s AND resource_type = 'post' AND parent_id = 0 AND is_deleted = 0
    ORDER BY create_time DESC 
    LIMIT %s OFFSET %s
    """
    comments = await execute_custom_query(comments_sql, [post_id, page_size, offset])
    
    # 丰富评论信息
    enriched_comments = await _enrich_comments(comments, current_openid)
    
    # 获取每个顶层评论的子评论
    for comment in enriched_comments:
        children = await get_child_comments(comment['id'], current_openid)
        if children:
            comment['children'] = children
            
    # 构建分页信息
    pagination = PaginationInfo(total=total_comments, page=page, page_size=page_size)
    
    return Response.paged(data=enriched_comments, pagination=pagination)

@router.get("/user", summary="获取用户的评论列表")
async def get_user_comments(
    target_openid: str,
    page: int = 1,
    page_size: int = 10,
    current_openid: Optional[str] = Query(None)
):
    """获取某个用户发布的所有评论，按时间倒序排列"""
    offset = (page - 1) * page_size
    
    # 计算总数
    count_sql = "SELECT COUNT(*) as total FROM wxapp_comment WHERE openid = %s AND is_deleted = 0"
    total_result = await execute_custom_query(count_sql, [target_openid], fetch='one')
    total_comments = total_result['total'] if total_result else 0
    
    if total_comments == 0:
        return Response.paged(data=[], pagination=PaginationInfo(total=0, page=page, page_size=page_size))
        
    # 获取分页后的评论
    comments_sql = """
    SELECT * FROM wxapp_comment 
    WHERE openid = %s AND is_deleted = 0 
    ORDER BY create_time DESC 
    LIMIT %s OFFSET %s
    """
    comments = await execute_custom_query(comments_sql, [target_openid, page_size, offset])

    # 丰富评论信息
    enriched_comments = await _enrich_comments(comments, current_openid)

    # 构建分页信息
    pagination = PaginationInfo(total=total_comments, page=page, page_size=page_size)

    return Response.paged(data=enriched_comments, pagination=pagination)


@router.post("/create", summary="发布评论")
async def create_comment(
    body: Dict[str, Any] = Body(...)
):
    """发布新评论或回复"""
    # 参数验证
    required_params = ['openid', 'resource_id', 'resource_type', 'content']
    if error_response := validate_params(body, required_params):
        return error_response

    # 准备要插入的数据
    comment_data = {
        "openid": body["openid"],
        "resource_id": body["resource_id"],
        "resource_type": body["resource_type"],
        "content": body["content"],
        "parent_id": body.get("parent_id", 0)
    }

    # 处理可选的 image 字段
    if 'image' in body and isinstance(body['image'], list):
        comment_data['image'] = json.dumps(body['image'], ensure_ascii=False)

    try:
        # 使用事务确保数据一致性
        async with _get_db_connection() as conn:
            async with conn.cursor() as cursor:
                # 1. 插入评论
                cols = ", ".join(f"`{k}`" for k in comment_data.keys())
                placeholders = ", ".join(["%s"] * len(comment_data))
                insert_sql = f"INSERT INTO wxapp_comment ({cols}) VALUES ({placeholders})"
                await cursor.execute(insert_sql, list(comment_data.values()))
                comment_id = cursor.lastrowid
                
                # 2. 更新帖子或父评论的回复数
                if comment_data['parent_id'] != 0:
                    # 更新父评论的回复数
                    update_sql = "UPDATE wxapp_comment SET reply_count = reply_count + 1, update_time = NOW() WHERE id = %s"
                    await cursor.execute(update_sql, [comment_data['parent_id']])
                else:
                    # 更新帖子的评论数
                    update_sql = "UPDATE wxapp_post SET comment_count = comment_count + 1, update_time = NOW() WHERE id = %s"
                    await cursor.execute(update_sql, [comment_data['resource_id']])
                
                await conn.commit()

        # 3. 发送通知 (在事务外)
        resource = await get_by_id(f"wxapp_{comment_data['resource_type']}", comment_data['resource_id'])
        if resource:
            await _send_comment_notification(
                comment_data['resource_type'], 
                resource, 
                comment_data['parent_id'], 
                comment_data['openid']
            )

        return Response.success(data={"comment_id": comment_id}, message="评论发布成功")

    except Exception as e:
        logger.error(f"发布评论失败: {e}", exc_info=True)
        return Response.error(details=f"数据库操作失败: {e}") 