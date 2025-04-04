"""
帖子相关API接口
处理帖子创建、查询、更新、删除、点赞、收藏等功能
"""
import time
import json
from typing import Dict, Any, Optional, List
from fastapi import Query, APIRouter
import asyncio

from api.models.common import Response, Request, validate_params
from etl.load.db_core import (
    async_query_records, async_get_by_id, async_insert, async_update, async_count_records, async_execute_custom_query
)
from config import Config
from core.utils.logger import register_logger

# 获取配置
config = Config()
router = APIRouter()
logger = register_logger('api.routes.wxapp.post')

@router.post("/post")
async def create_post(
    request: Request,
):
    """创建新帖子"""
    try:
        req_data = await request.json()
        required_params = ["title", "content"]
        error_response = validate_params(req_data, required_params)
        if(error_response):
            return error_response

        openid = req_data.get("openid")
        
        # 使用单一SQL直接获取用户信息
        user_data = await async_execute_custom_query(
            "SELECT nickname, avatar, bio FROM wxapp_user WHERE openid = %s LIMIT 1",
            [openid]
        )
        
        nickname = ""
        avatar = ""
        bio = ""
        if user_data:
            nickname = user_data[0].get("nickname", "")
            avatar = user_data[0].get("avatar", "")
            bio = user_data[0].get("bio", "")
        
        # 构造帖子数据
        db_post_data = {
            "openid": openid,
            "nickname": nickname,
            "avatar": avatar,
            "bio": bio,
            "category_id": req_data.get("category_id", 1),
            "title": req_data.get("title"),
            "content": req_data.get("content"),
            "is_deleted": 0
        }
        
        # 可选字段
        if "image" in req_data:
            db_post_data["image"] = req_data.get("image")
        if "tag" in req_data:
            db_post_data["tag"] = req_data.get("tag")
        
        # 创建帖子和更新用户发帖数并行执行
        post_insert = async_insert("wxapp_post", db_post_data)
        user_update = async_execute_custom_query(
            "UPDATE wxapp_user SET post_count = post_count + 1 WHERE openid = %s",
            [openid],
            fetch=False
        )
        
        # 并行执行两个操作
        post_id, _ = await asyncio.gather(post_insert, user_update)
        
        if not post_id or post_id == -1:
            logger.error("插入帖子数据失败")
            return Response.db_error(details={"message": "创建帖子失败"})

        logger.debug(f"创建帖子成功: {post_id}")
        # 修改返回格式，将post_id放在data中而不是details中
        return Response.success(data={"id": post_id}, details={"message":"创建帖子成功"})
    except Exception as e:
        logger.error(f"创建帖子接口异常: {str(e)}")
        return Response.error(details={"message": f"创建帖子失败: {str(e)}"})

@router.get("/post/detail")
async def get_post_detail(
    post_id: str = Query(..., description="帖子ID")
):
    """获取帖子详情"""
    if(not post_id):
        return Response.bad_request(details={"message": "缺少post_id参数"})
    try:
        # 确保post_id是整数
        post_id_int = int(post_id)
        
        # 使用单一SQL直接获取帖子详情，并行更新浏览次数
        post_query = async_execute_custom_query(
            "SELECT * FROM wxapp_post WHERE id = %s LIMIT 1",
            [post_id_int]
        )
        
        view_update = async_execute_custom_query(
            "UPDATE wxapp_post SET view_count = view_count + 1 WHERE id = %s",
            [post_id_int],
            fetch=False
        )
        
        # 并行执行查询和更新
        post_result, _ = await asyncio.gather(post_query, view_update)
        
        if not post_result:
            return Response.not_found(resource="帖子")
            
        post = post_result[0]
        
        # 获取用户信息，只查询必要字段
        user_info = None
        if post.get("openid"):
            user_data = await async_execute_custom_query(
                "SELECT openid, nickname, avatar, bio FROM wxapp_user WHERE openid = %s LIMIT 1",
                [post.get("openid")]
            )
            if user_data:
                user_info = user_data[0]

        # 构建详情响应
        detail_response = {
            **post,
            "user": user_info
        }

        return Response.success(data=detail_response)
    except Exception as e:
        return Response.error(details={"message": f"获取帖子详情失败: {str(e)}"})

