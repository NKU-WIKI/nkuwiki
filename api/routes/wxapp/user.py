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

        # 确保返回包含role字段
        user = user_data[0]
        if "role" not in user:
            user["role"] = None
        return Response.success(data=user)
    except Exception as e:
        return Response.error(details={"message": f"获取用户信息失败: {str(e)}"})

@router.get("/user/list")
async def get_user_list(
    type: Optional[str] = Query(None, description="列表类型：all(所有用户)、follower(粉丝)、following(关注)"),
    openid: Optional[str] = Query(None, description="用户openid，当type为follower或following时必填"),
    page: int = Query(1, description="页码"),
    page_size: int = Query(10, description="每页数量")
):
    """获取用户列表
    
    根据type参数返回不同类型的用户列表：
    - type=all或未指定：返回所有用户
    - type=follower：返回指定用户的粉丝列表
    - type=following：返回指定用户的关注列表
    """
    try:
        # 计算偏移量
        offset = (page - 1) * page_size
        
        # 如果type为follower或following，但未提供openid，返回错误
        if type in ["follower", "following"] and not openid:
            return Response.bad_request(details={"message": "当type为follower或following时，openid参数为必填"})
            
        # 根据type参数返回不同的用户列表
        if type == "follower":
            # 首先获取当前用户的数字ID
            user_id_query = "SELECT id FROM wxapp_user WHERE openid = %s LIMIT 1"
            user_id_result = await async_execute_custom_query(user_id_query, [openid])
            
            if not user_id_result:
                return Response.not_found(resource="用户")
                
            user_id = user_id_result[0]["id"]
            
            # 获取粉丝列表 - 使用用户的数字ID作为target_id查询
            followers = await async_query_records(
                "wxapp_action",
                conditions={
                    "target_id": user_id,
                    "action_type": "follow",
                    "target_type": "user"
                },
                fields=["openid", "create_time"],
                limit=page_size,
                offset=offset,
                order_by="create_time DESC"
            )
            
            if not followers or not followers.get('data'):
                # 返回空数据，但使用标准分页格式
                pagination = {
                    "total": 0,
                    "page": page,
                    "page_size": page_size,
                    "total_pages": 0,
                    "has_more": False
                }
                return Response.paged(data=[], pagination=pagination)
                
            # 获取粉丝用户的详细信息
            follower_ids = [item.get("openid") for item in followers.get("data", [])]
            
            # 使用高效的单一SQL查询获取用户详情
            if follower_ids:
                query_fields = "openid, nickname, avatar, bio, post_count, follower_count, following_count"
                
                user_info_dict = {}
                for follower_id in follower_ids:
                    # 这里follower_id已经是openid，可以直接用于查询
                    user_query = "SELECT openid, nickname, avatar, bio, post_count, follower_count, following_count FROM wxapp_user WHERE openid = %s LIMIT 1"
                    user_results = await async_execute_custom_query(user_query, [follower_id])
                    if user_results:
                        user_info_dict[follower_id] = user_results[0]
                
                # 构建结果
                result = []
                for follow in followers.get("data", []):
                    follower_id = follow.get("openid")
                    if follower_id in user_info_dict:
                        follower_user = user_info_dict[follower_id]
                        result.append({
                            **follower_user,
                            "follow_time": follow.get("create_time")
                        })
            else:
                result = []
            
            # 计算总页数
            total = followers.get("total", 0)
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
                data=result,
                pagination=pagination,
                details={"message": "获取粉丝列表成功"}
            )
            
        elif type == "following":
            # 获取关注列表
            followings = await async_query_records(
                "wxapp_action",
                conditions={
                    "openid": openid,
                    "action_type": "follow",
                    "target_type": "user"
                },
                fields=["target_id", "create_time"],
                limit=page_size,
                offset=offset,
                order_by="create_time DESC"
            )
            
            if not followings or not followings.get('data'):
                # 返回空数据，但使用标准分页格式
                pagination = {
                    "total": 0,
                    "page": page,
                    "page_size": page_size,
                    "total_pages": 0,
                    "has_more": False
                }
                return Response.paged(data=[], pagination=pagination)
            
            # 获取被关注用户的信息
            target_ids = [item.get("target_id") for item in followings.get("data", [])]
            
            # 使用高效的单一SQL查询获取用户详情
            if target_ids:
                query_fields = "openid, nickname, avatar, bio, post_count, follower_count, following_count"
                
                user_info_dict = {}
                for target_id in target_ids:
                    # 注意：target_id是用户的数字ID，需要先通过ID查询用户
                    user_query = "SELECT openid, nickname, avatar, bio, post_count, follower_count, following_count FROM wxapp_user WHERE id = %s LIMIT 1"
                    user_results = await async_execute_custom_query(user_query, [target_id])
                    if user_results:
                        user_info_dict[target_id] = user_results[0]
                
                # 构建结果
                result = []
                for follow in followings.get("data", []):
                    target_id = follow.get("target_id")
                    if target_id in user_info_dict:
                        target_user = user_info_dict[target_id]
                        result.append({
                            **target_user,
                            "follow_time": follow.get("create_time")
                        })
            else:
                result = []
            
            # 计算总页数
            total = followings.get("total", 0)
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
                data=result,
                pagination=pagination,
                details={"message": "获取关注列表成功"}
            )
        else:
            # 默认返回所有用户列表
            # 只返回需要的字段
            fields = ["id", "openid", "nickname", "avatar", "bio", "create_time", "update_time", "role"]
            users = await async_query_records(
                table_name="wxapp_user",
                fields=fields,
                    limit=page_size,
                    offset=offset,
                order_by="create_time DESC"
            )

        return Response.paged(data=users['data'],pagination=users['pagination'],details={"message":"获取用户列表成功"})
    except Exception as e:
        return Response.error(details={"message": f"获取用户列表失败: {str(e)}"})

