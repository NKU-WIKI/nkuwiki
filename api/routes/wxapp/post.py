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
    async_query_records, async_get_by_id, async_insert, async_update, async_count_records, execute_custom_query, async_execute_custom_query
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
        
        # 获取用户信息，用于昵称和头像
        user_data = await async_query_records(
            table_name="wxapp_user",
            conditions={"openid": openid},
            limit=1
        )
        
        nickname = ""
        avatar = ""
        if user_data and "data" in user_data and len(user_data["data"]) > 0:
            nickname = user_data["data"][0].get("nickname", "")
            avatar = user_data["data"][0].get("avatar", "")
        
        # 构造帖子数据
        db_post_data = {
            "openid": openid,
            "nickname": nickname,
            "avatar": avatar,
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
        
        try:
            # 创建帖子
            result = await async_insert("wxapp_post", db_post_data)
            
            # 更新用户发帖数
            await async_update(
                "wxapp_user",
                {"openid": openid},
                {"post_count": execute_custom_query(
                    "SELECT post_count FROM wxapp_user WHERE openid = %s",
                    [openid], fetch=True)[0]["post_count"] + 1}
            )

            logger.debug(f"创建帖子成功: {result}")
            return Response.success(details={"post_id": result, "message":"创建帖子成功"})
        except Exception as e:
            logger.error(f"插入帖子数据失败: {str(e)}")
            return Response.success(details={"post_id": -1, "message":"创建帖子失败"})
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
        
        # 使用async_query_records代替async_get_by_id
        post_result = await async_query_records(
            "wxapp_post",
            {"id": post_id_int},
            limit=1
        )
        
        if not post_result or not post_result['data']:
            return Response.not_found(resource="帖子")
            
        post = post_result['data'][0]

        # 更新浏览次数 - 使用异步版本
        await async_execute_custom_query(
            "UPDATE wxapp_post SET view_count = view_count + 1 WHERE id = %s",
            [post_id_int],
            fetch=False
        )

        # 获取用户信息
        user_info = None
        if post.get("openid"):
            user_data = await async_query_records(
                "wxapp_user",
                {"openid": post["openid"]},
                limit=1
            )
            if user_data and user_data['data']:
                user_info = user_data['data'][0]

        # 不再查询不存在的wxapp_post_stat表
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
    order_by: str = Query("update_time DESC", description="排序字段")
):
    """查询帖子列表"""
    try:
        conditions = {"status": 1}
        if category_id:
            conditions["category_id"] = category_id

        if tag:
            conditions["tag"] = {"$contains": [tag]}

        ALLOWED_ORDERS = {"update_time", "create_time", "view_count", "like_count"}

        order_by_parts = order_by.split()
        if len(order_by_parts) != 2 or order_by_parts[0] not in ALLOWED_ORDERS or order_by_parts[1].upper() not in {"ASC", "DESC"}:
            order_by = "update_time DESC"

        posts = await async_query_records(
            "wxapp_post",
            conditions,
            order_by,
            limit,
            (page - 1) * limit
        )

        total = await async_count_records("wxapp_post", conditions)
        
        # 确保每个帖子对象都有id字段
        for post in posts['data']:
            if 'id' not in post:
                post['id'] = post.get('_id')
        
        # 直接使用字典结构作为分页参数，避免使用model_dump
        return Response.paged(
            data=posts['data'],
            pagination=posts['pagination'],
            details={"message":"查询帖子列表成功"}
        )
    except Exception as e:
        return Response.error(details={"message": f"查询帖子列表失败: {str(e)}"})

@router.post("/post/update")
async def update_post(
    request: Request,
):
    """更新帖子"""
    try:
        req_data = await request.json()
        required_params = ["post_id"]
        error_response = validate_params(req_data, required_params)
        if(error_response):
            return error_response

        openid = req_data.get("openid")
        post_id = req_data.get("post_id")
        
        # 使用async_get_by_id获取帖子
        post = await async_get_by_id("wxapp_post", post_id)
        if not post:
            return Response.not_found(resource="帖子")

        if post["openid"] != openid:
            return Response.forbidden(details={"message": "无操作权限"})

        # 获取更新数据
        valid_data = req_data.get("data")
        if not valid_data:
            return Response.bad_request(details={"message": "无有效更新字段"})

        try:
            # 添加更新时间
            valid_data["update_time"] = time.strftime("%Y-%m-%d %H:%M:%S")
            
            # 直接使用async_update更新数据
            success = await async_update(
                "wxapp_post",
                post_id,
                valid_data
            )
            
            if not success:
                logger.error(f"更新帖子失败，帖子ID: {post_id}")
                return Response.error(details={"message": "更新帖子失败"})

            # 获取更新后的帖子
            updated_post = await async_get_by_id("wxapp_post", post_id)
            return Response.success(data=updated_post, details={"message": "更新帖子成功"})
        except Exception as e:
            logger.error(f"更新帖子操作异常，帖子ID: {post_id}, 错误: {str(e)}")
            return Response.error(details={"message": f"更新帖子操作异常: {str(e)}"})
    except Exception as e:
        logger.error(f"更新帖子接口异常: {str(e)}")
        return Response.error(details={"message": f"更新帖子失败: {str(e)}"})

