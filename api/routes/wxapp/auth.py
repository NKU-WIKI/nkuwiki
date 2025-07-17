"""
微信小程序用户认证API接口
"""
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

import httpx
from fastapi import APIRouter, Body, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError

from api.models.common import Response
from config import Config
from core.utils.logger import register_logger
from etl.load import get_by_id, insert_record, update_record

# ------------------------------
# 配置和初始化
# ------------------------------
config = Config()
logger = register_logger('api.routes.wxapp.auth')
router = APIRouter()

# 从配置加载JWT和微信设置
WECHAT_CONFIG = config.get("services.wxapp.auth", {})
APPID = WECHAT_CONFIG.get("appid")
APPSECRET = WECHAT_CONFIG.get("appsecret")
JWT_SECRET = WECHAT_CONFIG.get("jwt_secret")
JWT_ALGORITHM = WECHAT_CONFIG.get("jwt_algorithm", "HS256")
JWT_EXPIRE_MINUTES = WECHAT_CONFIG.get("jwt_expire_minutes", 10080) # 默认7天

# 检查基本配置
if not all([APPID, APPSECRET, JWT_SECRET]):
    logger.error("微信小程序AppID, AppSecret或JWT Secret未在config.json中配置")
    # 可以在这里引发一个启动错误
    # raise RuntimeError("微信小程序或JWT配置不完整")

default_avatar = config.get("services.app.default.default_avatar", "")
# oauth2_scheme现在由api.common.dependencies管理，此处的定义可以移除
# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/wxapp/login", auto_error=False)

# ------------------------------
# 内部帮助函数
# ------------------------------
async def _sync_user(openid: str, user_info_payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    根据OpenID同步用户信息，如果用户不存在则创建。
    这是一个内部函数，由登录流程调用。
    """
    if user_info_payload is None:
        user_info_payload = {}
        
    existing_user = await get_by_id("wxapp_user", openid, id_column='openid')
    
    if existing_user:
        # 用户存在，更新最后登录时间并直接返回，避免再次查询
        last_login_time = time.strftime('%Y-%m-%d %H:%M:%S')
        await update_record(
            "wxapp_user",
            conditions={"openid": openid},
            data={"last_login_time": last_login_time}
        )
        user_info = existing_user
        user_info["last_login_time"] = last_login_time
    else:
        # 用户不存在，创建新用户
        new_user_data = {
            "openid": openid,
            "nickname": user_info_payload.get("nickname", "微信用户"),
            "avatar": user_info_payload.get("avatar") or default_avatar,
            "gender": user_info_payload.get("gender"),
            "country": user_info_payload.get("country"),
            "province": user_info_payload.get("province"),
            "city": user_info_payload.get("city"),
            "language": user_info_payload.get("language"),
            "last_login_time": time.strftime('%Y-%m-%d %H:%M:%S'),
            "role": "user"
        }
        new_user_data = {k: v for k, v in new_user_data.items() if v is not None}
        
        user_id = await insert_record("wxapp_user", new_user_data)
        if not user_id:
            raise HTTPException(status_code=500, detail="创建新用户失败")
        
        # 直接使用刚插入的数据，并补充主键ID，避免再次查询
        user_info = new_user_data
        user_info['id'] = user_id
        
    # 不应将openid返回给前端
    if 'openid' in user_info:
        del user_info['openid']
        
    return user_info

def _create_access_token(data: dict) -> str:
    """
    创建JWT访问令牌
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=JWT_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt

# ------------------------------
# API端点
# ------------------------------
@router.post("/login", summary="微信小程序登录")
async def login_for_access_token(
    body: Dict[str, Any] = Body(...)
):
    """
    使用小程序端获取的code进行登录，返回JWT和用户信息。
    """
    code = body.get("code")
    if not code:
        return Response.bad_request(details={"message": "缺少'code'参数"})

    # 1. 使用code换取openid和session_key
    url = "https://api.weixin.qq.com/sns/jscode2session"
    params = {
        "appid": APPID,
        "secret": APPSECRET,
        "js_code": code,
        "grant_type": "authorization_code"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            res = await client.get(url, params=params)
            res.raise_for_status()
            wechat_data = res.json()
        except httpx.RequestError as exc:
            logger.error(f"请求微信API失败: {exc}")
            return Response.error(details="请求微信服务失败，请稍后重试")
        except Exception as e:
            logger.error(f"处理微信响应失败: {e}")
            return Response.error(details="处理微信响应时发生未知错误")
            
    if "errcode" in wechat_data and wechat_data["errcode"] != 0:
        logger.warning(f"微信登录失败: {wechat_data}")
        return Response.bad_request(details=f"微信登录凭证无效: {wechat_data.get('errmsg', '')}")
    
    openid = wechat_data.get("openid")
    if not openid:
        return Response.error(details="从微信获取openid失败")
        
    # session_key不应下发给客户端，但可以在服务端用于解密用户敏感信息

    # 2. 同步用户信息 (创建或更新)
    # 可以在body中可选地传递userInfo以在首次登录时填充信息
    user_info_payload = body.get("userInfo", {})
    try:
        user = await _sync_user(openid, user_info_payload)
    except HTTPException as http_exc:
        return Response.error(status_code=http_exc.status_code, details=http_exc.detail)

    # 3. 创建JWT
    user_id = user.get("id")
    if not user_id:
        # 这是一个重要的保险措施，确保user对象中有id
        logger.error(f"无法为用户 {openid} 获取user_id，无法创建令牌。")
        return Response.error(details="无法生成用户令牌，请联系管理员。")

    # JWT的sub应该是系统内的唯一标识符，即user_id
    token_data = {"sub": user_id, "user_id": user_id}
    access_token = _create_access_token(data=token_data)
    
    # 4. 返回JWT和用户信息
    return Response.success(data={
        "token": access_token,
        "token_type": "bearer",
        "user_info": user
    }) 