@router.get("/user/favorite")
async def get_user_favorites(
    openid: str = Query(..., description="用户openid"),
    page: int = Query(1, description="页码"), 
    page_size: int = Query(10, description="每页数量")
):
    """获取用户收藏的帖子列表"""
    try:
        # 计算偏移量
        offset = (page - 1) * page_size
        
        # 获取用户收藏的帖子ID列表，只查询必要字段
        favorites = await async_query_records(
            "wxapp_action",
            conditions={
                "openid": openid,
                "action_type": "favorite",
                "target_type": "post"
            },
            fields=["target_id", "create_time"],
            limit=page_size,
            offset=offset,
            order_by="create_time DESC"
        )
        
        if not favorites or not favorites.get('data'):
            # 返回空数据，但使用标准分页格式
            pagination = {
                "total": 0,
                "page": page,
                "page_size": page_size,
                "total_pages": 0,
                "has_more": False
            }
            return Response.paged(data=[], pagination=pagination)
            
        # 获取帖子详情，只查询需要的字段
        post_ids = [item["target_id"] for item in favorites["data"]]
        posts = await async_query_records(
            "wxapp_post",
            conditions={"id": ["IN", post_ids]},
            fields=["id", "title", "content", "image", "view_count", "like_count", "comment_count", "create_time"],
            order_by="create_time DESC"
        )
        
        # 计算总页数
        total = favorites.get("total", 0)
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
            data=posts.get("data", []),
            pagination=pagination,
            details={"message": "获取收藏列表成功"}
        )
    except Exception as e:
        return Response.error(details={"message": f"获取收藏列表失败: {str(e)}"})

