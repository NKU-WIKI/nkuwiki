import os
import pickle
import json
import copy
from singleton_decorator import singleton
from loguru import logger

# 默认配置值，config.json中未配置的项会使用此处的默认值
available_setting = {
    # 支持的部署通道
    "support_channel": ["terminal", "wechatmp", "wechatmp_service"],
    # openai api配置
    "open_ai_api_key": "",  # openai api key
    # openai apibase，当use_azure_chatgpt为true时，需要设置对应的api base
    "open_ai_api_base": "https://api.openai.com/v1",
    "proxy": "",  # openai使用的代理
    # chatgpt模型， 当use_azure_chatgpt为true时，其名称为Azure上model deployment名称
    "model": "coze",  # 可选择: gpt-4o, pt-4o-mini, gpt-4-turbo, claude-3-sonnet, wenxin, moonshot, qwen-turbo, xunfei, glm-4, minimax, gemini等模型，全部可选模型详见common/const.py文件
    "use_azure_chatgpt": False,  # 是否使用azure的chatgpt
    "azure_deployment_id": "",  # azure 模型部署名称
    "azure_api_version": "",  # azure api版本
    # Bot触发配置
    "single_chat_prefix": ["bot", "@bot"],  # 私聊时文本需要包含该前缀才能触发机器人回复
    "single_chat_reply_prefix": "[bot] ",  # 私聊时自动回复的前缀，用于区分真人
    "single_chat_reply_suffix": "",  # 私聊时自动回复的后缀，\n 可以换行
    "group_chat_prefix": ["@bot"],  # 群聊时包含该前缀则会触发机器人回复
    "no_need_at": False,  # 群聊回复时是否不需要艾特
    "group_chat_reply_prefix": "",  # 群聊时自动回复的前缀
    "group_chat_reply_suffix": "",  # 群聊时自动回复的后缀，\n 可以换行
    "group_chat_keyword": [],  # 群聊时包含该关键词则会触发机器人回复
    "group_at_off": False,  # 是否关闭群聊时@bot的触发
    "group_name_white_list": ["ChatGPT测试群", "ChatGPT测试群2"],  # 开启自动回复的群名称列表
    "group_name_keyword_white_list": [],  # 开启自动回复的群名称关键词列表
    "group_chat_in_one_session": ["ChatGPT测试群"],  # 支持会话上下文共享的群名称
    "nick_name_black_list": [],  # 用户昵称黑名单
    "group_welcome_msg": "",  # 配置新人进群固定欢迎语，不配置则使用随机风格欢迎
    "trigger_by_self": False,  # 是否允许机器人触发
    "text_to_image": "dall-e-2",  # 图片生成模型，可选 dall-e-2, dall-e-3
    # Azure OpenAI dall-e-3 配置
    "dalle3_image_style": "vivid", # 图片生成dalle3的风格，可选有 vivid, natural
    "dalle3_image_quality": "hd", # 图片生成dalle3的质量，可选有 standard, hd
    # Azure OpenAI DALL-E API 配置, 当use_azure_chatgpt为true时,用于将文字回复的资源和Dall-E的资源分开.
    "azure_openai_dalle_api_base": "", # [可选] azure openai 用于回复图片的资源 endpoint，默认使用 open_ai_api_base
    "azure_openai_dalle_api_key": "", # [可选] azure openai 用于回复图片的资源 key，默认使用 open_ai_api_key
    "azure_openai_dalle_deployment_id":"", # [可选] azure openai 用于回复图片的资源 deployment id，默认使用 text_to_image
    "image_proxy": True,  # 是否需要图片代理，国内访问LinkAI时需要
    "image_create_prefix": ["画", "看", "找"],  # 开启图片回复的前缀
    "concurrency_in_session": 1,  # 同一会话最多有多少条消息在处理中，大于1可能乱序
    "image_create_size": "256x256",  # 图片大小,可选有 256x256, 512x512, 1024x1024 (dall-e-3默认为1024x1024)
    "group_chat_exit_group": False,
    # chatgpt会话参数
    "expires_in_seconds": 3600,  # 无操作会话的过期时间
    # 人格描述
    "character_desc": "你是ChatGPT, 一个由OpenAI训练的大型语言模型, 你旨在回答并解决人们的任何问题，并且可以使用多种语言与人交流。",
    "conversation_max_tokens": 1000,  # 支持上下文记忆的最多字符数
    # chatgpt限流配置
    "rate_limit_chatgpt": 20,  # chatgpt的调用频率限制
    "rate_limit_dalle": 50,  # openai dalle的调用频率限制
    # chatgpt api参数 参考https://platform.openai.com/docs/api-reference/chat/create
    "temperature": 0.9,
    "top_p": 1,
    "frequency_penalty": 0,
    "presence_penalty": 0,
    "request_timeout": 180,  # chatgpt请求超时时间，openai接口默认设置为600，对于难问题一般需要较长时间
    "timeout": 120,  # chatgpt重试超时时间，在这个时间内，将会自动重试
    # Baidu 文心一言参数
    "baidu_wenxin_model": "eb-instant",  # 默认使用ERNIE-Bot-turbo模型
    "baidu_wenxin_api_key": "",  # Baidu api key
    "baidu_wenxin_secret_key": "",  # Baidu secret key
    "baidu_wenxin_prompt_enabled": False,  # Enable prompt if you are using ernie character model
    # 讯飞星火API
    "xunfei_app_id": "",  # 讯飞应用ID
    "xunfei_api_key": "",  # 讯飞 API key
    "xunfei_api_secret": "",  # 讯飞 API secret
    "xunfei_domain": "",  # 讯飞模型对应的domain参数，Spark4.0 Ultra为 4.0Ultra，其他模型详见: https://www.xfyun.cn/doc/spark/Web.html
    "xunfei_spark_url": "",  # 讯飞模型对应的请求地址，Spark4.0 Ultra为 wss://spark-api.xf-yun.com/v4.0/chat，其他模型参考详见: https://www.xfyun.cn/doc/spark/Web.html
    # claude 配置
    "claude_api_cookie": "",
    "claude_uuid": "",
    # claude api key
    "claude_api_key": "",
    # 通义千问API, 获取方式查看文档 https://help.aliyun.com/document_detail/2587494.html
    "qwen_access_key_id": "",
    "qwen_access_key_secret": "",
    "qwen_agent_key": "",
    "qwen_app_id": "",
    "qwen_node_id": "",  # 流程编排模型用到的id，如果没有用到qwen_node_id，请务必保持为空字符串
    # 阿里灵积(通义新版sdk)模型api key
    "dashscope_api_key": "",
    # Google Gemini Api Key
    "gemini_api_key": "",
    # wework的通用配置
    "wework_smart": True,  # 配置wework是否使用已登录的企业微信，False为多开
    # 语音设置
    "speech_recognition": True,  # 是否开启语音识别
    "group_speech_recognition": False,  # 是否开启群组语音识别
    "voice_reply_voice": False,  # 是否使用语音回复语音，需要设置对应语音合成引擎的api key
    "always_reply_voice": False,  # 是否一直使用语音回复
    "voice_to_text": "openai",  # 语音识别引擎，支持openai,baidu,google,azure,xunfei,ali
    "text_to_voice": "openai",  # 语音合成引擎，支持openai,baidu,google,azure,xunfei,ali,pytts(offline),elevenlabs,edge(online)
    "text_to_voice_model": "tts-1",
    "tts_voice_id": "alloy",
    # baidu 语音api配置， 使用百度语音识别和语音合成时需要
    "baidu_app_id": "",
    "baidu_api_key": "",
    "baidu_secret_key": "",
    # 1536普通话(支持简单的英文识别) 1737英语 1637粤语 1837四川话 1936普通话远场
    "baidu_dev_pid": 1536,
    # azure 语音api配置， 使用azure语音识别和语音合成时需要
    "azure_voice_api_key": "",
    "azure_voice_region": "japaneast",
    # elevenlabs 语音api配置
    "xi_api_key": "",  # 获取ap的方法可以参考https://docs.elevenlabs.io/api-reference/quick-start/authentication
    "xi_voice_id": "",  # ElevenLabs提供了9种英式、美式等英语发音id，分别是"Adam/Antoni/Arnold/Bella/Domi/Elli/Josh/Rachel/Sam"
    # 服务时间限制，目前支持itchat
    "chat_time_module": False,  # 是否开启服务时间限制
    "chat_start_time": "00:00",  # 服务开始时间
    "chat_stop_time": "24:00",  # 服务结束时间
    # 翻译api
    "translate": "baidu",  # 翻译api，支持baidu
    # baidu翻译api的配置
    "baidu_translate_app_id": "",  # 百度翻译api的appid
    "baidu_translate_app_key": "",  # 百度翻译api的秘钥
    # itchat的配置
    "hot_reload": False,  # 是否开启热重载
    # wechaty的配置
    "wechaty_puppet_service_token": "",  # wechaty的token
    # wechatmp的配置
    "wechatmp_token": "",  # 微信公众平台的Token
    "wechatmp_port": 8080,  # 微信公众平台的端口,需要端口转发到80或443
    "wechatmp_app_id": "",  # 微信公众平台的appID
    "wechatmp_app_secret": "",  # 微信公众平台的appsecret
    "wechatmp_aes_key": "",  # 微信公众平台的EncodingAESKey，加密模式需要
    # wechatcom的通用配置
    "wechatcom_corp_id": "",  # 企业微信公司的corpID
    # wechatcomapp的配置
    "wechatcomapp_token": "",  # 企业微信app的token
    "wechatcomapp_port": 9898,  # 企业微信app的服务端口,不需要端口转发
    "wechatcomapp_secret": "",  # 企业微信app的secret
    "wechatcomapp_agent_id": "",  # 企业微信app的agent_id
    "wechatcomapp_aes_key": "",  # 企业微信app的aes_key
    # 飞书配置
    "feishu_port": 80,  # 飞书bot监听端口
    "feishu_app_id": "",  # 飞书机器人应用APP Id
    "feishu_app_secret": "",  # 飞书机器人APP secret
    "feishu_token": "",  # 飞书 verification token
    "feishu_bot_name": "",  # 飞书机器人的名字
    # 钉钉配置
    "dingtalk_client_id": "",  # 钉钉机器人Client ID 
    "dingtalk_client_secret": "",  # 钉钉机器人Client Secret
    "dingtalk_card_enabled": False,
    
    # chatgpt指令自定义触发词
    "clear_memory_commands": ["#清除记忆"],  # 重置会话指令，必须以#开头
    # channel配置
    "channel_type": "",  # 通道类型，支持：{wx,wxy,terminal,wechatmp,wechatmp_service,wechatcom_app,dingtalk}
    "subscribe_msg": "",  # 订阅消息, 支持: wechatmp, wechatmp_service, wechatcom_app
    "appdata_dir": "",  # 数据目录
    # 插件配置
    "plugin_trigger_prefix": "&",  # 规范插件提供聊天相关指令的前缀，建议不要和管理员指令前缀"#"冲突
    # 是否使用全局插件配置
    "use_global_plugin_config": False,
    "max_media_send_count": 3,  # 单次最大发送媒体资源的个数
    "media_send_interval": 1,  # 发送图片的事件间隔，单位秒
    # 智谱AI 平台配置
    "zhipu_ai_api_key": "",
    "zhipu_ai_api_base": "https://open.bigmodel.cn/api/paas/v4",
    "moonshot_api_key": "",
    "moonshot_base_url": "https://api.moonshot.cn/v1/chat/completions",
    # LinkAI平台配置
    "use_linkai": False,
    "linkai_api_key": "",
    "linkai_app_code": "",
    "linkai_api_base": "https://api.link-ai.tech",  # linkAI服务地址
    "web_port": 9899,
    # coze配置
    "coze_api_key": "",
    "coze_bot_id": "",
    "coze_api_base": "https://api.coze.cn/open_api/v2",
    # hiagent配置
    "hiagent_api_key": "",
    "hiagent_app_id": "",
    "hiagent_api_base": "https://coze.nankai.edu.cn/api/proxy/api/v1",
    "hiagent_user_id": "default_user",
    "enable_knowledge_integration": True,
    "max_knowledge_display": 3,
    "max_knowledge_length": 100,
    "response_mode": "blocking",
    # 数据库配置项
    "db_host": "localhost",  # 数据库主机地址，类型str，默认"localhost"
    "db_port": 3306,  # 数据库端口，类型int，默认3306
    "db_user": "root",  # 数据库用户名，类型str，默认"root"
    "db_password": "",  # 数据库密码，类型str，默认为空
    "db_name": "mysql",  # 数据库名称，类型str，默认"mysql"
    "data_path": "",  # 数据存储路径，类型str，默认为空
    "proxy_pool": "http://127.0.0.1:7897",  # 代理池地址，类型str，URL格式
    # 微信公众号配置项
    "unofficial_account": "",  # 非官方公众号ID，类型str，默认为空
    "university_official_account": "",  # 大学官方公众号ID，类型str，默认为空
    "school_official_account": "",  # 学院官方公众号ID，类型str，默认为空
    "club_official_account": "",  # 社团公众号ID，类型str，默认为空
    "market_token": ""  # 集市token，类型str，默认为空
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
        config_path = os.path.join(os.path.dirname(__file__), "config.json")
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