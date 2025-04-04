"""
微信小程序用户API接口
"""
from typing import List, Dict, Any, Optional
from fastapi import Query, APIRouter
from api.models.common import Response, Request, validate_params
from etl.load.db_core import (
    async_query_records, async_get_by_id, async_insert, async_update, async_count_records, async_execute_custom_query
)
from config import Config
config = Config()
router = APIRouter()
default_avatar = config.get("services.app.default.default_avatar")

@router.get("/user/profile")
async def get_user_info(
    openid: str = Query(..., description="用户OpenID")
):
    """获取用户信息"""
    if not openid:
        return Response.bad_request(details={"message": "缺少openid参数"})
    try:
        # 使用自定义SQL直接查询指定openid的用户
        user_data = await async_execute_custom_query(
            "SELECT * FROM wxapp_user WHERE openid = %s LIMIT 1",
            [openid]
        )

        if not user_data:
            return Response.not_found(resource="用户")

        return Response.success(data=user_data[0])
    except Exception as e:
        return Response.error(details={"message": f"获取用户信息失败: {str(e)}"})

@router.get("/user/list")
async def get_user_list(
    limit: int = Query(10, description="每页数量")
):
    """获取用户列表"""
    try:
        # 只返回需要的字段
        fields = ["id", "openid", "nickname", "avatar", "bio", "create_time", "update_time"]
        users = await async_query_records(
            table_name="wxapp_user",
            fields=fields,
            limit=limit,
            order_by="create_time DESC"
        )

        return Response.paged(data=users['data'],pagination=users['pagination'],details={"message":"获取用户列表成功"})
    except Exception as e:
        return Response.error(details={"message": f"获取用户列表失败: {str(e)}"})

@router.post("/user/sync")
async def sync_user_info(
    request: Request
):
    """同步用户信息"""
    try:
        req_data = await request.json()
        required_params = ["openid"]
        error_response = validate_params(req_data, required_params)
        if(error_response):
            return error_response

        openid = req_data.get("openid")

        if not openid:
            return Response.bad_request(details={"message": "缺少openid参数"})

        avatar = req_data.get("avatar", default_avatar)
        nickname = req_data.get("nickname", f'用户_{openid[-6:]}')
        bio = req_data.get("bio", None)

        # 使用单一SQL直接查询用户，只查询必要字段
        existing_user = await async_execute_custom_query(
            "SELECT id, openid, nickname, avatar FROM wxapp_user WHERE openid = %s LIMIT 1",
            [openid]
        )
        
        if existing_user:
            return Response.success(data=existing_user[0], details={"message":"用户已存在", "user_id": existing_user[0]['id']})
        
        user_data = {
            'openid': openid,
            'nickname': nickname,
            'avatar': avatar,
        }
        
        # 如果提供了bio，添加到user_data
        if bio is not None:
            user_data['bio'] = bio
        
        user_id = await async_insert("wxapp_user", user_data)
        
        if not user_id:
            return Response.db_error(details={"message": "用户创建失败"})
            
        # 直接使用单一查询获取新创建的用户
        new_user = await async_execute_custom_query(
            "SELECT id, openid, nickname, avatar FROM wxapp_user WHERE id = %s LIMIT 1",
            [user_id]
        )
        
        if not new_user:
            return Response.success(details={"message": "新用户创建成功", "user_id": user_id})
        return Response.success(data=new_user[0], details={"message":"新用户创建成功", "user_id": user_id})
    except Exception as e:
        return Response.error(details={"message": f"同步用户信息失败: {str(e)}"})

