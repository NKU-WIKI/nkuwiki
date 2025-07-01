"""
微信小程序用户API接口
"""
from typing import List, Dict, Any, Optional
from fastapi import Query, APIRouter, Body
from api.models.common import Response, Request, validate_params, PaginationInfo
from etl.load import (
    query_records,
    get_by_id,
    insert_record,
    update_record,
    count_records,
    execute_custom_query
)
from config import Config
from core.utils.logger import register_logger
import time

logger = register_logger('api.routes.wxapp.user')

config = Config()
router = APIRouter()
default_avatar = config.get("services.app.default.default_avatar")

@router.get("/profile", summary="获取用户公开信息")
async def get_user_profile(
    openid: str = Query(..., description="要查询的用户openid"),
    current_openid: Optional[str] = Query(None, description="当前登录用户的openid，用于查询关注状态")
):
    """
    获取指定用户的公开信息，包括统计数据。
    如果提供了当前登录用户的openid，还会返回关注状态。
    """
    if not openid:
        return Response.bad_request(details={"message": "缺少openid参数"})
    try:
        # 使用自定义SQL直接查询指定openid的用户
        user_data = await execute_custom_query(
            "SELECT * FROM wxapp_user WHERE openid = %s LIMIT 1",
            [openid]
        )

        if not user_data:
            return Response.not_found(resource="用户")

        # 确保返回包含role字段
        user = user_data[0]
        if "role" not in user:
            user["role"] = None
        return Response.success(data=user)
    except Exception as e:
        return Response.error(details={"message": f"获取用户信息失败: {str(e)}"})

@router.get("/my/profile", summary="获取当前登录用户的完整信息")
async def get_my_profile(
    openid: str = Query(..., description="当前登录用户的openid")
):
    """
    获取当前登录用户的完整个人信息，用于"我的"页面或编辑页。
    """
    if not openid:
        return Response.bad_request(details={"message": "缺少openid参数"})
    try:
        # 使用自定义SQL直接查询指定openid的用户
        user_data = await execute_custom_query(
            "SELECT * FROM wxapp_user WHERE openid = %s LIMIT 1",
            [openid]
        )

        if not user_data:
            return Response.not_found(resource="用户")

        # 确保返回包含role字段
        user = user_data[0]
        if "role" not in user:
            user["role"] = None
        return Response.success(data=user)
    except Exception as e:
        return Response.error(details={"message": f"获取用户信息失败: {str(e)}"})

@router.post("/update", summary="更新用户信息")
async def update_user_profile(
    updates: Dict[str, Any] = Body(...)
):
    """
    更新当前登录用户的信息。
    """
    try:
        req_data = updates
        required_params = ["openid"]
        error_response = validate_params(req_data, required_params)
        if(error_response):
            return error_response

        # 使用单一SQL获取用户ID
        user_result = await execute_custom_query(
            "SELECT id FROM wxapp_user WHERE openid = %s LIMIT 1",
            [req_data["openid"]]
        )
        
        if not user_result:
            return Response.bad_request(details={"message": "用户不存在或openid无效"})
        
        user_id = user_result[0]['id']
        
        # 提取请求中的更新字段
        update_data = {}
        # 基本信息
        if "nickname" in req_data:
            update_data["nickname"] = req_data["nickname"]
        if "avatar" in req_data:
            update_data["avatar"] = req_data["avatar"] if req_data["avatar"] else default_avatar
        if "gender" in req_data:
            update_data["gender"] = req_data["gender"]
        if "bio" in req_data:
            update_data["bio"] = req_data["bio"]
        if "country" in req_data:
            update_data["country"] = req_data["country"]
        if "province" in req_data:
            update_data["province"] = req_data["province"]
        if "city" in req_data:
            update_data["city"] = req_data["city"]
        if "language" in req_data:
            update_data["language"] = req_data["language"]
        if "birthday" in req_data:
            update_data["birthday"] = req_data["birthday"]
        if "wechatId" in req_data:
            update_data["wechatId"] = req_data["wechatId"]
        if "qqId" in req_data:
            update_data["qqId"] = req_data["qqId"]
        if "phone" in req_data:
            update_data["phone"] = req_data["phone"]
        if "university" in req_data:
            update_data["university"] = req_data["university"]
        if "status" in req_data:
            update_data["status"] = req_data["status"]
            
        if not update_data:
            return Response.bad_request(details={"message": "未提供任何更新数据"})

        try:
            update_success = await update_record(
                table_name="wxapp_user",
                conditions={"id": user_id},
                data=update_data
            )
            
            # 此处修改判断逻辑，只有当明确返回False时才认为失败
            # 当数据无变化时，MySQL不会更新行，返回的affected rows为0
            # 但这种情况不应视为错误
            if update_success is False:  # 只有明确返回False时才视为失败
                return Response.db_error(details={"message": "用户信息更新失败"})
        except Exception as err:
            # 添加详细的错误日志
            logger.error(f"用户信息更新SQL执行错误: {str(err)}")
            return Response.db_error(details={"message": f"用户信息更新失败: {str(err)}"})
            
        # 获取更新后的用户信息，直接使用SQL查询
        query_fields = "id, openid, nickname, avatar, bio, gender, country, province, city, role"
        updated_user = await execute_custom_query(
            f"SELECT {query_fields} FROM wxapp_user WHERE id = %s LIMIT 1",
            [user_id]
        )
        
        if updated_user:
            return Response.success(data=updated_user[0], details={"message":"用户信息更新成功"})
        else:
            return Response.success(details={"message":"用户信息更新成功"})
    except Exception as e:
        return Response.error(details={"message": f"更新用户信息失败: {str(e)}"})

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
        fields = ["id", "openid", "nickname", "avatar", "bio", "create_time", "update_time", "role"]
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

