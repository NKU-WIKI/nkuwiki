"""
微信小程序用户相关模型
"""
from typing import List, Dict, Any, Optional
from pydantic import Field

from api.models.base import BaseAPIModel, BaseTimeStampModel

class UserInfo(BaseAPIModel):
    """用户基本信息"""
    nickName: str = Field(..., description="昵称")
    avatarUrl: str = Field(..., description="头像URL")
    gender: int = Field(0, description="性别：0未知，1男，2女")
    country: Optional[str] = Field(None, description="国家")
    province: Optional[str] = Field(None, description="省份")
    city: Optional[str] = Field(None, description="城市")
    language: Optional[str] = Field(None, description="语言")

class UserModel(BaseTimeStampModel):
    """用户模型"""
    id: int = Field(..., description="用户ID")
    openid: str = Field(..., description="微信用户唯一标识")
    unionid: Optional[str] = Field(None, description="微信开放平台唯一标识")
    nick_name: str = Field("微信用户", description="用户昵称")
    avatar: str = Field("", description="头像URL")
    gender: int = Field(0, description="性别：0-未知, 1-男, 2-女")
    bio: Optional[str] = Field(None, description="用户个人简介")
    country: Optional[str] = Field(None, description="国家")
    province: Optional[str] = Field(None, description="省份")
    city: Optional[str] = Field(None, description="城市")
    language: Optional[str] = Field(None, description="语言")
    token_count: int = Field(0, description="用户Token数量")
    likes_count: int = Field(0, description="获得的点赞数")
    favorites_count: int = Field(0, description="获得的收藏数")
    followers_count: int = Field(0, description="关注者数量")
    following_count: int = Field(0, description="关注的用户数量")
    last_login: Optional[str] = Field(None, description="最后登录时间")
    status: int = Field(1, description="状态：1-正常, 0-禁用")

class UserUpdateRequest(BaseAPIModel):
    """用户更新请求"""
    nick_name: Optional[str] = Field(None, description="用户昵称")
    avatar: Optional[str] = Field(None, description="头像URL")
    bio: Optional[str] = Field(None, description="个人简介")
    gender: Optional[int] = Field(None, description="性别：0-未知, 1-男, 2-女")
    status: Optional[int] = Field(None, description="用户状态")
    
class UserListResponse(BaseAPIModel):
    """用户列表响应"""
    users: List[UserModel] = Field(default_factory=list, description="用户列表")
    total: int = Field(0, description="总数量")
    limit: int = Field(20, description="每页数量")
    offset: int = Field(0, description="偏移量")

class UserSyncRequest(BaseAPIModel):
    """用户同步请求"""
    openid: str = Field(..., description="用户唯一标识")
    unionid: Optional[str] = Field(None, description="微信开放平台唯一标识")
    nick_name: Optional[str] = Field(None, description="用户昵称")
    avatar: Optional[str] = Field(None, description="头像URL")
    gender: Optional[int] = Field(None, description="性别：0-未知, 1-男, 2-女")
    bio: Optional[str] = Field(None, description="个人简介")
    country: Optional[str] = Field(None, description="国家")
    province: Optional[str] = Field(None, description="省份")
    city: Optional[str] = Field(None, description="城市")
    language: Optional[str] = Field(None, description="语言") 