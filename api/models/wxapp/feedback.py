"""
微信小程序反馈相关模型
"""
from typing import Dict, Any, Optional, List
from pydantic import Field

from api.models.base import BaseAPIModel, BaseTimeStampModel

class DeviceInfo(BaseAPIModel):
    """设备信息"""
    brand: Optional[str] = Field(None, description="设备品牌")
    model: Optional[str] = Field(None, description="设备型号")
    system: Optional[str] = Field(None, description="操作系统版本")
    platform: Optional[str] = Field(None, description="客户端平台")
    SDKVersion: Optional[str] = Field(None, description="客户端基础库版本")
    version: Optional[str] = Field(None, description="微信版本号")
    app_version: Optional[str] = Field(None, description="应用版本号")

class FeedbackModel(BaseTimeStampModel):
    """反馈模型"""
    id: int = Field(..., description="反馈ID")
    openid: str = Field(..., description="用户openid")
    content: str = Field(..., description="反馈内容")
    type: str = Field(..., description="反馈类型：bug-问题反馈, suggestion-建议, other-其他")
    contact: Optional[str] = Field(None, description="联系方式")
    images: List[str] = Field(default_factory=list, description="图片URL列表")
    device_info: Optional[DeviceInfo] = Field(None, description="设备信息")
    status: str = Field("pending", description="反馈状态：pending-待处理, processing-处理中, resolved-已解决, rejected-已拒绝")
    admin_reply: Optional[str] = Field(None, description="管理员回复")
    admin_id: Optional[str] = Field(None, description="处理管理员ID")
    
class FeedbackCreateRequest(BaseAPIModel):
    """反馈创建请求"""
    content: str = Field(..., description="反馈内容")
    type: str = Field("bug", description="反馈类型：bug-问题反馈, suggestion-建议, other-其他")
    contact: Optional[str] = Field(None, description="联系方式")
    images: Optional[List[str]] = Field(None, description="图片URL列表")
    device_info: Optional[DeviceInfo] = Field(None, description="设备信息")

class FeedbackUpdateRequest(BaseAPIModel):
    """反馈更新请求"""
    content: Optional[str] = Field(None, description="反馈内容")
    type: Optional[str] = Field(None, description="反馈类型：bug-问题反馈, suggestion-建议, other-其他")
    status: Optional[str] = Field(None, description="反馈状态：pending-待处理, processing-处理中, resolved-已解决, rejected-已拒绝")
    admin_reply: Optional[str] = Field(None, description="管理员回复")
    admin_id: Optional[str] = Field(None, description="处理管理员ID")

class FeedbackListItem(BaseAPIModel):
    """反馈列表项"""
    id: int = Field(..., description="反馈ID")
    content: str = Field(..., description="反馈内容")
    type: str = Field(..., description="反馈类型")
    status: str = Field(..., description="反馈状态")
    create_time: str = Field(..., description="创建时间")
    has_reply: bool = Field(False, description="是否有回复")
    
class FeedbackQueryParams(BaseAPIModel):
    """反馈查询参数"""
    type: Optional[str] = Field(None, description="反馈类型：bug-问题反馈, suggestion-建议, other-其他")
    status: Optional[str] = Field(None, description="反馈状态：pending-待处理, processing-处理中, resolved-已解决, rejected-已拒绝")
    limit: int = Field(20, description="返回记录数量限制", ge=1, le=100)
    offset: int = Field(0, description="分页偏移量", ge=0)

class FeedbackListResponse(BaseAPIModel):
    """反馈列表响应"""
    feedback_list: List[FeedbackListItem] = Field(default_factory=list, description="反馈列表")
    total: int = Field(0, description="总数量")
    limit: int = Field(20, description="每页数量")
    offset: int = Field(0, description="偏移量") 