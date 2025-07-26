
"""
Authentication utilities for NKUWiki.
- JWT creation and verification.
- Password hashing and verification.
"""
from typing import Dict, Any, Optional

import httpx
from jose import jwt, JWTError
from passlib.context import CryptContext

from config import Config
from core.utils.logger import register_logger

config = Config()
logger = register_logger("auth")

WX_APPID = config.get("services.weapp.auth.appid")
WX_SECRET = config.get("services.weapp.auth.appsecret")

async def code2session(code: str) -> Optional[Dict[str, Any]]:
    """
    通过 code 换取 session_key 和 openid
    """
    if not WX_APPID or not WX_SECRET:
        logger.error("微信小程序的 appid 或 appsecret 未配置")
        return None

    url = "https://api.weixin.qq.com/sns/jscode2session"
    params = {
        "appid": WX_APPID,
        "secret": WX_SECRET,
        "js_code": code,
        "grant_type": "authorization_code"
    }

    async with httpx.AsyncClient() as client:
        try:
            res = await client.get(url, params=params)
            res.raise_for_status()  # 抛出HTTP错误
            data = res.json()
        except httpx.RequestError as exc:
            logger.error(f"请求微信API失败: {exc}")
            return None
        except Exception as e:
            logger.error(f"处理微信响应失败: {e}")
            return None

    if "errcode" in data and data["errcode"] != 0:
        logger.warning(f"微信登录失败, errcode: {data['errcode']}, errmsg: {data.get('errmsg')}")
        return None
    
    return data

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a hashed password.
    """
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """
    Hash a plain password.
    """
    return pwd_context.hash(password) 