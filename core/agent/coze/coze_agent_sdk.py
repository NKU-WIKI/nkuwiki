#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
使用官方 coze-py SDK 的 CozeAgent 实现
"""
from core.agent import *
import sys
import os
import requests
from loguru import logger

# 确保项目根目录在 sys.path 中
current_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if current_dir not in sys.path:
    sys.path.append(current_dir)

from config import Config
from core.agent import Agent
from core.bridge.context import ContextType, Context
from core.bridge.reply import Reply, ReplyType
from core.agent.session_manager import SessionManager
from core.agent.chatgpt.chat_gpt_session import ChatGPTSession

import re
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# 需要先安装 cozepy: pip install cozepy
try:
    from cozepy import Coze, TokenAuth, Message, ChatEventType, COZE_CN_BASE_URL
except ImportError:
    logger.error("需要先安装 cozepy: pip install cozepy")
    raise

def create_http_session():
    """创建HTTP会话，带连接池和重试功能"""
    session = requests.Session()
    
    # 设置重试策略
    retry_strategy = Retry(
        total=3,  # 最多重试3次
        backoff_factor=0.3,  # 重试等待时间
        status_forcelist=[429, 500, 502, 503, 504],  # 哪些状态码需要重试
        allowed_methods=["GET", "POST"]  # 允许重试的HTTP方法
    )
    
    # 创建适配器，最大连接数为10
    adapter = HTTPAdapter(
        max_retries=retry_strategy,
        pool_connections=10,
        pool_maxsize=10
    )
    
    # 注册适配器
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    # 设置超时时间
    session.timeout = (3.05, 60)  # (连接超时, 读取超时)
    
    return session

class CozeAgent(Agent):
    """CozeAgent类，继承自Agent基类"""
    
    def __init__(self):
        super().__init__()
        self.config = Config()
        self.sessions = SessionManager(ChatGPTSession, model=self.config.get("model") or "coze")
        self.sdk = CozeAgentSDK(
            bot_id=self.config.get("core.agent.coze.wx_bot_id"),
            use_cn_api=True
        )

    def reply(self, query: str, context: Context) -> Reply:
        """处理用户输入，返回回复"""
        if context.type == ContextType.TEXT:
            logger.info("[COZE] query={}".format(query))
            
            session_id = context["session_id"]
            session = self.sessions.session_query(query, session_id)
            logger.debug("[COZE] session query={}".format(session.messages))
            
            # 使用流式输出
            logger.info("[COZE] 使用流式输出")
            logger.info("开始流式请求(SDK): {}...".format(query))
            
            def stream_wrapper():
                try:
                    for chunk in self.sdk.stream_reply(query):
                        yield chunk
                except Exception as e:
                    logger.error(f"[COZE] 流式回复出错: {str(e)}")
                    yield f"\n[错误: {str(e)}]"
            
            # 处理完成后更新会话
            completion_tokens, total_tokens = self._calc_tokens(session.messages, "流式回复")
            self.sessions.session_reply("流式回复", session_id, total_tokens)
            
            return Reply(ReplyType.STREAM, stream_wrapper())
            
        elif context.type == ContextType.IMAGE_CREATE:
            return Reply(ReplyType.TEXT, "暂不支持图片生成")
        else:
            return Reply(ReplyType.TEXT, "暂不支持该类型消息")

    def _calc_tokens(self, messages, answer):
        """计算token数量"""
        completion_tokens = len(answer)  # noqa: F841
        prompt_tokens = 0
        for message in messages:
            prompt_tokens += len(message["content"])
        return completion_tokens, prompt_tokens + completion_tokens

class CozeAgentSDK(object):
    """
    使用官方 coze-py SDK 的 CozeAgent 实现
    包含SDK和直接HTTP请求两种实现方式
    """
    
    def __init__(self, bot_id, max_retries=30, poll_interval=0.3, use_cn_api=True, use_sdk=True):
        """
        初始化 CozeAgentSDK
        
        Args:
            bot_id: Coze 机器人 ID，可以是字符串或字符串数组
            max_retries: 最大重试次数
            poll_interval: 轮询间隔时间(秒)
            use_cn_api: 是否使用国内API
            use_sdk: 是否使用SDK (否则使用HTTP请求)
        """
        # 处理 bot_id
        if isinstance(bot_id, str):
            self.bot_id = bot_id
        elif isinstance(bot_id, (list, tuple)) and len(bot_id) > 0:
            self.bot_id = bot_id[0]  # 使用第一个 bot_id
            if len(bot_id) > 1:
                logger.warning(f"配置了多个 bot_id，当前使用第一个: {self.bot_id}")
        else:
            raise ValueError("bot_id 必须是字符串或非空字符串数组")
            
        self.max_retries = max_retries
        self.poll_interval = poll_interval
        self.use_cn_api = use_cn_api
        self.use_sdk = use_sdk
        
        # 获取配置
        self.config = Config()
        
        # 获取API密钥
        self.api_key = self.config.get("core.agent.coze.api_key", "")
        
        if not self.api_key:
            raise ValueError("API 密钥未配置")
        
        # 根据官方示例设置 API 基地址
        if use_cn_api:
            # 使用国内API
            self.base_url = COZE_CN_BASE_URL
            logger.debug(f"使用国内API: {COZE_CN_BASE_URL}")
        else:
            # 使用海外API
            self.base_url = None  # 默认使用 api.coze.com
            logger.debug("使用海外API: api.coze.com")
        
        # 用于HTTP请求的base_url    
        self.http_base_url = self.config.get("core.agent.coze.base_url", COZE_CN_BASE_URL if use_cn_api else "https://api.coze.com")
            
        # 如果使用SDK，初始化Coze客户端
        if use_sdk:
            # 按照官方示例初始化 Coze 客户端
            self.client = Coze(
                auth=TokenAuth(token=self.api_key), 
                base_url=self.base_url if self.use_cn_api else None
            )
            
        # 创建HTTP会话
        self.session = create_http_session()
        
        logger.info(f"CozeAgentSDK 初始化完成，bot_id: {self.bot_id}, API: {'国内' if use_cn_api else '海外'}, 模式: {'SDK' if use_sdk else 'HTTP'}")
    
    def _get_headers(self):
        """获取HTTP请求头"""
        return {
            'Authorization': f"Bearer {self.api_key}",
            'Content-Type': 'application/json'
        }
        
    def reply(self, query):
        """
        同步请求对话响应
        
        Args:
            query: 用户输入
            
        Returns:
            助手回复内容，如果失败则返回None
        """
        if self.use_sdk:
            return self._sdk_reply(query)
        else:
            return self._http_reply(query)
    
    def _sdk_reply(self, query):
        """使用SDK进行对话请求"""
        try:
            logger.info(f"开始请求(SDK)，bot_id: {self.bot_id}, query: {query}")
            
            # 创建对话
            chat = self.client.chat.create(
                bot_id=self.bot_id,
                user_id="default_user",
                additional_messages=[
                    Message.build_user_question_text(query)
                ]
            )
            
            # 获取会话ID和聊天ID
            conversation_id = chat.conversation_id
            chat_id = chat.id
            logger.debug(f"对话创建成功，Chat ID: {chat_id}, Conversation ID: {conversation_id}")
            
            # 等待对话完成
            status = None
            
            for attempt in range(self.max_retries):
                time.sleep(self.poll_interval)
                
                chat_status = self.client.chat.retrieve(
                    conversation_id=conversation_id,
                    chat_id=chat_id
                )
                status = chat_status.status
                logger.debug(f"当前对话状态: {status}, 尝试次数: {attempt+1}/{self.max_retries}")
                
                if status in ["completed", "required_action"]:
                    logger.info(f"对话已完成，状态: {status}")
                    break
            
            if status not in ["completed", "required_action"]:
                logger.warning(f"对话未完成，最终状态: {status}")
                return None
            
            # 获取消息列表
            messages = self.client.chat.messages.list(
                conversation_id=conversation_id,
                chat_id=chat_id
            )
            
            # 提取助手回复
            answer = None
            
            for message in messages:
                if message.role == "assistant" and message.type == "answer":
                    answer = message.content
                    break
            
            if not answer:
                logger.error(f"未找到助手回复: {conversation_id} {chat_id}")
                return None
                
            return answer
            
        except Exception as e:
            logger.exception(f"请求对话失败(SDK): {str(e)}")
            return None
    
    def _http_reply(self, query):
        """使用HTTP请求进行对话"""
        try:
            logger.info(f"开始请求(HTTP)，bot_id: {self.bot_id}, query: {query}")
            
            # 创建对话
            conversation_id, chat_id = self._create_chat(query)
            
            if conversation_id is None or chat_id is None:
                logger.error(f"创建对话失败: {query}")
                return None
                
            # 轮询对话状态  
            status = self._poll_chat_status(conversation_id, chat_id)
            if status != "success":
                logger.error(f"对话状态轮询失败: {conversation_id} {chat_id}")
                return None
                
            # 获取对话消息
            messages = self._get_chat_messages(conversation_id, chat_id)
            if not messages:
                logger.error(f"获取对话消息失败: {conversation_id} {chat_id}")
                return None
                
            # 提取助手回复
            for message in messages:
                if(message.get("role") == "assistant" and message.get("type") == "answer"):
                    return message.get("content")
            
            logger.error(f"未找到助手回复: {conversation_id} {chat_id}")
            return None
            
        except Exception as e:
            logger.exception(f"请求对话失败(HTTP): {str(e)}")
            return None
    
    def stream_reply(self, query):
        """
        流式返回对话响应
        
        Args:
            query: 用户输入
            
        Returns:
            生成器，每次迭代返回一个响应片段
        """
        if self.use_sdk:
            return self._sdk_stream_reply(query)
        else:
            return self._http_stream_reply(query)
    
    def _sdk_stream_reply(self, query):
        """使用SDK进行流式对话请求"""
        try:
            logger.debug(f"开始流式请求(SDK): {query[:30]}...")
            
            # 使用SDK的流式接口
            stream = self.client.chat.stream(
                bot_id=self.bot_id,
                user_id="default_user",
                additional_messages=[
                    Message.build_user_question_text(query)
                ]
            )
            
            # 处理流式响应
            for event in stream:
                if event.event == ChatEventType.CONVERSATION_MESSAGE_DELTA:
                    if event.message and event.message.content:
                        yield event.message.content
                        
        except Exception as e:
            logger.exception(f"SDK流式请求失败: {e}")
            # 尝试切换到HTTP模式
            logger.info("尝试切换到HTTP模式...")
            for chunk in self._http_stream_reply(query):
                yield chunk
                
    def _http_stream_reply(self, query):
        """使用HTTP请求进行流式对话请求"""
        try:
            logger.info(f"开始流式请求(HTTP): {query[:30]}...")
            
            # 构建请求URL
            url = f"{self.http_base_url}/v3/chat"
            
            # 构建请求体
            payload = {
                "bot_id": self.bot_id,
                "user_id": "default_user",
                "stream": True,
                "additional_messages": [
                    {
                        "content": query,
                        "content_type": "text",
                        "role": "user",
                        "type": "question"
                    }
                ]
            }
            
            # 自定义请求头，优化流式传输
            headers = self._get_headers()
            headers.update({
                'Accept': 'text/event-stream',
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'X-Accel-Buffering': 'no'  # 禁用代理服务器的缓冲
            })
            
            # 发送请求
            with self.session.post(url, headers=headers, json=payload, stream=True, timeout=(3.05, 120)) as response:
                response.raise_for_status()
                
                # 使用更高效的缓冲区处理
                buffer = b""
                last_chunk_time = time.time()
                total_received_bytes = 0
                
                for chunk in response.iter_content(chunk_size=1024):  # 提高块大小至1KB
                    if not chunk:
                        continue
                    
                    total_received_bytes += len(chunk)    
                    # 记录收到数据的时间
                    current_time = time.time()
                    if current_time - last_chunk_time > 1.0:  # 如果超过1秒没有收到数据，记录日志
                        logger.debug(f"数据流中断 {current_time - last_chunk_time:.2f}秒")
                    last_chunk_time = current_time
                    
                    buffer += chunk
                    
                    # 处理缓冲区中的行
                    while b'\n' in buffer:
                        try:
                            line, buffer = buffer.split(b'\n', 1)
                            if not line:  # 跳过空行
                                continue
                                
                            # 尝试解码行
                            try:
                                line = line.decode('utf-8')
                                
                                # 检查是否是SSE数据行
                                if line.startswith('data: '):
                                    data = line[6:]  # 去掉 'data: ' 前缀
                                    
                                    # 检查是否是结束标记
                                    if data == '[DONE]':
                                        logger.debug(f"流式响应结束，共接收 {total_received_bytes/1024:.2f} KB 数据")
                                        return
                                    
                                    # 尝试解析JSON数据
                                    try:
                                        json_data = json.loads(data)
                                        if 'data' in json_data and isinstance(json_data['data'], dict):
                                            content = json_data['data'].get('content', '')  # noqa: F841
                                            if content:
                                                yield content
                                    except json.JSONDecodeError:
                                        logger.debug(f"非JSON数据: {data[:30]}...")
                            except UnicodeDecodeError:
                                # 对于解码错误，跳过当前行
                                logger.debug("跳过无法解码的行")
                                continue
                        except Exception as e:
                            logger.debug(f"处理行时出错: {str(e)}")
                            continue
                
                # 处理剩余的buffer
                if buffer:
                    try:
                        line = buffer.decode('utf-8')
                        if line.startswith('data: '):
                            data = line[6:]
                            if data != '[DONE]':
                                try:
                                    json_data = json.loads(data)
                                    if 'data' in json_data and isinstance(json_data['data'], dict):
                                        content = json_data['data'].get('content', '')  # noqa: F841
                                        if content:
                                            yield content
                                except json.JSONDecodeError:
                                    logger.debug(f"剩余缓冲区非JSON数据: {data[:30]}...")
                    except Exception as e:
                        logger.debug(f"处理剩余缓冲区出错: {str(e)}")
                
                logger.debug(f"流式请求完成，共接收 {total_received_bytes/1024:.2f} KB 数据")
                
        except Exception as e:
            logger.exception(f"HTTP流式请求失败: {e}")
            yield f"请求失败: {e}"

    def get_knowledge_results(self, query):
        """
        获取对话的知识库召回结果
        
        Args:
            query: 用户输入
            
        Returns:
            知识库召回结果列表
        """
        if self.use_sdk:
            return self._sdk_get_knowledge_results(query)
        else:
            # HTTP方式暂不支持获取知识库结果，使用SDK方式
            logger.warning("HTTP方式不支持获取知识库结果，切换到SDK方式")
            return self._sdk_get_knowledge_results(query)
    
    def _sdk_get_knowledge_results(self, query):
        """使用SDK获取知识库召回结果"""
        try:
            logger.info(f"开始获取知识库召回结果(SDK)，bot_id: {self.bot_id}, query: {query}")
            
            # 创建对话
            chat = self.client.chat.create(
                bot_id=self.bot_id,
                user_id="default_user",
                additional_messages=[
                    Message.build_user_question_text(query)
                ]
            )
            
            # 获取会话ID和聊天ID
            conversation_id = chat.conversation_id
            chat_id = chat.id
            
            # 等待对话完成
            status = None
            
            for attempt in range(self.max_retries):
                time.sleep(self.poll_interval)
                
                chat_status = self.client.chat.retrieve(
                    conversation_id=conversation_id,
                    chat_id=chat_id
                )
                status = chat_status.status
                
                if status in ["completed", "required_action"]:
                    break
            
            if status not in ["completed", "required_action"]:
                logger.warning(f"对话未完成，最终状态: {status}")
                return []
            
            # 获取消息列表
            messages = self.client.chat.messages.list(
                conversation_id=conversation_id,
                chat_id=chat_id
            )
            
            # 提取知识库内容
            knowledge_results = []
            
            for message in messages:
                if message.role == "assistant" and message.type == "verbose":
                    try:
                        verbose_content = json.loads(message.content)
                        if verbose_content.get("msg_type") == "knowledge_recall":
                            data = json.loads(verbose_content.get("data", "{}"))
                            for chunk in data.get("chunks", []):
                                knowledge_slice = chunk.get("slice", "")
                                if knowledge_slice:
                                    knowledge_results.append(knowledge_slice)
                                
                                link = chunk.get("meta", {}).get("link", {}).get("url", "")
                                if link:
                                    clean_link = link.replace("u0026", "&")
                                    knowledge_results.append(clean_link)
                    except Exception as e:
                        logger.error(f"解析知识库内容错误: {str(e)}")
            
            return knowledge_results
            
        except Exception as e:
            logger.exception(f"获取知识库召回结果失败(SDK): {str(e)}")
            return []
    
    # 以下是HTTP请求的辅助方法，从coze_agent_new.py移植
    def _create_chat(self, content):
        """创建对话"""
        # 构建请求URL
        url = f"{self.http_base_url}/v3/chat"
        
        # 构建请求头
        headers = self._get_headers()
        
        # 构建请求体
        payload = {
            "bot_id": self.bot_id,
            "user_id": "default_user",
            "stream": False,
            "additional_messages": [
                {
                    "content": content,
                    "content_type": "text",
                    "role": "user",
                    "type": "question"
                }
            ]
        }
        
        try:
            # 发送请求，使用session及超时设置提高性能
            response = self.session.post(url, headers=headers, json=payload, timeout=(3.05, 10))
            response.raise_for_status()
            
            response_data = response.json()
            if not response_data:
                logger.error("API返回空响应")
                return None, None
                
            data = response_data.get("data")
            if not data:
                logger.error(f"API响应中没有data字段: {response_data}")
                return None, None
                
            conversation_id = data.get("conversation_id")
            chat_id = data.get("id")
            
            logger.debug(f"对话创建成功，Chat ID: {chat_id}, Conversation ID: {conversation_id}")
            
            return conversation_id, chat_id
        
        except Exception as e:
            logger.exception(e)
            return None, None

    def _poll_chat_status(self, conversation_id, chat_id):
        """轮询检查对话状态"""
        if not conversation_id or not chat_id:
            logger.error("conversation_id或chat_id为空，无法轮询状态")
            return None
            
        url = f"{self.http_base_url}/v3/chat/retrieve?chat_id={chat_id}&conversation_id={conversation_id}"
        headers = self._get_headers()
        
        start_time = time.time()
        
        for attempt in range(self.max_retries):
            try:
                # 等待一段时间再查询
                time.sleep(self.poll_interval)
                # 发送请求
                response = self.session.get(url, headers=headers, timeout=(3.05, 5))
                response.raise_for_status()
                response_data = response.json()
                if not response_data:
                    logger.error("API返回空响应")
                    continue
                    
                data = response_data.get("data")
                if not data:
                    logger.error(f"API响应中没有data字段: {response_data}")
                    continue
                    
                status = data.get("status")
                logger.debug(f"当前对话状态: {status}, 尝试次数: {attempt+1}/{self.max_retries}")
                if status in ["completed", "required_action"]:
                    elapsed = time.time() - start_time
                    logger.info(f"对话已完成，状态: {status}，尝试次数: {attempt+1}，耗时: {elapsed:.2f}秒")
                    return "success"
            except Exception as e:
                logger.exception(e)
                continue
        
        elapsed = time.time() - start_time
        logger.warning(f"对话状态轮询达到最大次数 {self.max_retries}，可能未完成，总耗时: {elapsed:.2f}秒")
        return None

    def _get_chat_messages(self, conversation_id, chat_id):
        """获取对话消息列表"""
        if not conversation_id or not chat_id:
            logger.error("conversation_id或chat_id为空，无法获取消息")
            return None
            
        url = f"{self.http_base_url}/v3/chat/message/list?chat_id={chat_id}&conversation_id={conversation_id}"
        headers = self._get_headers()
        try:
            response = self.session.get(url, headers=headers, timeout=(3.05, 10))
            response.raise_for_status()
            response_data = response.json()
            if not response_data:
                logger.error("API返回空响应")
                return None
                
            data = response_data.get("data")
            if not data:
                logger.error(f"API响应中没有data字段: {response_data}")
                return None
                
            logger.info(f"成功获取对话消息列表，共 {len(data)} 条消息")
            return data
        except Exception as e:
            logger.exception(e)
            return None

def remove_markdown(text):
    """移除Markdown格式"""
    # 替换Markdown的粗体标记
    text = text.replace("**", "")
    # 替换Markdown的标题标记
    text = text.replace("### ", "").replace("## ", "").replace("# ", "")
    # 去除链接外部括号
    text = re.sub(r'\((https?://[^\s\)]+)\)', r'\1', text)
    text = re.sub(r'\[(https?://[^\s\]]+)\]', r'\1', text)
    return text

def has_url(content):
    """检查内容中是否包含URL"""
    # 定义URL匹配的正则表达式模式
    url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    # 使用正则表达式模式进行匹配，找到第一个URL
    url = re.search(url_pattern, content)
    # 判断是否存在URL
    if url:
        return url.group()
    else:
        return False 