"""
JWT认证处理模块
提供JWT令牌的生成、验证和管理功能
"""

from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, Optional, Any
import jwt
import time
from datetime import datetime, timedelta
from loguru import logger
from config import Config

# 获取配置
config = Config()

# JWT配置
JWT_SECRET = config.get("auth.jwt_secret", "nkuwiki_default_secret_key")
JWT_ALGORITHM = config.get("auth.jwt_algorithm", "HS256")
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = config.get("auth.access_token_expire_minutes", 60)  # 1小时
JWT_REFRESH_TOKEN_EXPIRE_MINUTES = config.get("auth.refresh_token_expire_minutes", 10080)  # 7天

# 安全验证类
security = HTTPBearer()

def create_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    创建JWT令牌
    
    Args:
        data: 要编码到令牌中的数据
        expires_delta: 过期时间增量，默认为配置的访问令牌过期时间
        
    Returns:
        编码后的JWT令牌字符串
    """
    to_encode = data.copy()
    
    # 设置过期时间
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    
    return encoded_jwt

def create_access_token(user_id: str, username: str, additional_data: Dict[str, Any] = None) -> str:
    """
    创建访问令牌
    
    Args:
        user_id: 用户ID
        username: 用户名
        additional_data: 要包含在令牌中的其他数据
        
    Returns:
        访问令牌字符串
    """
    token_data = {
        "sub": str(user_id),
        "username": username,
        "token_type": "access",
        "iat": datetime.utcnow().timestamp()
    }
    
    # 添加额外数据
    if additional_data:
        token_data.update(additional_data)
    
    return create_token(
        token_data, 
        timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    )

def create_refresh_token(user_id: str) -> str:
    """
    创建刷新令牌
    
    Args:
        user_id: 用户ID
        
    Returns:
        刷新令牌字符串
    """
    token_data = {
        "sub": str(user_id),
        "token_type": "refresh",
        "iat": datetime.utcnow().timestamp()
    }
    
    return create_token(
        token_data, 
        timedelta(minutes=JWT_REFRESH_TOKEN_EXPIRE_MINUTES)
    )

def verify_token(token: str) -> Dict[str, Any]:
    """
    验证JWT令牌
    
    Args:
        token: JWT令牌字符串
        
    Returns:
        解码后的令牌数据
    
    Raises:
        HTTPException: 令牌无效或已过期
    """
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="令牌已过期")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="无效的令牌")

async def validate_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """
    验证请求中的JWT令牌
    
    Args:
        credentials: HTTP授权凭证
        
    Returns:
        验证通过的令牌，包含用户ID等信息
    
    Raises:
        HTTPException: 凭证无效或令牌验证失败
    """
    if not credentials:
        raise HTTPException(status_code=401, detail="未提供授权凭证")
    
    token = credentials.credentials
    payload = verify_token(token)
    
    # 调试日志
    logger.debug(f"验证通过的令牌负载: {payload}")
    
    return payload 