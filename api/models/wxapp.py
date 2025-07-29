"""
微信小程序模型
"""
from typing import List, Optional, Dict, Any
from pydantic import Field
from api.models.common import BaseAPI, BaseTimeStamp

class User(BaseTimeStamp):
    """用户"""
    id: int = Field(..., description="用户ID")
    openid: str = Field(..., description="发送者openid")
    nickname: str = Field("", description="发送者昵称")
    avatar: str = Field("", description="发送者头像")
    level: int = Field(0, description="用户等级")

class Post(BaseTimeStamp):
    """帖子模型"""
    id: int = Field(..., description="帖子ID")
    openid: str = Field(..., description="发布者openid")
    title: str = Field(..., description="帖子标题")
    content: str = Field(..., description="帖子内容")
    image: List[str] = Field(default_factory=list, description="帖子图片列表")
    tag: List[str] = Field(default_factory=list, description="帖子标签")
    category_id: int = Field(0, description="分类ID")
    location: Optional[LocationInfo] = Field(None, description="位置信息")
    phone: Optional[str] = Field(None, description="手机号")
    wechatId: Optional[str] = Field(None, description="微信号")
    qqId: Optional[str] = Field(None, description="QQ号")
    view_count: int = Field(0, description="浏览次数")
    like_count: int = Field(0, description="点赞次数")
    comment_count: int = Field(0, description="评论次数")
    favorite_count: int = Field(0, description="收藏次数")
    status: int = Field(1, description="状态：0-草稿，1-已发布，2-审核中，3-已删除")

class Comment(BaseTimeStamp):
    """评论模型"""
    id: int = Field(..., description="评论ID")
    post_id: int = Field(..., description="帖子ID")
    openid: str = Field(..., description="评论用户openid")
    content: str = Field(..., description="评论内容")
    parent_id: Optional[int] = Field(None, description="父评论ID（回复）")
    root_id: Optional[int] = Field(None, description="根评论ID")
    image: List[str] = Field(default_factory=list, description="图片列表")
    like_count: int = Field(0, description="点赞数")
    status: int = Field(1, description="状态：1-正常, 0-禁用")
    liked: Optional[bool] = Field(None, description="是否已点赞")

class Action(BaseTimeStamp):
    """动作"""
    id: int = Field(..., description="动作ID")
    openid: str = Field(..., description="执行者openid")
    action_type: str = Field(..., description="动作类型：like-点赞, comment-评论, follow-关注")
    target_id: Optional[int] = Field(None, description="目标ID，如帖子ID、评论ID等")
    target_type: Optional[str] = Field(None, description="目标类型，如post、comment等")
    extra_data: Optional[Dict[str, Any]] = Field(None, description="额外数据")

class Notification(BaseTimeStamp):
    """通知"""
    id: int = Field(..., description="通知ID")
    openid: str = Field(..., description="接收者openid")
    title: str = Field(..., description="通知标题")
    content: str = Field(..., description="通知内容")
    type: str = Field("system", description="通知类型：system-系统通知, like-点赞, comment-评论, follow-关注")
    is_read: bool = Field(False, description="是否已读")
    sender: Optional[User] = Field(None, description="发送者信息")
    target_id: Optional[int] = Field(None, description="目标ID，如帖子ID、评论ID等")
    target_type: Optional[str] = Field(None, description="目标类型，如post、comment等")
    extra_data: Optional[Dict[str, Any]] = Field(None, description="额外数据")

class Feedback(BaseTimeStamp):
    """反馈模型"""
    id: int = Field(..., description="反馈ID")
    content: str = Field(..., description="反馈内容")
    type: str = Field(..., description="反馈类型：bug-问题反馈, suggestion-建议, other-其他")
    contact: Optional[str] = Field(None, description="联系方式")
    image: List[str] = Field(default_factory=list, description="图片URL列表")
    device_info: Optional[DeviceInfo] = Field(None, description="设备信息")
    version: Optional[str] = Field(None, description="应用版本号")
    status: str = Field("pending", description="反馈状态：pending-待处理, processing-处理中, resolved-已解决, rejected-已拒绝")
    admin_reply: Optional[str] = Field(None, description="管理员回复")
    admin_id: Optional[str] = Field(None, description="处理管理员ID")

class DeviceInfo(BaseAPI):
    """设备信息"""
    brand: Optional[str] = Field(None, description="设备品牌")
    model: Optional[str] = Field(None, description="设备型号")
    system: Optional[str] = Field(None, description="操作系统版本")
    platform: Optional[str] = Field(None, description="客户端平台")
    SDKVersion: Optional[str] = Field(None, description="客户端基础库版本")
    version: Optional[str] = Field(None, description="微信版本号")
    app_version: Optional[str] = Field(None, description="应用版本号")

class LocationInfo(BaseAPI):
    """位置信息模型"""
    city: Optional[str] = Field(None, description="城市")
    country: Optional[str] = Field(None, description="国家")
    address: Optional[str] = Field(None, description="详细地址")

class UserInfo(User):
    """用户模型"""
    unionid: Optional[str] = Field(None, description="微信开放平台唯一标识")
    gender: int = Field(0, description="性别：0-未知, 1-男, 2-女")
    bio: Optional[str] = Field(None, description="用户个人简介")
    country: Optional[str] = Field(None, description="国家")
    province: Optional[str] = Field(None, description="省份")
    city: Optional[str] = Field(None, description="城市")
    language: Optional[str] = Field(None, description="语言")
    birthday: Optional[str] = Field(None, description="生日")
    wechatId: Optional[str] = Field(None, description="微信号")
    qqId: Optional[str] = Field(None, description="QQ号")
    phone: Optional[str] = Field(None, description="手机号")
    university: Optional[str] = Field(None, description="大学")
    token_count: int = Field(0, description="用户Token数量")
    like_count: int = Field(0, description="获得的点赞数")
    favorite_count: int = Field(0, description="获得的收藏数")
    post_count: int = Field(0, description="发布的帖子数")
    follower_count: int = Field(0, description="关注者数量")
    following_count: int = Field(0, description="关注的用户数量")
    last_login: Optional[str] = Field(None, description="最后登录时间")
    status: int = Field(1, description="状态：1-正常, 0-禁用")
    level: int = Field(0, description="用户等级")

class AboutInfo(BaseAPI):
    """关于页信息模型"""
    app_name: str = Field(..., description="应用名称")
    version: str = Field(..., description="版本号")
    description: str = Field(..., description="应用描述")
    company: str = Field(..., description="公司名称")
    email: str = Field(..., description="联系方式")
    github: str = Field(..., description="GitHub仓库链接")
    website: str = Field(..., description="网站链接")
    copyright: str = Field(..., description="版权信息")


