"""
图像处理工具模块
提供图像压缩、格式转换等基础图像处理函数
"""
import io
import os
from urllib.parse import urlparse
from typing import Optional, Union, BinaryIO

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


def fsize(file: Union[str, io.BytesIO, BinaryIO]) -> int:
    """
    获取文件大小
    
    Args:
        file: 文件路径、BytesIO对象或支持seek和tell的文件对象
        
    Returns:
        文件大小（字节数）
        
    Raises:
        TypeError: 不支持的文件类型
    """
    if isinstance(file, io.BytesIO):
        return file.getbuffer().nbytes
    elif isinstance(file, str):
        return os.path.getsize(file)
    elif hasattr(file, "seek") and hasattr(file, "tell"):
        pos = file.tell()
        file.seek(0, os.SEEK_END)
        size = file.tell()
        file.seek(pos)
        return size
    else:
        raise TypeError("不支持的文件类型")


def compress_imgfile(file: Union[str, io.BytesIO, BinaryIO], max_size: int) -> Optional[io.BytesIO]:
    """
    压缩图像文件到指定大小以下
    
    Args:
        file: 图像文件（路径、BytesIO对象或类文件对象）
        max_size: 压缩后的最大大小（字节数）
        
    Returns:
        压缩后的图像文件（BytesIO对象），如果压缩失败则返回None
    """
    if not PIL_AVAILABLE:
        raise ImportError("PIL库未安装，无法进行图像处理")
        
    try:
        # 如果文件已经小于最大尺寸，直接返回
        if fsize(file) <= max_size:
            if isinstance(file, io.BytesIO):
                file.seek(0)
                return file
            else:
                # 将文件转换为BytesIO对象
                if isinstance(file, str):
                    with open(file, 'rb') as f:
                        buf = io.BytesIO(f.read())
                else:
                    file.seek(0)
                    buf = io.BytesIO(file.read())
                buf.seek(0)
                return buf
        
        # 需要压缩，先读取图像
        if isinstance(file, str):
            img = Image.open(file)
        else:
            file.seek(0)
            img = Image.open(file)
            
        # 转换为RGB模式
        rgb_image = img.convert("RGB")
        
        # 通过降低质量来压缩
        quality = 95
        while True:
            out_buf = io.BytesIO()
            rgb_image.save(out_buf, "JPEG", quality=quality)
            if fsize(out_buf) <= max_size:
                out_buf.seek(0)
                return out_buf
            quality -= 5
            if quality < 10:  # 质量已经很低，但仍然太大
                # 尝试缩小图像尺寸
                width, height = rgb_image.size
                rgb_image = rgb_image.resize((int(width * 0.8), int(height * 0.8)), Image.LANCZOS)
                if rgb_image.width < 100 or rgb_image.height < 100:  # 图像已经很小了
                    break
    except Exception as e:
        from core.utils.logger import logger
        logger.error(f"图像处理错误: {str(e)}")
        return None
        
    return None


def get_path_suffix(path: str) -> str:
    """
    获取路径的后缀（文件扩展名）
    
    Args:
        path: 文件路径或URL
        
    Returns:
        文件扩展名（不包含点）
    """
    path = urlparse(path).path
    return os.path.splitext(path)[-1].lstrip('.')


def convert_webp_to_png(webp_image: Union[str, io.BytesIO, BinaryIO]) -> io.BytesIO:
    """
    将WebP图像转换为PNG格式
    
    Args:
        webp_image: WebP图像（路径、BytesIO对象或类文件对象）
        
    Returns:
        PNG格式的图像（BytesIO对象）
        
    Raises:
        ImportError: PIL库未安装
        Exception: 转换过程中的其他错误
    """
    if not PIL_AVAILABLE:
        raise ImportError("PIL库未安装，无法进行图像转换")
        
    try:
        # 打开图像
        if isinstance(webp_image, str):
            img = Image.open(webp_image).convert("RGBA")
        else:
            webp_image.seek(0)
            img = Image.open(webp_image).convert("RGBA")
            
        # 保存为PNG
        png_image = io.BytesIO()
        img.save(png_image, format="PNG")
        png_image.seek(0)
        return png_image
    except Exception as e:
        from core.utils.logger import logger
        logger.error(f"WebP转PNG失败: {str(e)}")
        raise 