@router.post("/user/update")
async def update_user_info(
    request: Request,
):
    """更新用户信息"""
    try:
        req_data = await request.json()
        required_params = ["openid"]
        error_response = validate_params(req_data, required_params)
        if(error_response):
            return error_response

        openid = req_data.get("openid")
        
        # 使用单一SQL获取用户ID
        user_result = await async_execute_custom_query(
            "SELECT id FROM wxapp_user WHERE openid = %s LIMIT 1",
            [openid]
        )
        
        if not user_result:
            return Response.not_found(resource="用户")
        
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
        if "status" in req_data:
            update_data["status"] = req_data["status"]
        if "extra" in req_data:
            update_data["extra"] = req_data["extra"]
            
        if not update_data:
            return Response.bad_request(details={"message": "未提供任何更新数据"})

        update_success = await async_update(
            table_name="wxapp_user",
            record_id=user_id,
            data=update_data
        )
        
        if not update_success:
            return Response.db_error(details={"message": "用户信息更新失败"})
            
        # 获取更新后的用户信息，直接使用SQL查询
        query_fields = "id, openid, nickname, avatar, bio, gender, country, province, city"
        updated_user = await async_execute_custom_query(
            f"SELECT {query_fields} FROM wxapp_user WHERE id = %s LIMIT 1",
            [user_id]
        )
        
        if updated_user:
            return Response.success(data=updated_user[0], details={"message":"用户信息更新成功"})
        else:
            return Response.success(details={"message":"用户信息更新成功"})
    except Exception as e:
        return Response.error(details={"message": f"更新用户信息失败: {str(e)}"})

@router.get("/user/favorites")
async def get_user_favorites(
    openid: str = Query(..., description="用户openid"),
    offset: int = Query(0, description="分页偏移量"),
    limit: int = Query(10, description="每页数量")
):
    """获取用户收藏的帖子列表"""
    try:
        # 获取用户收藏的帖子ID列表，只查询必要字段
        favorites = await async_query_records(
            "wxapp_action",
            conditions={
                "openid": openid,
                "action_type": "favorite",
                "target_type": "post"
            },
            fields=["target_id", "create_time"],
            limit=limit,
            offset=offset,
            order_by="create_time DESC"
        )
        
        if not favorites or not favorites.get('data'):
            return Response.success(data={"total": 0, "list": []})
            
        # 获取帖子详情，只查询需要的字段
        post_ids = [item["target_id"] for item in favorites["data"]]
        posts = await async_query_records(
            "wxapp_post",
            conditions={"id": ["IN", post_ids]},
            fields=["id", "title", "content", "image", "view_count", "like_count", "comment_count", "create_time"],
            order_by="create_time DESC"
        )
        
        return Response.paged(
            data=posts.get("data", []),
            pagination={
                "total": favorites.get("total", 0),
                "offset": offset,
                "limit": limit
            }
        )
    except Exception as e:
        return Response.error(details={"message": f"获取收藏列表失败: {str(e)}"})

@router.get("/user/like")
async def get_user_likes(
    openid: str = Query(..., description="用户openid"),
    offset: int = Query(0, description="分页偏移量"),
    limit: int = Query(10, description="每页数量")
):
    """获取用户点赞的帖子列表"""
    try:
        # 获取用户点赞的帖子ID列表
        likes = await async_query_records(
            "wxapp_action",
            conditions={
                "openid": openid,
                "action_type": "like",
                "target_type": "post"
            },
            limit=limit,
            offset=offset,
            order_by="create_time DESC"
        )
        
        if not likes or not likes.get('data'):
            return Response.success(data={"total": 0, "list": []})
            
        # 获取帖子详情
        post_ids = [item["target_id"] for item in likes["data"]]
        posts = await async_query_records(
            "wxapp_post",
            conditions={"id": ["IN", post_ids]},
            order_by="create_time DESC"
        )
        
        return Response.paged(
            data=posts.get("data", []),
            pagination={
                "total": likes.get("total", 0),
                "offset": offset,
                "limit": limit
            }
        )
    except Exception as e:
        return Response.error(details={"message": f"获取点赞列表失败: {str(e)}"})

@router.get("/user/comment")
async def get_user_comments(
    openid: str = Query(..., description="用户openid"),
    offset: int = Query(0, description="分页偏移量"),
    limit: int = Query(10, description="每页数量")
):
    """获取用户的评论列表"""
    try:
        comments = await async_query_records(
            "wxapp_comment",
            conditions={"openid": openid},
            limit=limit,
            offset=offset,
            order_by="create_time DESC"
        )
        
        if not comments or not comments.get('data'):
            return Response.success(data={"total": 0, "list": []})
            
        # 获取评论对应的帖子信息
        post_ids = list(set([item["post_id"] for item in comments["data"]]))
        posts = await async_query_records(
            "wxapp_post",
            conditions={"id": ["IN", post_ids]}
        )
        
        # 将帖子信息添加到评论中
        post_map = {post["id"]: post for post in posts.get("data", [])}
        for comment in comments["data"]:
            comment["post"] = post_map.get(comment["post_id"])
            
        return Response.paged(
            data=comments.get("data", []),
            pagination={
                "total": comments.get("total", 0),
                "offset": offset,
                "limit": limit
            }
        )
    except Exception as e:
        return Response.error(details={"message": f"获取评论列表失败: {str(e)}"})

