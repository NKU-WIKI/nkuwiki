"""
Services模块，负责提供多渠道服务接口

此模块实现了多种渠道（如终端、微信公众号、企业微信等）的交互功能，
为用户提供统一的访问入口，支持多种对话场景。

子模块:
- terminal: 终端服务，用于开发和调试
- wechatmp: 微信公众号服务
- wework: 企业微信服务
- weworktop: 企业微信桌面版服务
- website: 网站服务
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))
from config import Config

# 导入配置
config = Config()

# 创建日志目录并初始化日志
LOG_PATH = Path(__file__).resolve().parent / "logs"
LOG_PATH.mkdir(exist_ok=True, parents=True)

# 使用core中的日志模块
from core.utils.logger import init_logger, logger, get_module_logger

# 初始化服务模块日志
init_logger(LOG_PATH / "services.log", rotation="1 day", retention="3 months", level="DEBUG")
services_logger = get_module_logger("services")

# 版本信息
__version__ = "1.0.0"

# 定义导出的符号列表
__all__ = [
    'config', 'logger', 'services_logger', 'LOG_PATH'
]

# Services模块主要功能：
# 1. 提供多渠道服务接口，包括终端、微信公众号、企业微信等
# 2. 通过Channel基类定义统一的接口标准
# 3. 使用渠道工厂创建不同类型的渠道实例
# 4. 处理消息的接收、处理和发送
