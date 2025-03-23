"""
阿里云Dashscope服务（通义千问）聊天机器人
"""
import json  # noqa: F401
import time  # noqa: F401
import requests
from core.utils.logger import get_module_logger
logger = get_module_logger('core.agent.dashscope')
from config import Config
from core.bridge.reply import Reply
from core.bridge.context import Context
from core.agent.agent import Agent
from core.agent.dashscope.dashscope_session import DashscopeSessionManager
from core.utils import singleton_decorator
from typing import Generator, AsyncGenerator


@singleton_decorator
class DashscopeAgent(Agent):
    def __init__(self):
        # 获取配置
        self.config = Config()
        self.api_key = self.config.get("core.agent.dashscope.api_key")
        
        # 获取模型配置
        self.model = self.config.get("core.agent.dashscope.model", "qwen-max")
        
        # 初始化参数
        self.temperature = self.config.get("core.agent.dashscope.temperature", 0.8)
        self.top_p = self.config.get("core.agent.dashscope.top_p", 0.8)
        self.max_tokens = self.config.get("core.agent.dashscope.max_tokens", 2048)
        
        # 流式响应
        self.stream = self.config.get("core.agent.dashscope.stream", True)
        
        # API基础URL
        self.api_base = self.config.get("core.agent.dashscope.base_url", "https://dashscope.aliyuncs.com/v1/services/aigc/text-generation/generation")
        
        # 会话管理
        self.session_manager = DashscopeSessionManager()
        
        # 调试信息
        self.show_user_prompt = self.config.get("debug_info", False)
        
    def reply(self, query, context: Context = None):
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
                reply.content = "请先配置Dashscope API Key"  # noqa: F841
                return reply
            
            # 获取会话
            session = self.session_manager.session_query(query, session_id)
            
            # 构建请求
            payload = {
                "model": self.model,
                "input": {
                    "messages": session.messages
                },
                "parameters": {
                    "temperature": self.temperature,
                    "top_p": self.top_p,
                    "result_format": "message",
                    "stream": self.stream
                }
            }
            
            # 添加可选参数
            if self.max_tokens > 0:
                payload["parameters"]["max_tokens"] = self.max_tokens
            
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
                            output = response_item.get("output", {})
                            choices = output.get("choices", [])
                            if choices and len(choices) > 0:
                                choice = choices[0]
                                if "message" in choice and "content" in choice["message"]:
                                    content = choice["message"]["content"]  # noqa: F841
                                    # 对于流式响应，可能会重复返回内容，需要计算新增的部分
                                    if len(content) > len(response_text):
                                        new_content = content[len(response_text):]  # noqa: F841
                                        response_text = content
                                        reply.content = response_text  # noqa: F841
                                        if context.get("stream"):
                                            yield reply
                    
                    if not context.get("stream"):
                        reply.content = response_text  # noqa: F841
                # 非流式响应
                else:
                    response = requests.post(self.api_base, headers=headers, json=payload)
                    if response.status_code == 200:
                        result = response.json()
                        output = result.get("output", {})
                        choices = output.get("choices", [])
                        if choices and len(choices) > 0:
                            if "message" in choices[0] and "content" in choices[0]["message"]:
                                reply.content = choices[0]["message"]["content"]  # noqa: F841
                            else:
                                logger.error(f"Dashscope返回格式异常: {result}")
                                reply.content = "Dashscope返回数据格式异常"  # noqa: F841
                                return reply
                        else:
                            logger.error(f"Dashscope返回异常: {result}")
                            reply.content = "Dashscope返回数据异常"  # noqa: F841
                            return reply
                    else:
                        logger.error(f"Dashscope请求失败: {response.status_code}, {response.text}")
                        reply.content = f"Dashscope接口请求失败: {response.status_code}"  # noqa: F841
                        return reply
                
                # 保存会话并返回
                self.session_manager.session_reply(reply.content, session_id)
                if self.show_user_prompt:
                    logger.debug(f"[Dashscope] {query} \n {reply.content}")
                return reply
                
            except Exception as e:
                logger.error(f"Dashscope接口异常: {e}")
                reply.content = f"Dashscope接口异常: {e}"  # noqa: F841
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

    async def reply_stream(self, query, context=None) -> AsyncGenerator[Reply, None]:
        """
        流式回复消息
        :param query: 用户消息
        :param context: 上下文
        :return: 生成器，返回Reply对象
        """
        if context and context.type == Context.TYPE_TEXT:
            session_id = context.get("session_id")
            reply = Reply()
            
            # 检查API参数是否已配置
            if not self.api_key:
                reply.content = "请先配置Dashscope API Key"  # noqa: F841
                yield reply
                return
            
            # 获取会话
            session = self.session_manager.session_query(query, session_id)
            
            # 构建请求
            payload = {
                "model": self.model,
                "input": {
                    "messages": session.messages
                },
                "parameters": {
                    "temperature": self.temperature,
                    "top_p": self.top_p,
                    "result_format": "message",
                    "stream": True  # 流式响应必须为True
                }
            }
            
            # 添加可选参数
            if self.max_tokens > 0:
                payload["parameters"]["max_tokens"] = self.max_tokens
            
            # 设置请求头
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {self.api_key}'
            }
            
            try:
                response_text = ""
                for response_item in self.fetch_stream(self.api_base, headers, payload):
                    if response_item:
                        output = response_item.get("output", {})
                        choices = output.get("choices", [])
                        if choices and len(choices) > 0:
                            choice = choices[0]
                            if "message" in choice and "content" in choice["message"]:
                                content = choice["message"]["content"]  # noqa: F841
                                # 计算新增内容
                                if len(content) > len(response_text):
                                    response_text = content
                                    reply = Reply()
                                    reply.content = response_text  # noqa: F841
                                    yield reply
                
                # 保存会话
                if response_text:
                    self.session_manager.session_reply(response_text, session_id)
                    if self.show_user_prompt:
                        logger.debug(f"[Dashscope Stream] {query} \n {response_text}")
                
            except Exception as e:
                logger.error(f"Dashscope流式接口异常: {e}")
                reply = Reply()
                reply.content = f"Dashscope流式接口异常: {e}"  # noqa: F841
                yield reply 