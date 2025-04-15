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
        required_params = ["title", "content", "openid"]
        error_response = validate_params(req_data, required_params)
        if(error_response):
            return error_response

        openid = req_data.get("openid")
        
        # 构造帖子数据
        db_post_data = {
            "openid": openid,
            "nickname": req_data.get("nickname", ""),
            "avatar": req_data.get("avatar", ""),
            "bio": req_data.get("bio", ""),
            "category_id": req_data.get("category_id", 1),
            "title": req_data.get("title"),
            "content": req_data.get("content"),
            "is_deleted": 0,
            "allow_comment": req_data.get("allow_comment", 1),
            "is_public": req_data.get("is_public", 1)
        }
        
        # 处理可选联系方式字段
        if "phone" in req_data:
            db_post_data["phone"] = req_data.get("phone")
        if "wechatId" in req_data:
            db_post_data["wechatId"] = req_data.get("wechatId")
        if "qqId" in req_data:
            db_post_data["qqId"] = req_data.get("qqId")
        
        # 处理其他可选字段
        if "image" in req_data:
            db_post_data["image"] = req_data.get("image")
        if "tag" in req_data:
            db_post_data["tag"] = req_data.get("tag")
        if "location" in req_data:
            db_post_data["location"] = req_data.get("location")
        
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
    try:
        # 直接使用单一SQL查询帖子，包含所有字段
        post_query = """
        SELECT 
            id, openid, title, content, image, tag, category_id, location, nickname, avatar,
            phone, wechatId, qqId, view_count, like_count, comment_count, favorite_count,
            allow_comment, is_public, create_time, update_time, status, is_deleted
        FROM wxapp_post
        WHERE id = %s AND status = 1 AND is_deleted = 0
        LIMIT 1
        """
        
        post_data = await async_execute_custom_query(post_query, [post_id])
        
        if not post_data:
            return Response.not_found(resource="帖子")
            
        # 增加浏览量
        increment_views_query = """
        UPDATE wxapp_post SET view_count = view_count + 1 WHERE id = %s
        """
        await async_execute_custom_query(increment_views_query, [post_id], fetch=False)

        # 构建详情响应
        detail_response = post_data[0]
        
        # 只有公开帖子才查询用户详细信息
        if detail_response.get("is_public", 1) == 1 and detail_response.get("openid"):
            user_data = await async_execute_custom_query(
                "SELECT openid, nickname, avatar, bio FROM wxapp_user WHERE openid = %s LIMIT 1",
                [detail_response.get("openid")]
            )
            if user_data:
                detail_response["user"] = user_data[0]
        else:
            # 非公开帖子提供匿名信息
            detail_response["user"] = {
                "openid": "",  # 不提供真实openid
                "nickname": "匿名用户",
                "avatar": ""  # 空头像
            }
            
            # 清除可能泄露用户信息的字段
            detail_response["nickname"] = "匿名用户"
            detail_response["avatar"] = ""
            detail_response["bio"] = ""
            detail_response["phone"] = None
            detail_response["wechatId"] = None
            detail_response["qqId"] = None
            detail_response["openid"] = ""  # 不暴露原始openid

        return Response.success(data=detail_response)
    except Exception as e:
        return Response.error(details={"message": f"获取帖子详情失败: {str(e)}"})

