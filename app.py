# encoding:utf-8
import sys
import signal
import time
from loguru import logger
from config import Config
from pathlib import Path
from services import channel_factory
from singleton_decorator import singleton
from core.utils.plugins.plugin_manager import PluginManager
config = Config()
@singleton
class App():
    def __init__(self):
        log_day_str = '{time:%Y-%m-%d}'
        self.base_log_dir = Path('./infra/deploy/log')
        self.base_log_dir.mkdir(exist_ok=True, parents=True)
        self.logger = logger
        self.logger.add(f'{self.base_log_dir}/app_{log_day_str}.log', 
                 rotation="1 day", retention='3 months', level="INFO")
        config.load_config(self.logger)
        self._setup_signal_handlers()
        self.channel_factory = channel_factory
        self.support_channel = config.get("support_channel")
        self.channel_name = config.get("channel_type")
        self.model = config.get("model")

    def _setup_signal_handlers(self):
        import signal
        self.old_handlers = {}
        for sig in [signal.SIGINT, signal.SIGTERM]:
            self.old_handlers[sig] = signal.getsignal(sig)
            signal.signal(sig, self._handle_signal)

    def _handle_signal(self, signum, frame):
        self.logger.info(f"Signal {signum} received, exiting...")
        Config.save_user_datas()
        if callable(self.old_handlers.get(signum)):
            self.old_handlers[signum](signum, frame)
        sys.exit(0)

    def run(self):
        if self.channel_name in self.support_channel:
            PluginManager().load_plugins()
            channel = self.channel_factory.create_channel(self.channel_name)
            self.logger.info(f"Starting channel {self.channel_name}...")
            channel.startup()
        else:
            self.logger.error(f"Unsupported channel: {self.channel_name}")
            sys.exit(1)
        while True:
            time.sleep(1)

if __name__ == "__main__":
    
    App().run()
