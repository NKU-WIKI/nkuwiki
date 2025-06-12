"""
微信小程序关于页API
提供小程序关于页信息
"""
from fastapi import APIRouter
from api.models.common import Response, Request
from config import Config
config = Config()
router = APIRouter()

@router.get("/about")
async def get_about_info():
    """获取小程序关于页信息"""
    try:
        about_info = config.get("services.app.aboutinfo")
        return Response.success(data=about_info)
    except Exception as e:
        return Response.error(message=f"获取关于页信息失败: {str(e)}") 