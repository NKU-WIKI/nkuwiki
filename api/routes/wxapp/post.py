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
from api.common.dependencies import get_current_active_user, get_current_active_user_optional

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
    post_data: Dict[str, Any] = Body(...),
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """创建帖子"""
    try:
        # 获取请求数据
        req_data = post_data
        user_id = current_user['id']
        
        # 定义必须的参数
        required_params = ["title", "content"]
        
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
            "user_id": user_id,
            "nickname": current_user.get("nickname", "微信用户"),
            "avatar": current_user.get("avatar", ""),
            "bio": current_user.get("bio", ""),
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
            "UPDATE wxapp_user SET post_count = post_count + 1 WHERE id = %s",
            [user_id],
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
    current_user: Optional[Dict[str, Any]] = Depends(get_current_active_user_optional)
):
    """获取帖子详情，包括作者信息和当前用户的互动状态"""
    post_query = "SELECT * FROM wxapp_post WHERE id = %s AND is_deleted = 0"
    post_data = await execute_custom_query(post_query, [post_id], fetch='one')
    
    if not post_data:
        return Response.not_found(resource="帖子")
        
    # 增加浏览量
    await execute_custom_query("UPDATE wxapp_post SET view_count = view_count + 1 WHERE id = %s", [post_id], fetch=False)
    
    post = dict(post_data)
    post['view_count'] += 1
    
    # 解析JSON字符串字段
    for field in ['image', 'tag', 'location']:
        if isinstance(post.get(field), str):
            try:
                post[field] = json.loads(post[field])
            except json.JSONDecodeError:
                post[field] = None # or some default value
    
    # 获取作者信息
    author_id = post.get('user_id')
    if author_id:
        user_data = await execute_custom_query(
            "SELECT id, nickname, avatar, bio, post_count, follower_count, following_count, level FROM wxapp_user WHERE id = %s",
            [author_id], 
            fetch='one'
        )
        post['author_info'] = user_data if user_data else {}
    else:
        post['author_info'] = {
            'id': None,
            'nickname': '匿名用户',
            'avatar': '',
            'bio': '',
            'level': 0
        }

    # 如果提供了当前用户，查询互动状态
    if current_user:
        current_user_id = current_user['id']
        actions_task = query_records(
            "wxapp_action",
            {"user_id": current_user_id, "target_id": post_id, "target_type": "post"},
            fields=['action_type']
        )
        follow_action_task = query_records(
            "wxapp_action",
            {"user_id": current_user_id, "target_id": author_id, "target_type": "user", "action_type": "follow"},
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

    # 移除顶层冗余的用户信息和敏感信息
    for key in ['openid', 'nickname', 'avatar', 'bio', 'post_count', 'follower_count', 'following_count']:
        post.pop(key, None)

    return Response.success(data=post)

@router.get("/list", summary="获取帖子列表")
async def get_posts(
    page: int = 1,
    page_size: int = 10,
    category_id: Optional[int] = Query(None),
    sort_by: str = Query("latest", description="排序方式: latest, popular"),
    favorite: bool = Query(False, description="是否只看收藏"),
    following: bool = Query(False, description="是否只看关注"),
    current_user: Optional[Dict[str, Any]] = Depends(get_current_active_user_optional)
):
    """获取帖子列表，支持分类、排序、收藏、关注等筛选"""
    user_id = current_user['id'] if current_user else None
    
    # 基础查询
    conditions = {"is_deleted": 0}
    if category_id:
        conditions["category_id"] = category_id

    # 排序逻辑
    order_by = {"create_time": "DESC"}
    if sort_by == "popular":
        order_by = {"view_count": "DESC", "like_count": "DESC"}

    # TODO: favorite 和 following 的逻辑需要更复杂的JOIN查询，暂时简化
    
    # 获取帖子总数
    total_result = await count_records("wxapp_post", conditions=conditions)
    
    # 获取分页后的帖子数据
    posts_result = await query_records(
        "wxapp_post",
        conditions=conditions,
        fields=[
            "id", "user_id", "title", "content", "image", "tag", "location",
            "view_count", "like_count", "comment_count", "favorite_count",
            "create_time"
        ],
        order_by=order_by,
        limit=page_size,
        offset=(page - 1) * page_size
    )

    enriched_posts = await batch_enrich_posts_with_user_info(posts_result['data'], user_id)
    
    pagination = PaginationInfo(
        total=total_result,
        page=page,
        page_size=page_size
    )

    return Response.paged(data=enriched_posts, pagination=pagination)

@router.post("/update", summary="更新帖子")
async def update_post(
    post_data: Dict[str, Any] = Body(...),
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """更新帖子信息"""
    try:
        req_data = post_data
        user_id = current_user['id']
        
        if "id" not in req_data:
            return Response.invalid_params(details={"message": "缺少帖子ID"})
        
        if not req_data.get("id"):
            return Response.invalid_params(details={"message": "post_id是必需的"})
        
        # 获取帖子现有信息
        post_id = req_data.get("id")
        if not post_id:
            return Response.bad_request(details={"message": "缺少帖子ID"})

        # 检查帖子是否存在以及用户是否有权编辑
        post = await get_by_id("wxapp_post", post_id, fields=['user_id'])
        if not post:
            return Response.not_found(resource="帖子")

        if post.get("user_id") != user_id:
            return Response.forbidden(details={"message": "无权编辑此帖子"})

        # 清理和准备更新数据
        db_post_data = {}
        
        if "title" in req_data:
            db_post_data["title"] = sanitize_input(req_data["title"])
        if "content" in req_data:
            db_post_data["content"] = sanitize_input(req_data["content"])
        if "image" in req_data and isinstance(req_data["image"], list):
            db_post_data["image"] = json.dumps(req_data["image"], ensure_ascii=False)
        if "category_id" in req_data:
            try:
                db_post_data["category_id"] = int(req_data["category_id"])
            except (ValueError, TypeError):
                db_post_data["category_id"] = 1
        if "tag" in req_data and isinstance(req_data["tag"], list):
            db_post_data["tag"] = json.dumps(req_data["tag"], ensure_ascii=False)
        if "phone" in req_data:
            db_post_data["phone"] = req_data["phone"]
        if "wechatId" in req_data:
            db_post_data["wechatId"] = req_data["wechatId"]
        if "qqId" in req_data:
            db_post_data["qqId"] = req_data["qqId"]
        if "allow_comment" in req_data:
            db_post_data["allow_comment"] = 1 if req_data["allow_comment"] in [1, "1", True, "true", "True"] else 0
        if "is_public" in req_data:
            db_post_data["is_public"] = 1 if req_data["is_public"] in [1, "1", True, "true", "True"] else 0
        if "location" in req_data and isinstance(req_data["location"], dict):
            db_post_data["location"] = json.dumps(req_data["location"], ensure_ascii=False)
        if "url_link" in req_data:
            db_post_data["url_link"] = req_data["url_link"]
        
        if not db_post_data:
            return Response.bad_request(details={"message": "未提供任何更新数据"})
            
        # 更新帖子
        update_success = await update_record(
            "wxapp_post",
            {"id": post_id},
            db_post_data
        )
        
        if not update_success:
            return Response.db_error(details={"message": "更新帖子失败"})
        
        # 获取完整帖子信息以返回
        post_detail = await get_post_with_stats(post_id)
        return Response.success(data=post_detail, details={"message": "帖子更新成功"})
    except Exception as e:
        logger.error(f"更新帖子失败: {e}", exc_info=True)
        return Response.error(details={"message": f"更新帖子失败: {str(e)}"})

@router.post("/delete", summary="删除帖子")
async def delete_post(
    body: Dict[str, Any] = Body(...),
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """删除帖子"""
    try:
        req_data = body
        user_id = current_user['id']
        
        # 验证请求参数
        if 'id' not in req_data:
            return Response.invalid_params(details={"message": "缺少帖子ID"})
            
        # 验证操作权限
        post_id = req_data.get("id")
        if not post_id:
            return Response.bad_request(details={"message": "缺少帖子ID"})

        # 检查帖子是否存在以及用户是否有权删除
        post = await get_by_id("wxapp_post", post_id, fields=['user_id'])
        if not post:
            return Response.not_found(resource="帖子")

        if post.get("user_id") != user_id and current_user.get("role") != 'admin':
            return Response.forbidden(details={"message": "无权删除此帖子"})

        # 逻辑删除帖子
        update_result = await update_record(
            "wxapp_post",
            {"id": post_id},
            {"is_deleted": 1}
        )
        
        if not update_result:
            return Response.db_error(details={"message": "删除帖子失败"})
        
        # 逻辑删除帖子，同时减少用户的发帖数
        # 并发执行两个SQL操作
        delete_post_query = execute_custom_query(
            "UPDATE wxapp_post SET is_deleted = 1, status = 0, update_time = NOW() WHERE id = %s",
            [post_id],
            fetch=False
        )
        update_user_query = execute_custom_query(
            "UPDATE wxapp_user SET post_count = GREATEST(post_count - 1, 0) WHERE id = %s",
            [post.get("user_id")],
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
    current_user: Optional[Dict[str, Any]] = Depends(get_current_active_user_optional)
):
    """根据关键词等条件搜索帖子"""
    offset = (page - 1) * limit
    
    # 基础查询
    base_query = "FROM wxapp_post WHERE is_deleted = 0"
    conditions = []
    params = []
    
    if keywords:
        conditions.append("(title LIKE %s OR content LIKE %s)")
        params.extend([f"%{keywords}%", f"%{keywords}%"])
        
    if category_id:
        conditions.append("category_id = %s")
        params.append(category_id)
        
    if min_likes is not None:
        conditions.append("like_count >= %s")
        params.append(min_likes)
    
    if max_likes is not None:
        conditions.append("like_count <= %s")
        params.append(max_likes)

    # 拼接WHERE子句
    if conditions:
        base_query += " AND " + " AND ".join(conditions)

    # 获取总数
    total_query = f"SELECT COUNT(*) as total {base_query}"
    total_result = await execute_custom_query(total_query, params, fetch='one')
    total = total_result['total'] if total_result else 0
    
    # 获取数据
    data_query = f"SELECT * {base_query} ORDER BY {order_by} LIMIT %s OFFSET %s"
    posts = await execute_custom_query(data_query, params + [limit, offset])

    # 丰富帖子信息
    user_id = current_user['id'] if current_user else None
    enriched_posts = await batch_enrich_posts_with_user_info(posts, user_id)
    
    pagination = PaginationInfo(total=total, page=page, page_size=limit)

    return Response.paged(data=enriched_posts, pagination=pagination, details={"message":"查询帖子列表成功"})


# 使用并行查询优化
async def get_post_with_stats(post_id):
    """获取帖子和统计信息"""
    try:
        # 获取帖子
        post_result = await query_records(
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
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """获取帖子的状态，如点赞、收藏等"""
    raw_ids = post_id.split(',')
    post_ids = [int(pid) for pid in raw_ids if pid.isdigit()]
    
    if not post_ids:
        return Response.bad_request(details={"message": "无效的帖子ID"})

    user_id = current_user['id']
    
    # 使用单一查询获取所有互动状态
    placeholders = ','.join(['%s'] * len(post_ids))
    sql = f"""
    SELECT target_id, action_type
    FROM wxapp_action
    WHERE user_id = %s AND target_type = 'post' AND target_id IN ({placeholders})
    """
    actions = await execute_custom_query(sql, [user_id] + post_ids)
    
    # 将结果组织成方便查找的字典
    actions_map = {}
    for action in actions:
        pid = action['target_id']
        if pid not in actions_map:
            actions_map[pid] = set()
        actions_map[pid].add(action['action_type'])
    
    # 构建最终的响应数据
    result = {}
    for pid in post_ids:
        result[str(pid)] = {
            "is_liked": 'like' in actions_map.get(pid, set()),
            "is_favorited": 'favorite' in actions_map.get(pid, set())
        }
        
    return Response.success(data=result)