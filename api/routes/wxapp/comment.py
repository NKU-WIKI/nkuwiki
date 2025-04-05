"""
微信小程序评论相关API接口
处理评论创建、查询、更新、删除和点赞等功能
"""
from api.models.common import Request, Response, validate_params, PaginationInfo
from fastapi import APIRouter, Query, BackgroundTasks
import asyncio
from etl.load.db_core import (
    async_query_records, async_get_by_id, async_insert, async_update, async_count_records,
    async_execute_custom_query
)
from core.utils.logger import register_logger
import time, json

# 初始化日志
logger = register_logger('api.routes.wxapp.comment')

router = APIRouter()

@router.get("/comment/detail")
async def get_comment_detail(
    openid: str = Query(..., description="用户OpenID"),
    comment_id: str = Query(..., description="评论ID"),
):
    """获取评论详情"""
    if(not openid):
        return Response.bad_request(details={"message": "缺少openid参数"})
    if(not comment_id):
        return Response.bad_request(details={"message": "缺少comment_id参数"})
    try:
        # 使用单一SQL查询获取评论详情
        comment_sql = """
        SELECT * FROM wxapp_comment 
        WHERE id = %s
        """
        comment_result = await async_execute_custom_query(comment_sql, [comment_id])

        if not comment_result:
            return Response.not_found(resource="评论")
            
        comment = comment_result[0]

        # 使用单一查询并行获取回复和点赞状态
        replies_query = async_execute_custom_query(
            """
            SELECT * FROM wxapp_comment 
            WHERE parent_id = %s AND status = 1
            ORDER BY create_time
            """, 
            [comment_id]
        )
        
        like_query = async_execute_custom_query(
            """
            SELECT 1 FROM wxapp_action 
            WHERE openid = %s AND action_type = 'like' AND target_id = %s AND target_type = 'comment' 
            LIMIT 1
            """, 
            [openid, comment_id]
        )
        
        # 并行执行查询
        replies, like_record = await asyncio.gather(replies_query, like_query)
        
        # 判断是否已点赞
        liked = bool(like_record)

        result = {
            **comment,
            "replies": replies or [],
            "liked": liked,
            "like_count": comment.get("like_count", 0)
        }

        return Response.success(data=result)
    except Exception as e:
        return Response.error(details={"message": f"获取评论详情失败: {str(e)}"})


@router.get("/comment/status")
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
        # 分割评论ID列表
        ids = comment_ids.split(',')
        if not ids:
            return Response.bad_request(details={"message": "评论ID列表格式错误"})
        
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
        comments = await async_execute_custom_query(comment_sql, ids)
        like_params = [openid] + ids
        likes = await async_execute_custom_query(like_sql, like_params)
        
        # 转换点赞结果为集合，方便快速查找
        liked_ids = {record['target_id'] for record in likes} if likes else set()
        
        # 为每个请求的评论ID构建状态信息
        result = {}
        comment_dict = {comment['id']: comment for comment in comments} if comments else {}
        
        for cid in ids:
            comment = comment_dict.get(cid)
            if comment:
                result[cid] = {
                    "exists": True,
                    "liked": cid in liked_ids,
                    "reply_count": int(comment.get('reply_count', 0))
                }
            else:
                result[cid] = {
                    "exists": False,
                    "liked": False,
                    "reply_count": 0
                }
        
        return Response.success(data=result)
    except Exception as e:
        logger.error(f"获取评论状态失败: {e}")
        return Response.error(details={"message": f"获取评论状态失败: {str(e)}"})


@router.get("/comment/replies")
async def get_comment_replies(
    comment_id: str = Query(..., description="评论ID"),
    limit: int = Query(10, description="返回回复数量")
):
    """获取评论回复列表"""
    if(not comment_id):
        return Response.bad_request(details={"message": "缺少comment_id参数"})
    try:
        # 使用直接SQL查询获取评论回复
        replies_sql = """
        SELECT * FROM wxapp_comment 
        WHERE parent_id = %s AND status = 1
        ORDER BY create_time
        LIMIT %s
        """
        replies = await async_execute_custom_query(replies_sql, [comment_id, limit])

        return Response.success(data={
            "comment_id": comment_id,
            "replies": replies,
            "total": len(replies)
        })
    except Exception as e:
        return Response.error(details={"message": f"获取评论回复列表失败: {str(e)}"})


@router.post("/comment/delete")
async def delete_comment(
    request: Request,
):
    """删除评论"""
    try:
        req_data = await request.json()
        required_params = ["comment_id", "openid"]
        error_response = validate_params(req_data, required_params)
        if(error_response):
            return error_response
        openid = req_data.get("openid")
        comment_id = req_data.get("comment_id")

        comment = await async_get_by_id(
            table_name="wxapp_comment",
            record_id=comment_id
        )

        if not comment:
            return Response.not_found(resource="评论")

        if comment["openid"] != openid:
            return Response.forbidden(details={"message": "只有评论作者才能删除评论"})

        post = await async_get_by_id(
            table_name="wxapp_post",
            record_id=comment["post_id"]
        )

        try:
            await async_update(
                table_name="wxapp_comment",
                record_id=comment_id,
                data={"status": 0}
            )
        except Exception as e:
            return Response.db_error(details={"message": f"评论删除失败: {str(e)}"})

        if post and post.get("comment_count", 0) > 0:
            try:
                await async_update(
                    table_name="wxapp_post",
                    record_id=comment["post_id"],
                    data={"comment_count": post.get("comment_count", 1) - 1}
                )
            except Exception as e:
                return Response.db_error(details={"message": f"帖子评论数更新失败: {str(e)}"})

        return Response.success(data={
            "affected_items": 1
        },details={"message": "评论删除成功"})
    except Exception as e:
        return Response.error(details={"message": f"删除评论失败: {str(e)}"})

