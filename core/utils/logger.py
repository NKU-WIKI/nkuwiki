"""
日志配置模块
提供日志初始化和配置功能
"""
import os
import sys
from pathlib import Path
from loguru import logger
import logging

# 移除默认处理器
logger.remove()

# 定义导出的符号列表
__all__ = [
    'logger',
    'register_logger',
    'setup_library_loggers'
]

# 配置项
LOG_ROOT_DIR = Path("logs")
LOG_FORMAT = "{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} - {message}"
LOG_CONSOLE_FORMAT = "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"

# 定义日志过滤函数
def filter_noise(record):
    """过滤掉一些无用的日志消息"""
    # 过滤掉包含以下内容的日志
    noise_patterns = [
        "register_logger:",
        "日志记录器初始化完成",
        "日志系统初始化完成",
        "cleanup_resources:",
        "开始清理资源",
        "数据库连接池已关闭",
        "正在关闭日志处理器",
        "MySQL连接池已清理",
        "资源清理完成"
    ]
    
    # 当系统正在启动或关闭时产生的常见日志
    startup_shutdown_patterns = [
        "初始化数据库线程池",
        "关闭数据库线程池"
    ]
    
    # 如果消息中包含任何噪音模式，则过滤掉
    message = record["message"]
    for pattern in noise_patterns:
        if pattern in message:
            return False
    
    # 确保我们有正确的数字类型进行比较
    try:
        record_level = record["level"].no
        error_level = logger.level("ERROR").no
    
        # 如果是启动/关闭相关的日志，只允许ERROR及以上级别通过
        for pattern in startup_shutdown_patterns:
            if pattern in message and record_level < error_level:
                return False
    
        # 过滤掉重复的初始化和清理类日志（避免循环启停时产生大量日志）
        if ("初始化" in message or "清理" in message or "关闭" in message) and record_level < error_level:
            return False
        
        # 过滤掉具有某些特定函数和模块的日志
        if record["function"] in ["cleanup_resources", "close_thread_pool", "cleanup_pool"] and record_level < error_level:
            return False
        
        # 特定过滤 __main__ 模块中的非错误日志
        if record["name"] == "__main__" and record_level < error_level:
            return False
    except (TypeError, ValueError, KeyError):
        # 如果出现任何类型转换问题，让日志通过
        pass
    
    return True

# 确保日志根目录存在
LOG_ROOT_DIR.mkdir(exist_ok=True)

# 添加控制台处理器（ERROR级别），过滤掉大部分日志
logger.add(
    sys.stderr,
    level="ERROR",
    format=LOG_CONSOLE_FORMAT,
    filter=filter_noise
)

# 添加全局文件处理器，记录所有INFO级别及以上的日志
logger.add(
    LOG_ROOT_DIR / "nkuwiki.log",
    rotation="10 MB",
    retention="1 week",
    level="INFO",
    format=LOG_FORMAT,
    enqueue=True,
    filter=filter_noise
)

# 添加调试日志处理器 - 包含所有详细日志，但只保留最近的
logger.add(
    LOG_ROOT_DIR / "debug.log",
    rotation="5 MB",
    retention="3 days",
    level="DEBUG",
    format=LOG_FORMAT,
    enqueue=True,
    filter=filter_noise
)

# 添加专用的API调用日志处理器 - 记录API请求和响应，包括详细信息
logger.add(
    LOG_ROOT_DIR / "api_calls.log",
    rotation="10 MB",
    retention="1 week",
    level="INFO",
    format=LOG_FORMAT,
    filter=lambda record: (
        ("API请求" in record["message"] or 
         "API响应" in record["message"] or 
         "请求体:" in record["message"]) and 
        filter_noise(record)
    ),
    enqueue=True
)

# 添加错误日志专用处理器 - 确保所有错误都被记录
logger.add(
    LOG_ROOT_DIR / "errors.log",
    rotation="10 MB",
    retention="1 week",
    level="ERROR",
    format=LOG_FORMAT,
    enqueue=True
)

_added_log_handlers = set()

def register_logger(module_name: str):
    """
    为指定模块注册专用的日志记录器，仅etl相关模块会创建独立日志文件
    
    Args:
        module_name: 模块名称，例如'api.wxapp'，'core.agent'等
        
    Returns:
        专用的日志记录器实例
    """
    # 只保留前两级模块名
    parts = module_name.split('.')
    short_name = '.'.join(parts[:2]) if len(parts) > 1 else parts[0]
    # 日志文件名
    file_name = short_name + ".log"
    # 日志文件路径始终在项目根目录 logs/
    file_path = Path("logs") / file_name
    # 创建绑定了模块名的日志记录器
    module_logger = logger.bind(name=module_name)
    # 只为etl相关模块添加文件handler
    key = (module_name, str(file_path))
    if "etl" in module_name and key not in _added_log_handlers:
        module_logger.add(
            file_path,
            rotation="10 MB",
            retention="7 days",
            level="DEBUG",
            format=LOG_FORMAT,
            enqueue=True,
            filter=lambda record: record["extra"].get("name") == module_name
        )
        _added_log_handlers.add(key)
    return module_logger

# 为了兼容使用标准logging的第三方库，使用loguru的拦截器
class InterceptHandler(logging.Handler):
    """
    拦截标准logging模块的日志，重定向到loguru
    """
    def __init__(self, level=logging.WARNING):
        super().__init__(level)
        
    def emit(self, record):
        # 获取对应的loguru级别
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # 找到发出日志的调用者
        frame, depth = sys._getframe(6), 6
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        # 将日志发送到loguru
        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )

def setup_library_loggers():
    """
    设置第三方库的日志拦截，使其通过loguru记录
    """
    # 移除所有现有的处理器
    logging.root.handlers = []
    
    # 添加拦截器
    handler = InterceptHandler(logging.WARNING)
    logging.root.addHandler(handler)
    
    # 设置日志级别
    logging.root.setLevel(logging.WARNING)
    
    # 设置常见库的日志级别
    for name in [
        "httpx", 
        "httpcore", 
        "uvicorn", 
        "uvicorn.access", 
        "urllib3", 
        "asyncio",
        "requests",
        "urllib3.connectionpool"
    ]:
        lib_logger = logging.getLogger(name)
        lib_logger.handlers = []
        lib_logger.addHandler(handler)
        lib_logger.propagate = False
        lib_logger.setLevel(logging.WARNING)

# 设置第三方库的日志拦截
setup_library_loggers()

# 记录日志系统初始化完成信息 - 使用DEBUG级别避免无用日志
logger.debug("nkuwiki 日志系统初始化完成")