@router.post("/post/delete")
async def delete_post(
    request: Request,
):
    """删除帖子"""
    try:
        req_data = await request.json()
        required_params = ["post_id"]
        error_response = validate_params(req_data, required_params)
        if(error_response):
            return error_response
            
        openid = req_data.get("openid")
        post_id = req_data.get("post_id")
        
        # 检查帖子是否存在
        post = await async_get_by_id("wxapp_post", post_id)
        if not post:
            return Response.not_found(resource="帖子")

        # 检查权限
        if post["openid"] != openid:
            return Response.forbidden(details={"message": "无删除权限"})

        # 更新帖子状态为已删除
        success = await async_update(
            "wxapp_post",
            post_id,
            {"status": 0, "update_time": time.strftime("%Y-%m-%d %H:%M:%S")}
        )
        
        if not success:
            return Response.error(details={"message": "删除帖子失败"})

        return Response.success(details={"deleted_id": post_id, "message": "删除帖子成功"})
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
    limit: int = Query(10, description="每页数量")
):
    """搜索帖子"""
    try:
        # 构建查询条件
        conditions = {"status": 1}
        
        if category_id:
            conditions["category_id"] = category_id
            
        if keywords:
            # 全文检索需要使用特殊查询
            sql = """
            SELECT * FROM wxapp_post
            WHERE status = 1
            AND (title LIKE %s OR content LIKE %s)
            """
            params = [f"%{keywords}%", f"%{keywords}%"]
            
            if category_id:
                sql += " AND category_id = %s"
                params.append(category_id)
                
            if min_likes is not None:
                sql += " AND like_count >= %s"
                params.append(min_likes)
                
            if max_likes is not None:
                sql += " AND like_count <= %s"
                params.append(max_likes)
                
            sql += " ORDER BY update_time DESC LIMIT %s OFFSET %s"
            params.append(limit)
            params.append((page - 1) * limit)
            
            # 执行自定义查询
            results = await async_execute_custom_query(sql, params)
            
            # 计算总数
            count_sql = """
            SELECT COUNT(*) as total FROM wxapp_post
            WHERE status = 1
            AND (title LIKE %s OR content LIKE %s)
            """
            count_params = [f"%{keywords}%", f"%{keywords}%"]
            
            if category_id:
                count_sql += " AND category_id = %s"
                count_params.append(category_id)
                
            if min_likes is not None:
                count_sql += " AND like_count >= %s"
                count_params.append(min_likes)
                
            if max_likes is not None:
                count_sql += " AND like_count <= %s"
                count_params.append(max_likes)
                
            count_result = await async_execute_custom_query(count_sql, count_params)
            total = count_result[0]['total'] if count_result else 0
            
            # 构建分页信息
            pagination = {
                "total": total,
                "page": page,
                "page_size": limit,
                "total_pages": (total + limit - 1) // limit if limit > 0 else 1
            }
            
            return Response.paged(
                data=results,
                pagination=pagination,
                details={"message": "搜索帖子成功"}
            )
        else:
            # 使用标准查询方式
            if min_likes is not None:
                conditions["like_count"] = {"$gte": min_likes}
                
            if max_likes is not None:
                conditions["like_count"] = {"$lte": max_likes}
                
            posts = await async_query_records(
                "wxapp_post",
                conditions,
                "update_time DESC",
                limit,
                (page - 1) * limit
            )
            
            return Response.paged(
                data=posts['data'],
                pagination=posts['pagination'],
                details={"message": "搜索帖子成功"}
            )
    except Exception as e:
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
    post_id: str = Query(..., description="帖子ID"),
    openid: str = Query(..., description="用户openid")
):
    """获取帖子交互状态"""
    try:
        if not post_id:
            return Response.bad_request(details={"message": "缺少post_id参数"})
            
        post_id_int = int(post_id)
        
        # 获取帖子
        post = await async_get_by_id("wxapp_post", post_id_int)
        if not post:
            return Response.not_found(resource="帖子")

        # 获取用户交互
        actions = await async_query_records(
            "wxapp_action",
            {
                "openid": openid,
                "target_id": post_id_int,
                "target_type": "post"
            }
        )

        # 分析交互类型
        is_liked = False
        is_favorited = False
        
        if actions and actions['data']:
            for action in actions['data']:
                if action["action_type"] == "like":
                    is_liked = True
                elif action["action_type"] == "favorite":
                    is_favorited = True

        # 构建状态
        status = {
            "is_liked": is_liked,
            "is_favorited": is_favorited,
            "like_count": post.get("like_count", 0),
            "favorite_count": post.get("favorite_count", 0),
            "comment_count": post.get("comment_count", 0),
            "view_count": post.get("view_count", 0),
            "is_author": post.get("openid") == openid
        }

        return Response.success(data=status)
    except Exception as e:
        return Response.error(details={"message": f"获取帖子状态失败: {str(e)}"})