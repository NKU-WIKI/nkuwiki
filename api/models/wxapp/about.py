"""
微信小程序关于页模型
"""
from typing import List
from pydantic import Field
from api.models.base import BaseAPIModel

class AboutInfoModel(BaseAPIModel):
    """关于页信息模型"""
    app_name: str = Field(..., description="应用名称")
    version: str = Field(..., description="版本号")
    description: str = Field(..., description="应用描述")
    team: str = Field(..., description="团队名称")
    contact: str = Field(..., description="联系方式")
    github: str = Field(..., description="GitHub仓库链接")
    values: List[str] = Field(..., description="价值观列表")
    goals: List[str] = Field(..., description="目标列表")
    copyright: str = Field(..., description="版权信息") 