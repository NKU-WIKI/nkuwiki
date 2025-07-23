"""
微信小程序用户API接口
"""
from typing import List, Dict, Any, Optional
from fastapi import Query, APIRouter, Body, Depends
from api.models.common import Response, Request, validate_params, PaginationInfo
from etl.load import (
    query_records,
    insert_record,
    update_record,
    count_records,
    execute_custom_query
)
from config import Config
from core.utils.logger import register_logger
import time

from api.common.dependencies import get_current_active_user, get_current_active_user_optional

logger = register_logger('api.routes.wxapp.user')

config = Config()
router = APIRouter()
default_avatar = config.get("services.weapp.default.default_avatar")

@router.get("/profile", summary="获取用户公开信息")
async def get_user_profile(
    user_id: int = Query(..., description="要查询的用户ID"),
    current_user: Optional[Dict[str, Any]] = Depends(get_current_active_user_optional)
):
    """
    获取指定用户的公开信息，包括统计数据。
    如果提供了当前登录用户的JWT，还会返回关注状态。
    """
    try:
        user_result = await execute_custom_query(
            "SELECT * FROM wxapp_user WHERE id = %s", (user_id,)
        )
        if not user_result:
            return Response.not_found(resource="用户")
        user_data = user_result[0]

        # 为了安全，移除敏感信息
        sensitive_keys = ['phone', 'wechatId', 'qqId', 'openid', 'unionid']
        for key in sensitive_keys:
            user_data.pop(key, None)

        # 检查关注状态
        user_data['is_following'] = False
        if current_user and current_user['id'] != user_id:
            # 在 action 表中，操作的发起者是 user_id，被操作者是 target_id
            # 我关注别人，所以我的 id 是 user_id，别人的 id 是 target_id
            follow_action = await query_records(
                "wxapp_action",
                {
                    "user_id": current_user['id'], 
                    "target_id": user_id, 
                    "target_type": "user", 
                    "action_type": "follow"
                },
                limit=1
            )
            if follow_action and follow_action.get('data'):
                user_data['is_following'] = True

        return Response.success(data=user_data)
    except Exception as e:
        logger.error(f"获取用户信息失败: {e}")
        return Response.error(details={"message": f"获取用户信息失败: {str(e)}"})

