"""
阿里通义千问聊天机器人
"""
import json
import time
import requests
from core.utils.logger import register_logger
logger = register_logger("core.agent.ali")
from config import Config
from core.bridge.reply import Reply
from core.bridge.context import Context
from core.agent.agent import Agent
from core.agent.ali.ali_qwen_session import AliQwenSessionManager
from core.utils import singleton_decorator


@singleton_decorator
class AliQwenAgent(Agent):
    def __init__(self):
        # 获取配置
        self.config = Config()
        self.api_key = self.config.get("core.agent.qwen.api_key")
        
        # 获取模型配置
        self.model = self.config.get("core.agent.qwen.model", "qwen-plus")
        
        # 初始化参数
        self.temperature = self.config.get("core.agent.qwen.temperature", 0.8)
        self.top_p = self.config.get("core.agent.qwen.top_p", 0.8)
        self.top_k = self.config.get("core.agent.qwen.top_k", 0)
        self.max_tokens = self.config.get("core.agent.qwen.max_tokens", 2048)
        
        # 流式响应
        self.stream = self.config.get("core.agent.qwen.stream", True)
        
        # API基础URL
        self.api_base = self.config.get("core.agent.qwen.base_url", "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions")
        
        # 会话管理
        self.session_manager = AliQwenSessionManager()
        
        # 调试信息
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
            if not self.api_key:
                reply.content = "请先配置阿里通义千问API Key"
                return reply
            
            # 获取会话
            session = self.session_manager.session_query(query, session_id)
            
            # 构建请求
            payload = {
                "messages": session.messages,
                "model": self.model,
                "temperature": self.temperature,
                "top_p": self.top_p,
                "stream": self.stream
            }
            
            # 添加可选参数
            if self.max_tokens > 0:
                payload["max_tokens"] = self.max_tokens
            if self.top_k > 0:
                payload["top_k"] = self.top_k
            
            # 设置请求头
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {self.api_key}'
            }
            
            try:
                # 处理流式响应
                if self.stream:
                    response_text = ""
                    for response_item in self.fetch_stream(self.api_base, headers, payload):
                        if response_item:
                            choices = response_item.get("choices", [])
                            if choices and len(choices) > 0:
                                choice = choices[0]
                                if "delta" in choice and "content" in choice["delta"]:
                                    content = choice["delta"]["content"]
                                    response_text += content
                                    reply.content = response_text
                                    if context.get("stream"):
                                        yield reply
                    
                    if not context.get("stream"):
                        reply.content = response_text
                # 非流式响应
                else:
                    response = requests.post(self.api_base, headers=headers, json=payload)
                    if response.status_code == 200:
                        result = response.json()
                        choices = result.get("choices", [])
                        if choices and len(choices) > 0:
                            if "message" in choices[0] and "content" in choices[0]["message"]:
                                reply.content = choices[0]["message"]["content"]
                            else:
                                logger.error(f"阿里通义千问返回格式异常: {result}")
                                reply.content = "阿里通义千问返回数据格式异常"
                                return reply
                        else:
                            logger.error(f"阿里通义千问返回异常: {result}")
                            reply.content = "阿里通义千问返回数据异常"
                            return reply
                    else:
                        logger.error(f"阿里通义千问请求失败: {response.status_code}, {response.text}")
                        reply.content = f"阿里通义千问接口请求失败: {response.status_code}"
                        return reply
                
                # 保存会话并返回
                self.session_manager.session_reply(reply.content, session_id)
                if self.show_user_prompt:
                    logger.debug(f"[阿里通义千问] {query} \n {reply.content}")
                return reply
                
            except Exception as e:
                logger.error(f"阿里通义千问接口异常: {e}")
                reply.content = f"阿里通义千问接口异常: {e}"
                return reply
    
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