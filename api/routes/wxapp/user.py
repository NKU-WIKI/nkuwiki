"""
用户相关API接口
处理用户登录、注册、信息查询等
"""
from fastapi import Depends, HTTPException, Query
from datetime import datetime
from typing import Optional

from api import wxapp_router
from api.common import handle_api_errors, get_api_logger_dep
from api.models.wxapp.user import UserModel, UserUpdateRequest, UserSyncRequest, UserListResponse
from api.models.common import create_response
logger = get_api_logger_dep()
# 获取配置
# config = Config()
# JWT_SECRET = config.get("api.auth.jwt_secret", "nkuwiki_default_secret")
# JWT_ALGORITHM = config.get("api.auth.jwt_algorithm", "HS256")
# JWT_EXPIRATION = config.get("api.auth.jwt_expiration", 86400)  # 默认24小时

@wxapp_router.get("/users/{openid}", response_model=UserModel)
@handle_api_errors("获取用户信息")
async def get_user_info(
    openid: str,
    api_logger=Depends(get_api_logger_dep)
):
    """
    获取用户信息
    
    根据openid获取用户详细信息
    """
    from api.database.wxapp import user_dao
    
    api_logger.debug(f"获取用户信息 (openid: {openid[:8]}...)")
    
    # 查询用户信息
    user = await user_dao.get_user_by_openid(openid)
    
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 手动处理datetime对象
    if user and 'create_time' in user and isinstance(user['create_time'], datetime):
        user['create_time'] = user['create_time'].strftime("%Y-%m-%d %H:%M:%S")
    if user and 'update_time' in user and isinstance(user['update_time'], datetime):
        user['update_time'] = user['update_time'].strftime("%Y-%m-%d %H:%M:%S")
    if user and 'last_login' in user and isinstance(user['last_login'], datetime):
        user['last_login'] = user['last_login'].strftime("%Y-%m-%d %H:%M:%S")
    
    return user

@wxapp_router.get("/users/me", response_model=UserModel)
@handle_api_errors("获取当前用户信息")
async def get_current_user_info(
    openid: str = Query(..., description="用户openid"),
    api_logger=Depends(get_api_logger_dep)
):
    """
    获取当前用户信息
    
    根据openid获取当前登录用户的详细信息
    """
    from api.database.wxapp import user_dao
    
    api_logger.debug(f"获取当前用户信息 (openid: {openid[:8]}...)")
    
    # 查询用户信息
    user = await user_dao.get_user_by_openid(openid)
    
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 手动处理datetime对象
    if user and 'create_time' in user and isinstance(user['create_time'], datetime):
        user['create_time'] = user['create_time'].strftime("%Y-%m-%d %H:%M:%S")
    if user and 'update_time' in user and isinstance(user['update_time'], datetime):
        user['update_time'] = user['update_time'].strftime("%Y-%m-%d %H:%M:%S")
    if user and 'last_login' in user and isinstance(user['last_login'], datetime):
        user['last_login'] = user['last_login'].strftime("%Y-%m-%d %H:%M:%S")
    
    return user

@wxapp_router.get("/users", response_model=dict)
@handle_api_errors("获取用户列表")
async def get_user_list(
    limit: int = Query(10, description="每页数量", ge=1, le=100),
    offset: int = Query(0, description="偏移量", ge=0),
    api_logger=Depends(get_api_logger_dep)
):
    """获取用户列表"""
    from api.database.wxapp import user_dao
    
    api_logger.debug(f"获取用户列表 (limit: {limit}, offset: {offset})")
    
    # 查询用户列表
    users, total = await user_dao.get_users(limit=limit, offset=offset)
    
    # 手动处理每个用户的datetime字段
    for user in users:
        if 'create_time' in user and isinstance(user['create_time'], datetime):
            user['create_time'] = user['create_time'].strftime("%Y-%m-%d %H:%M:%S")
        if 'update_time' in user and isinstance(user['update_time'], datetime):
            user['update_time'] = user['update_time'].strftime("%Y-%m-%d %H:%M:%S")
        if 'last_login' in user and isinstance(user['last_login'], datetime):
            user['last_login'] = user['last_login'].strftime("%Y-%m-%d %H:%M:%S")
    
    return {
        "users": users,
        "total": total,
        "limit": limit,
        "offset": offset
    }

