import os
import pickle
import json
import copy
from singleton_decorator import singleton
from loguru import logger

# 默认配置值，config.json中未配置的项会使用此处的默认值
available_setting = {
    # 核心配置
    "core": {
        # AI智能体配置
        "agent": {
            # Coze AI配置
            "coze": {
                "base_url": "https://api.coze.cn",  # API基础URL
                "bot_id": "",  # Coze机器人ID
                "api_key": ""  # Coze API密钥
            },
            # OpenAI配置
            "openai": {
                "api_key": "",  # OpenAI API密钥
                "base_url": "https://api.openai.com/v1",  # API基础URL
                "proxy": "",  # 代理设置
                "model": "coze",  # 使用的模型
                "use_azure": False,  # 是否使用Azure OpenAI
                "azure_deployment_id": "",  # Azure部署ID
                "azure_api_version": "",  # Azure API版本
                "temperature": 0.9,  # 温度参数
                "top_p": 1,  # Top P采样
                "frequency_penalty": 0,  # 频率惩罚
                "presence_penalty": 0,  # 存在惩罚
                "request_timeout": 180,  # 请求超时时间
                "timeout": 120  # 总体超时时间
            },
            # 百度文心一言配置
            "baidu": {
                "wenxin": {
                    "base_url": "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop",  # API基础URL
                    "model": "eb-instant",  # 使用的模型
                    "api_key": "",  # API密钥
                    "secret_key": "",  # 密钥
                    "prompt_enabled": False  # 是否启用提示
                }
            },
            # 讯飞配置
            "xunfei": {
                "base_url": "https://spark-api.xf-yun.com",  # API基础URL
                "app_id": "",  # 应用ID
                "api_key": "",  # API密钥
                "api_secret": "",  # API密钥
                "domain": "",  # 域名
                "spark_url": ""  # Spark服务URL
            },
            # Claude配置
            "claude": {
                "base_url": "https://api.anthropic.com",  # API基础URL
                "api_cookie": "",  # API Cookie
                "uuid": "",  # UUID
                "api_key": ""  # API密钥
            },
            # 通义千问配置
            "qwen": {
                "base_url": "https://dashscope.aliyuncs.com",  # API基础URL
                "access_key_id": "",  # 访问密钥ID
                "access_key_secret": "",  # 访问密钥
                "agent_key": "",  # 代理密钥
                "app_id": "",  # 应用ID
                "node_id": ""  # 节点ID
            },
            # DashScope配置
            "dashscope": {
                "base_url": "https://dashscope.aliyuncs.com/api/v1",  # API基础URL
                "api_key": ""  # API密钥
            },
            # Gemini配置
            "gemini": {
                "base_url": "https://generativelanguage.googleapis.com",  # API基础URL
                "api_key": ""  # API密钥
            },
            # 智谱AI配置
            "zhipu": {
                "api_key": "",  # API密钥
                "base_url": "https://open.bigmodel.cn/api/paas/v4"  # API基础URL
            },
            # Moonshot配置
            "moonshot": {
                "api_key": "",  # API密钥
                "base_url": "https://api.moonshot.cn/v1/chat/completions"  # API基础URL
            },
            # LinkAI配置
            "linkai": {
                "use": False,  # 是否使用
                "api_key": "",  # API密钥
                "app_code": "",  # 应用代码
                "base_url": "https://api.link-ai.tech"  # API基础URL
            },
            # HiAgent配置
            "hiagent": {
                "api_key": "",  # API密钥
                "app_id": "",  # 应用ID
                "base_url": "https://coze.nankai.edu.cn/api/proxy/api/v1",  # API基础URL
                "user_id": "default_user"  # 用户ID
            }
        }
    },
    # 服务配置
    "services": {
        "channel_type": "wechatmp_service",  # 渠道类型
        "agent_type": "coze",  # 智能体类型
        "plugin_trigger_prefix": "&",  # 插件触发前缀
        "image_create_prefix": ["画"],  # 图像创建前缀
        "speech_recognition": True,  # 语音识别开关
        "group_speech_recognition": False,  # 群组语音识别开关
        "voice_reply_voice": False,  # 语音回复语音开关
        "always_reply_voice": False,  # 始终语音回复开关
        "voice_to_text": "openai",  # 语音转文本服务
        "text_to_voice": "openai",  # 文本转语音服务
        "text_to_voice_model": "tts-1",  # 文本转语音模型
        "tts_voice_id": "alloy",  # TTS语音ID
        # 微信公众号服务配置
        "wechatmp_service": {
            "token": "",  # 验证令牌
            "port": 80,  # 服务端口
            "app_id": "",  # 应用ID
            "app_secret": "",  # 应用密钥
            "aes_key": "",  # 消息加解密密钥
            "hot_reload": False,  # 热重载
            "conversation_max_tokens": 100000000,  # 会话最大token数
            "expires_in_seconds": 3600,  # 过期时间
            "subscribe_msg": ""  # 订阅消息
        },
        # 网站配置
        "website": {
            "ssl_key_path": "/etc/ssl/private.key",  # SSL私钥路径
            "ssl_cert_path": "/etc/ssl/certificate.pem"  # SSL证书路径
        },
        # 企业微信配置
        "wework": {
            "single_chat_prefix": [""],  # 单聊前缀
            "single_chat_reply_prefix": "",  # 单聊回复前缀
            "expires_in_seconds": 3600,  # 过期时间
            "conversation_max_tokens": 1000,  # 会话最大token数
            "clear_memory_commands": ["#清除记忆"],  # 清除记忆命令
            "character_desc": "你是ChatGPT, 一个由OpenAI训练的大型语言模型, 你旨在回答并解决人们的任何问题，并且可以使用多种语言与人交流。",  # 角色描述
            "rate_limit_chatgpt": 20,  # ChatGPT速率限制
            "rate_limit_dalle": 50,  # DALL-E速率限制
            "concurrency_in_session": 1,  # 会话并发数
            "group_chat_exit_group": False  # 群聊退出群组
        },
        # 微信企业号配置
        "wechatcom": {
            "corp_id": "",  # 企业ID
            "app": {
                "token": "",  # 验证令牌
                "port": 9898,  # 服务端口
                "secret": "",  # 应用密钥
                "agent_id": "",  # 应用ID
                "aes_key": ""  # 消息加解密密钥
            }
        },
        # 飞书配置
        "feishu": {
            "port": 80,  # 服务端口
            "app_id": "",  # 应用ID
            "app_secret": "",  # 应用密钥
            "token": "",  # 验证令牌
            "bot_name": ""  # 机器人名称
        },
        # 钉钉配置
        "dingtalk": {
            "client_id": "",  # 客户端ID
            "client_secret": "",  # 客户端密钥
            "card_enabled": False  # 是否启用卡片
        },
        # 插件配置
        "plugin": {
            "trigger_prefix": "&",  # 触发前缀
            "use_global_config": False,  # 使用全局配置
            "max_media_send_count": 3,  # 最大媒体发送数量
            "media_send_interval": 1  # 媒体发送间隔
        },
        # 语音服务配置
        "voice": {
            "speech_recognition": True,  # 语音识别开关
            "group_speech_recognition": False,  # 群组语音识别开关
            "voice_reply_voice": False,  # 语音回复语音开关
            "always_reply_voice": False,  # 始终语音回复开关
            "voice_to_text": "openai",  # 语音转文本服务
            "text_to_voice": "openai",  # 文本转语音服务
            "text_to_voice_model": "tts-1",  # 文本转语音模型
            "tts_voice_id": "alloy",  # TTS语音ID
            # 百度语音服务配置
            "baidu": {
                "app_id": "",  # 应用ID
                "api_key": "",  # API密钥
                "secret_key": "",  # 密钥
                "dev_pid": 1536  # 开发PID
            },
            # Azure语音服务配置
            "azure": {
                "api_key": "",  # API密钥
                "region": "japaneast"  # 区域
            },
            # ElevenLabs语音服务配置
            "elevenlabs": {
                "api_key": "",  # API密钥
                "voice_id": ""  # 语音ID
            }
        },
        # 翻译服务配置
        "translate": {
            "type": "baidu",  # 翻译服务类型
            "baidu": {
                "app_id": "",  # 应用ID
                "app_key": ""  # 应用密钥
            }
        },
        # 图像服务配置
        "image": {
            "type": "dall-e-2",  # 图像服务类型
            "proxy": True,  # 是否使用代理
            "create_prefix": ["画", "看", "找"],  # 创建前缀
            "size": "256x256",  # 图像大小
            # DALL-E 3配置
            "dalle3": {
                "style": "vivid",  # 风格
                "quality": "hd"  # 质量
            },
            # Azure图像服务配置
            "azure": {
                "base_url": "",  # API基础URL
                "api_key": "",  # API密钥
                "deployment_id": ""  # 部署ID
            }
        }
    },
    # ETL配置
    "etl": {
        # 爬虫配置
        "crawler": {
            "accounts": {
                "unofficial": "",  # 非官方账号
                "university_official": "",  # 大学官方账号
                "school_official": "",  # 学院官方账号
                "club_official": ""  # 社团官方账号
            },
            "market_token": "",  # 市场令牌
            "proxy_pool": "http://127.0.0.1:7897"  # 代理池
        },
        # 检索配置
        "retrieval": {
            "re_only": False,  # 是否只检索，用于调试检索
            "rerank_fusion_type": 1,  # 重排融合类型：0-不使用精排后fusion 1-两路检索结果rrf 2-生成长度最大的作为最终结果 3-两路生成结果拼接
            "ans_refine_type": 0,  # 答案优化类型：0-不对答案做后处理 1-LLM利用top1文档和参考答案生成新答案 2-LLM将top1文档和参考答案拼接生成新答案
            "retrieval_type": 3,  # 检索类型：1-密集检索 2-稀疏检索 3-混合检索
            "f_topk": 128,  # 混合检索器最终的fusion数量
            "f_topk_1": 288,  # 密集检索粗排topk
            "f_topk_2": 192,  # 稀疏检索粗排topk
            "f_topk_3": 6,  # 路径搜索粗排topk
            "reindex": False,  # 是否从头开始构建索引
            "bm25_type": 0  # BM25类型：0-官方实现 1-bm25s实现(速度更快)
        },
        # 向量嵌入配置
        "embedding": {
            "name": "BAAI/bge-large-zh-v1.5",  # 嵌入模型名称
            "vector_size": 1024,  # 向量维度大小
            "embed_dim": 1024,  # 嵌入维度大小
            "f_embed_type_1": 1,  # 密集检索的文档编码方式
            "f_embed_type_2": 2,  # 稀疏检索的文档编码方式
            "r_embed_type": 1,  # 重排的文档编码方式
            "llm_embed_type": 3  # 最终的上下文文档编码参数
        },
        # 重排配置
        "reranker": {
            "name": "BAAI/bge-reranker-base",  # 重排模型名称
            "use_reranker": 2,  # 重排器使用类型：0-不使用 1-ST的普通Reranker 2-bge LLM Reranker
            "r_topk": 6,  # 精排topk
            "r_topk_1": 6,  # 精排后Fusion的topk
            "r_embed_bs": 32,  # 重排批次大小
            "r_use_efficient": 0  # 重排加速方式：0-不加速 1-使用最大值选择方法加速 2-使用熵选择方法加速
        },
        # 分块配置
        "chunking": {
            "split_type": 0,  # 分割类型：0-Sentence 1-Hierarchical
            "chunk_size": 512,  # 块大小
            "chunk_overlap": 200  # 块重叠大小
        },
        # 压缩配置
        "compression": {
            "compress_method": "",  # 压缩方法：bm25_extract/llmlingua/longllmlingua
            "compress_rate": 0.5  # 压缩率
        },
        # HYDE配置
        "hyde": {
            "enabled": False,  # 是否启用虚假文档
            "merging": False  # 是否合并虚假文档
        },
        # 数据配置
        "data": {
            "base_path": "./etl/data",  # 基础路径
            "cache": {
                "path": "/cache"  # 缓存路径
            },
            "raw": {
                "path": "/raw"  # 原始数据路径
            },
            "index": {
                "path": "/index"  # 索引路径
            },
            "qdrant": {
                "path": "/qdrant",  # Qdrant路径
                "url": "http://localhost:6333",  # Qdrant URL
                "collection": "main_index",  # 集合名称
                "vector_size": 1024,  # 向量大小
                "timeout": 10  # 超时时间
            },
            "mysql": {
                "path": "/mysql",  # MySQL路径
                "host": "127.0.0.1",  # 主机地址
                "port": 3306,  # 端口
                "user": "root",  # 用户名
                "password": "",  # 密码
                "name": "mysql"  # 数据库名
            },
            "nltk": {
                "path": "/nltk_data"  # NLTK数据路径
            },
            "models": {
                "path": "/models",  # 模型路径
                "hf_endpoint": "https://hf-api.gitee.com",  # HuggingFace端点
                "hf_home": "/models",  # HuggingFace主目录
                "sentence_transformers_home": "/models"  # Sentence Transformers主目录
            }
        }
    }
}

