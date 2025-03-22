"""
日志配置模块
提供日志初始化和配置功能
"""
import os
import sys
from pathlib import Path
from loguru import logger

def setup_logger(app_name: str = "nkuwiki"):
    """
    设置日志记录器配置
    
    Args:
        app_name: 应用名称，用于日志文件命名
    """
    # 创建日志目录
    log_dir = Path("logs")
    api_log_dir = log_dir / "api"
    
    # 确保日志目录存在
    os.makedirs(log_dir, exist_ok=True)
    os.makedirs(api_log_dir, exist_ok=True)
    
    # 移除默认处理器
    logger.remove()
    
    # 添加控制台处理器
    logger.add(
        sys.stderr,
        level="INFO",
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    )
    
    # 添加文件处理器 - 通用日志
    logger.add(
        log_dir / f"{app_name}.log",
        rotation="10 MB",
        retention="1 week",
        level="DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} - {message}",
        enqueue=True
    )
    
    # 添加API请求日志文件
    logger.add(
        api_log_dir / "api.log",
        rotation="10 MB",
        retention="1 week",
        level="DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} - {message}",
        filter=lambda record: "api" in record["name"],
        enqueue=True
    )
    
    # 添加API请求-响应日志文件
    logger.add(
        api_log_dir / "api_requests.log",
        rotation="10 MB",
        retention="1 week",
        level="DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
        filter=lambda record: "api.request" in record["name"],
        enqueue=True
    )
    
    # 创建各模块独立日志
    for module in ["wxapp", "mysql", "agent"]:
        module_log_dir = api_log_dir / module
        os.makedirs(module_log_dir, exist_ok=True)
        
        logger.add(
            module_log_dir / f"{module}.log",
            rotation="10 MB",
            retention="1 week",
            level="DEBUG",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} - {message}",
            filter=lambda record, m=module: f"api.{m}" in record["name"],
            enqueue=True
        )
    
    logger.info(f"{app_name} 日志系统初始化完成")
    return logger

# 提供快速访问特定模块日志记录器的函数
def get_module_logger(module_name: str):
    """
    获取特定模块的日志记录器
    
    Args:
        module_name: 模块名称
        
    Returns:
        模块专用的日志记录器
    """
    return logger.bind(name=module_name)

def get_api_logger(module: str = "api"):
    """
    获取API模块专用日志记录器
    
    Args:
        module: API子模块名称
        
    Returns:
        API模块专用的日志记录器
    """
    return logger.bind(name=f"api.{module}")

def get_request_logger():
    """
    获取请求日志记录器
    
    Returns:
        请求专用的日志记录器
    """
    return logger.bind(name="api.request") 