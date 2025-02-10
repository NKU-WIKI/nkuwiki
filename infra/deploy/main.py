# encoding:utf-8

import sys
import os

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
from config import load_config
from config import conf
from core.utils.plugins import *
import threading


def sigterm_handler_wrap(_signo):
    old_handler = signal.getsignal(_signo)

    def func(_signo, _stack_frame):
        logger.info("signal {} received, exiting...".format(_signo))
        conf().save_user_datas()
        if callable(old_handler):  #  check old_handler
            return old_handler(_signo, _stack_frame)
        sys.exit(0)

    signal.signal(_signo, func)


def start_channel(channel_name: str):
    channel = channel_factory.create_channel(channel_name)
    if channel_name in ["wx", "wxy", "terminal", "wechatmp","web", "wechatmp_service", "wechatcom_app", "wework",
                        const.FEISHU, const.DINGTALK]:
        PluginManager().load_plugins()

    channel.startup()


def run():
    try:
        # load config
        load_config()
        # ctrl + c
        sigterm_handler_wrap(signal.SIGINT)
        # kill signal
        sigterm_handler_wrap(signal.SIGTERM)
        
        # create channel
        channel_name = conf().get("channel_type")
        model = conf().get("model")
        logger.info(f"channel_name: {channel_name}")
        logger.info(f"model: {model}")
        if "--cmd" in sys.argv:
            channel_name = "terminal"

        start_channel(channel_name)

        while True:
            time.sleep(1)
    except Exception as e:
        logger.error("App startup failed!")
        logger.exception(e)


if __name__ == "__main__":
    run()