@wxapp_router.put("/users/{openid}", response_model=UserModel)
@handle_api_errors("更新用户信息")
async def update_user_info(
    openid: str,
    update_info: UserUpdateRequest,
    api_logger=Depends(get_api_logger_dep)
):
    """
    更新用户信息
    
    更新用户的昵称、头像等基本信息
    """
    from api.database.wxapp import user_dao
    
    api_logger.debug(f"更新用户信息 (openid: {openid[:8]}...)")
    
    # 检查用户是否存在
    user = await user_dao.get_user_by_openid(openid)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 处理nickname和nick_name字段，确保一致性
    update_dict = update_info.model_dump(exclude_unset=True)
    if 'nickname' in update_dict and update_dict['nickname'] is not None:
        update_dict['nick_name'] = update_dict['nickname']
    
    # 更新用户信息
    updated_user = await user_dao.update_user(openid, update_dict)
    
    # 手动处理datetime对象
    if updated_user and 'create_time' in updated_user and isinstance(updated_user['create_time'], datetime):
        updated_user['create_time'] = updated_user['create_time'].strftime("%Y-%m-%d %H:%M:%S")
    if updated_user and 'update_time' in updated_user and isinstance(updated_user['update_time'], datetime):
        updated_user['update_time'] = updated_user['update_time'].strftime("%Y-%m-%d %H:%M:%S")
    if updated_user and 'last_login' in updated_user and isinstance(updated_user['last_login'], datetime):
        updated_user['last_login'] = updated_user['last_login'].strftime("%Y-%m-%d %H:%M:%S")
    
    return updated_user

@wxapp_router.post("/users/sync", response_model=UserModel)
@handle_api_errors("同步用户信息")
async def sync_user_info(
    user_info: UserSyncRequest,
    api_logger=Depends(get_api_logger_dep)
):
    """
    同步用户信息
    
    同步微信用户信息到系统
    """
    from api.database.wxapp import user_dao
    
    api_logger.debug(f"同步用户信息 (openid: {user_info.openid[:8]}...)")
    
    # 同步用户信息
    user_data = user_info.model_dump(exclude_unset=True)
    user = await user_dao.upsert_user(user_data)
    
    # 手动处理datetime对象
    if user and 'create_time' in user and isinstance(user['create_time'], datetime):
        user['create_time'] = user['create_time'].strftime("%Y-%m-%d %H:%M:%S")
    if user and 'update_time' in user and isinstance(user['update_time'], datetime):
        user['update_time'] = user['update_time'].strftime("%Y-%m-%d %H:%M:%S")
    if user and 'last_login' in user and isinstance(user['last_login'], datetime):
        user['last_login'] = user['last_login'].strftime("%Y-%m-%d %H:%M:%S")
    
    return user

@wxapp_router.get("/users/{openid}/follow-stats", response_model=dict)
@handle_api_errors("获取用户关注统计")
async def get_user_follow_stats(
    openid: str,
    api_logger=Depends(get_api_logger_dep)
):
    """
    获取用户关注统计
    
    获取用户的关注数量和粉丝数量
    """
    from api.database.wxapp import user_dao
    
    api_logger.debug(f"获取用户关注统计 (openid: {openid[:8]}...)")
    
    # 查询用户信息
    user = await user_dao.get_user_by_openid(openid)
    
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 获取关注统计
    return {
        "following": user.get("following_count", 0),
        "followers": user.get("followers_count", 0)
    }

@wxapp_router.post("/users/{follower_id}/follow/{followed_id}", response_model=dict)
@handle_api_errors("关注用户")
async def follow_user(
    follower_id: str,
    followed_id: str,
    api_logger=Depends(get_api_logger_dep)
):
    """
    关注用户
    
    将当前用户设为目标用户的粉丝
    """
    from api.database.wxapp import follow_dao, user_dao
    
    api_logger.debug(f"关注用户 (follower: {follower_id[:8]}..., followed: {followed_id[:8]}...)")
    
    # 检查用户是否存在
    follower = await user_dao.get_user_by_openid(follower_id)
    if not follower:
        raise HTTPException(status_code=404, detail="关注者不存在")
    
    followed = await user_dao.get_user_by_openid(followed_id)
    if not followed:
        raise HTTPException(status_code=404, detail="被关注者不存在")
    
    # 不能关注自己
    if follower_id == followed_id:
        raise HTTPException(status_code=400, detail="不能关注自己")
    
    # 执行关注操作
    success = await follow_dao.follow_user(follower_id, followed_id)
    
    if not success:
        raise HTTPException(status_code=500, detail="关注操作失败")
    
    # 查询最新的关注状态
    following_count = follower.get("following_count", 0)
    followers_count = followed.get("followers_count", 0)
    
    # 重新查询最新的统计数据
    follower = await user_dao.get_user_by_openid(follower_id)
    followed = await user_dao.get_user_by_openid(followed_id)
    
    return {
        "status": "success",
        "following_count": follower.get("following_count", 0),
        "followers_count": followed.get("followers_count", 0),
        "is_following": True
    }

