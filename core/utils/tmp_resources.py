"""
临时资源工具模块
提供临时目录、临时文件等资源管理功能
"""
import os
import pathlib
import tempfile
import shutil
from typing import Optional


class TmpDir:
    """临时目录管理器，在对象销毁时可选择性地删除目录"""
    
    def __init__(self, base_path: str = "./tmp/", auto_clean: bool = False):
        """
        初始化临时目录
        
        Args:
            base_path: 临时目录基础路径
            auto_clean: 是否在对象销毁时自动清理
        """
        self.tmp_file_path = pathlib.Path(base_path)
        self.auto_clean = auto_clean
        
        # 确保目录存在
        if not os.path.exists(self.tmp_file_path):
            os.makedirs(self.tmp_file_path, exist_ok=True)
    
    def path(self) -> str:
        """返回临时目录路径"""
        return str(self.tmp_file_path) + "/"
    
    def create_subdir(self, subdir_name: str) -> str:
        """
        在临时目录下创建子目录
        
        Args:
            subdir_name: 子目录名
            
        Returns:
            子目录的完整路径
        """
        subdir_path = self.tmp_file_path / subdir_name
        os.makedirs(subdir_path, exist_ok=True)
        return str(subdir_path) + "/"
    
    def clean(self) -> bool:
        """
        清理临时目录
        
        Returns:
            是否成功清理
        """
        try:
            if os.path.exists(self.tmp_file_path):
                shutil.rmtree(self.tmp_file_path)
            return True
        except Exception as e:
            from core.utils.logger import logger
            logger.error(f"清理临时目录失败: {str(e)}")
            return False
    
    def __del__(self):
        """析构函数，可选择性地清理临时目录"""
        if self.auto_clean:
            self.clean()


def create_tmp_file(content: str = "", suffix: str = "", prefix: str = "tmp_", 
                    dir: Optional[str] = None, encoding: str = "utf-8") -> str:
    """
    创建临时文件
    
    Args:
        content: 写入临时文件的内容
        suffix: 临时文件后缀
        prefix: 临时文件前缀
        dir: 临时文件所在目录，None则使用系统临时目录
        encoding: 文件编码
        
    Returns:
        临时文件的路径
    """
    try:
        # 创建临时文件
        fd, tmp_path = tempfile.mkstemp(suffix=suffix, prefix=prefix, dir=dir, text=True)
        
        # 写入内容
        with os.fdopen(fd, 'w', encoding=encoding) as f:
            f.write(content)
            
        return tmp_path
    except Exception as e:
        from core.utils.logger import logger
        logger.error(f"创建临时文件失败: {str(e)}")
        raise


def create_tmp_binary_file(content: bytes, suffix: str = "", prefix: str = "tmp_", 
                          dir: Optional[str] = None) -> str:
    """
    创建二进制临时文件
    
    Args:
        content: 写入临时文件的二进制内容
        suffix: 临时文件后缀
        prefix: 临时文件前缀
        dir: 临时文件所在目录，None则使用系统临时目录
        
    Returns:
        临时文件的路径
    """
    try:
        # 创建临时文件
        fd, tmp_path = tempfile.mkstemp(suffix=suffix, prefix=prefix, dir=dir, text=False)
        
        # 写入内容
        with os.fdopen(fd, 'wb') as f:
            f.write(content)
            
        return tmp_path
    except Exception as e:
        from core.utils.logger import logger
        logger.error(f"创建二进制临时文件失败: {str(e)}")
        raise 