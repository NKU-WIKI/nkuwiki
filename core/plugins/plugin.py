import os
import json
from config import Config
from core.utils.logger import register_logger

class Plugin:
    def __init__(self):
        self.logger = register_logger(f"core.plugins.{self.__class__.__name__}")
        self.handlers = {}
        self.name = "BasePlugin"  # 添加默认名称属性
        # ...其他属性初始化...

    def load_config(self) -> dict:
        """
        加载当前插件配置
        :return: 插件配置字典
        """
        # 优先获取 plugins/config.json 中的全局配置
        plugin_conf = Config().get(self.name)
        if not plugin_conf:
            # 全局配置不存在，则获取插件目录下的配置
            plugin_config_path = os.path.join(self.path, "config.json")
            self.logger.debug(f"loading plugin config, plugin_config_path={plugin_config_path}, exist={os.path.exists(plugin_config_path)}")
            if os.path.exists(plugin_config_path):
                with open(plugin_config_path, "r", encoding="utf-8") as f:
                    plugin_conf = json.load(f)

                # 写入全局配置内存
                Config.write_plugin_config({self.name: plugin_conf})
        self.logger.debug(f"loading plugin config, plugin_name={self.name}, conf={plugin_conf}")
        return plugin_conf

    def save_config(self, config: dict):
        try:
            Config.write_plugin_config({self.name: config})
            # 写入全局配置
            global_config_path = "./plugins/config.json"
            if os.path.exists(global_config_path):
                with open(global_config_path, "w", encoding='utf-8') as f:
                    json.dump(Config(), f, indent=4, ensure_ascii=False)
            # 写入插件配置
            plugin_config_path = os.path.join(self.path, "config.json")
            if os.path.exists(plugin_config_path):
                with open(plugin_config_path, "w", encoding='utf-8') as f:
                    json.dump(config, f, indent=4, ensure_ascii=False)

        except Exception as e:
            self.logger.warn("save plugin config failed: {}".format(e))

    def get_help_text(self, **kwargs):
        return "暂无帮助信息"

    def reload(self):
        pass
