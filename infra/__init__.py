"""
Infra模块，负责提供基础设施功能

此模块提供部署、监控和性能评测等基础功能，为整个项目提供底层支持服务。

子模块:
- deploy: 项目部署工具
- monitoring: 系统监控工具
- benchmark: 性能评测工具
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))
from config import Config

# 导入配置
config = Config()

# 使用core中的日志模块
from core.utils.logger import register_logger

# 初始化基础设施模块日志
infra_logger = register_logger("infra")
infra_logger.debug("Infra模块日志初始化完成")

# 版本信息
__version__ = "1.0.0"

# 定义导出的符号列表
__all__ = [
    'config', 'infra_logger', 'LOG_PATH'
]

# Infra模块主要功能：
# 1. 提供部署工具，支持Docker和Kubernetes部署
# 2. 提供监控工具，支持系统状态监控和告警
# 3. 提供性能评测工具，支持压力测试和性能分析
