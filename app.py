"""应用主入口模块，负责服务启动、配置加载和插件管理"""

import sys
import time
from loguru import logger
from config import Config
from pathlib import Path
from services import channel_factory
from singleton_decorator import singleton
from core.utils.plugins.plugin_manager import PluginManager
@singleton
class App:
    """应用核心类，采用单例模式管理全局状态
    
    属性：
        logger: 日志记录器实例
        channel_factory: 渠道工厂对象
        support_channel: 支持的渠道列表
        channel_name: 当前渠道类型
        model: 当前AI模型
    """
    
    def __init__(self):
        """初始化应用实例，加载配置并设置日志系统"""
        log_day_str = '{time:%Y-%m-%d}'
        self.base_log_dir = Path('./infra/deploy/log')
        self.base_log_dir.mkdir(exist_ok=True, parents=True)
        
        self.logger = logger
        self.logger.add(f'{self.base_log_dir}/app_{log_day_str}.log',
                 rotation="1 day", retention='3 months', level="INFO")
        
        Config().load_config(self.logger)
        PluginManager().load_plugins()
        self._setup_signal_handlers()
        
        self.channel_factory = channel_factory
        self.support_channel = Config().get("support_channel")
        self.channel_name = Config().get("channel_type")
        self.model = Config().get("model")

    def _setup_signal_handlers(self):
        """设置信号处理函数，用于优雅退出"""
        import signal
        self.old_handlers = {}
        for sig in [signal.SIGINT, signal.SIGTERM]:
            self.old_handlers[sig] = signal.getsignal(sig)
            signal.signal(sig, self._handle_signal)

    def _handle_signal(self, signum, frame):
        """信号处理回调函数
        Args:
            signum: 信号编号
            frame: 当前执行栈帧
        """
        self.logger.info(f"Signal {signum} received, exiting...")
        Config.save_user_datas()
        if callable(self.old_handlers.get(signum)):
            self.old_handlers[signum](signum, frame)
        sys.exit(0)

    def run(self):
        """启动主运行循环，加载插件并初始化指定渠道"""
        if self.channel_name in self.support_channel:
            channel = self.channel_factory.create_channel(self.channel_name)
            self.logger.info(f"Starting channel {self.channel_name}...")
            channel.startup()
        else:
            self.logger.error(f"Unsupported channel: {self.channel_name}")
            sys.exit(1)
            
        while True:  # 保持主线程运行
            time.sleep(1)

if __name__ == "__main__":
    App().run()
