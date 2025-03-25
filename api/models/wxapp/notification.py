"""
通知相关数据模型
"""
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from api.models.base import BaseAPIModel, BaseTimeStampModel


class NotificationSender(BaseAPIModel):
    """通知发送者信息"""
    openid: str = Field(..., description="发送者openid")
    nick_name: str = Field("", description="发送者昵称")
    avatar: str = Field("", description="发送者头像")


class NotificationModel(BaseTimeStampModel):
    """通知模型 - 对应wxapp_notifications表"""
    id: int = Field(..., description="通知ID")
    openid: str = Field(..., description="接收者openid")
    title: str = Field(..., description="通知标题")
    content: str = Field(..., description="通知内容")
    type: str = Field("system", description="通知类型：system-系统通知, like-点赞, comment-评论, follow-关注")
    is_read: bool = Field(False, description="是否已读")
    sender: Optional[NotificationSender] = Field(None, description="发送者信息")
    target_id: Optional[int] = Field(None, description="目标ID，如帖子ID、评论ID等")
    target_type: Optional[str] = Field(None, description="目标类型，如post、comment等")
    extra_data: Optional[Dict[str, Any]] = Field(None, description="额外数据")


class NotificationCreateRequest(BaseModel):
    """创建通知请求"""
    openid: str = Field(..., description="接收者用户openid")
    title: str = Field(..., description="通知标题")
    content: str = Field(..., description="通知内容")
    type: str = Field(..., description="通知类型: system-系统通知, like-点赞, comment-评论, follow-关注")
    sender_openid: Optional[str] = Field(None, description="发送者openid")
    related_id: Optional[str] = Field(None, description="关联ID")
    related_type: Optional[str] = Field(None, description="关联类型")
    extra: Optional[Dict[str, Any]] = Field(None, description="扩展字段")


class NotificationReadRequest(BaseAPIModel):
    """标记通知已读请求"""
    notification_ids: Optional[List[int]] = Field(None, description="通知ID列表，为空则标记所有通知为已读")


class NotificationQueryParams(BaseModel):
    """通知查询参数"""
    openid: str = Field(..., description="用户openid")
    type: Optional[str] = Field(None, description="通知类型")
    is_read: Optional[int] = Field(None, description="是否已读")
    related_type: Optional[str] = Field(None, description="关联类型")
    order_by: Optional[str] = Field("create_time DESC", description="排序方式")
    limit: Optional[int] = Field(20, description="返回数量限制")
    offset: Optional[int] = Field(0, description="偏移量")


class BatchOperationResponse(BaseAPIModel):
    """批量操作响应"""
    success: bool = Field(True, description="操作是否成功")
    message: str = Field("操作成功", description="操作消息")
    count: int = Field(0, description="受影响的记录数")


class NotificationListResponse(BaseAPIModel):
    """通知列表响应"""
    notifications: List[NotificationModel] = Field(default_factory=list, description="通知列表")
    total: int = Field(0, description="总数量")
    unread: int = Field(0, description="未读数量")
    limit: int = Field(20, description="每页数量")
    offset: int = Field(0, description="偏移量") 