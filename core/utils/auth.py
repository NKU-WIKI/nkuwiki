# import jwt
# from datetime import datetime, timedelta
# from typing import Dict, Any, Optional
# from fastapi import HTTPException, status, Depends, Security
# from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# from config import Config
# from core.utils.logger import register_logger

# # 获取配置
# config = Config()
# logger = register_logger("auth")

# # JWT 配置
# SECRET_KEY = config.get("jwt.secret_key", "your-256-bit-secret")
# ALGORITHM = config.get("jwt.algorithm", "HS256")
# ACCESS_TOKEN_EXPIRE_MINUTES = config.get("jwt.access_token_expire_minutes", 30 * 24 * 60)  # 默认30天

# security = HTTPBearer()

# class TokenManager:
#     """Token管理器，负责生成和验证JWT Token"""
    
#     def __init__(self, secret_key: str = SECRET_KEY, algorithm: str = ALGORITHM, 
#                  expire_minutes: int = ACCESS_TOKEN_EXPIRE_MINUTES):
#         self.secret_key = secret_key
#         self.algorithm = algorithm
#         self.expire_minutes = expire_minutes
    
#     def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
#         """
#         创建访问令牌
        
#         Args:
#             data: 令牌载荷数据
#             expires_delta: 过期时间增量，默认为配置中的ACCESS_TOKEN_EXPIRE_MINUTES
            
#         Returns:
#             生成的JWT令牌
#         """
#         to_encode = data.copy()
#         expire = datetime.utcnow() + (expires_delta or timedelta(minutes=self.expire_minutes))
#         to_encode.update({"exp": expire})
        
#         try:
#             encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
#             return encoded_jwt
#         except Exception as e:
#             logger.error(f"生成令牌时出错: {str(e)}")
#             raise HTTPException(
#                 status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#                 detail="无法生成令牌"
#             )
    
#     def decode_token(self, token: str) -> Dict[str, Any]:
#         """
#         解码并验证访问令牌
        
#         Args:
#             token: JWT令牌
            
#         Returns:
#             解码后的令牌载荷
            
#         Raises:
#             HTTPException: 令牌无效或已过期
#         """
#         try:
#             payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
#             return payload
#         except jwt.ExpiredSignatureError:
#             logger.warning("令牌已过期")
#             raise HTTPException(
#                 status_code=status.HTTP_401_UNAUTHORIZED,
#                 detail="令牌已过期"
#             )
#         except jwt.InvalidTokenError:
#             logger.warning("无效的令牌")
#             raise HTTPException(
#                 status_code=status.HTTP_401_UNAUTHORIZED,
#                 detail="无效的令牌"
#             )
    
#     async def get_current_user(self, credentials: HTTPAuthorizationCredentials = Security(security)) -> Dict[str, Any]:
#         """
#         获取当前用户信息
        
#         Args:
#             credentials: HTTP授权凭据，由Depends(security)自动注入
            
#         Returns:
#             当前用户信息
            
#         Raises:
#             HTTPException: 认证失败
#         """
#         try:
#             token = credentials.credentials
#             payload = self.decode_token(token)
#             return payload
#         except Exception as e:
#             logger.error(f"认证失败: {str(e)}")
#             raise HTTPException(
#                 status_code=status.HTTP_401_UNAUTHORIZED,
#                 detail="认证失败"
#             )

# token_manager = TokenManager()

# async def get_current_openid(user: Dict[str, Any] = Depends(token_manager.get_current_user)) -> str:
#     """
#     从令牌中获取当前用户的openid
#     这是一个便捷的依赖函数，用于大多数需要用户身份验证的wxapp路由。
#     """
#     openid = user.get("openid")
#     if not openid:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="无法从令牌中解析openid"
#         )
#     return openid

# def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
#     """
#     创建访问令牌的便捷函数
    
#     Args:
#         data: 令牌载荷数据
#         expires_delta: 过期时间增量，默认为配置中的ACCESS_TOKEN_EXPIRE_MINUTES
        
#     Returns:
#         生成的JWT令牌
#     """
#     token_manager = TokenManager()
#     return token_manager.create_access_token(data, expires_delta) 

import httpx
from config import Config
from core.utils.logger import register_logger
from typing import Dict, Any, Optional

config = Config()
logger = register_logger("auth")

WX_APPID = config.get("services.app.appid")
WX_SECRET = config.get("services.app.secret")

async def code2session(code: str) -> Optional[Dict[str, Any]]:
    """
    使用 code 换取 session_key 和 openid
    
    Args:
        code: 微信小程序登录时获取的code
        
    Returns:
        包含 openid 和 session_key 的字典，或者在出错时返回 None
    """
    if not WX_APPID or not WX_SECRET:
        logger.error("小程序 AppID 或 AppSecret 未配置")
        return None

    url = f"https://api.weixin.qq.com/sns/jscode2session"
    params = {
        "appid": WX_APPID,
        "secret": WX_SECRET,
        "js_code": code,
        "grant_type": "authorization_code"
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            response.raise_for_status()  # 如果请求失败则抛出HTTPError
            data = response.json()
            
            if data.get("errcode"):
                logger.error(f"微信code2session接口返回错误: {data}")
                return None
            
            return data
    except httpx.RequestError as e:
        logger.error(f"请求微信code2session接口失败: {e}")
        return None
    except Exception as e:
        logger.error(f"处理code2session时发生未知错误: {e}")
        return None 