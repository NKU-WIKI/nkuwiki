"""
微信小程序 - 文件上传接口
"""
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import List

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Form
from PIL import Image

from api.common.dependencies import get_current_active_user
from api.models.common import Response
from core.utils.logger import register_logger
from config import Config

# ------------------------------
# 配置和初始化
# ------------------------------
config = Config()
logger = register_logger('api.routes.wxapp.upload')
router = APIRouter()

# 从配置中获取域名和上传设置
# 确保在 config.json 中有 'app_host' 字段，例如 "https://nkuwiki.com"
APP_HOST = config.get("services.weapp.base_url", "https://nkuwiki.com")
UPLOAD_DIR = Path("/data/uploads")
# 确保目录存在
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# 允许的图片类型
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/gif"}
# 图片质量 (0-100)
IMAGE_QUALITY = 85


# ------------------------------
# 内部帮助函数
# ------------------------------
def _is_image(file: UploadFile) -> bool:
    """检查文件是否为允许的图片类型"""
    return file.content_type in ALLOWED_IMAGE_TYPES

def _sanitize_filename(filename: str) -> str:
    """
    生成一个安全且唯一的文件名。
    格式: YYYYMM/uuid.extension
    """
    # 提取文件扩展名
    extension = Path(filename).suffix.lower()
    if not extension:
        extension = ".jpg" # 默认扩展名

    # 创建基于年月日的子目录
    date_path = datetime.now().strftime("%Y%m")
    save_dir = UPLOAD_DIR / date_path
    save_dir.mkdir(parents=True, exist_ok=True)
    
    # 生成唯一文件名
    unique_name = f"{uuid.uuid4()}{extension}"
    
    return str(save_dir / unique_name)

# ------------------------------
# API端点
# ------------------------------
@router.post("/image", summary="上传单个图片")
async def upload_single_image(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_active_user)
):
    """
    上传单个图片文件。
    - 需要用户认证。
    - 文件将被压缩并保存。
    - 返回图片的公开访问URL。
    """
    if not _is_image(file):
        return Response.bad_request(details="不支持的文件类型，请上传jpeg, png或gif格式的图片。")

    # 生成安全的文件保存路径
    save_path_str = _sanitize_filename(file.filename)
    save_path = Path(save_path_str)

    try:
        # 使用Pillow处理图片
        img = Image.open(file.file)
        
        # 转换为RGB以统一格式 (特别是对于RGBA的PNG)
        if img.mode in ('RGBA', 'P'):
            img = img.convert('RGB')
            
        # 保存压缩后的图片
        img.save(save_path, format='JPEG', quality=IMAGE_QUALITY, optimize=True)

    except Exception as e:
        logger.error(f"处理图片失败: {e}", exc_info=True)
        return Response.error(details="图片处理失败，请稍后重试。")

    # 构建可访问的URL
    # save_path 现在是绝对路径: /data/uploads/202310/some-uuid.jpg
    # 我们需要移除 /data/uploads 部分，然后加上 /static 前缀
    url_path_part = save_path.relative_to(UPLOAD_DIR)
    url_path = f"/static/{url_path_part.as_posix()}"
    full_url = f"{APP_HOST}{url_path}"

    return Response.success(data={"url": full_url}, details="图片上传成功") 