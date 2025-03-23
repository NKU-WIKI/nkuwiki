"""
Claude API聊天机器人
"""
import json  # noqa: F401
import time  # noqa: F401
import requests
from core.utils.logger import get_module_logger
logger = get_module_logger('core.agent.claudeapi')
from config import Config
from core.bridge.reply import Reply
from core.bridge.context import Context
from core.agent.agent import Agent
from core.agent.claudeapi.claude_api_session import ClaudeAPISessionManager
from core.utils import singleton_decorator
from typing import Generator, AsyncGenerator, Any


@singleton_decorator
class ClaudeAPIAgent(Agent):
    def __init__(self):
        # 获取配置
        self.config = Config()
        self.api_key = self.config.get("core.agent.claude.api_key")
        
        # 获取模型配置
        self.model = self.config.get("core.agent.claude.model", "claude-3-opus-20240229")
        
        # 初始化参数
        self.temperature = self.config.get("core.agent.claude.temperature", 0.7)
        self.top_p = self.config.get("core.agent.claude.top_p", 0.9)
        self.max_tokens = self.config.get("core.agent.claude.max_tokens", 4096)
        
        # 流式响应
        self.stream = self.config.get("core.agent.claude.stream", True)
        
        # API基础URL
        self.api_base = self.config.get("core.agent.claude.base_url", "https://api.anthropic.com/v1/messages")
        
        # 会话管理
        self.session_manager = ClaudeAPISessionManager()
        
        # 调试信息
        self.show_user_prompt = self.config.get("debug_info", False)
        
        # API版本
        self.anthropic_version = self.config.get("core.agent.claude.api_version", "2023-06-01")
        
    def reply(self, query, context: Context = None) -> Generator[Reply, Any, Reply]:
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
                reply.content = "请先配置Claude API Key"  # noqa: F841
                return reply
            
            # 获取会话
            session = self.session_manager.session_query(query, session_id)
            
            # 构建请求
            payload = {
                "model": self.model,
                "messages": session.messages,
                "max_tokens": self.max_tokens,
                "temperature": self.temperature,
                "system": session.system_prompt if session.system_prompt else "",
                "stream": self.stream
            }
            
            # 添加可选参数
            if self.top_p:
                payload["top_p"] = self.top_p
            
            # 设置请求头
            headers = {
                'Content-Type': 'application/json',
                'x-api-key': self.api_key,
                'anthropic-version': self.anthropic_version
            }
            
            try:
                # 处理流式响应
                if self.stream:
                    response_text = ""
                    for response_item in self.fetch_stream(self.api_base, headers, payload):
                        if response_item and "delta" in response_item:
                            delta = response_item.get("delta", {})
                            if "text" in delta:
                                content = delta["text"]  # noqa: F841
                                response_text += content
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
                        if "content" in result and isinstance(result["content"], list):
                            for content_item in result["content"]:
                                if content_item.get("type") == "text":
                                    reply.content = content_item.get("text", "")  # noqa: F841
                                    break
                        else:
                            logger.error(f"Claude API返回格式异常: {result}")
                            reply.content = "Claude API返回数据格式异常"  # noqa: F841
                            return reply
                    else:
                        logger.error(f"Claude API请求失败: {response.status_code}, {response.text}")
                        reply.content = f"Claude API接口请求失败: {response.status_code}"  # noqa: F841
                        return reply
                
                # 保存会话并返回
                self.session_manager.session_reply(reply.content, session_id)
                if self.show_user_prompt:
                    logger.debug(f"[Claude API] {query} \n {reply.content}")
                return reply
                
            except Exception as e:
                logger.error(f"Claude API接口异常: {e}")
                reply.content = f"Claude API接口异常: {e}"  # noqa: F841
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
                            line_text = line.decode('utf-8')
                            if line_text.startswith("data: "):
                                if line_text == "data: [DONE]":
                                    break
                                data_str = line_text[6:]  # 去掉"data: "前缀
                                try:
                                    data = json.loads(data_str)
                                    yield data
                                except json.JSONDecodeError:
                                    logger.error(f"无法解析数据: {data_str}")
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
        # 实现流式回复的逻辑，确保返回值是Generator[Reply, None, None]
        if context and context.type == Context.TYPE_TEXT:
            session_id = context.get("session_id")
            reply = Reply()
            
            # 检查API参数是否已配置
            if not self.api_key:
                reply.content = "请先配置Claude API Key"  # noqa: F841
                yield reply
                return
            
            # 获取会话
            session = self.session_manager.session_query(query, session_id)
            
            # 调用API进行流式返回
            try:
                # 在此调用实际的Claude API并处理流式响应
                response_text = ""
                # 示例实现，实际应该使用Claude流式API
                for content_chunk in self._get_stream_response(session):
                    if content_chunk:
                        response_text += content_chunk
                        reply = Reply()
                        reply.content = response_text  # noqa: F841
                        yield reply
                
                # 保存会话
                if response_text:
                    self.session_manager.session_reply(response_text, session_id)
                    
            except Exception as e:
                logger.error(f"Claude API流式接口异常: {e}")
                reply = Reply()
                reply.content = f"Claude API流式接口异常: {e}"  # noqa: F841
                yield reply 