"""
百度文心一言聊天机器人
"""
import json
import requests
import time
from core.utils.logger import get_module_logger
logger = get_module_logger('core.agent.baidu')
from config import Config
from core.bridge.reply import Reply
from core.bridge.context import Context
from core.agent.agent import Agent
from core.agent.session_manager import Session, SessionManager
from core.utils import singleton_decorator


class BaiduWenxinSession(Session):
    def __init__(self, session_id, system_prompt=None):
        super().__init__(session_id, system_prompt)
        self.config = Config()
        self.max_tokens = self.config.get("core.agent.baidu.wenxin.max_tokens", 2000)
        self.reset()

    def reset(self):
        system_content = self.system_prompt
        self.messages = []
        if system_content:
            system_item = {"role": "system", "content": system_content}
            self.messages.append(system_item)
    
    def discard_exceeding(self, max_tokens=None, cur_tokens=None):
        if max_tokens is None:
            max_tokens = self.max_tokens
        if max_tokens <= 0:
            return 0

        # 根据约束，计算要保留的消息数量
        num_of_tokens = 0
        for idx, message in enumerate(self.messages[::-1]):
            content = message.get("content", "")
            num_of_tokens += len(content) * 4  # 简单字数估算
            if num_of_tokens > max_tokens and idx > 0:
                self.messages = self.messages[-(idx):]
                break
        return num_of_tokens

    def calc_tokens(self):
        num_of_tokens = 0
        for message in self.messages:
            content = message.get("content", "")
            num_of_tokens += len(content) * 4  # 简单字数估算
        return num_of_tokens


class BaiduWenxinSessionManager(SessionManager):
    def __init__(self):
        super().__init__(BaiduWenxinSession)


@singleton_decorator
class BaiduWenxinAgent(Agent):
    def __init__(self):
        # 创建配置实例
        self.config = Config()
        
        # 获取配置
        self.api_key = self.config.get("core.agent.baidu.wenxin.api_key")
        self.secret_key = self.config.get("core.agent.baidu.wenxin.secret_key")
        
        # 百度AI Studio提供的API接口
        self.api_base = self.config.get("core.agent.baidu.wenxin.base_url", "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/")

        # 获取模型配置
        self.model = self.config.get("core.agent.baidu.wenxin.model", "wenxin-4")
        
        # 初始化参数
        self.temperature = self.config.get("core.agent.baidu.wenxin.temperature", 0.8)
        self.top_p = self.config.get("core.agent.baidu.wenxin.top_p", 0.8)
        self.top_k = self.config.get("core.agent.baidu.wenxin.top_k", 0)
        self.max_output_tokens = self.config.get("core.agent.baidu.wenxin.max_output_tokens", 2048)
        
        # 流式响应
        self.stream = self.config.get("core.agent.baidu.wenxin.stream", True)
        
        # 会话管理
        self.session_manager = BaiduWenxinSessionManager()
        
        # 访问令牌和过期时间
        self.access_token = None
        self.expires_time = 0
        self.show_user_prompt = self.config.get("debug_info", False)
        
    def reply(self, query, context: Context = None) -> Reply:
        """
        回复消息
        :param query: 用户消息
        :param context: 上下文
        :return: 回复
        """
        if context.type == Context.TYPE_TEXT:
            session_id = context.get("session_id")
            reply = Reply()
            
            # 检查API参数是否已配置
            if not self.api_key or not self.secret_key:
                reply.content = "请先配置百度文心一言API参数"
                return reply
            
            # 获取会话
            session = self.session_manager.session_query(query, session_id)
            
            # 获取访问令牌
            token = self.get_access_token()
            if not token:
                reply.content = "获取百度访问令牌失败"
                return reply
            
            # 构建请求
            payload = {
                "messages": session.messages,
                "temperature": self.temperature,
                "top_p": self.top_p,
                "stream": self.stream
            }
            
            # 添加可选参数
            if self.max_output_tokens > 0:
                payload["max_output_tokens"] = self.max_output_tokens
            if self.top_k > 0:
                payload["top_k"] = self.top_k
            
            # API URL，根据模型拼接
            api_url = f"{self.api_base}{self.model}?access_token={token}"
            headers = {'Content-Type': 'application/json'}
            
            try:
                # 处理流式响应
                if self.stream:
                    response_text = ""
                    for response_item in self.fetch_stream(api_url, headers, payload):
                        if response_item:
                            if "result" in response_item:
                                response_text += response_item["result"]
                                reply.content = response_text
                                if context.get("stream"):
                                    yield reply
                    
                    if not context.get("stream"):
                        reply.content = response_text
                # 非流式响应
                else:
                    response = requests.post(api_url, headers=headers, json=payload)
                    if response.status_code == 200:
                        result = response.json()
                        if "result" in result:
                            reply.content = result["result"]
                        else:
                            logger.error(f"百度文心一言返回异常: {result}")
                            reply.content = "百度文心一言返回数据异常"
                            return reply
                    else:
                        logger.error(f"百度文心一言请求失败: {response.status_code}, {response.text}")
                        reply.content = f"百度文心一言接口请求失败: {response.status_code}"
                        return reply
                
                # 保存会话并返回
                self.session_manager.session_reply(reply.content, session_id)
                if self.show_user_prompt:
                    logger.debug(f"[百度文心] {query} \n {reply.content}")
                return reply
                
            except Exception as e:
                logger.error(f"百度文心一言接口异常: {e}")
                reply.content = f"百度文心一言接口异常: {e}"
                return reply
    
    def get_access_token(self):
        """
        获取百度API访问令牌
        :return: access_token
        """
        # 如果已有有效的令牌，则直接返回
        if self.access_token and time.time() < self.expires_time:
            return self.access_token
        
        # 否则重新获取令牌
        url = "https://aip.baidubce.com/oauth/2.0/token"
        params = {
            "grant_type": "client_credentials",
            "client_id": self.api_key,
            "client_secret": self.secret_key
        }
        
        try:
            response = requests.post(url, params=params)
            if response.status_code == 200:
                result = response.json()
                self.access_token = result.get("access_token")
                # 设置过期时间，提前10分钟刷新
                expires_in = result.get("expires_in", 2592000) - 600
                self.expires_time = time.time() + expires_in
                return self.access_token
            else:
                logger.error(f"获取百度访问令牌失败: {response.status_code}, {response.text}")
                return None
        except Exception as e:
            logger.error(f"获取百度访问令牌异常: {e}")
            return None
    
    def fetch_stream(self, url, headers, payload, retry=2):
        """
        获取流式数据
        :param url: API URL
        :param headers: 请求头
        :param payload: 请求体
        :param retry: 重试次数
        :return: 生成器，返回数据流
        """
        while retry > 0:
            try:
                response = requests.post(url, headers=headers, json=payload, stream=True)
                if response.status_code == 200:
                    for line in response.iter_lines():
                        if line:
                            try:
                                line_data = json.loads(line.decode('utf-8'))
                                yield line_data
                            except json.JSONDecodeError:
                                logger.error(f"无法解析数据: {line.decode('utf-8')}")
                else:
                    logger.error(f"获取流式数据失败: {response.status_code}, {response.text}")
                    raise Exception(f"获取流式数据失败: {response.status_code}")
                break
            except Exception as e:
                logger.error(f"流式数据请求异常: {e}")
                retry -= 1
                if retry == 0:
                    logger.error("已达最大重试次数")
                    raise
                time.sleep(1) 