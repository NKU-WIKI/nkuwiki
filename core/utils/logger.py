"""
日志配置模块
提供日志初始化和配置功能
"""
import os
import sys
from pathlib import Path
from loguru import logger

# 移除默认处理器
logger.remove()

# 定义导出的符号列表
__all__ = [
    'logger',
    'register_logger'
]

# 配置项
LOG_ROOT_DIR = Path("logs")
LOG_FORMAT = "{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} - {message}"
LOG_CONSOLE_FORMAT = "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"

# 确保日志根目录存在
LOG_ROOT_DIR.mkdir(exist_ok=True)

# 添加控制台处理器（警告及以上级别）
logger.add(
    sys.stderr,
    level="WARNING",
    format=LOG_CONSOLE_FORMAT
)

# 添加全局文件处理器
logger.add(
    LOG_ROOT_DIR / "nkuwiki.log",
    rotation="10 MB",
    retention="1 week",
    level="DEBUG",
    format=LOG_FORMAT,
    enqueue=True
)

# 添加警告级别专用日志处理器
logger.add(
    LOG_ROOT_DIR / "nkuwiki(warning).log",
    rotation="10 MB",
    retention="1 week",
    level="WARNING",
    format=LOG_FORMAT,
    enqueue=True,
    filter=lambda record: record["level"].no >= logger.level("WARNING").no
)

def register_logger(module_name: str):
    """
    为指定模块注册专用的日志记录器
    
    Args:
        module_name: 模块名称，例如'api.wxapp'，'core.agent'等
        
    Returns:
        专用的日志记录器实例
    """
    # 根据模块名创建日志目录路径
    module_parts = module_name.split('.')
    module_log_dir = LOG_ROOT_DIR
    
    # 如果是多级模块，创建相应的目录结构
    if len(module_parts) > 1:
        # 创建一级模块目录，例如'api'、'core'等
        main_module = module_parts[0]
        module_log_dir = LOG_ROOT_DIR / main_module
        module_log_dir.mkdir(exist_ok=True)
    
    # 创建模块日志文件路径
    log_filename = f"{module_name.replace('.', '_')}.log"
    module_log_file = module_log_dir / log_filename
    
    # 创建绑定了模块名的日志记录器
    module_logger = logger.bind(name=module_name)
    
    # 为该模块添加文件处理器
    logger.add(
        module_log_file,
        rotation="5 MB",
        retention="1 week",
        level="DEBUG",
        format=LOG_FORMAT,
        filter=lambda record: record["extra"].get("name") == module_name,
        enqueue=True
    )
    
    # 记录模块日志初始化信息
    module_logger.debug(f"{module_name} 日志记录器初始化完成，日志文件: {module_log_file}")
    
    return module_logger

# 初始化常用模块的日志目录
for module in ["api", "core", "etl", "services"]:
    module_dir = LOG_ROOT_DIR / module
    module_dir.mkdir(exist_ok=True)

# 禁用某些库的冗余日志
import logging
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

# 记录日志系统初始化完成信息
logger.info("nkuwiki 日志系统初始化完成")