@router.get("/post/list")
async def get_posts(
    request: Request,
    page: int = Query(1, description="页码"),
    limit: int = Query(10, description="每页数量"),
    category_id: Optional[int] = Query(None, description="分类ID"),
    tag: Optional[str] = Query(None, description="标签"),
    order_by: str = Query("create_time DESC", description="排序字段")
):
    """查询帖子列表"""
    try:
        # 验证并规范排序字段
        ALLOWED_ORDERS = {"update_time", "create_time", "view_count", "like_count"}
        
        order_by_parts = order_by.split()
        if len(order_by_parts) != 2 or order_by_parts[0] not in ALLOWED_ORDERS or order_by_parts[1].upper() not in {"ASC", "DESC"}:
            order_by = "create_time DESC"
        
        # 构建基础SQL查询和条件
        base_sql = """
        SELECT 
            id, title, content, image, openid, nickname, avatar, bio, 
            view_count, like_count, comment_count, favorite_count, 
            create_time, update_time, tag, category_id, status,
            is_deleted
        FROM wxapp_post
        WHERE status = 1
        """
        
        # 构建查询参数和条件
        params = []
        
        # 添加分类筛选
        if category_id:
            base_sql += " AND category_id = %s"
            params.append(category_id)
        
        # 添加标签筛选
        if tag:
            base_sql += " AND tag LIKE %s"
            params.append(f"%{tag}%")
        
        # 添加排序和分页
        base_sql += f" ORDER BY {order_by} LIMIT %s OFFSET %s"
        params.extend([limit, (page - 1) * limit])
        
        # 构建计数SQL
        count_sql = """
        SELECT COUNT(*) as total FROM wxapp_post WHERE status = 1
        """
        
        # 添加筛选条件到计数查询
        count_params = []
        if category_id:
            count_sql += " AND category_id = %s"
            count_params.append(category_id)
        
        if tag:
            count_sql += " AND tag LIKE %s"
            count_params.append(f"%{tag}%")
        
        # 并行执行帖子查询和计数查询
        posts_query = async_execute_custom_query(base_sql, params)
        count_query = async_execute_custom_query(count_sql, count_params)
        
        posts, count_result = await asyncio.gather(posts_query, count_query)
        
        # 计算总页数
        total = count_result[0]['total'] if count_result else 0
        total_pages = (total + limit - 1) // limit
        
        # 构建分页信息
        pagination = {
            "page": page,
            "size": limit,
            "total": total,
            "pages": total_pages
        }
        
        # 返回结果
        return Response.paged(
            data=posts or [],
            pagination=pagination,
            details={"message":"查询帖子列表成功"}
        )
    except Exception as e:
        logger.error(f"查询帖子列表失败: {e}")
        return Response.error(details={"message": f"查询帖子列表失败: {str(e)}"})

@router.post("/post/update")
async def update_post(
    request: Request,
):
    """更新帖子信息"""
    try:
        req_data = await request.json()
        required_params = ["post_id", "openid"]
        error_response = validate_params(req_data, required_params)
        if(error_response):
            return error_response
            
        openid = req_data.get("openid")
        post_id = req_data.get("post_id")
        
        # 使用单条SQL验证帖子是否存在并且属于当前用户
        post_result = await async_execute_custom_query(
            "SELECT id FROM wxapp_post WHERE id = %s AND openid = %s LIMIT 1",
            [post_id, openid]
        )
        
        if not post_result:
            return Response.not_found(resource="帖子")
        
        # 提取更新字段
        update_data = {}
        
        if "title" in req_data:
            update_data["title"] = req_data["title"]
        if "content" in req_data:
            update_data["content"] = req_data["content"]
        if "image" in req_data:
            update_data["image"] = req_data["image"]
        if "category_id" in req_data:
            update_data["category_id"] = req_data["category_id"]
        if "tag" in req_data:
            update_data["tag"] = req_data["tag"]
        
        if not update_data:
            return Response.bad_request(details={"message": "未提供任何更新数据"})
            
        # 更新帖子
        update_success = await async_update(
            "wxapp_post",
            post_id,
            update_data
        )
        
        if not update_success:
            return Response.db_error(details={"message": "更新帖子失败"})
        
        # 直接使用SQL获取更新后的帖子
        fields = "id, title, content, image, tag, category_id, update_time"
        updated_post = await async_execute_custom_query(
            f"SELECT {fields} FROM wxapp_post WHERE id = %s LIMIT 1",
            [post_id]
        )
        
        # 更新帖子成功
        if updated_post:
            return Response.success(data=updated_post[0], details={"message": "更新帖子成功"})
        else:
            return Response.success(details={"message": "更新帖子成功"})
    except Exception as e:
        return Response.error(details={"message": f"更新帖子失败: {str(e)}"})

