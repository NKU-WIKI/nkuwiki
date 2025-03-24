"""
用户相关API接口
处理用户登录、注册、信息查询等
"""
from fastapi import Depends, HTTPException, Query
from datetime import datetime

from api import wxapp_router
from api.common import handle_api_errors, get_api_logger_dep
from api.models.wxapp.user import UserModel, UserUpdateRequest, UserSyncRequest
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
    
    # 更新用户信息
    updated_user = await user_dao.update_user(openid, update_info.model_dump(exclude_unset=True))
    
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