@router.get("/post/list")
async def get_posts(
    page: int = Query(1, description="页码"),
    limit: int = Query(10, description="每页数量"),
    category_id: Optional[int] = Query(None, description="分类ID"),
    tag: Optional[str] = Query(None, description="标签"),
    openid: Optional[str] = Query(None, description="用户openid，查询该用户的帖子或收藏的帖子"),
    favorite: bool = Query(False, description="是否查询用户收藏的帖子，为true时使用openid参数查询用户收藏的帖子"),
    order_by: str = Query("create_time DESC", description="排序字段")
):
    """查询帖子列表"""
    try:
        # 验证并规范排序字段
        ALLOWED_ORDERS = {"update_time", "create_time", "view_count", "like_count"}
        
        order_by_parts = order_by.split()
        if len(order_by_parts) != 2 or order_by_parts[0] not in ALLOWED_ORDERS or order_by_parts[1].upper() not in {"ASC", "DESC"}:
            order_by = "create_time DESC"
        
        # 处理收藏查询
        if favorite and openid:
            # 先查询用户收藏的帖子ID
            favorite_sql = """
            SELECT target_id FROM wxapp_action 
            WHERE openid = %s AND action_type = 'favorite' AND target_type = 'post'
            """
            favorite_results = await async_execute_custom_query(favorite_sql, [openid])
            
            if not favorite_results:
                # 用户没有收藏帖子，直接返回空结果
                pagination = {
                    "total": 0,
                    "page": page,
                    "page_size": limit,
                    "total_pages": 0,
                    "has_more": False
                }
                return Response.paged(data=[], pagination=pagination)
            
            # 提取收藏的帖子ID
            favorite_post_ids = [item['target_id'] for item in favorite_results]
            
            # 构建基础SQL查询，加入收藏条件
            base_sql = """
            SELECT 
                id, title, content, image, openid, nickname, avatar, bio, phone, wechatId, qqId,
                view_count, like_count, comment_count, favorite_count, allow_comment, is_public,
                create_time, update_time, tag, category_id, status, is_deleted
            FROM wxapp_post
            WHERE is_deleted = 0 AND id IN %s
            """
            params = [tuple(favorite_post_ids) if len(favorite_post_ids) > 1 else f"({favorite_post_ids[0]})"]
            
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
            SELECT COUNT(*) as total FROM wxapp_post 
            WHERE is_deleted = 0 AND id IN %s
            """
            count_params = [tuple(favorite_post_ids) if len(favorite_post_ids) > 1 else f"({favorite_post_ids[0]})"]
            
            # 添加分类筛选到计数查询
            if category_id:
                count_sql += " AND category_id = %s"
                count_params.append(category_id)
            
            # 添加标签筛选到计数查询
            if tag:
                count_sql += " AND tag LIKE %s"
                count_params.append(f"%{tag}%")
        else:
            # 常规查询流程（非收藏查询）
            # 构建基础SQL查询和条件
            base_sql = """
            SELECT 
                id, title, content, image, openid, nickname, avatar, bio, phone, wechatId, qqId,
                view_count, like_count, comment_count, favorite_count, allow_comment, is_public,
                create_time, update_time, tag, category_id, status, is_deleted
            FROM wxapp_post
            WHERE is_deleted = 0
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
                
            # 添加作者筛选
            if openid and not favorite:  # 只有在非收藏模式下，openid才用作作者筛选
                base_sql += " AND openid = %s"
                params.append(openid)
            
            # 添加排序和分页
            base_sql += f" ORDER BY {order_by} LIMIT %s OFFSET %s"
            params.extend([limit, (page - 1) * limit])
            
            # 构建计数SQL
            count_sql = """
            SELECT COUNT(*) as total FROM wxapp_post WHERE is_deleted = 0
            """
            
            # 添加筛选条件到计数查询
            count_params = []
            if category_id:
                count_sql += " AND category_id = %s"
                count_params.append(category_id)
            
            if tag:
                count_sql += " AND tag LIKE %s"
                count_params.append(f"%{tag}%")
                
            # 添加作者筛选到计数查询
            if openid and not favorite:  # 只有在非收藏模式下，openid才用作作者筛选
                count_sql += " AND openid = %s"
                count_params.append(openid)
        
        # 并行执行帖子查询和总数查询
        post_query = async_execute_custom_query(base_sql, params)
        count_query = async_execute_custom_query(count_sql, count_params)
        
        posts, count_result = await asyncio.gather(post_query, count_query)
        
        # 获取总记录数
        total = count_result[0]['total'] if count_result else 0
        
        # 计算总页数
        total_pages = (total + limit - 1) // limit if limit > 0 else 1
        
        # 构建标准分页信息
        pagination = {
            "total": total,
            "page": page,
            "page_size": limit,
            "total_pages": total_pages,
            "has_more": page < total_pages
        }
        
        # 为公开帖子补充用户信息
        if posts:
            # 收集所有公开帖子的openid
            public_post_openids = []
            for post in posts:
                if post.get("is_public", 1) == 1 and post.get("openid"):
                    # 如果帖子公开且有openid，加入查询列表
                    public_post_openids.append(post.get("openid"))
            
            # 如果有公开帖子，查询用户信息
            if public_post_openids:
                # 使用IN查询批量获取用户信息
                user_query = """
                SELECT openid, nickname, avatar, bio 
                FROM wxapp_user 
                WHERE openid IN %s
                """
                user_results = await async_execute_custom_query(
                    user_query, 
                    [tuple(public_post_openids)] if len(public_post_openids) > 1 else [(public_post_openids[0],)]
                )
                
                # 构建用户信息映射
                user_info_map = {}
                if user_results:
                    for user in user_results:
                        user_info_map[user.get("openid")] = user
                
                # 更新帖子信息
                for post in posts:
                    # 对公开帖子，补充用户信息
                    if post.get("is_public", 1) == 1 and post.get("openid") in user_info_map:
                        user_info = user_info_map.get(post.get("openid"))
                        # 如果数据库中的用户信息更新，覆盖帖子中的用户信息
                        post["nickname"] = user_info.get("nickname") or post.get("nickname", "")
                        post["avatar"] = user_info.get("avatar") or post.get("avatar", "")
                        post["bio"] = user_info.get("bio") or post.get("bio", "")
                        # 添加用户对象
                        post["user"] = user_info
                    elif post.get("is_public", 0) == 0:
                        # 非公开帖子处理：清除可能泄露用户信息的字段
                        post["nickname"] = "匿名用户"
                        post["avatar"] = ""
                        post["bio"] = ""
                        post["phone"] = None
                        post["wechatId"] = None
                        post["qqId"] = None
                        post["openid"] = ""  # 不暴露原始openid
                        # 添加匿名用户对象
                        post["user"] = {
                            "openid": "",
                            "nickname": "匿名用户",
                            "avatar": ""
                        }
            
            # 如果是收藏查询，添加收藏标记
            if favorite and openid:
                for post in posts:
                    post["is_favorited"] = True
        
        # 返回标准分页响应
        return Response.paged(
            data=posts,
            pagination=pagination,
            details={"message": "查询帖子列表成功"}
        )
    except Exception as e:
        logger.error(f"查询帖子列表异常: {str(e)}")
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
        if "phone" in req_data:
            update_data["phone"] = req_data["phone"]
        if "wechatId" in req_data:
            update_data["wechatId"] = req_data["wechatId"]
        if "qqId" in req_data:
            update_data["qqId"] = req_data["qqId"]
        if "allow_comment" in req_data:
            update_data["allow_comment"] = req_data["allow_comment"]
        if "is_public" in req_data:
            update_data["is_public"] = req_data["is_public"]
        if "location" in req_data:
            update_data["location"] = req_data["location"]
        
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
        fields = "id, title, content, image, tag, category_id, phone, wechatId, qqId, allow_comment, is_public, location, update_time"
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
        # 验证并规范排序字段
        ALLOWED_ORDERS = {"update_time", "create_time", "view_count", "like_count", "comment_count"}
        
        order_by_parts = order_by.split()
        if len(order_by_parts) != 2 or order_by_parts[0] not in ALLOWED_ORDERS or order_by_parts[1].upper() not in {"ASC", "DESC"}:
            order_by = "create_time DESC"
            
        # 构建基础SQL和条件
        base_sql = """
        SELECT 
            id, title, content, image, openid, nickname, avatar, bio, phone, wechatId, qqId,
            view_count, like_count, comment_count, favorite_count, allow_comment, is_public,
            create_time, update_time, tag, category_id, status
        FROM wxapp_post
        WHERE status = 1 AND is_deleted = 0 AND is_public = 1
        """
        
        params = []
        
        # 添加关键词筛选
        if keywords:
            base_sql += " AND (title LIKE %s OR content LIKE %s)"
            params.extend([f"%{keywords}%", f"%{keywords}%"])
        
        # 添加分类筛选
        if category_id:
            base_sql += " AND category_id = %s"
            params.append(category_id)
        
        # 添加点赞数范围筛选
        if min_likes is not None:
            base_sql += " AND like_count >= %s"
            params.append(min_likes)
            
        if max_likes is not None:
            base_sql += " AND like_count <= %s"
            params.append(max_likes)
        
        # 计数SQL
        count_sql = base_sql.replace("SELECT \n            id, title, content, image, openid, nickname, avatar, bio, \n            view_count, like_count, comment_count, favorite_count, \n            create_time, update_time, tag, category_id, status", "SELECT COUNT(*) as total")
        
        # 添加排序和分页
        base_sql += f" ORDER BY {order_by} LIMIT %s OFFSET %s"
        params.extend([limit, (page - 1) * limit])
        
        # 并行执行查询
        post_query = async_execute_custom_query(base_sql, params)
        count_query = async_execute_custom_query(count_sql, params[:-2])  # 移除分页参数
        
        posts, count_result = await asyncio.gather(post_query, count_query)
        
        # 获取总记录数
        total = count_result[0]['total'] if count_result else 0
        
        # 计算总页数
        total_pages = (total + limit - 1) // limit if limit > 0 else 1
        
        # 构建标准分页信息
        pagination = {
            "total": total,
            "page": page,
            "page_size": limit,
            "total_pages": total_pages,
            "has_more": page < total_pages
        }
        
        # 返回标准分页响应
        return Response.paged(
            data=posts,
            pagination=pagination,
            details={"message": "搜索帖子成功", "keywords": keywords}
        )
        
    except Exception as e:
        logger.error(f"搜索帖子异常: {str(e)}")
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
        SELECT 
            u.openid as author_openid 
        FROM 
            wxapp_action a
        JOIN 
            wxapp_user u ON a.target_id = u.id
        WHERE 
            a.openid = %s AND a.action_type = 'follow' AND a.target_type = 'user'
        """
        
        following_result = await async_execute_custom_query(following_sql, [openid])
        following_openids = set()
        if following_result:
            following_openids = {item['author_openid'] for item in following_result}
        
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