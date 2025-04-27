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

# 递归获取子评论的函数
async def get_child_comments(comment_id, openid=None):
    """递归获取评论的所有子评论，直到叶子节点"""
    # 确保comment_id是整数
    try:
        if isinstance(comment_id, str):
            comment_id = int(comment_id.strip('()').strip())
        elif comment_id is None:
            return []
    except (ValueError, TypeError) as e:
        logger.error(f"评论ID格式错误: {comment_id}, 错误: {str(e)}")
        return []
        
    # 获取当前层级的子评论
    logger.debug(f"正在获取评论ID {comment_id} 的子评论")
    replies_sql = """
    SELECT 
        id, resource_id, resource_type, parent_id, openid, 
        content, image, like_count, reply_count, status, is_deleted, 
        create_time, update_time
    FROM wxapp_comment 
    WHERE parent_id = %s AND status = 1
    ORDER BY create_time ASC
    """
    replies = await async_execute_custom_query(replies_sql, [comment_id])
    
    logger.debug(f"评论ID {comment_id} 找到 {len(replies) if replies else 0} 条子评论")
    
    if not replies:
        return []
    
    # 为每个回复添加用户信息和递归获取其子评论
    for reply in replies:
        # 获取用户信息
        user_sql = "SELECT nickname, avatar, bio FROM wxapp_user WHERE openid = %s LIMIT 1"
        user_info = await async_execute_custom_query(user_sql, [reply.get("openid")])
        if user_info and len(user_info) > 0:
            reply["nickname"] = user_info[0].get("nickname")
            reply["avatar"] = user_info[0].get("avatar")
            reply["bio"] = user_info[0].get("bio")
        
        # 如果提供了openid，检查用户是否点赞
        if openid:
            like_sql = "SELECT id FROM wxapp_action WHERE action_type = 'like' AND target_id = %s AND openid = %s LIMIT 1"
            like_result = await async_execute_custom_query(like_sql, [reply.get("id"), openid])
            reply["is_liked"] = bool(like_result and len(like_result) > 0)
        
        # 计算父评论数量
        parent_id = reply.get("parent_id")
        if parent_id:
            try:
                # 确保parent_id是整数
                if isinstance(parent_id, str):
                    parent_id_int = int(parent_id.strip('()').strip())
                else:
                    parent_id_int = int(parent_id)
                
                parent_comment_sql = """
                SELECT COUNT(*) as count 
                FROM wxapp_comment 
                WHERE id < %s AND parent_id = %s AND status = 1
                """
                parent_comment_count_result = await async_execute_custom_query(
                    parent_comment_sql, 
                    [reply.get("id"), parent_id_int]
                )
                parent_comment_count = parent_comment_count_result[0]['count'] if parent_comment_count_result else 0
                reply["parent_comment_count"] = parent_comment_count
            except (ValueError, TypeError) as e:
                logger.error(f"parent_id格式错误: {parent_id}, 错误: {str(e)}")
                reply["parent_comment_count"] = 0
        else:
            reply["parent_comment_count"] = 0
        
        # 递归获取子评论，不依赖reply_count字段
        children = await get_child_comments(reply.get("id"), openid)
        if children:
            reply["children"] = children
    
    return replies

