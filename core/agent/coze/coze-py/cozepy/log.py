"""
CozePy日志工具

使用项目自定义的日志系统而不是标准logging模块
"""
import sys
import os
# 加入系统路径以能够导入core包
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))))

try:
    from core.utils.logger import register_logger
    # 创建cozepy专用日志记录器
    logger = register_logger("core.agent.coze")
except ImportError:
    # 如果无法导入自定义日志系统，则回退到简单的控制台输出
    import logging
    logging.basicConfig(format="[cozepy][%(levelname)s][%(asctime)s] %(message)s", 
                       datefmt="%Y-%m-%d %H:%M:%S",
                       level=logging.ERROR)
    logger = logging.getLogger("cozepy")
    logger.propagate = False


def setup_logging(level: str = "ERROR") -> None:
    """
    设置日志级别
    
    Args:
        level: 日志级别，可以是 "FATAL", "ERROR", "WARNING", "INFO", "DEBUG", "NOTSET"
    """
    valid_levels = ["FATAL", "ERROR", "WARNING", "INFO", "DEBUG", "NOTSET"]
    if level not in valid_levels:
        raise ValueError(f"无效的日志级别: {level}")
    
    try:
        # 由于是loguru，不需要设置日志级别，它使用bind方式
        pass
    except Exception as e:
        print(f"设置日志级别失败: {e}")


# 导出日志函数
log_fatal = logger.critical
log_error = logger.error
log_warning = logger.warning
log_info = logger.info
log_debug = logger.debug

# 默认设置为ERROR级别
setup_logging("ERROR")
