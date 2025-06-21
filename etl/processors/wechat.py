"""
微信处理器

提供微信公众号文章处理功能
"""

import os
import sys
import subprocess
import platform
import asyncio
from pathlib import Path
from typing import Optional
from core.utils import register_logger

logger = register_logger("etl.processors.wechat")

class WechatProcessor:
    """微信公众号文章处理器"""
    
    def __init__(self, max_concurrent: int = 20):
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._executable_path = self._find_executable()
        
    def _find_executable(self) -> Optional[str]:
        """根据操作系统查找wechatmp2markdown可执行文件"""
        system = platform.system().lower()
        
        # 设置可执行文件匹配模式
        if system == "windows":
            pattern = "wechatmp2markdown*.exe"
        else:
            pattern = "wechatmp2markdown*"
        
        possible_paths = [
            # 同目录下
            Path(__file__).parent,
            # transform目录下
            Path(__file__).parent.parent / "transform",
            # 项目根目录下
            Path(__file__).parent.parent.parent,
        ]
        
        # 在可能的路径中查找匹配的可执行文件
        for path in possible_paths:
            matches = list(path.glob(pattern))
            if matches:
                exe_path = matches[0]
                # 在非Windows系统上检查并添加可执行权限
                if system != "windows":
                    try:
                        current_mode = exe_path.stat().st_mode
                        exe_path.chmod(current_mode | 0o111)
                    except Exception as e:
                        logger.warning(f"无法设置可执行权限: {e}")
                return str(exe_path)
                
        # 在系统PATH中查找
        if os.getenv('PATH'):
            for path in os.getenv('PATH').split(os.pathsep):
                matches = list(Path(path).glob(pattern))
                if matches:
                    exe_path = matches[0]
                    if system != "windows":
                        try:
                            current_mode = exe_path.stat().st_mode
                            exe_path.chmod(current_mode | 0o111)
                        except Exception as e:
                            logger.warning(f"无法设置可执行权限: {e}")
                    return str(exe_path)
        
        return None
    
    async def convert_to_markdown(
        self, 
        url: str, 
        output_dir: str, 
        image_option: str = 'url'
    ) -> bool:
        """异步将微信公众号文章转换为Markdown
        
        Args:
            url: 微信公众号文章URL
            output_dir: 输出目录路径
            image_option: 图片处理选项 ('save'或'url')
            
        Returns:
            转换是否成功
        """
        async with self._semaphore:
            if not self._executable_path:
                logger.error("未找到wechatmp2markdown可执行文件")
                return False
                
            # 构建命令
            cmd = [self._executable_path, url, str(output_dir), f"--image={image_option}"]
            
            try:
                logger.debug(f"执行命令: {' '.join(cmd)}")
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(None, lambda: subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    check=False
                ))
                
                if result.returncode == 0:
                    logger.debug("微信文章转换完成")
                    return True
                else:
                    logger.error(f"转换失败 (返回码: {result.returncode})")
                    if result.stdout:
                        logger.debug(f"输出: {result.stdout}")
                    if result.stderr:
                        logger.error(f"错误输出: {result.stderr}")
                    return False
                    
            except Exception as e:
                logger.error(f"转换过程中出错: {str(e)}")
                return False
    
    def convert_sync(
        self, 
        url: str, 
        output_dir: str, 
        image_option: str = 'url'
    ) -> bool:
        """同步版本的转换方法"""
        try:
            loop = asyncio.get_running_loop()
            # 在已有事件循环中执行
            return asyncio.run_coroutine_threadsafe(
                self.convert_to_markdown(url, output_dir, image_option), 
                loop
            ).result()
        except RuntimeError:
            # 如果没有正在运行的事件循环，则创建一个新的
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(
                    self.convert_to_markdown(url, output_dir, image_option)
                )
            finally:
                loop.close()


# 向后兼容的函数
async def wechatmp2md_async(original_url, data_path, image_option='url'):
    """向后兼容的异步转换函数"""
    processor = WechatProcessor()
    return await processor.convert_to_markdown(original_url, data_path, image_option)


def wechatmp2md(original_url, data_path, image_option='url'):
    """向后兼容的同步转换函数"""
    processor = WechatProcessor()
    return processor.convert_sync(original_url, data_path, image_option) 