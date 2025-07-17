
"""
通用依赖项
- an dependencies module that can be used across the application.
"""
from typing import Optional, Dict, Any

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError

from config import Config
from etl.load import db_core
from core.utils.logger import register_logger

# ------------------------------
# 配置和初始化
# ------------------------------
config = Config()
logger = register_logger("api.common.dependencies")

# 从配置加载JWT设置
# We must use the same settings as in api/routes/wxapp/auth.py
WECHAT_CONFIG = config.get("services.weapp.auth", {})
JWT_SECRET = WECHAT_CONFIG.get("jwt_secret")
JWT_ALGORITHM = WECHAT_CONFIG.get("jwt_algorithm", "HS256")

# OAuth2 scheme
# The tokenUrl should point to the login endpoint.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/wxapp/auth/login", auto_error=True)
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="/api/wxapp/auth/login", auto_error=False)


# ------------------------------
# 认证依赖 (Authentication Dependencies)
# ------------------------------
async def get_current_active_user(token: str = Depends(oauth2_scheme)) -> Dict[str, Any]:
    """
    解码JWT，从数据库获取并返回当前活跃用户。
    如果令牌无效或用户不存在，则会引发HTTPException。
    这是一个严格的依赖，用于必须登录才能访问的端点。
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id: int = payload.get("user_id")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    # 从数据库获取用户
    user = await db_core.get_by_id("wxapp_user", user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="用户不存在"
        )
    
    return user


async def get_current_active_user_optional(token: Optional[str] = Depends(oauth2_scheme_optional)) -> Optional[Dict[str, Any]]:
    """
    解码JWT，从数据库获取并返回当前用户（如果存在）。
    如果token不存在或无效，则返回None，不会引发错误。
    这是一个可选的依赖项，用于那些对登录和未登录用户有不同行为的端点。
    """
    if token is None:
        return None
        
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id: int = payload.get("user_id")
        if user_id is None:
            return None # payload中没有user_id
    except JWTError:
        return None # token无效

    # 从数据库获取用户
    user = await db_core.get_by_id("wxapp_user", user_id)
    # 即使用户在数据库中不存在，也只返回None，而不抛出异常
    
    return user


async def get_current_admin_user(current_user: Dict[str, Any] = Depends(get_current_active_user)) -> Dict[str, Any]:
    """
    一个依赖于 get_current_active_user 的附加依赖。
    它会检查当前用户是否具有管理员权限。
    如果用户不是管理员，则会引发HTTPException。
    用于需要管理员权限的端点。
    """
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="操作未被授权，需要管理员权限",
        )
    return current_user 