@router.get("/user/like")
async def get_user_likes(
    openid: str = Query(..., description="用户openid"),
    page: int = Query(1, description="页码"),
    page_size: int = Query(10, description="每页数量")
):
    """获取用户点赞的帖子列表"""
    try:
        # 计算偏移量
        offset = (page - 1) * page_size
        
        # 获取用户点赞的帖子ID列表
        likes = await async_query_records(
            "wxapp_action",
            conditions={
                "openid": openid,
                "action_type": "like",
                "target_type": "post"
            },
            limit=page_size,
            offset=offset,
            order_by="create_time DESC"
        )
        
        if not likes or not likes.get('data'):
            # 返回空数据，但使用标准分页格式
            pagination = {
                "total": 0,
                "page": page,
                "page_size": page_size,
                "total_pages": 0,
                "has_more": False
            }
            return Response.paged(data=[], pagination=pagination)
            
        # 获取帖子详情
        post_ids = [item["target_id"] for item in likes["data"]]
        posts = await async_query_records(
            "wxapp_post",
            conditions={"id": ["IN", post_ids]},
            order_by="create_time DESC"
        )
        
        # 计算总页数
        total = likes.get("total", 0)
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
            data=posts.get("data", []),
            pagination=pagination,
            details={"message": "获取点赞列表成功"}
        )
    except Exception as e:
        return Response.error(details={"message": f"获取点赞列表失败: {str(e)}"})

@router.get("/user/comment")
async def get_user_comments(
    openid: str = Query(..., description="用户openid"),
    page: int = Query(1, description="页码"),
    page_size: int = Query(10, description="每页数量")
):
    """获取用户的评论列表"""
    try:
        # 计算偏移量
        offset = (page - 1) * page_size
        
        comments = await async_query_records(
            "wxapp_comment",
            conditions={"openid": openid},
            limit=page_size,
            offset=offset,
            order_by="create_time DESC"
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
        posts = await async_query_records(
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
        phone = req_data.get("phone", None)
        university = req_data.get("university", None)

        # 使用单一SQL直接查询用户，只查询必要字段
        existing_user = await async_execute_custom_query(
            "SELECT id, openid, nickname, avatar, role FROM wxapp_user WHERE openid = %s LIMIT 1",
            [openid]
        )
        
        if existing_user:
            return Response.success(data=existing_user[0], details={"message":"用户已存在", "user_id": existing_user[0]['id']})
        
        user_data = {
            'openid': openid,
            'nickname': nickname,
            'avatar': avatar,
            'role': req_data.get("role", None)
        }
        
        # 如果提供了bio，添加到user_data
        if bio is not None:
            user_data['bio'] = bio
        
        # 添加phone和university字段
        if phone is not None:
            user_data['phone'] = phone
        if university is not None:
            user_data['university'] = university
        
        user_id = await async_insert("wxapp_user", user_data)
        
        if not user_id:
            return Response.db_error(details={"message": "用户创建失败"})
            
        # 直接使用单一查询获取新创建的用户
        new_user = await async_execute_custom_query(
            "SELECT id, openid, nickname, avatar, role FROM wxapp_user WHERE id = %s LIMIT 1",
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
        if "phone" in req_data:
            update_data["phone"] = req_data["phone"]
        if "university" in req_data:
            update_data["university"] = req_data["university"]
        if "status" in req_data:
            update_data["status"] = req_data["status"]
            
        if not update_data:
            return Response.bad_request(details={"message": "未提供任何更新数据"})

        try:
            update_success = await async_update(
                table_name="wxapp_user",
                record_id=user_id,
                data=update_data
            )
            
            # 此处修改判断逻辑，只有当明确返回False时才认为失败
            # 当数据无变化时，MySQL不会更新行，返回的affected rows为0
            # 但这种情况不应视为错误
            if update_success is False:  # 只有明确返回False时才视为失败
                return Response.db_error(details={"message": "用户信息更新失败"})
        except Exception as err:
            # 添加详细的错误日志
            import logging
            logging.error(f"用户信息更新SQL执行错误: {str(err)}")
            return Response.db_error(details={"message": f"用户信息更新失败: {str(err)}"})
            
        # 获取更新后的用户信息，直接使用SQL查询
        query_fields = "id, openid, nickname, avatar, bio, gender, country, province, city, role"
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