@router.post("/post/delete")
async def delete_post(
    request: Request,
):
    """删除帖子"""
    try:
        req_data = await request.json()
        required_params = ["post_id", "openid"]
        error_response = validate_params(req_data, required_params)
        if(error_response):
            return error_response
            
        openid = req_data.get("openid") 
        post_id = req_data.get("post_id")
        
        # 先查询帖子是否存在并且属于当前用户
        post_query = f"SELECT id FROM wxapp_post WHERE id = %s AND openid = %s AND is_deleted = 0"
        post_result = await async_execute_custom_query(post_query, [post_id, openid])
        
        if not post_result:
            return Response.not_found(resource="帖子")
            
        # 逻辑删除帖子，同时减少用户的发帖数
        # 并发执行两个SQL操作
        delete_post_query = async_execute_custom_query(
            "UPDATE wxapp_post SET is_deleted = 1, status = 0, update_time = NOW() WHERE id = %s",
            [post_id],
            fetch=False
        )
        
        update_user_query = async_execute_custom_query(
            "UPDATE wxapp_user SET post_count = GREATEST(post_count - 1, 0) WHERE openid = %s",
            [openid],
            fetch=False
        )
        
        await asyncio.gather(delete_post_query, update_user_query)
        
        return Response.success(details={"message": "删除帖子成功"})
    except Exception as e:
        return Response.error(details={"message": f"删除帖子失败: {str(e)}"})

@router.get("/post/search")
async def search_posts(
    request: Request,
    keywords: Optional[str] = Query(None, description="搜索关键词"),
    category_id: Optional[int] = Query(None, description="分类ID"),
    min_likes: Optional[int] = Query(None, description="最小点赞数"),
    max_likes: Optional[int] = Query(None, description="最大点赞数"),
    page: int = Query(1, description="页码"),
    limit: int = Query(10, description="每页数量"),
    order_by: str = Query("create_time DESC", description="排序方式")
):
    """搜索帖子"""
    try:
        # 构建查询条件
        conditions = []
        params = []
        
        # 忽略已删除的帖子
        conditions.append("is_deleted = 0")
        
        # 搜索关键词
        if keywords:
            conditions.append("(title LIKE %s OR content LIKE %s)")
            keywords_param = f"%{keywords}%"
            params.extend([keywords_param, keywords_param])
            
        # 分类ID
        if category_id:
            conditions.append("category_id = %s")
            params.append(category_id)
            
        # 点赞数范围
        if min_likes is not None:
            conditions.append("like_count >= %s")
            params.append(min_likes)
            
        if max_likes is not None:
            conditions.append("like_count <= %s")
            params.append(max_likes)
            
        # 构建查询条件字符串
        where_clause = " AND ".join(conditions)
        
        # 只查询需要的字段
        fields = ["id", "title", "content", "image", "openid", "nickname", "avatar", 
                 "view_count", "like_count", "comment_count", "create_time", "update_time"]
        
        # 计算分页参数
        offset = (page - 1) * limit
        
        # 验证并规范排序字段
        ALLOWED_ORDERS = {"update_time", "create_time", "view_count", "like_count"}
        
        order_by_parts = order_by.split()
        if len(order_by_parts) != 2 or order_by_parts[0] not in ALLOWED_ORDERS or order_by_parts[1].upper() not in {"ASC", "DESC"}:
            order_by = "create_time DESC"
        
        # 构建查询SQL
        sql = f"""
            SELECT {', '.join(fields)}
            FROM wxapp_post
            WHERE {where_clause}
            ORDER BY {order_by}
            LIMIT %s OFFSET %s
        """
        query_params = params.copy()
        query_params.extend([limit, offset])
        
        # 构建计数SQL
        count_sql = f"""
            SELECT COUNT(*) as total
            FROM wxapp_post 
            WHERE {where_clause}
        """
        
        # 并行执行查询和计数
        posts_query = async_execute_custom_query(sql, query_params)
        count_query = async_execute_custom_query(count_sql, params)
        
        posts_result, count_result = await asyncio.gather(posts_query, count_query)
        
        # 处理结果
        total = count_result[0]['total'] if count_result else 0
        total_pages = (total + limit - 1) // limit if total > 0 else 0
        
        # 构建分页信息
        pagination = {
            "page": page,
            "size": limit,
            "total": total,
            "pages": total_pages
        }
        
        # 返回结果
        return Response.paged(
            data=posts_result or [],
            pagination=pagination,
            details={"message": "搜索帖子成功"}
        )
    except Exception as e:
        logger.error(f"搜索帖子失败: {e}")
        return Response.error(details={"message": f"搜索帖子失败: {str(e)}"})

