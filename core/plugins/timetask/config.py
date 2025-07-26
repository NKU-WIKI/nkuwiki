"""
定时任务插件配置
"""

import json
import os
from typing import Dict, Any
from loguru import logger

# 插件配置
plugin_config = {
    "command_prefix": "$time",  # 命令前缀
    "remind_add_success": "查看任务【$time 任务列表】\n取消任务【$time 取消任务 1】\n发送格式【$time 每天 10:00 吃饭】",  # 添加任务成功提示
    "remind_add_failed": "查看格式【$time help】",  # 添加任务失败提示
    "remind_cancel_success": "查看任务【$time 任务列表】\n添加任务【$time 明天 10:00 吃饭】",  # 取消任务成功提示
    "remind_cancel_failed": "查看任务【$time 任务列表】\n添加任务【$time 明天 10:00 吃饭】",  # 取消任务失败提示
    "remind_no_task": "添加任务【$time 明天 10:00 吃饭】",  # 没有任务提示
    "remind_tasklist_success": "\n取消任务【$time 取消任务 1】\n添加任务【$time 明天 10:00 吃饭】",  # 获取任务列表成功提示
    "data_file": "data/plugins/timetask/timetask.xlsx",  # 数据文件
}

def load_config():
    """加载配置文件"""
    global plugin_config
    config_path = os.path.join(os.path.dirname(__file__), "config.json")
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                plugin_config.update(json.load(f))
                logger.debug("[TimeTask] 配置加载成功")
        except Exception as e:
            logger.error(f"[TimeTask] 配置加载失败: {e}")
    
    # 确保数据目录存在
    data_dir = os.path.dirname(plugin_config["data_file"])
    os.makedirs(data_dir, exist_ok=True)

def conf() -> Dict[str, Any]:
    """获取配置"""
    return plugin_config 