@wxapp_router.post("/users/{follower_id}/unfollow/{followed_id}", response_model=dict)
@handle_api_errors("取消关注用户")
async def unfollow_user(
    follower_id: str,
    followed_id: str,
    api_logger=Depends(get_api_logger_dep)
):
    """
    取消关注用户
    
    将当前用户从目标用户的粉丝列表中移除
    """
    from api.database.wxapp import follow_dao, user_dao
    
    api_logger.debug(f"取消关注用户 (follower: {follower_id[:8]}..., followed: {followed_id[:8]}...)")
    
    # 检查用户是否存在
    follower = await user_dao.get_user_by_openid(follower_id)
    if not follower:
        raise HTTPException(status_code=404, detail="关注者不存在")
    
    followed = await user_dao.get_user_by_openid(followed_id)
    if not followed:
        raise HTTPException(status_code=404, detail="被关注者不存在")
    
    # 执行取消关注操作
    success = await follow_dao.unfollow_user(follower_id, followed_id)
    
    if not success:
        raise HTTPException(status_code=500, detail="取消关注操作失败")
    
    # 重新查询最新的统计数据
    follower = await user_dao.get_user_by_openid(follower_id)
    followed = await user_dao.get_user_by_openid(followed_id)
    
    return {
        "status": "success",
        "following_count": follower.get("following_count", 0),
        "followers_count": followed.get("followers_count", 0),
        "is_following": False
    }

@wxapp_router.get("/users/{follower_id}/check-follow/{followed_id}", response_model=dict)
@handle_api_errors("检查关注状态")
async def check_follow_status(
    follower_id: str,
    followed_id: str,
    api_logger=Depends(get_api_logger_dep)
):
    """
    检查关注状态
    
    检查用户是否已关注某用户
    """
    from api.database.wxapp import follow_dao
    
    api_logger.debug(f"检查关注状态 (follower: {follower_id[:8]}..., followed: {followed_id[:8]}...)")
    
    # 检查关注状态
    is_following = await follow_dao.check_follow_status(follower_id, followed_id)
    
    return {
        "is_following": is_following
    }

@wxapp_router.get("/users/{openid}/followings", response_model=UserListResponse)
@handle_api_errors("获取用户关注列表")
async def get_user_followings(
    openid: str,
    limit: int = Query(20, description="每页数量", ge=1, le=100),
    offset: int = Query(0, description="偏移量", ge=0),
    api_logger=Depends(get_api_logger_dep)
):
    """
    获取用户关注列表
    
    获取用户关注的所有用户
    """
    from api.database.wxapp import follow_dao
    
    api_logger.debug(f"获取用户关注列表 (openid: {openid[:8]}..., limit: {limit}, offset: {offset})")
    
    # 获取关注列表
    users, total = await follow_dao.get_user_followings(openid, limit, offset)
    
    return {
        "users": users,
        "total": total,
        "limit": limit,
        "offset": offset
    }

@wxapp_router.get("/users/{openid}/followers", response_model=UserListResponse)
@handle_api_errors("获取用户粉丝列表")
async def get_user_followers(
    openid: str,
    limit: int = Query(20, description="每页数量", ge=1, le=100),
    offset: int = Query(0, description="偏移量", ge=0),
    api_logger=Depends(get_api_logger_dep)
):
    """
    获取用户粉丝列表
    
    获取关注该用户的所有用户
    """
    from api.database.wxapp import follow_dao
    
    api_logger.debug(f"获取用户粉丝列表 (openid: {openid[:8]}..., limit: {limit}, offset: {offset})")
    
    # 获取粉丝列表
    users, total = await follow_dao.get_user_followers(openid, limit, offset)
    
    return {
        "users": users,
        "total": total,
        "limit": limit,
        "offset": offset
    } 