# 使用并行查询优化
async def get_post_with_stats(post_id):
    """获取帖子和统计信息"""
    try:
        # 获取帖子
        post_result = await async_query_records(
            "wxapp_post",
            {"id": post_id},
            limit=1
        )
        
        if not post_result or not post_result['data']:
            return None
        
        post = post_result['data'][0]
        
        # 不再查询不存在的wxapp_post_stat表
        # 直接返回帖子信息
        return post
    except Exception as e:
        logger.error(f"获取帖子信息失败: {str(e)}")
        return None

@router.get("/post/status")
async def get_post_status(
    post_id: str = Query(..., description="帖子ID，多个ID用逗号分隔"),
    openid: str = Query(..., description="用户openid")
):
    """获取帖子交互状态"""
    try:
        if not post_id:
            return Response.bad_request(details={"message": "缺少post_id参数"})
            
        # 处理多个post_id
        post_ids = [int(pid.strip()) for pid in post_id.split(",")]
        
        # 使用单一SQL联合查询，获取帖子信息和用户交互状态
        status_sql = """
        SELECT 
            p.id,
            p.openid,
            p.openid = %s AS is_author,
            p.like_count,
            p.favorite_count,
            p.comment_count,
            p.view_count,
            MAX(CASE WHEN a.action_type = 'like' THEN 1 ELSE 0 END) AS is_liked,
            MAX(CASE WHEN a.action_type = 'favorite' THEN 1 ELSE 0 END) AS is_favorited
        FROM 
            wxapp_post p
        LEFT JOIN 
            wxapp_action a ON p.id = a.target_id AND a.openid = %s AND a.target_type = 'post'
        WHERE 
            p.id IN %s
        GROUP BY 
            p.id, p.openid, p.like_count, p.favorite_count, p.comment_count, p.view_count
        """
        
        # 执行联合查询
        posts_with_actions = await async_execute_custom_query(
            status_sql,
            [openid, openid, tuple(post_ids)]
        )
        
        # 查询当前用户关注的用户列表
        following_sql = """
        SELECT target_id FROM wxapp_action 
        WHERE openid = %s AND action_type = 'follow' AND target_type = 'user'
        """
        
        following_result = await async_execute_custom_query(following_sql, [openid])
        following_openids = set()
        if following_result:
            following_openids = {item['target_id'] for item in following_result}
        
        # 构建状态响应
        status_map = {}
        existing_post_ids = set()
        
        if posts_with_actions:
            for post in posts_with_actions:
                post_id = post.get("id")
                author_openid = post.get("openid")
                if post_id:
                    existing_post_ids.add(post_id)
                    status_map[str(post_id)] = {
                        "exist": True,
                        "is_liked": bool(post.get("is_liked")),
                        "is_favorited": bool(post.get("is_favorited")),
                        "is_author": bool(post.get("is_author")),
                        "is_following": author_openid in following_openids,
                        "like_count": post.get("like_count", 0),
                        "favorite_count": post.get("favorite_count", 0),
                        "comment_count": post.get("comment_count", 0),
                        "view_count": post.get("view_count", 0)
                    }
        
        # 为不存在的帖子添加状态
        for pid in post_ids:
            if pid not in existing_post_ids:
                status_map[str(pid)] = {
                    "exist": False,
                    "is_liked": False,
                    "is_favorited": False,
                    "is_author": False,
                    "is_following": False,
                    "like_count": 0,
                    "favorite_count": 0,
                    "comment_count": 0,
                    "view_count": 0
                }

        return Response.success(data=status_map)
    except Exception as e:
        return Response.error(details={"message": f"获取帖子状态失败: {str(e)}"})