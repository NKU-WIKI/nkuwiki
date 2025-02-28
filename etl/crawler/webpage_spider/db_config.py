import os
import pickle
import json
import copy
from singleton_decorator import singleton
from loguru import logger

# 默认配置值，config.json中未配置的项会使用此处的默认值
available_setting = {
    # 数据库配置项
    "db_host": "localhost",  # 数据库主机地址，类型str，默认"localhost"
    "db_port": 3306,  # 数据库端口，类型int，默认3306
    "db_user": "root",  # 数据库用户名，类型str，默认"root"
    "db_password": "",  # 数据库密码，类型str，默认为空
    "db_name": "mysql",  # 数据库名称，类型str，默认"mysql"
    "data_path": "",  # 数据存储路径，类型str，默认为空
    "proxy_pool": "http://127.0.0.1:7897",  # 代理池地址，类型str，URL格式
}

@singleton
class Config(dict):
    """配置管理单例类，继承字典类型实现配置存储
    
    属性:
        user_datas: 用户数据存储字典
        logger: 日志记录器实例
    """
    def __init__(self, d=None):
        """初始化配置实例
        
        Args:
            d: 初始配置字典，默认为None
        """
        super().__init__()
        self.update(available_setting)
        if d is None:
            d = {}
        # 统一转换为小写键名
        d = {k.lower(): v for k, v in d.items()}
        for k, v in d.items():
            self[k] = v
        self.user_datas = {}
        self.plugin_config = {}

    def __getitem__(self, key):
        """重写字典获取项方法，实现配置键名大小写不敏感"""
        key = key.lower()  # 统一转小写
        if key not in available_setting:
            raise Exception(f"无效配置项：{key}")
        return super().__getitem__(key)

    def get(self, key, default=None):
        """安全获取配置项方法
        
        Args:
            key: 配置键名
            default: 默认返回值，默认为None
            
        Returns:
            配置项值或默认值
        """
        try:
            return self[key.lower()]  # 统一转小写
        except KeyError:
            return default
        except Exception as e:
            self.logger.exception(f"[config] 配置获取异常")
            return default
        
    @staticmethod
    def get_root():
        """获取配置文件根目录路径
        
        Returns:
            str: 当前文件的绝对路径目录
        """
        return os.path.dirname(os.path.abspath(__file__))
    
    @staticmethod
    def read_file(path):
        """读取文件内容
        
        Args:
            path: 文件路径
            
        Returns:
            str: 文件内容字符串
        """
        with open(path, mode="r", encoding="utf-8") as f:
            return f.read()
        
    def get_appdata_dir(self):
        """获取应用数据存储目录，自动创建不存在的目录
        
        Returns:
            str: 数据存储目录路径
        """
        data_path = os.path.join(self.get_root(), self.get("appdata_dir", ""))
        if not os.path.exists(data_path):
            self.logger.info("[INIT] data path not exists, create it: {}".format(data_path))
            os.makedirs(data_path)
        return data_path
    
    def get_user_data(self, user) -> dict:
        """获取指定用户数据字典
        
        Args:
            user: 用户标识符
            
        Returns:
            dict: 用户数据字典
        """
        if self.user_datas.get(user) is None:
            self.user_datas[user] = {}
        return self.user_datas[user]

    def load_user_datas(self):
        """从持久化存储加载用户数据"""
        try:
            with open(os.path.join(self.get_appdata_dir(), "user_datas.pkl"), "rb") as f:
                self.user_datas = pickle.load(f)
                self.logger.info("[Config] User datas loaded.")
        except FileNotFoundError as e:
            self.logger.debug("[Config] User datas file not found, ignore.")
        except Exception as e:
            self.logger.debug("[Config] User datas error")
            self.user_datas = {}

    def save_user_datas(self):
        """持久化保存用户数据到文件"""
        try:
            import copy
            save_data = copy.deepcopy(self.user_datas)
            for user in list(save_data.keys()):
                for key in list(save_data[user].keys()):
                    if not isinstance(save_data[user][key], (str, int, float, bool, list, dict)):
                        del save_data[user][key]
            
            with open(os.path.join(self.get_appdata_dir(), "user_datas.pkl"), "wb") as f:
                pickle.dump(save_data, f)
                self.logger.info("[Config] User datas saved.")
        except Exception as e:
            self.logger.error(f"[Config] 保存用户数据失败: {str(e)}")

    def drag_sensitive(self):
        """生成脱敏后的配置信息
        
        Returns:
            dict: 脱敏处理后的配置字典
        """
        try:
            if isinstance(self, str):
                conf_dict: dict = json.loads(self)
                conf_dict_copy = copy.deepcopy(conf_dict)
                for key in conf_dict_copy:
                    if "key" in key or "secret" in key:
                        if isinstance(conf_dict_copy[key], str):
                            conf_dict_copy[key] = conf_dict_copy[key][0:3] + "*" * 5 + conf_dict_copy[key][-3:]
                return json.dumps(conf_dict_copy, indent=4)

            elif isinstance(self, dict):
                config_copy = copy.deepcopy({k: v for k, v in self.items()})
                for key in config_copy:
                    if "key" in key or "secret" in key:
                        if isinstance(config_copy[key], str):
                            config_copy[key] = config_copy[key][0:3] + "*" * 5 + config_copy[key][-3:]
                return config_copy
            else:
                config_copy = copy.deepcopy(dict(self))
                config_copy.pop('logger', None)
                config_copy.pop('user_datas', None)
                return config_copy
        except Exception as e:
            self.logger.exception(e)
            return self
        
    def write_plugin_config(self, pconf: dict):
        """写入插件全局配置
        
        Args:
            pconf: 插件配置字典
        """
        for k in pconf:
            self.plugin_config[k.lower()] = pconf[k]

    def remove_plugin_config(self, name: str):
        """移除待重新加载的插件配置
        
        Args:
            name: 插件名称
        """
        self.plugin_config.pop(name.lower(), None)

    def pconf(self, plugin_name: str) -> dict:
        """获取指定插件配置
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            dict: 插件配置字典
        """
        return self.plugin_config.get(plugin_name.lower())
    
    def subscribe_msg(self):
        """生成订阅消息模板
        
        Returns:
            str: 格式化后的订阅消息
        """
        trigger_prefix = self.get("single_chat_prefix", [""])[0]
        msg = self.get("subscribe_msg", "")
        return msg.format(trigger_prefix=trigger_prefix)
    
    def load_config(self, logger = logger):
        """加载配置文件并初始化配置
        
        Args:
            logger: 日志记录器实例，默认为全局logger
            
        Returns:
            self: 配置实例
        """
        self.logger = logger
        parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
        config_path = os.path.join(parent_dir, "config.json")
        try:
            with open(config_path, "r", encoding="utf-8-sig") as f:
                config_str = f.read()
                config_data = json.loads(config_str)
                config_data = {k.lower(): v for k, v in config_data.items()}
                self.update(config_data)
        except json.JSONDecodeError as e:
            self.logger.exception(f"[config] 配置文件格式错误")
        self.logger.debug("[config] load config: {}".format(self.drag_sensitive()))
        self.load_user_datas()
        return self

# 全局配置，用于存放全局生效的状态
# global_config = {
#     "admin_users": []
# }


# def get_model_config(model_name: str) -> dict:
#     """安全获取模型配置"""
#     global plugin_config
#     config = plugin_config.get(model_name)
#     if not isinstance(config, dict):
#         App().logger.warning(f"模型{model_name}配置格式错误，预期字典类型")
#         return {}
#     return config