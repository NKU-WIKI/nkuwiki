"""
帖子相关API接口
处理帖子创建、查询、更新、删除、点赞、收藏等功能
"""
import time
import json
from typing import Dict, Any, Optional, List
from fastapi import Query, APIRouter, Depends, Body, Request
import asyncio
import re

from api.models.common import Response, Request, validate_params, PaginationInfo
from etl.load import (
    query_records, 
    insert_record, 
    update_record, 
    execute_custom_query, 
    count_records,
    get_by_id
)
from config import Config
from core.utils.logger import register_logger
from ._utils import batch_enrich_posts_with_user_info

# 获取配置
config = Config()
router = APIRouter()
logger = register_logger('api.routes.wxapp.post')

def sanitize_input(text):
    """清理可能包含SQL注入的文本输入"""
    if text is None:
        return None
        
    # 过滤常见的SQL注入模式
    sql_patterns = [
        "union select", 
        "--",
        "1=1",
        "drop table",
        "delete from",
        "insert into",
        "select *",
        "select 1",
        "sleep(",
        "benchmark(",
        "md5(",
        "or 1=1",
        "' or '",
        "\" or \"",
        ";--",
        ";#",
        "/*",
        "*/",
        "@@"
    ]
    
    result = str(text)
    for pattern in sql_patterns:
        # 使用简单的替换而不是完全移除，以保留文本的基本含义
        result = result.replace(pattern, "")
    
    return result

