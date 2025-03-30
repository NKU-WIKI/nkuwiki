"""
微信小程序评论相关API接口
处理评论创建、查询、更新、删除和点赞等功能
"""
from api.models.common import Request, Response, validate_params, PaginationInfo
from fastapi import APIRouter, Query
from etl.load.db_core import (
    query_records, get_record_by_id, insert_record, update_record, count_records, delete_record,
    async_query_records, async_get_by_id, async_insert, async_update, async_count_records, execute_custom_query,
    async_query, execute_query
)
from core.utils.logger import register_logger
import time

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
        comment = await async_get_by_id(
            table_name="wxapp_comment",
            record_id=comment_id
        )

        if not comment:
            return Response.not_found(resource="评论")

        # 使用直接SQL查询获取评论回复
        replies_sql = """
        SELECT * FROM wxapp_comment 
        WHERE parent_id = %s AND status = 1
        ORDER BY create_time
        """
        replies = execute_query(replies_sql, [comment_id])

        # 使用直接SQL查询检查是否已点赞
        sql = "SELECT * FROM wxapp_action WHERE openid = %s AND action_type = %s AND target_id = %s AND target_type = %s LIMIT 1"
        like_record = execute_query(sql, [openid, "like", comment_id, "comment"])
        
        # 判断是否已点赞
        liked = bool(like_record)

        result = {
            **comment,
            "replies": replies,
            "liked": liked,
            "like_count": comment.get("like_count", 0)
        }

        return Response.success(data=result)
    except Exception as e:
        return Response.error(details={"message": f"获取评论详情失败: {str(e)}"})


@router.get("/post/comment")
async def get_post_comments(
    post_id: str = Query(..., description="帖子ID"),
    page: int = Query(1, description="页码"),
    size: int = Query(10, description="每页数量")
):
    if(not post_id):
        return Response.bad_request(details={"message": "缺少post_id参数"})
    """获取帖子评论列表（分页）"""
    try:
        offset = (page - 1) * size

        post = await async_get_by_id(
            table_name="wxapp_post",
            record_id=post_id
        )

        if not post:
            return Response.not_found(resource="帖子")

        # 使用直接SQL查询获取评论总数
        count_sql = "SELECT COUNT(*) as total FROM wxapp_comment WHERE post_id = %s AND parent_id IS NULL AND status = 1"
        count_result = execute_query(count_sql, [post_id])
        comment_count = count_result[0]['total'] if count_result else 0

        # 使用直接SQL查询获取评论列表
        comments_sql = """
        SELECT * FROM wxapp_comment 
        WHERE post_id = %s AND parent_id IS NULL AND status = 1
        ORDER BY create_time DESC
        LIMIT %s OFFSET %s
        """
        comments = execute_query(comments_sql, [post_id, size, offset])

        result = {
            "comments": comments,
            "pagination": {
                "page": page,
                "size": size,
                "total": comment_count,
                "pages": (comment_count + size - 1) // size if size > 0 else 0
            }
        }

        return Response.success(data=result)
    except Exception as e:
        return Response.error(details={"message": f"获取帖子评论列表失败: {str(e)}"})


@router.get("/comment/status")
async def get_comment_status(
    comment_id: str = Query(..., description="评论ID"),
    openid: str = Query(..., description="用户OpenID")
):
    """获取评论状态"""
    if(not comment_id):
        return Response.bad_request(details={"message": "缺少comment_id参数"})
    if(not openid):
        return Response.bad_request(details={"message": "缺少openid参数"})
    try:
        comment = await async_get_by_id(
            table_name="wxapp_comment",
            record_id=comment_id
        )

        if not comment:
            return Response.not_found(resource="评论")

        # 使用直接SQL查询检查是否已点赞
        sql = "SELECT * FROM wxapp_action WHERE openid = %s AND action_type = %s AND target_id = %s AND target_type = %s LIMIT 1"
        like_record = execute_query(sql, [openid, "like", comment_id, "comment"])
        
        # 判断是否已点赞
        liked = bool(like_record)

        return Response.success(data={
            "comment_id": comment_id,
            "is_liked": liked,
            "like_count": comment.get("like_count", 0)
        })
    except Exception as e:
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
        replies = execute_query(replies_sql, [comment_id, limit])

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
        images = req_data.get("images")


        comment = await async_get_by_id(
            table_name="wxapp_comment",
            record_id=comment_id
        )

        if not comment:
            return Response.not_found(resource="评论")

        if comment["openid"] != openid:
            return Response.forbidden(details={"message": "只有评论作者才能更新评论"})

        allowed_fields = ["content", "images"]
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

@router.post("/comment")
async def create_comment(
    request: Request,
):
    """创建评论"""
    try:
        req_data = await request.json()
        required_params = ["post_id", "content", "openid"]
        error_response = validate_params(req_data, required_params)
        if(error_response):
            return error_response
        
        post_id = req_data.get("post_id")
        content = req_data.get("content")
        openid = req_data.get("openid")
        parent_id = req_data.get("parent_id")
        images = req_data.get("images")
        
        # 验证帖子是否存在
        post = await async_get_by_id(
            table_name="wxapp_post",
            record_id=post_id
        )
        
        if not post:
            return Response.not_found(resource="帖子")
        
        # 验证用户是否存在
        user_data = await async_query_records(
            table_name="wxapp_user",
            conditions={"openid": openid},
            limit=1
        )
        
        if not user_data or not user_data['data']:
            return Response.not_found(resource="用户")
        
        # 构建评论数据
        comment_data = {
            "post_id": post_id,
            "openid": openid,
            "content": content,
            "status": 1,
            "like_count": 0,
            "create_time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "update_time": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # 如果有父评论ID，添加到数据中
        if parent_id:
            parent_comment = await async_get_by_id(
                table_name="wxapp_comment",
                record_id=parent_id
            )
            
            if not parent_comment:
                return Response.not_found(resource="父评论")
                
            comment_data["parent_id"] = parent_id
        
        # 如果有图片，添加到数据中
        if images:
            comment_data["images"] = images
        
        # 插入评论
        try:
            comment_id = await async_insert(
                table_name="wxapp_comment",
                data=comment_data
            )
            
            if comment_id <= 0:
                return Response.db_error(details={"message": "创建评论失败"})
                
            # 更新帖子评论数
            await async_update(
                table_name="wxapp_post",
                record_id=post_id,
                data={
                    "comment_count": post.get("comment_count", 0) + 1,
                    "update_time": time.strftime("%Y-%m-%d %H:%M:%S")
                }
            )
            
            return Response.success(details={
                "comment_id": comment_id,
                "message": "评论创建成功"
            })
            
        except Exception as e:
            logger.error(f"创建评论失败: {str(e)}")
            return Response.db_error(details={"message": f"创建评论失败: {str(e)}"})
            
    except Exception as e:
        logger.error(f"评论接口异常: {str(e)}")
        return Response.error(details={"message": f"创建评论失败: {str(e)}"})