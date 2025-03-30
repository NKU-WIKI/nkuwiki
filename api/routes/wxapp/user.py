"""
微信小程序用户API接口
"""
from typing import List, Dict, Any, Optional
from fastapi import Query, APIRouter
from api.models.common import Response, Request, validate_params
from etl.load.db_core import (
    async_query_records, async_get_by_id, async_insert, async_update, async_count_records
)

router = APIRouter()

@router.get("/user/profile")
async def get_user_info(
    openid: str = Query(..., description="用户OpenID")
):
    """获取用户信息"""
    if not openid:
        return Response.bad_request(details={"message": "缺少openid参数"})
    try:
        user_data = await async_query_records(
            table_name="wxapp_user",
            conditions={"openid": openid},
            limit=1
        )

        if not user_data or not user_data['data']:
            return Response.not_found(resource="用户")

        return Response.success(data=user_data['data'][0])
    except Exception as e:
        return Response.error(details={"message": f"获取用户信息失败: {str(e)}"})

@router.get("/user/list")
async def get_user_list(
    limit: int = Query(10, description="每页数量")
):
    """获取用户列表"""
    try:
        users = await async_query_records(
            table_name="wxapp_user",
            limit=limit,
            order_by="create_time DESC"
        )

        return Response.paged(data=users['data'],pagination=users['pagination'],details={"message":"获取用户列表成功"})
    except Exception as e:
        return Response.error(details={"message": f"获取用户列表失败: {str(e)}"})

@router.get("/user/check-follow")
async def get_user_follow_status(
    follower_id: str = Query(..., description="关注者OpenID"),
    followed_id: str = Query(..., description="被关注者OpenID")
):
    """检查关注状态"""
    if not follower_id:
        return Response.bad_request(details={"message": "缺少参数follower_id"})
    if not followed_id:
        return Response.bad_request(details={"message": "缺少参数followed_id"})
    try:
        existing_follow = await async_query_records(
            table_name="wxapp_action",
            conditions={
                "openid": follower_id,
                "action_type": "follow",
                "target_type": "user",
                "target_id": followed_id
            },
            limit=1
        )
        is_following = bool(existing_follow and existing_follow.get('data'))

        return Response.success(data={"is_following": is_following})
    except Exception as e:
        return Response.error(details={"message": f"检查关注状态失败: {str(e)}"})

@router.get("/user/followings")
async def get_user_followings(
    openid: str = Query(..., description="用户OpenID"),
    limit: int = Query(20, description="每页数量"),
    offset: int = Query(0, description="偏移量")
):
    """获取用户关注列表"""
    if not openid:
        return Response.bad_request(details={"message": "缺少参数openid"})
    try:
        follow_relations = await async_query_records(
            table_name="wxapp_action",
            conditions={
                "openid": openid,
                "action_type": "follow",
                "target_type": "user"
            },
            limit=limit,
            offset=offset
        )

        if not follow_relations or not follow_relations.get('data'):
            return Response.success(data={"followings": []})

        followed_user_ids = [relation.get("target_id") for relation in follow_relations.get('data', [])]

        following_users = []
        if followed_user_ids:
            following_users_result = await async_query_records(
                table_name="wxapp_user",
                conditions={"openid": followed_user_ids}
            )
            following_users = following_users_result.get('data', [])

        return Response.success(data={"followings": following_users})
    except Exception as e:
        return Response.error(details={"message": f"获取用户关注列表失败: {str(e)}"})

@router.get("/user/followers")
async def get_user_followers(
    openid: str = Query(..., description="用户OpenID"),
    limit: int = Query(20, description="每页数量"),
    offset: int = Query(0, description="偏移量")
):
    """获取用户粉丝列表"""
    if not openid:
        return Response.bad_request(details={"message": "缺少参数openid"})
    try:
        follower_relations = await async_query_records(
            table_name="wxapp_action",
            conditions={
                "target_id": openid,
                "action_type": "follow",
                "target_type": "user"
            },
            limit=limit,
            offset=offset
        )

        if not follower_relations or not follower_relations.get('data'):
            return Response.success(data={"followers": []})

        follower_user_ids = [relation.get("openid") for relation in follower_relations.get('data', [])]

        follower_users = []
        if follower_user_ids:
            follower_users_result = await async_query_records(
                table_name="wxapp_user",
                conditions={"openid": follower_user_ids}
            )
            follower_users = follower_users_result.get('data', [])

        return Response.success(data={"followers": follower_users})
    except Exception as e:
        return Response.error(details={"message": f"获取用户粉丝列表失败: {str(e)}"})

@router.get("/user/follow-stats")
async def get_user_follow_stats(
    openid: str = Query(..., description="用户OpenID")
):
    """获取用户关注统计"""
    if not openid:
        return Response.bad_request(details={"message": "缺少参数openid"})
    try:
        user = await async_query_records(
            table_name="wxapp_user",
            conditions={"openid": openid},
            limit=1
        )
        if not user:
            return Response.not_found(resource="用户")

        following_count = await async_count_records(
            table_name="wxapp_action",
            conditions={"openid": openid, "action_type": "follow", "target_type": "user"}
        )

        follower_count = await async_count_records(
            table_name="wxapp_action",
            conditions={"target_id": openid, "action_type": "follow", "target_type": "user"}
        )

        return Response.success(data={
            "following_count": following_count,
            "follower_count": follower_count
        })
    except Exception as e:
        return Response.error(details={"message": f"获取用户关注统计失败: {str(e)}"})

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
        user = await async_query_records(
            table_name="wxapp_user",
            conditions={"openid": openid},
            limit=1
        )
        if not user:
            return Response.not_found(resource="用户")

        update_data = {}
        if not update_data:
            return Response.bad_request(details={"message": "未提供任何更新数据"})

        await async_update(
            table_name="wxapp_user",
            record_id=openid,
            update_data=update_data
        )

        return Response.success(details={"message":"用户信息更新成功"})
    except Exception as e:
        return Response.error(details={"message": f"更新用户信息失败: {str(e)}"})

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

        existing_user = await async_query_records(
            table_name="wxapp_user",
            conditions={"openid": openid},
            limit=1
        )
        
        if existing_user and existing_user['data']:
            # 用户存在，返回用户信息
            return Response.success(data=existing_user['data'][0], details={"message":"用户已存在"})

        # 构造基本用户数据
        user_data = {
            'openid': openid,
            'nickname': f'用户_{openid[-6:]}',  # 使用openid后六位作为默认昵称
            'avatar': '',  # 默认头像
            'gender': 0,   # 默认性别
            'status': 1,   # 默认状态：正常
            'token_count': 0  # 默认代币数
        }
        
        # 插入用户数据
        user_id = await async_insert("wxapp_user", user_data)
        
        if not user_id:
            return Response.error(details={"message": "用户创建失败"})
            
        return Response.success(details={"message":"用户信息同步成功", "user_id": user_id})
    except Exception as e:
        return Response.error(details={"message": f"同步用户信息失败: {str(e)}"})

@router.get("/user/token")
async def get_user_token(
    openid: str = Query(..., description="用户OpenID")
):
    """获取用户代币"""
    if not openid:
        return Response.bad_request(details={"message": "缺少openid参数"})
    try:
        user_data = await async_query_records(
            table_name="wxapp_user",
            conditions={"openid": openid},
            limit=1
        )

        if not user_data or not user_data['data']:
            return Response.not_found(resource="用户")

        user = user_data['data'][0]
        return Response.success(data={"token": user.get("token_count", 0)}, details={"message":"获取用户代币成功"})
    except Exception as e:
        return Response.error(details={"message": f"获取用户代币失败: {str(e)}"})