@router.post("/comment/update")
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


        comment = await async_get_by_id(
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

        try:
            await async_update(
                table_name="wxapp_comment",
                record_id=comment_id,
                data=filtered_data
            )

        except Exception as e:
            return Response.db_error(details={"message": f"评论更新失败: {str(e)}"})

        updated_comment = await async_get_by_id(
            table_name="wxapp_comment",
            record_id=comment_id
        )

        return Response.success(data=updated_comment)
    except Exception as e:
        return Response.error(details={"message": f"更新评论失败: {str(e)}"})

@router.get("/comment/list")
async def get_comment_list(
    post_id: str = Query(..., description="帖子ID"),
    limit: int = Query(20, description="每页数量"),
    offset: int = Query(0, description="偏移量"),
    page: int = Query(None, description="页码"),
    openid: str = Query(None, description="用户OpenID"),
    parent_id: str = Query(None, description="父评论ID")
):
    """获取帖子评论列表"""
    if not post_id:
        return Response.bad_request(details={"message": "缺少post_id参数"})
    
    # 如果提供了page参数，计算偏移量
    if page is not None:
        offset = (page - 1) * limit if page > 0 else 0
    
    try:
        # 确保post_id是整数
        try:
            post_id_int = int(post_id)
        except ValueError:
            return Response.bad_request(details={"message": "post_id必须是整数"})
            
        # 获取帖子信息
        post = await async_get_by_id(
            table_name="wxapp_post",
            record_id=post_id_int
        )
        
        if not post:
            return Response.not_found(resource="帖子")
        
        # 使用直接SQL查询获取评论总数
        count_sql = "SELECT COUNT(*) as total FROM wxapp_comment WHERE post_id = %s AND parent_id IS NULL AND status = 1"
        count_result = await async_execute_custom_query(count_sql, [post_id_int])
        comment_count = count_result[0]['total'] if count_result else 0

        # 使用直接SQL查询获取评论列表
        comments_sql = """
        SELECT 
            id, post_id, parent_id, openid, 
            content, image, like_count, reply_count, status, is_deleted, 
            create_time, update_time
        FROM wxapp_comment
        WHERE post_id = %s AND parent_id IS NULL AND status = 1
        ORDER BY create_time DESC
        LIMIT %s OFFSET %s
        """
        logger.debug(f"SQL查询: {comments_sql}")
        logger.debug(f"参数: [post_id={post_id_int}, limit={limit}, offset={offset}]")
        
        comments = await async_execute_custom_query(comments_sql, [post_id_int, limit, offset])
        logger.debug(f"SQL结果: {comments}")
        logger.debug(f"结果类型: {type(comments)}, 长度: {len(comments)}")
        
        # 处理每个评论的点赞状态和回复预览
        for comment in comments:
            # 手动获取用户昵称和头像
            user_sql = "SELECT nickname, avatar FROM wxapp_user WHERE openid = %s LIMIT 1"
            user_info = await async_execute_custom_query(user_sql, [comment.get("openid")])
            if user_info and len(user_info) > 0:
                comment["nickname"] = user_info[0].get("nickname")
                comment["avatar"] = user_info[0].get("avatar")
            
            # 如果提供了openid，检查用户是否点赞
            if openid:
                # 使用直接SQL查询检查是否已点赞
                sql = "SELECT 1 FROM wxapp_action WHERE openid = %s AND action_type = 'like' AND target_id = %s AND target_type = 'comment' LIMIT 1"
                like_record = await async_execute_custom_query(sql, [openid, str(comment.get("id"))])
                comment["liked"] = bool(like_record)
            else:
                comment["liked"] = False
            
            # 获取回复预览（最新的3条回复）
            if not parent_id:  # 只为一级评论获取回复预览
                replies_sql = """
                SELECT 
                    c.id, c.post_id, c.parent_id, c.openid, 
                    u.nickname as user_nickname, 
                    u.avatar as user_avatar, 
                    c.content, c.image, c.like_count, c.status, c.is_deleted, 
                    c.create_time, c.update_time
                FROM wxapp_comment c
                LEFT JOIN wxapp_user u ON c.openid = u.openid
                WHERE c.parent_id = %s AND c.status = 1
                ORDER BY c.create_time DESC
                LIMIT 3
                """
                reply_preview = await async_execute_custom_query(replies_sql, [comment.get("id")])
                
                # 处理回复预览中的用户昵称和头像
                for reply in reply_preview:
                    if 'user_nickname' in reply and reply['user_nickname']:
                        reply['nickname'] = reply.pop('user_nickname')
                    if 'user_avatar' in reply and reply['user_avatar']:
                        reply['avatar'] = reply.pop('user_avatar')
                
                # 获取回复总数
                reply_count_sql = "SELECT COUNT(*) as total FROM wxapp_comment WHERE parent_id = %s AND status = 1"
                reply_count_result = await async_execute_custom_query(reply_count_sql, [comment.get("id")])
                reply_count = reply_count_result[0]['total'] if reply_count_result else 0
                
                comment["reply_preview"] = reply_preview
                comment["reply_count"] = reply_count
        
        # 构建分页信息
        pagination = {
            "total": comment_count,
            "limit": limit,
            "offset": offset,
            "has_more": offset + len(comments) < comment_count
        }
        
        return Response.paged(data=comments, pagination=pagination)
    except Exception as e:
        logger.error(f"获取评论列表失败: {str(e)}")
        return Response.error(details={"message": f"获取评论列表失败: {str(e)}"})