@router.post("/create", summary="创建新帖子")
async def create_post(
    post_data: Dict[str, Any] = Body(...)
):
    """创建帖子"""
    try:
        # 获取请求数据
        req_data = post_data
        
        # 定义必须的参数
        required_params = ["openid", "title", "content"]
        
        # 验证必要参数
        error_response = validate_params(req_data, required_params)
        if(error_response):
            return error_response
        
        # 清理和过滤输入，防止SQL注入
        title = sanitize_input(req_data.get("title"))
        content = sanitize_input(req_data.get("content"))
        
        # 如果标题或内容为空，返回错误
        if not title or not content:
            return Response.invalid_params(details={"message": "标题或内容不能为空"})
        
        try:
            # 尝试将category_id转换为整数，如果失败则使用默认值1
            category_id = int(req_data.get("category_id", 1))
        except (ValueError, TypeError):
            category_id = 1
            
        db_post_data = {
            "openid": req_data.get("openid"),
            "nickname": req_data.get("nickname", ""),
            "avatar": req_data.get("avatar", ""),
            "bio": req_data.get("bio", ""),
            "category_id": category_id,
            "title": title,
            "content": content,
            "is_deleted": 0,
            "allow_comment": 1 if req_data.get("allow_comment") in [1, "1", True, "true", "True"] else 0,
            "is_public": 1 if req_data.get("is_public") in [1, "1", True, "true", "True"] else 0
        }
        
        # 处理可选联系方式字段
        if "phone" in req_data:
            db_post_data["phone"] = req_data.get("phone")
        if "wechatId" in req_data:
            db_post_data["wechatId"] = req_data.get("wechatId")
        if "qqId" in req_data:
            db_post_data["qqId"] = req_data.get("qqId")
        
        # 处理需要JSON序列化的可选字段
        if "image" in req_data and isinstance(req_data["image"], list):
            db_post_data["image"] = json.dumps(req_data["image"], ensure_ascii=False)
        if "tag" in req_data and isinstance(req_data["tag"], list):
            db_post_data["tag"] = json.dumps(req_data["tag"], ensure_ascii=False)
        if "location" in req_data and isinstance(req_data["location"], dict):
            db_post_data["location"] = json.dumps(req_data["location"], ensure_ascii=False)
        
        # 创建帖子和更新用户发帖数并行执行
        post_insert = insert_record("wxapp_post", db_post_data)
        user_update = execute_custom_query(
            "UPDATE wxapp_user SET post_count = post_count + 1 WHERE openid = %s",
            [req_data.get("openid")],
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

@router.get("/detail", summary="获取帖子详情")
async def get_post_detail(
    post_id: int,
    openid: Optional[str] = Query(None)
):
    """获取帖子详情，包括作者信息和当前用户的互动状态"""
    post_query = "SELECT * FROM wxapp_post WHERE id = %s AND is_deleted = 0"
    post_data = await execute_custom_query(post_query, [post_id], fetch='one')
    
    if not post_data:
        return Response.error(message="帖子不存在或已被删除")
        
    # 增加浏览量
    await execute_custom_query("UPDATE wxapp_post SET view_count = view_count + 1 WHERE id = %s", [post_id], fetch=False)
    
    post = dict(post_data)
    post['view_count'] += 1
    
    # 获取作者信息
    author_openid = post.get('openid')
    if author_openid:
        user_data = await execute_custom_query(
            "SELECT openid, nickname, avatar, bio, post_count, follower_count, following_count FROM wxapp_user WHERE openid = %s",
            [author_openid], 
            fetch='one'
        )
        if user_data:
            post.update(user_data) # 合并用户信息到post字典
    else:
        # 即使没有作者信息，也初始化一些空字段以保证前端结构一致
        post.update({
            'openid': None,
            'nickname': '匿名用户',
            'avatar': '',
            'bio': ''
        })

    # 如果提供了当前用户openid，查询互动状态
    if openid and author_openid:
        actions_task = query_records(
            "wxapp_action",
            {"openid": openid, "target_id": post_id, "target_type": "post"},
            fields=['action_type']
        )
        follow_action_task = query_records(
            "wxapp_action",
            {"openid": openid, "target_id": author_openid, "target_type": "user", "action_type": "follow"},
            limit=1
        )
        actions_result, follow_action_result = await asyncio.gather(actions_task, follow_action_task)
        
        action_types = {action['action_type'] for action in actions_result.get('data', [])}
        post['is_liked'] = 'like' in action_types
        post['is_favorited'] = 'favorite' in action_types
        post['is_following_author'] = len(follow_action_result.get('data', [])) > 0
    else:
        post['is_liked'] = False
        post['is_favorited'] = False
        post['is_following_author'] = False

    return Response.success(data=post)

@router.get("/list", summary="获取帖子列表")
async def get_posts(
    page: int = 1,
    page_size: int = 10,
    category_id: Optional[int] = Query(None),
    sort_by: str = Query("latest", description="排序方式: latest, popular"),
    favorite: bool = Query(False, description="是否只看收藏"),
    following: bool = Query(False, description="是否只看关注"),
    openid: Optional[str] = Query(None) # 改为可选的查询参数
):
    """获取帖子列表，支持分类、排序、收藏、关注等筛选"""
    base_query = "FROM wxapp_post p"
    select_query = "SELECT p.* "
    
    conditions = ["p.is_deleted = 0"]
    params = []
    joins = ""

    # 处理筛选条件
    if category_id:
        conditions.append("p.category_id = %s")
        params.append(category_id)
            
    if favorite:
        if not openid:
            return Response.bad_request(details={"message": "查看收藏帖子需要提供openid"})
        joins += " JOIN wxapp_action a ON p.id = a.target_id"
        conditions.append("a.openid = %s AND a.target_type = 'post' AND a.action_type = 'favorite'")
        params.append(openid)
            
    if following:
        if not openid:
            return Response.bad_request(details={"message": "查看关注帖子需要提供openid"})
        following_actions = await query_records(
            "wxapp_action",
            {"openid": openid, "target_type": "user", "action_type": "follow"},
            fields=['target_id']
        )
        followed_openids = [action['target_id'] for action in following_actions.get('data', [])]

        if not followed_openids:
            return Response.paged(data=[], pagination=PaginationInfo(
                total=0, page=page, page_size=page_size
            ))
        
        placeholders = ', '.join(['%s'] * len(followed_openids))
        conditions.append(f"p.openid IN ({placeholders})")
        params.extend(followed_openids)

    where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""
    
    # 排序
    order_clause = " ORDER BY p.like_count DESC, p.view_count DESC" if sort_by == 'popular' else " ORDER BY p.create_time DESC"
    
    # 分页
    limit_clause = " LIMIT %s OFFSET %s"
    offset = (page - 1) * page_size
    
    # 构造完整查询
    full_query = select_query + base_query + joins + where_clause + order_clause + limit_clause
    count_query = "SELECT COUNT(p.id) as total " + base_query + joins + where_clause

    # 执行查询
    try:
        count_result = await execute_custom_query(count_query, params, fetch='one')
        total = count_result['total'] if count_result else 0

        if total == 0:
            return Response.paged(data=[], pagination=PaginationInfo(
                total=0, page=page, page_size=page_size
            ))

        posts_data = await execute_custom_query(full_query, params + [page_size, offset], fetch='all')
        
        # 批量数据增强
        enriched_posts = await batch_enrich_posts_with_user_info(posts_data, openid)
        
        # 使用最新的用户信息覆盖帖子顶层的过时信息
        for post in enriched_posts:
            user_info = post.get("user_info")
            if user_info:
                post["nickname"] = user_info.get("nickname", post.get("nickname"))
                post["avatar"] = user_info.get("avatar", post.get("avatar"))

        pagination = PaginationInfo(
            total=total,
            page=page,
            page_size=page_size
        )
        return Response.paged(data=enriched_posts, pagination=pagination)
    except Exception as e:
        logger.error(f"获取帖子列表失败: {e}")
        return Response.error(details=f"数据库查询异常: {e}")

@router.post("/update", summary="更新帖子")
async def update_post(
    post_data: Dict[str, Any] = Body(...)
):
    """更新帖子信息"""
    try:
        req_data = post_data
        required_params = ["post_id", "openid"]
        error_response = validate_params(req_data, required_params)
        if(error_response):
            return error_response
            
        post_id = req_data.get("post_id")
        openid = req_data.get("openid")
        
        if not post_id or not openid:
            return Response.invalid_params(details={"message": "post_id和openid是必需的"})
        
        # 验证帖子是否存在且属于该用户
        post_check = await get_by_id("wxapp_post", post_id)
        if not post_check or post_check['openid'] != openid:
            return Response.forbidden(details={"message": "无权修改该帖子"})
        
        # 提取更新字段
        update_data = {}
        
        if "title" in req_data:
            update_data["title"] = sanitize_input(req_data["title"])
        if "content" in req_data:
            update_data["content"] = sanitize_input(req_data["content"])
        if "image" in req_data and isinstance(req_data["image"], list):
            update_data["image"] = json.dumps(req_data["image"], ensure_ascii=False)
        if "category_id" in req_data:
            try:
                update_data["category_id"] = int(req_data["category_id"])
            except (ValueError, TypeError):
                update_data["category_id"] = 1
        if "tag" in req_data and isinstance(req_data["tag"], list):
            update_data["tag"] = json.dumps(req_data["tag"], ensure_ascii=False)
        if "phone" in req_data:
            update_data["phone"] = req_data["phone"]
        if "wechatId" in req_data:
            update_data["wechatId"] = req_data["wechatId"]
        if "qqId" in req_data:
            update_data["qqId"] = req_data["qqId"]
        if "allow_comment" in req_data:
            update_data["allow_comment"] = 1 if req_data["allow_comment"] in [1, "1", True, "true", "True"] else 0
        if "is_public" in req_data:
            update_data["is_public"] = 1 if req_data["is_public"] in [1, "1", True, "true", "True"] else 0
        if "location" in req_data and isinstance(req_data["location"], dict):
            update_data["location"] = json.dumps(req_data["location"], ensure_ascii=False)
        if "url_link" in req_data:
            update_data["url_link"] = req_data["url_link"]
        
        if not update_data:
            return Response.bad_request(details={"message": "未提供任何更新数据"})
            
        # 更新帖子
        update_success = update_record(
            "wxapp_post",
            post_id,
            update_data
        )
        
        if not update_success:
            return Response.db_error(details={"message": "更新帖子失败"})
        
        # 直接使用SQL获取更新后的帖子
        fields = "id, title, content, image, tag, category_id, phone, wechatId, qqId, allow_comment, is_public, location, update_time"
        updated_post = await execute_custom_query(
            f"SELECT {fields} FROM wxapp_post WHERE id = %s LIMIT 1",
            [post_id]
        )
        
        if not updated_post:
            return Response.db_error(details={"message": "更新帖子失败"})

        # 获取完整帖子信息以返回
        post_detail = await get_post_with_stats(post_id)
        return Response.success(data=post_detail, details={"message": "帖子更新成功"})
    except Exception as e:
        return Response.error(details={"message": f"更新帖子失败: {str(e)}"})

@router.post("/delete", summary="删除帖子")
async def delete_post(
    body: Dict[str, Any] = Body(...)
):
    """删除帖子"""
    try:
        # 查询当前操作用户的角色
        user_info = await execute_custom_query(
            "SELECT role FROM wxapp_user WHERE openid = %s LIMIT 1",
            [body.get("openid")]
        )
        user_role = user_info[0]["role"] if user_info and user_info[0] else None

        # 先查询帖子是否存在
        post_query = f"SELECT id, openid FROM wxapp_post WHERE id = %s AND is_deleted = 0"
        post_result = await execute_custom_query(post_query, [body.get("post_id")])
        if not post_result:
            return Response.not_found(resource="帖子")
        post_owner = post_result[0]["openid"]

        # 只有admin可以无视openid，普通用户只能删除自己帖子
        if user_role != "admin" and post_owner != body.get("openid"):
            return Response.forbidden(details={"message": "只有帖子作者才能删除帖子"})
        
        # 逻辑删除帖子，同时减少用户的发帖数
        # 并发执行两个SQL操作
        delete_post_query = execute_custom_query(
            "UPDATE wxapp_post SET is_deleted = 1, status = 0, update_time = NOW() WHERE id = %s",
            [body.get("post_id")],
            fetch=False
        )
        update_user_query = execute_custom_query(
            "UPDATE wxapp_user SET post_count = GREATEST(post_count - 1, 0) WHERE openid = %s",
            [post_owner],
            fetch=False
        )
        await asyncio.gather(delete_post_query, update_user_query)
        
        return Response.success(details={"message": "删除帖子成功"})
    except Exception as e:
        return Response.error(details={"message": f"删除帖子失败: {str(e)}"})

@router.get("/search")
async def search_posts(
    request: Request,
    keywords: Optional[str] = Query(None, description="搜索关键词"),
    category_id: Optional[int] = Query(None, description="分类ID"),
    min_likes: Optional[int] = Query(None, description="最小点赞数"),
    max_likes: Optional[int] = Query(None, description="最大点赞数"),
    page: int = Query(1, description="页码"),
    limit: int = Query(10, description="每页数量"),
    order_by: str = Query("create_time DESC", description="排序方式"),
    favorite: bool = Query(False, description="是否只看收藏"),
    following: bool = Query(False, description="是否只看关注"),
    openid: Optional[str] = Query(None, description="当前用户OpenID，用于查询收藏和关注")
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
        
        # 使用正则表达式替换SELECT子句，更健壮
        count_sql = re.sub(r"SELECT .*? FROM", "SELECT COUNT(*) as total FROM", base_sql, flags=re.IGNORECASE | re.DOTALL)
        
        # 添加排序和分页
        base_sql += f" ORDER BY {order_by} LIMIT %s OFFSET %s"
        params.extend([limit, (page - 1) * limit])
        
        # 并行执行查询
        post_query_coro = execute_custom_query(base_sql, params)
        count_query_coro = execute_custom_query(count_sql, params[:-2])  # 移除分页参数
        
        posts, count_result = await asyncio.gather(post_query_coro, count_query_coro)
        
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
                # 动态生成占位符
                user_placeholders = ', '.join(['%s'] * len(public_post_openids))
                # 使用IN查询批量获取用户信息
                user_query = f"""
                SELECT openid, nickname, avatar, bio 
                FROM wxapp_user 
                WHERE openid IN ({user_placeholders})
                """
                user_results = await execute_custom_query(
                    user_query, 
                    public_post_openids
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

# 使用并行查询优化
async def get_post_with_stats(post_id):
    """获取帖子和统计信息"""
    try:
        # 获取帖子
        post_result = query_records(
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

@router.get("/status")
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
            MAX(CASE WHEN a.action_type = 'favorite' THEN 1 ELSE 0 END) AS is_favorited,
            MAX(CASE WHEN c.id IS NOT NULL THEN 1 ELSE 0 END) AS is_commented
        FROM 
            wxapp_post p
        LEFT JOIN 
            wxapp_action a ON p.id = a.target_id AND a.openid = %s AND a.target_type = 'post'
        LEFT JOIN 
            wxapp_comment c ON c.resource_id = p.id AND c.resource_type = 'post' AND c.openid = %s AND c.is_deleted = 0
        WHERE 
            p.id IN %s
        GROUP BY 
            p.id, p.openid, p.like_count, p.favorite_count, p.comment_count, p.view_count
        """
        
        # 执行联合查询
        posts_with_actions = await execute_custom_query(
            status_sql,
            [openid, openid, openid, tuple(post_ids)]
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
        
        following_result = await execute_custom_query(following_sql, [openid])
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
                        "is_commented": bool(post.get("is_commented")),
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
                    "is_commented": False,
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