@singleton
class Config(dict):
    """配置管理单例类，继承字典类型实现配置存储"""
    
    def __init__(self, d=None):
        """初始化配置实例"""
        super().__init__()
        self.update(available_setting)  # 先加载默认配置
        if d is None:
            d = {}
        # 统一转换为小写键名并更新配置
        self.update(self._convert_keys_to_lower(d))
        self.user_datas = {}
        self.plugin_config = {}

    def _convert_keys_to_lower(self, d):
        """递归地将字典的所有键转换为小写"""
        if not isinstance(d, dict):
            return d
            
        return {k.lower(): self._convert_keys_to_lower(v) for k, v in d.items()}

    def __getitem__(self, key):
        """支持嵌套键的访问，如 config['etl.data.cache.path']"""
        try:
            if "." in key:
                parts = key.lower().split(".")
                value = self
                for part in parts:
                    value = value[part]
                return value
            return super().__getitem__(key.lower())
        except KeyError:
            return None

    def get(self, key, default=None):
        """获取配置项，支持点号分隔的嵌套路径访问
        
        Args:
            key: 配置键名，支持点号分隔的路径格式，如 'etl.data.cache.path'
            default: 默认返回值
            
        Returns:
            配置项值或默认值
        """
        try:
            if "." in key:
                parts = key.lower().split(".")
                value = self
                for part in parts:
                    if isinstance(value, dict) and part in value:
                        value = value[part]
                    else:
                        return default
                return value
            return super().get(key.lower(), default)
        except Exception as e:
            logger.exception(f"[config] 配置获取异常: {str(e)}")
            return default

    def set(self, key, value):
        """设置配置项，支持点号分隔的嵌套路径
        
        Args:
            key: 配置键名，支持点号分隔的路径格式
            value: 要设置的值
        """
        try:
            if "." in key:
                parts = key.lower().split(".")
                current = self
                for part in parts[:-1]:
                    if part not in current:
                        current[part] = {}
                    current = current[part]
                current[parts[-1]] = value
            else:
                self[key.lower()] = value
        except Exception as e:
            logger.exception(f"[config] 配置设置异常: {str(e)}")

    def update(self, other):
        """递归更新配置字典
        
        Args:
            other: 要更新的配置字典
        """
        for k, v in other.items():
            if isinstance(v, dict) and k in self and isinstance(self[k], dict):
                self[k].update(self._convert_keys_to_lower(v))
            else:
                self[k] = self._convert_keys_to_lower(v)

    @staticmethod
    def get_root():
        """获取配置文件根目录路径"""
        return os.path.dirname(os.path.abspath(__file__))
    
    def get_appdata_dir(self):
        """获取应用数据存储目录"""
        data_path = os.path.join(self.get_root(), self.get("etl.data.cache.path", ""))
        if not os.path.exists(data_path):
            logger.info("[INIT] data path not exists, create it: {}".format(data_path))
            os.makedirs(data_path)
        return data_path

    def get_user_data(self, user) -> dict:
        """获取指定用户数据字典"""
        if self.user_datas.get(user) is None:
            self.user_datas[user] = {}
        return self.user_datas[user]

    def load_user_datas(self):
        """从持久化存储加载用户数据"""
        try:
            with open(os.path.join(self.get_appdata_dir(), "user_datas.pkl"), "rb") as f:
                self.user_datas = pickle.load(f)
                logger.info("[Config] User datas loaded.")
        except FileNotFoundError:
            pass
        except Exception as e:
            logger.error(f"[Config] 加载用户数据失败: {str(e)}")
            self.user_datas = {}

    def save_user_datas(self):
        """持久化保存用户数据"""
        try:
            save_data = copy.deepcopy(self.user_datas)
            for user in list(save_data.keys()):
                for key in list(save_data[user].keys()):
                    if not isinstance(save_data[user][key], (str, int, float, bool, list, dict)):
                        del save_data[user][key]
            
            with open(os.path.join(self.get_appdata_dir(), "user_datas.pkl"), "wb") as f:
                pickle.dump(save_data, f)
                logger.info("[Config] User datas saved.")
        except Exception as e:
            logger.error(f"[Config] 保存用户数据失败: {str(e)}")

    def load_config(self, logger=logger):
        """加载配置文件"""
        self.logger = logger
        config_path = os.path.join(os.path.dirname(__file__), "config.json")
        try:
            with open(config_path, "r", encoding="utf-8-sig") as f:
                config_str = f.read()
                config_data = json.loads(config_str)
                self.update(config_data)
        except json.JSONDecodeError as e:
            self.logger.exception(f"[config] 配置文件格式错误: {str(e)}")
        except Exception as e:
            self.logger.exception(f"[config] 加载配置文件失败: {str(e)}")
        
        self.load_user_datas()
        return self

    def write_plugin_config(self, pconf: dict):
        """写入插件配置"""
        for k in pconf:
            self.plugin_config[k.lower()] = pconf[k]

    def remove_plugin_config(self, name: str):
        """移除插件配置"""
        self.plugin_config.pop(name.lower(), None)

    def pconf(self, plugin_name: str) -> dict:
        """获取插件配置"""
        return self.plugin_config.get(plugin_name.lower())
    
    def subscribe_msg(self):
        """获取订阅消息"""
        trigger_prefix = self.get("services.wechatmp_service.subscribe_msg", "")
        return trigger_prefix

    def drag_sensitive(self):
        """生成脱敏配置信息"""
        try:
            config_copy = copy.deepcopy(dict(self))
            config_copy.pop('logger', None)
            config_copy.pop('user_datas', None)
            
            def mask_sensitive(d):
                if not isinstance(d, dict):
                    return d
                    
                for k, v in d.items():
                    if isinstance(v, dict):
                        d[k] = mask_sensitive(v)
                    elif isinstance(v, str) and ('key' in k.lower() or 'secret' in k.lower() or 'password' in k.lower()):
                        if len(v) > 8:
                            d[k] = v[:3] + '*' * (len(v)-6) + v[-3:]
                        else:
                            d[k] = '*' * len(v)
                return d
            
            return mask_sensitive(config_copy)
            
        except Exception as e:
            logger.exception(e)
            return self
        return self