@router.get("/user/follower")
async def get_user_followers(
    openid: str = Query(..., description="用户openid"),
    offset: int = Query(0, description="分页偏移量"),
    limit: int = Query(10, description="每页数量")
):
    """获取用户的粉丝列表"""
    try:
        # 先获取用户的数字ID
        user_query = "SELECT id FROM wxapp_user WHERE openid = %s LIMIT 1"
        user_result = await async_execute_custom_query(user_query, [openid])
        
        if not user_result:
            return Response.not_found(resource="用户")
            
        user_id = user_result[0]["id"]
        
        # 获取关注该用户的用户openid列表 - 使用数字ID查询
        followers = await async_query_records(
            "wxapp_action",
            conditions={
                "action_type": "follow",
                "target_type": "user",
                "target_id": user_id  # 使用数字ID
            },
            limit=limit,
            offset=offset,
            order_by="create_time DESC"
        )
        
        if not followers or not followers.get('data'):
            return Response.success(data={"total": 0, "list": []})
            
        # 获取粉丝用户信息
        follower_ids = [item["openid"] for item in followers["data"]]
        users = await async_query_records(
            "wxapp_user",
            conditions={"openid": ["IN", follower_ids]},
            fields=["openid", "nickname", "avatar", "bio"]
        )
        
        return Response.paged(
            data=users.get("data", []),
            pagination={
                "total": followers.get("total", 0),
                "offset": offset,
                "limit": limit
            }
        )
    except Exception as e:
        return Response.error(details={"message": f"获取粉丝列表失败: {str(e)}"})

@router.get("/user/following")
async def get_user_followings(
    openid: str = Query(..., description="用户openid"),
    offset: int = Query(0, description="分页偏移量"),
    limit: int = Query(10, description="每页数量")
):
    """获取用户关注的用户列表"""
    try:
        # 获取用户关注的用户ID列表
        followings = await async_query_records(
            "wxapp_action",
            conditions={
                "openid": openid,
                "action_type": "follow",
                "target_type": "user"
            },
            limit=limit,
            offset=offset,
            order_by="create_time DESC"
        )
        
        if not followings or not followings.get('data'):
            return Response.success(data={"total": 0, "list": []})
            
        # 获取关注的用户信息 - 通过数字ID查询
        following_ids = [item["target_id"] for item in followings["data"]]
        users_query = """
        SELECT openid, nickname, avatar, bio
        FROM wxapp_user
        WHERE id IN (%s)
        """
        placeholders = ', '.join(['%s'] * len(following_ids))
        users_query = users_query.replace('%s', placeholders)
        users_result = await async_execute_custom_query(users_query, following_ids)
        
        if not users_result:
            users_result = []
        
        return Response.paged(
            data=users_result,
            pagination={
                "total": followings.get("total", 0),
                "offset": offset,
                "limit": limit
            }
        )
    except Exception as e:
        return Response.error(details={"message": f"获取关注列表失败: {str(e)}"})

@router.get("/user/status")
async def get_user_status(
    openid: str = Query(..., description="当前用户openid"),
    target_id: str = Query(..., description="目标用户openid")
):
    """获取用户的交互状态"""
    try:
        # 获取目标用户信息
        target_user = await async_query_records(
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
        current_user = await async_execute_custom_query(current_user_query, [openid])
        
        if not current_user:
            return Response.not_found(resource="当前用户")
            
        current_user_id = current_user[0]["id"]

        # 检查是否已关注 - 使用数字ID
        follow_sql = """
        SELECT * FROM wxapp_action 
        WHERE openid = %s AND action_type = 'follow' AND target_type = 'user' AND target_id = %s
        LIMIT 1
        """
        follow_record = await async_execute_custom_query(follow_sql, [openid, target_user_id])
        is_following = bool(follow_record)

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