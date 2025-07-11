"""
微信小程序关于页API
提供小程序关于页信息
"""
from fastapi import APIRouter
from api.models.common import Response
from config import Config

router = APIRouter()
config = Config()

@router.get("", summary="获取关于信息")
async def get_about_info():
    """
    获取"关于我们"页面的信息，通常是静态配置。
    """
    about_info = config.get("services.app.aboutinfo")
    if about_info:
        return Response.success(data=about_info)
    else:
        return Response.error(message="关于信息未配置") 