@router.get("/my/profile", summary="获取当前登录用户的完整信息")
async def get_my_profile(
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    获取当前登录用户的完整个人信息，用于"我的"页面或编辑页。
    直接返回依赖注入的用户对象，无需额外查询。
    """
    return Response.success(data=current_user)

@router.post("/update", summary="更新用户信息")
async def update_user_profile(
    updates: Dict[str, Any] = Body(...),
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    更新当前登录用户的信息。
    """
    openid = current_user['openid']
    user_id = current_user['id']
    
    # 提取请求中的更新字段
    update_data = {}
    # 基本信息
    if "nickname" in updates:
        update_data["nickname"] = updates["nickname"]
    if "avatar" in updates:
        update_data["avatar"] = updates["avatar"] if updates["avatar"] else default_avatar
    if "gender" in updates:
        update_data["gender"] = updates["gender"]
    if "bio" in updates:
        update_data["bio"] = updates["bio"]
    if "country" in updates:
        update_data["country"] = updates["country"]
    if "province" in updates:
        update_data["province"] = updates["province"]
    if "city" in updates:
        update_data["city"] = updates["city"]
    if "language" in updates:
        update_data["language"] = updates["language"]
    if "birthday" in updates:
        update_data["birthday"] = updates["birthday"]
    if "wechatId" in updates:
        update_data["wechatId"] = updates["wechatId"]
    if "qqId" in updates:
        update_data["qqId"] = updates["qqId"]
    if "phone" in updates:
        update_data["phone"] = updates["phone"]
    if "university" in updates:
        update_data["university"] = updates["university"]
    if "status" in updates:
        update_data["status"] = updates["status"]
        
    if not update_data:
        return Response.bad_request(details={"message": "未提供任何更新数据"})

    try:
        await update_record(
            table_name="wxapp_user",
            conditions={"id": user_id},
            data=update_data
        )
    except Exception as err:
        # 添加详细的错误日志
        logger.error(f"用户信息更新SQL执行错误: {str(err)}")
        return Response.db_error(details={"message": f"用户信息更新失败: {str(err)}"})
        
    # 将更新应用到当前用户对象上，并返回最新的信息
    # 这样可以避免因数据库延迟或缓存导致返回旧数据
    current_user.update(update_data)
    
    return Response.success(data=current_user, details={"message":"用户信息更新成功"})


@router.get("/list", summary="获取用户列表")
async def get_user_list(
    page: int = 1,
    page_size: int = 10,
    nickname: Optional[str] = Query(None, description="按昵称搜索"),
    sort_by: str = Query("latest", description="排序方式: latest, popular"),
):
    """
    获取用户列表，支持分页、搜索和排序。
    """
    try:
        # 计算偏移量
        offset = (page - 1) * page_size
        
        # 只返回需要的字段
        fields = ["id", "openid", "nickname", "avatar", "bio", "create_time", "update_time", "role", "level"]
        users_result = await query_records(
            table_name="wxapp_user",
            fields=fields,
            limit=page_size,
            offset=offset,
            order_by={"create_time": "DESC"}
        )
        
        total_users = users_result.get('total', 0)
        pagination = PaginationInfo(
            total=total_users,
            page=page,
            page_size=page_size
        )

        return Response.paged(
            data=users_result.get('data', []),
            pagination=pagination,
            details={"message":"获取用户列表成功"}
        )
    except Exception as e:
        return Response.error(details={"message": f"获取用户列表失败: {str(e)}"})

@router.get("/followers", summary="获取指定用户的粉丝列表")
async def get_followers(
    user_id: int = Query(..., description="目标用户的ID"),
    page: int = 1,
    page_size: int = 10,
):
    """
    获取指定用户的粉丝列表。
    """
    # 1. 在action表中，我是被关注者(target_id)，粉丝是发起者(user_id)
    all_followers_actions = await query_records(
        "wxapp_action",
        conditions={
            "target_id": user_id,
            "action_type": "follow",
            "target_type": "user"
        },
        fields=["user_id", "create_time"],
        order_by={"create_time": "DESC"}
    )

    if not all_followers_actions or not all_followers_actions.get('data'):
        return Response.paged(data=[], pagination=PaginationInfo(
            total=0, page=page, page_size=page_size
        ))

    # 2. 计算总数并进行内存分页
    all_follower_actions_data = all_followers_actions['data']
    total = len(all_follower_actions_data)
    
    start_index = (page - 1) * page_size
    paginated_actions = all_follower_actions_data[start_index : start_index + page_size]
    paginated_follower_user_ids = [item['user_id'] for item in paginated_actions]

    if not paginated_follower_user_ids:
        return Response.paged(data=[], pagination=PaginationInfo(
            total=total, page=page, page_size=page_size
        ))

    # 3. 获取粉丝的详细信息
    followers_details = await query_records(
        "wxapp_user",
        conditions={"id": paginated_follower_user_ids},
        fields=["id", "nickname", "avatar", "bio"],
    )

    # 4. 组装响应
    pagination = PaginationInfo(
        total=total, page=page, page_size=page_size
    )
    return Response.paged(data=followers_details.get('data', []), pagination=pagination)


@router.get("/following", summary="获取指定用户的关注列表")
async def get_following(
    user_id: int = Query(..., description="目标用户的ID"),
    page: int = 1,
    page_size: int = 10,
):
    """
    获取指定用户正在关注的用户列表。
    """
    # 1. 在action表中，我是关注者(user_id)，我关注的人是被关注者(target_id)
    all_following_actions = await query_records(
        "wxapp_action",
        conditions={
            "user_id": user_id,
            "action_type": "follow",
            "target_type": "user"
        },
        fields=["target_id", "create_time"],
        order_by={"create_time": "DESC"}
    )
    
    if not all_following_actions or not all_following_actions.get('data'):
        return Response.paged(data=[], pagination=PaginationInfo(
            total=0, page=page, page_size=page_size
        ))
        
    # 2. 计算总数并进行内存分页
    all_following_actions_data = all_following_actions['data']
    total = len(all_following_actions_data)
    
    start_index = (page - 1) * page_size
    paginated_actions = all_following_actions_data[start_index : start_index + page_size]
    paginated_following_user_ids = [item['target_id'] for item in paginated_actions]

    if not paginated_following_user_ids:
        return Response.paged(data=[], pagination=PaginationInfo(
            total=total, page=page, page_size=page_size
        ))

    # 3. 获取关注用户的详细信息
    following_details = await query_records(
        "wxapp_user",
        conditions={"id": paginated_following_user_ids},
        fields=["id", "nickname", "avatar", "bio"],
    )

    # 4. 组装响应
    pagination = PaginationInfo(
        total=total, page=page, page_size=page_size
    )
    return Response.paged(data=following_details.get('data', []), pagination=pagination)


@router.get("/me/followers", summary="获取我的粉丝列表")
async def get_my_followers(
    current_user: Dict[str, Any] = Depends(get_current_active_user),
    page: int = 1,
    page_size: int = 10,
):
    """获取当前登录用户的粉丝列表。"""
    return await get_followers(user_id=current_user['id'], page=page, page_size=page_size)


@router.get("/me/following", summary="获取我的关注列表")
async def get_my_following(
    current_user: Dict[str, Any] = Depends(get_current_active_user),
    page: int = 1,
    page_size: int = 10,
):
    """获取当前登录用户正在关注的用户列表。"""
    return await get_following(user_id=current_user['id'], page=page, page_size=page_size)


@router.get("/favorite", summary="获取用户的收藏列表")
async def get_user_favorites(
    current_user: Dict[str, Any] = Depends(get_current_active_user),
    page: int = Query(1, description="页码"), 
    page_size: int = Query(10, description="每页数量")
):
    """
    获取当前用户收藏的所有内容。
    目前仅支持收藏的帖子(post)。
    """
    try:
        # 1. 直接从 wxapp_action 表中查找该用户所有收藏类型的动作
        favorite_actions_result = await query_records(
            table_name="wxapp_action",
            conditions={
                "user_id": current_user['id'],
                "action_type": "favorite"
            },
            order_by={"create_time": "DESC"},
            limit=page_size,
            offset=(page - 1) * page_size
        )
        
        favorite_actions = favorite_actions_result.get("data", [])
        total_favorites = favorite_actions_result.get("total", 0)

        if not favorite_actions:
            return Response.paged(data=[], pagination=PaginationInfo(total=0, page=page, page_size=page_size))
            
        # 2. 根据target_type和target_id分类，并提取ID
        post_ids = [action['target_id'] for action in favorite_actions if action['target_type'] == 'post']
        
        # 3. 批量获取收藏的帖子详情
        favorites_list = []
        if post_ids:
            placeholders = ', '.join(['%s'] * len(post_ids))
            posts_query = f"""
            SELECT p.id, p.title, p.content, p.image, p.create_time, 
                   u.nickname as author_nickname, u.avatar as author_avatar
            FROM wxapp_post p
            LEFT JOIN wxapp_user u ON p.user_id = u.id
            WHERE p.id IN ({placeholders}) AND p.is_deleted = 0
            """
            # 注意：这里可能需要处理id顺序问题，以保持收藏时间倒序
            posts = await execute_custom_query(posts_query, post_ids)
            
            # 转换数据格式以匹配通用响应
            for post in posts:
                favorites_list.append({
                    "type": "post",
                    **post
                })

        # 4. 获取总收藏数用于分页
        # total_favorites = await count_records(
        #     "wxapp_action",
        #     conditions={"openid": openid, "action_type": "favorite"}
        # )
        
        pagination = PaginationInfo(total=total_favorites, page=page, page_size=page_size)
        
        return Response.paged(data=favorites_list, pagination=pagination)
    except Exception as e:
        logger.error(f"获取用户收藏列表失败: {e}")
        return Response.error(details={"message": f"获取用户收藏列表失败: {str(e)}"})


@router.get("/like")
async def get_user_likes(
    current_user: Dict[str, Any] = Depends(get_current_active_user),
    page: int = Query(1, description="页码"),
    page_size: int = Query(10, description="每页数量")
):
    """获取当前用户点赞过的内容，目前只支持帖子"""
    openid = current_user['openid']
    offset = (page - 1) * page_size
    
    # 1. 连表查询，直接获取点赞帖子的信息
    liked_posts_query = """
    SELECT p.id, p.title, p.content, p.image, p.create_time,
           u.nickname as author_nickname, u.avatar as author_avatar
    FROM wxapp_action a
    JOIN wxapp_post p ON a.target_id = p.id
    LEFT JOIN wxapp_user u ON p.openid = u.openid
    WHERE a.openid = %s AND a.action_type = 'like' AND a.target_type = 'post' AND p.is_deleted = 0
    ORDER BY a.create_time DESC
    LIMIT %s OFFSET %s
    """
    liked_posts = await execute_custom_query(liked_posts_query, [openid, page_size, offset])

    # 2. 获取总点赞数用于分页
    total_likes = await count_records(
        "wxapp_action",
        conditions={"openid": openid, "action_type": "like", "target_type": "post"}
    )
    
    pagination = PaginationInfo(total=total_likes, page=page, page_size=page_size)
    
    # 格式化数据
    data = [{"type": "post", **post} for post in liked_posts]
    
    return Response.paged(data=data, pagination=pagination)

@router.get("/comment")
async def get_user_comments(
    current_user: Dict[str, Any] = Depends(get_current_active_user),
    page: int = Query(1, description="页码"),
    page_size: int = Query(10, description="每页数量")
):
    """获取当前用户发布的所有评论"""
    openid = current_user['openid']
    offset = (page - 1) * page_size
    
    # 连表查询，获取评论及其关联帖子的标题
    comments_query = """
    SELECT c.*, p.title as post_title
    FROM wxapp_comment c
    LEFT JOIN wxapp_post p ON c.resource_id = p.id AND c.resource_type = 'post'
    WHERE c.openid = %s AND c.is_deleted = 0
    ORDER BY c.create_time DESC
    LIMIT %s OFFSET %s
    """
    comments = await execute_custom_query(comments_query, [openid, page_size, offset])
    
    # 获取总评论数
    total_comments = await count_records(
        "wxapp_comment",
        conditions={"openid": openid, "is_deleted": 0}
    )
    
    pagination = PaginationInfo(total=total_comments, page=page, page_size=page_size)
    
    return Response.paged(data=comments, pagination=pagination)


@router.post("/sync", summary="同步用户信息(兼容旧版,已废弃)")
async def sync_user_info(req: Request):
    """
    兼容旧版接口，登录逻辑已迁移至 /login
    """
    return Response.error(
        status_code=410, 
        message="此接口已废弃", 
        details={"message": "请使用POST /api/wxapp/auth/login接口进行登录和同步"}
    )


@router.get("/status", summary="获取用户关系状态")
async def get_user_status(
    target_user_id: int = Query(..., description="目标用户ID"),
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    获取当前登录用户与目标用户的关系状态（是否互相关注等）
    """
    current_user_id = current_user['id']

    if target_user_id == current_user_id:
        return Response.success(data={"is_following": False, "is_followed_by": False, "is_self": True})

    # 1. 检查我是否关注了目标用户 (is_following)
    following_action = await query_records(
        "wxapp_action",
        conditions={
            "user_id": current_user_id,
            "target_id": target_user_id,
            "target_type": "user",
            "action_type": "follow"
        },
        limit=1
    )
    is_following = bool(following_action and following_action.get('data'))

    # 2. 检查目标用户是否关注了我 (is_followed_by)
    followed_by_action = await query_records(
        "wxapp_action",
        conditions={
            "user_id": target_user_id,
            "target_id": current_user_id,
            "target_type": "user",
            "action_type": "follow"
        },
        limit=1
    )
    is_followed_by = bool(followed_by_action and followed_by_action.get('data'))

    return Response.success(data={
        "is_following": is_following,
        "is_followed_by": is_followed_by,
        "is_self": False
    })

