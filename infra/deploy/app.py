# encoding:utf-8

import sys
import os
from pathlib import Path
# 获取项目根目录路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# 添加核心模块路径
sys.path.extend([
    project_root,
    os.path.join(project_root, 'core'),
    os.path.join(project_root, 'core/bridge'),
    os.path.join(project_root, 'services'),
    os.path.join(project_root, 'core/utils'),
    os.path.join(project_root, 'core/bridge'),
    os.path.join(project_root, 'core/agent'),
    os.path.join(project_root, 'infra'),
])

import signal
import time

from services import channel_factory
from core.utils.common import const
from core.utils.plugins import *
from loguru import logger
# from core.utils.plugins.plugin_manager import PluginManager


class App:
    def __init__(self):
        log_day_str = '{time:%Y-%m-%d}'
        self.base_log_dir = Path(__file__).resolve().parent.parent / 'logs'
        self.base_log_dir.mkdir(exist_ok=True, parents=True)  # 创建目录，如果目录不存在
        logger.add(f'{self.base_log_dir}/app_{log_day_str}.log', rotation="1 day", retention='3 months', level="INFO")
        from config import load_config
        from config import conf
        load_config()
        self.sigterm_handler_wrap(signal.SIGINT)
        self.sigterm_handler_wrap(signal.SIGTERM)
        self.support_channel = conf().get("support_channel")
        self.channel_name = conf().get("channel_type")
        self.model = conf().get("model")
        
    def sigterm_handler_wrap(self, _signo):
        self.old_handler = signal.getsignal(_signo)

    def func(self, _signo, _stack_frame):
        logger.info("signal {} received, exiting...".format(_signo))
        from config import conf
        conf().save_user_datas()
        if callable(self.old_handler):  #  check old_handler
            return self.old_handler(_signo, _stack_frame)
        signal.signal(_signo, self.func)
        sys.exit(0)

    def run(self):
        if self.channel_name in self.support_channel:
            # PluginManager().load_plugins()
            channel = channel_factory.create_channel(self.channel_name)
            logger.info(f"start channel {self.channel_name}...")
            channel.startup()
            
        else:
            logger.error(f"channel {self.channel_name} not supported, support channel: {self.support_channel}")
            sys.exit(1)
        while True:
            time.sleep(1)

if __name__ == "__main__":
    app = App()
    app.run()
