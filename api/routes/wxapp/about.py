"""
微信小程序关于页API
提供小程序关于页信息
"""
from fastapi import Depends

from api import wxapp_router
from api.common import handle_api_errors, get_api_logger_dep
from api.models.wxapp.about import AboutInfoModel
from config import Config
config = Config()

@wxapp_router.get("/about", response_model=AboutInfoModel)
@handle_api_errors("获取关于页信息")
async def get_about_info(
    api_logger=Depends(get_api_logger_dep)
):
    """获取小程序关于页信息"""
    api_logger.debug("获取关于页信息")
    
    return AboutInfoModel(
        app_name="南开Wiki",
        version=config.get("services.app.version", "1.0.0"),
        description="南开Wiki是南开大学校园知识共享平台，致力于构建南开知识共同体，践行开源·共治·普惠三位一体价值体系。",
        team="南开Wiki开发团队",
        contact="contact@nkuwiki.com",
        github="https://github.com/ghost233lism/Nkuwiki",
        values=[
            "🔓 技术开源透明",
            "🤝 社区协同共治",
            "🆓 服务永久普惠"
        ],
        goals=[
            "🚀 消除南开学子信息差距",
            "💡 开放知识资源免费获取",
            "🌱 构建可持续的互助社区"
        ],
        copyright=f"© {config.get('services.app.copyright_year', '2025')} 南开Wiki团队"
    ) 