@router.get("/comment/detail")
async def get_comment_detail(
    openid: str = Query(..., description="用户OpenID"),
    comment_id: str = Query(..., description="评论ID"),
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
        comment_result = await async_execute_custom_query(comment_sql, [comment_id_int])

        if not comment_result:
            return Response.not_found(resource="评论")
            
        comment = comment_result[0]

        # 使用单一查询获取点赞状态
        like_query = async_execute_custom_query(
            """
            SELECT 1 FROM wxapp_action 
            WHERE openid = %s AND action_type = 'like' AND target_id = %s AND target_type = 'comment' 
            LIMIT 1
            """, 
            [openid, comment_id_int]
        )
        
        # 获取用户信息
        user_query = async_execute_custom_query(
            """
            SELECT nickname, avatar, bio FROM wxapp_user 
            WHERE openid = %s 
            LIMIT 1
            """, 
            [comment.get("openid")]
        )
        
        # 并行执行查询
        like_record, user_info = await asyncio.gather(like_query, user_query)
        
        # 判断是否已点赞
        liked = bool(like_record)
        
        # 添加用户信息
        if user_info and len(user_info) > 0:
            comment["nickname"] = user_info[0].get("nickname")
            comment["avatar"] = user_info[0].get("avatar")
            comment["bio"] = user_info[0].get("bio")
        
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


@router.get("/comment/replies")
async def get_comment_replies(
    comment_id: str = Query(..., description="评论ID"),
    limit: int = Query(10, description="返回回复数量")
):
    """获取评论回复列表"""
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
        
        # 使用直接SQL查询获取评论回复
        replies_sql = """
        SELECT 
            id, resource_id, resource_type, parent_id, openid,
            content, image, like_count, reply_count, status, is_deleted,
            create_time, update_time
        FROM wxapp_comment 
        WHERE parent_id = %s AND status = 1
        ORDER BY create_time
        LIMIT %s
        """
        replies = await async_execute_custom_query(replies_sql, [comment_id_int, limit])

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

        # 查询当前操作用户的角色
        user_info = await async_execute_custom_query(
            "SELECT role FROM wxapp_user WHERE openid = %s LIMIT 1",
            [openid]
        )
        user_role = user_info[0]["role"] if user_info and user_info[0] else None

        # 只有admin可以无视openid，普通用户只能删除自己评论
        if user_role != "admin" and comment["openid"] != openid:
            return Response.forbidden(details={"message": "只有评论作者才能删除评论"})

        # 更新评论计数
        resource_id = comment.get("resource_id")
        resource_type = comment.get("resource_type", "post")
        
        if resource_id:
            if resource_type == "post":
                resource = await async_get_by_id(
                    table_name="wxapp_post",
                    record_id=resource_id
                )
                if resource and resource.get("comment_count", 0) > 0:
                    try:
                        await async_update(
                            table_name="wxapp_post",
                            record_id=resource_id,
                            data={"comment_count": resource.get("comment_count", 1) - 1}
                        )
                    except Exception as e:
                        logger.warning(f"资源评论数更新失败: {str(e)}")
            elif resource_type == "knowledge":
                resource = await async_get_by_id(
                    table_name="wxapp_knowledge",
                    record_id=resource_id
                )
                if resource and resource.get("comment_count", 0) > 0:
                    try:
                        await async_update(
                            table_name="wxapp_knowledge",
                            record_id=resource_id,
                            data={"comment_count": resource.get("comment_count", 1) - 1}
                        )
                    except Exception as e:
                        logger.warning(f"资源评论数更新失败: {str(e)}")

        try:
            await async_update(
                table_name="wxapp_comment",
                record_id=comment_id,
                data={"status": 0}
            )
        except Exception as e:
            return Response.db_error(details={"message": f"评论删除失败: {str(e)}"})

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
    resource_id: str = Query(..., description="资源ID"),
    resource_type: str = Query('post', description="资源类型：post-帖子, knowledge-知识"),
    page: int = Query(1, description="页码"),
    page_size: int = Query(20, description="每页数量"),
    openid: str = Query(None, description="用户OpenID"),
    parent_id: str = Query(None, description="父评论ID")
):
    """获取评论列表"""
    if not resource_id:
        return Response.bad_request(details={"message": "缺少resource_id参数"})
    
    try:
        # 确保resource_id是整数
        try:
            resource_id_int = int(resource_id)
        except ValueError:
            return Response.bad_request(details={"message": "resource_id必须是整数"})
        
        # 验证资源类型
        if resource_type not in ['post', 'knowledge']:
            return Response.bad_request(details={"message": "resource_type必须是post或knowledge"})
        
        # 处理parent_id参数，确保为整数或None
        parent_id_int = None
        if parent_id:
            try:
                # 移除可能存在的括号，只保留数字部分
                parent_id_clean = parent_id.strip('()').strip()
                parent_id_int = int(parent_id_clean)
                logger.debug(f"处理parent_id参数: 原值={parent_id}, 清理后={parent_id_clean}, 转换为整数={parent_id_int}")
            except ValueError:
                logger.warning(f"parent_id参数格式错误: {parent_id}")
                return Response.bad_request(details={"message": "parent_id必须是整数"})
        
        # 根据资源类型检查资源是否存在
        resource_exists = False
        if resource_type == 'post':
            resource = await async_get_by_id(
                table_name="wxapp_post",
                record_id=resource_id_int
            )
            resource_exists = resource is not None
        elif resource_type == 'knowledge':
            resource = await async_get_by_id(
                table_name="wxapp_knowledge",
                record_id=resource_id_int
            )
            resource_exists = resource is not None
        
        if not resource_exists:
            return Response.not_found(resource=f"资源({resource_type})")
        
        # 构建SQL查询，根据是否有parent_id使用不同的查询条件
        query_params = [resource_id_int, resource_type]
        if parent_id_int is not None:
            all_comments_sql = """
            SELECT 
                id, resource_id, resource_type, parent_id, openid, 
                content, image, like_count, reply_count, status, is_deleted, 
                create_time, update_time
            FROM wxapp_comment
            WHERE resource_id = %s AND resource_type = %s AND parent_id = %s AND status = 1
            ORDER BY create_time DESC
            """
            query_params.append(parent_id_int)
            logger.debug(f"查询子评论SQL参数: [resource_id={resource_id_int}, resource_type={resource_type}, parent_id={parent_id_int}]")
        else:
            all_comments_sql = """
            SELECT 
                id, resource_id, resource_type, parent_id, openid, 
                content, image, like_count, reply_count, status, is_deleted, 
                create_time, update_time
            FROM wxapp_comment
            WHERE resource_id = %s AND resource_type = %s AND status = 1 AND parent_id IS NULL
            ORDER BY create_time DESC
            """
            logger.debug(f"查询顶层评论SQL参数: [resource_id={resource_id_int}, resource_type={resource_type}]")
        
        # 添加分页
        all_comments_sql += f" LIMIT {page_size} OFFSET {(page - 1) * page_size}"
        
        # 执行查询
        all_comments = await async_execute_custom_query(all_comments_sql, query_params)
        logger.debug(f"找到 {len(all_comments) if all_comments else 0} 条评论")
        
        # 计算评论总数，用于分页
        count_sql = ""
        count_params = [resource_id_int, resource_type]
        if parent_id_int is not None:
            count_sql = "SELECT COUNT(*) as total FROM wxapp_comment WHERE resource_id = %s AND resource_type = %s AND parent_id = %s AND status = 1"
            count_params.append(parent_id_int)
        else:
            count_sql = "SELECT COUNT(*) as total FROM wxapp_comment WHERE resource_id = %s AND resource_type = %s AND parent_id IS NULL AND status = 1"
        
        count_result = await async_execute_custom_query(count_sql, count_params)
        total_count = count_result[0]['total'] if count_result else 0
        
        # 处理每个评论的用户信息和点赞状态
        for comment in all_comments:
            # 获取用户信息
            user_sql = "SELECT nickname, avatar, bio FROM wxapp_user WHERE openid = %s LIMIT 1"
            user_info = await async_execute_custom_query(user_sql, [comment.get("openid")])
            if user_info and len(user_info) > 0:
                comment["nickname"] = user_info[0].get("nickname")
                comment["avatar"] = user_info[0].get("avatar")
                comment["bio"] = user_info[0].get("bio")
            
            # 如果提供了openid，检查用户是否点赞
            if openid:
                like_sql = "SELECT id FROM wxapp_action WHERE action_type = 'like' AND target_id = %s AND openid = %s LIMIT 1"
                like_result = await async_execute_custom_query(like_sql, [comment.get("id"), openid])
                comment["is_liked"] = bool(like_result and len(like_result) > 0)
            
            # 计算父评论数量
            if comment.get("parent_id"):
                parent_comment_sql = """
                SELECT COUNT(*) as count 
                FROM wxapp_comment 
                WHERE id < %s AND parent_id = %s AND status = 1
                """
                parent_comment_count_result = await async_execute_custom_query(
                    parent_comment_sql, 
                    [comment.get("id"), comment.get("parent_id")]
                )
                parent_comment_count = parent_comment_count_result[0]['count'] if parent_comment_count_result else 0
                comment["parent_comment_count"] = parent_comment_count
            else:
                comment["parent_comment_count"] = 0
        
        # 计算总页数
        total_pages = (total_count + page_size - 1) // page_size if page_size > 0 else 1
        
        # 构建标准分页信息
        pagination = {
            "total": total_count,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "has_more": page < total_pages
        }
        
        # 返回标准分页响应
        return Response.paged(
            data=all_comments,
            pagination=pagination,
            details={"message": "获取评论列表成功", "resource_id": resource_id, "resource_type": resource_type}
        )
    except Exception as e:
        logger.error(f"获取评论列表异常: {str(e)}")
        return Response.error(details={"message": f"获取评论列表失败: {str(e)}"})