@router.get("/follower", summary="获取粉丝列表")
async def get_followers(
    openid: str = Query(..., description="目标用户的openid"),
    page: int = 1,
    page_size: int = 10,
):
    """
    获取指定用户的粉丝列表。
    """
    # 1. 获取所有粉丝的 action 记录
    all_followers_actions = await query_records(
        "wxapp_action",
        conditions={
            "target_id": openid,
            "action_type": "follow",
            "target_type": "user"
        },
        fields=["openid", "create_time"],
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
    paginated_follower_openids = [item['openid'] for item in paginated_actions]

    if not paginated_follower_openids:
        # 这种情况通常在请求一个不存在的页码时发生
        return Response.paged(data=[], pagination=PaginationInfo(
            total=total, page=page, page_size=page_size
        ))

    # 3. 获取粉丝的详细信息
    followers_details = await query_records(
        "wxapp_user",
        conditions={"openid": paginated_follower_openids},
        fields=["openid", "nickname", "avatar", "bio"],
    )

    # 4. 组装响应
    pagination = PaginationInfo(
        total=total, page=page, page_size=page_size
    )
    return Response.paged(data=followers_details.get('data', []), pagination=pagination)

@router.get("/following", summary="获取关注列表")
async def get_following(
    openid: str = Query(..., description="目标用户的openid"),
    page: int = 1,
    page_size: int = 10,
):
    """
    获取指定用户正在关注的用户列表。
    """
    # 1. 获取所有关注的 action 记录
    all_following_actions = await query_records(
        "wxapp_action",
        conditions={
            "openid": openid,
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
    paginated_following_openids = [item['target_id'] for item in paginated_actions]

    if not paginated_following_openids:
        return Response.paged(data=[], pagination=PaginationInfo(
            total=total, page=page, page_size=page_size
        ))
        
    # 3. 获取关注用户的详细信息
    following_details = await query_records(
        "wxapp_user",
        conditions={"openid": paginated_following_openids},
        fields=["openid", "nickname", "avatar", "bio"],
    )

    # 4. 组装响应
    pagination = PaginationInfo(
        total=total, page=page, page_size=page_size
    )
    return Response.paged(data=following_details.get('data', []), pagination=pagination)

@router.get("/favorite")
async def get_user_favorites(
    openid: str = Query(..., description="用户openid"),
    page: int = Query(1, description="页码"), 
    page_size: int = Query(10, description="每页数量")
):
    """获取用户收藏的帖子列表"""
    offset = (page - 1) * page_size
    
    # 首先，获取用户收藏的帖子ID
    favorites = await query_records(
        "wxapp_action",
        conditions={
            "openid": openid,
            "target_type": "post",
            "action_type": "favorite",
            "is_active": True
        },
        order_by={"create_time": "DESC"},
        limit=page_size,
        offset=(page - 1) * page_size
    )
    
    if not favorites or not favorites.get('data'):
        return Response.paged(data=[], pagination=PaginationInfo(
            total=0,
            page=page,
            page_size=page_size
        ))

    total = favorites.get('total', 0)

    # 内存分页
    favorite_actions = favorites['data']
    start_index = (page - 1) * page_size
    paginated_actions = favorite_actions[start_index : start_index + page_size]
    post_ids = [fav['target_id'] for fav in paginated_actions]

    if not post_ids:
        return Response.paged(data=[], pagination=PaginationInfo(total=total, page=page, page_size=page_size))

    # 然后，根据帖子ID获取帖子详情
    placeholders = ', '.join(['%s'] * len(post_ids))
    posts_query = f"SELECT * FROM wxapp_post WHERE id IN ({placeholders}) AND is_deleted = 0"
    
    posts = await execute_custom_query(posts_query, post_ids, fetch='all')

    # 批量数据增强
    enriched_posts = await batch_enrich_posts_with_user_info(posts, openid)

    pagination = PaginationInfo(
        total=total,
        page=page,
        page_size=page_size
    )
    return Response.paged(data=enriched_posts, pagination=pagination)


@router.get("/like")
async def get_user_likes(
    openid: str = Query(..., description="用户openid"),
    page: int = Query(1, description="页码"),
    page_size: int = Query(10, description="每页数量")
):
    """获取用户点赞的帖子列表"""
    offset = (page - 1) * page_size

    # 首先，获取用户点赞的帖子ID
    likes = await query_records(
        "wxapp_action",
        conditions={
            "openid": openid,
            "target_type": "post",
            "action_type": "like",
            "is_active": True
        },
        order_by={"create_time": "DESC"},
        limit=page_size,
        offset=(page - 1) * page_size,
    )
    
    if not likes or not likes.get('data'):
        return Response.paged(data=[], pagination=PaginationInfo(
            total=0,
            page=page,
            page_size=page_size
        ))

    total = likes.get('total', 0)
    
    # 内存分页
    liked_actions = likes['data']
    start_index = (page - 1) * page_size
    paginated_actions = liked_actions[start_index : start_index + page_size]
    post_ids = [like['target_id'] for like in paginated_actions]

    if not post_ids:
        return Response.paged(data=[], pagination=PaginationInfo(total=total, page=page, page_size=page_size))

    # 然后，根据帖子ID获取帖子详情
    placeholders = ', '.join(['%s'] * len(post_ids))
    posts_query = f"SELECT * FROM wxapp_post WHERE id IN ({placeholders}) AND is_deleted = 0"
    
    posts = await execute_custom_query(posts_query, post_ids, fetch='all')

    # 批量数据增强
    enriched_posts = await batch_enrich_posts_with_user_info(posts, openid)

    pagination = PaginationInfo(
        total=total,
        page=page,
        page_size=page_size
    )
    return Response.paged(data=enriched_posts, pagination=pagination)

@router.get("/comment")
async def get_user_comments(
    openid: str = Query(..., description="用户openid"),
    page: int = Query(1, description="页码"),
    page_size: int = Query(10, description="每页数量")
):
    """获取用户的评论列表"""
    try:
        # 计算偏移量
        offset = (page - 1) * page_size
        
        comments = await query_records(
            "wxapp_comment",
            conditions={
                "openid": openid,
                "action_type": "comment",
                "is_active": True
            },
            order_by={"create_time": "DESC"},
            limit=page_size,
            offset=(page - 1) * page_size,
        )
        
        if not comments or not comments.get('data'):
            # 返回空数据，但使用标准分页格式
            pagination = {
                "total": 0,
                "page": page,
                "page_size": page_size,
                "total_pages": 0,
                "has_more": False
            }
            return Response.paged(data=[], pagination=pagination)
        
        # 获取涉及的帖子ID
        post_ids = [comment["post_id"] for comment in comments["data"] if "post_id" in comment]
        
        # 没有对应的帖子ID，直接返回评论列表
        if not post_ids:
            # 计算总页数
            total = comments.get("total", 0)
            total_pages = (total + page_size - 1) // page_size if page_size > 0 else 1
            
            # 构建标准分页信息
            pagination = {
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages,
                "has_more": page < total_pages
            }
            
            return Response.paged(
                data=comments.get("data", []),
                pagination=pagination,
                details={"message": "获取评论列表成功"}
            )
        
        # 查询帖子信息
        posts = await query_records(
            "wxapp_post",
            conditions={"id": ["IN", post_ids]},
            fields=["id", "title", "content"]
        )
        
        # 构建帖子映射
        post_map = {post["id"]: post for post in posts.get("data", [])} if posts.get("data") else {}
        
        # 为每个评论添加帖子信息
        for comment in comments["data"]:
            post_id = comment.get("post_id")
            if post_id and post_id in post_map:
                comment["post"] = post_map[post_id]
        
        # 计算总页数
        total = comments.get("total", 0)
        total_pages = (total + page_size - 1) // page_size if page_size > 0 else 1
        
        # 构建标准分页信息
        pagination = {
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "has_more": page < total_pages
        }
        
        return Response.paged(
            data=comments.get("data", []),
            pagination=pagination,
            details={"message": "获取评论列表成功"}
        )
    except Exception as e:
        return Response.error(details={"message": f"获取评论列表失败: {str(e)}"})

@router.get("/status")
async def get_user_status(
    openid: str = Query(..., description="当前用户openid"),
    target_id: str = Query(..., description="目标用户openid")
):
    """获取用户的交互状态"""
    try:
        # 获取目标用户信息
        target_user = await query_records(
            table_name="wxapp_user",
            conditions={"openid": target_id},
            limit=1
        )
        if not target_user or not target_user['data']:
            return Response.not_found(resource="用户")
            
        # 获取目标用户的数字ID
        target_user_id = target_user['data'][0]["id"]

        # 获取当前用户的数字ID
        current_user_query = "SELECT id FROM wxapp_user WHERE openid = %s LIMIT 1"
        current_user = await execute_custom_query(current_user_query, [openid])
        
        if not current_user:
            return Response.not_found(resource="当前用户")
            
        current_user_id = current_user[0]["id"]

        # 检查是否已关注 - 使用数字ID
        follow_action = await query_records(
            "wxapp_action",
            conditions={
                "openid": openid,
                "target_id": target_id,
                "action_type": "follow",
                "target_type": "user"
            },
            limit=1
        )
        is_following = bool(follow_action['data'])

        # 获取目标用户的统计数据
        user_data = target_user['data'][0]
        
        # 构建状态
        status = {
            "is_following": is_following,
            "is_self": openid == target_id,
            "post_count": user_data.get("post_count", 0),
            "follower_count": user_data.get("follower_count", 0),
            "following_count": user_data.get("following_count", 0),
            "like_count": user_data.get("like_count", 0)
        }

        return Response.success(data=status)
    except Exception as e:
        return Response.error(details={"message": f"获取用户状态失败: {str(e)}"})

@router.post("/sync", summary="同步微信用户信息（登录/注册）")
async def sync_user_info(
    body: Dict[str, Any] = Body(...)
):
    """
    根据openid同步用户信息，如果用户不存在则创建，如果存在则仅更新登录时间或传入的字段。
    这是小程序端登录或更新信息的统一入口。
    """
    openid = body.get("openid")
    if not openid:
        return Response.bad_request(details={"message": "openid是必需的"})

    try:
        # 1. 检查用户是否存在
        existing_user = await get_by_id("wxapp_user", openid, id_column='openid')
        
        if existing_user:
            # 用户存在，只更新最后登录时间，忽略请求体中的所有其他字段
            logger.debug(f"用户 {openid} 已存在，仅更新登录时间。")
            
            update_data = {
                "last_login_time": time.strftime('%Y-%m-%d %H:%M:%S')
            }

            await update_record(
                "wxapp_user",
                conditions={"openid": openid},
                data=update_data
            )
            user_info = await get_by_id("wxapp_user", openid, id_column='openid')
        else:
            # 用户不存在，执行插入，此时使用默认值是合理的
            logger.debug(f"用户 {openid} 不存在，执行创建。")
            
            new_user_data = {
                "openid": openid,
                "nickname": body.get("nickname", "微信用户"),
                "avatar": body.get("avatar") or default_avatar,
                "gender": body.get("gender"),
                "country": body.get("country"),
                "province": body.get("province"),
                "city": body.get("city"),
                "language": body.get("language"),
                "last_login_time": time.strftime('%Y-%m-%d %H:%M:%S'),
                "role": "user" # 新用户默认为普通用户
            }
            # 移除值为None的键
            new_user_data = {k: v for k, v in new_user_data.items() if v is not None}

            user_id = await insert_record("wxapp_user", new_user_data)
            if not user_id:
                return Response.db_error(details={"message": "创建新用户失败"})
            user_info = await get_by_id("wxapp_user", user_id)

        return Response.success(data=user_info, details={"message": "用户信息同步成功"})

    except Exception as e:
        logger.error(f"同步用户信息失败: {e}", exc_info=True)
        return Response.error(details=f"同步用户信息时发生错误: {e}")

