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
    from cozepy.bots import BotOnboardingInfo, Bot as CozeBot
    COZE_SDK_AVAILABLE = True
except ImportError:
    COZE_SDK_AVAILABLE = False
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
        
        # 处理 bot_id
        bot_id = self.config.get("core.agent.coze.bot_id")
        if isinstance(bot_id, str):
            self.bot_id = bot_id
        elif isinstance(bot_id, (list, tuple)) and len(bot_id) > 0:
            self.bot_id = bot_id[0]  # 使用第一个 bot_id
            if len(bot_id) > 1:
                logger.warning(f"配置了多个 bot_id，当前使用第一个: {self.bot_id}")
        else:
            raise ValueError("bot_id 必须是字符串或非空字符串数组")
            
        # 初始化配置
        self.max_retries = 30
        self.poll_interval = 0.3
        self.use_cn_api = True
        self.use_sdk = True
        
        # 获取API密钥
        self.api_key = self.config.get("core.agent.coze.api_key", "")
        if not self.api_key:
            raise ValueError("API 密钥未配置")
        
        # 根据官方示例设置 API 基地址
        if self.use_cn_api:
            # 使用国内API
            self.base_url = COZE_CN_BASE_URL
            logger.debug(f"使用国内API: {COZE_CN_BASE_URL}")
        else:
            # 使用海外API
            self.base_url = None  # 默认使用 api.coze.com
            logger.debug("使用海外API: api.coze.com")
        
        # 用于HTTP请求的base_url    
        self.http_base_url = self.config.get("core.agent.coze.base_url", COZE_CN_BASE_URL if self.use_cn_api else "https://api.coze.com")
            
        # 如果使用SDK，初始化Coze客户端
        if self.use_sdk:
            # 按照官方示例初始化 Coze 客户端
            self.client = Coze(
                auth=TokenAuth(token=self.api_key), 
                base_url=self.base_url if self.use_cn_api else None
            )
            
        # 创建HTTP会话
        self.session = create_http_session()
        
        logger.info(f"CozeAgent 初始化完成，bot_id: {self.bot_id}, API: {'国内' if self.use_cn_api else '海外'}, 模式: {'SDK' if self.use_sdk else 'HTTP'}")

    def _get_headers(self):
        """获取HTTP请求头"""
        return {
            'Authorization': f"Bearer {self.api_key}",
            'Content-Type': 'application/json'
        }

    def reply(self, query: str, context: Context) -> Reply:
        """处理用户输入，返回回复"""
        if context.type == ContextType.TEXT:
            logger.info("[COZE] query={}".format(query))
            
            session_id = context["session_id"]
            session = self.sessions.session_query(query, session_id)
            logger.debug("[COZE] session query={}".format(session.messages))
            
            # 使用流式输出
            logger.info("[COZE] 使用流式输出")
            logger.info("开始流式请求: {}...".format(query))
            
            def stream_wrapper():
                try:
                    for chunk in self.stream_reply(query):
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
            
            # 添加整体超时机制
            start_time = time.time()
            max_total_timeout = 30  # 设置30秒的总体超时时间
            
            # 发送请求
            with self.session.post(url, headers=headers, json=payload, stream=True, timeout=(3.05, 15)) as response:
                response.raise_for_status()
                
                # 使用更高效的缓冲区处理
                buffer = b""
                last_chunk_time = time.time()
                total_received_bytes = 0
                
                for chunk in response.iter_content(chunk_size=1024):  # 提高块大小至1KB
                    if not chunk:
                        continue
                    
                    # 检查总体超时
                    current_time = time.time()
                    if current_time - start_time > max_total_timeout:
                        logger.warning(f"流式请求总体超时 ({max_total_timeout}秒)，强制结束")
                        yield f"\n[请求超时: 超过{max_total_timeout}秒没有完成]"
                        return
                    
                    total_received_bytes += len(chunk)    
                    # 记录收到数据的时间
                    if current_time - last_chunk_time > 5.0:  # 如果超过5秒没有收到数据，记录警告
                        logger.warning(f"数据流中断 {current_time - last_chunk_time:.2f}秒")
                        yield f"\n[提示: 连接不稳定，请稍候...]"
                    last_chunk_time = current_time
                    
                    buffer += chunk
                    
                    # 添加单次处理超时保护
                    process_start = time.time()
                    
                    # 处理缓冲区中的行
                    while b'\n' in buffer and time.time() - process_start < 1.0:  # 添加1秒处理超时
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
                                            content = json_data['data'].get('content', '')
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
                                        content = json_data['data'].get('content', '')
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

    def get_bot_info(self):
        """
        获取Bot配置信息
        
        Returns:
            Bot对象，包含Bot的配置信息
        """
        try:
            if not self.use_sdk or not COZE_SDK_AVAILABLE:
                logger.warning("获取Bot信息需要使用SDK模式")
                return None
                
            # 获取Bot信息
            bot_info = self.client.bots.retrieve(bot_id=self.bot_id)
            logger.debug(f"成功获取Bot信息: {self.bot_id}")
            return bot_info
        except Exception as e:
            logger.error(f"获取Bot信息失败: {str(e)}")
            return None
            
    def get_welcome_message(self):
        """
        获取Bot配置的欢迎语和推荐问题
        
        Returns:
            tuple: (欢迎语, 推荐问题列表)
        """
        try:
            if not self.use_sdk or not COZE_SDK_AVAILABLE:
                logger.warning("获取欢迎语需要使用SDK模式")
                return None, []
                
            # 获取Bot信息
            bot_info = self.get_bot_info()
            if not bot_info:
                return None, []
                
            # 获取onboarding信息
            onboarding_info = bot_info.onboarding_info
            if not onboarding_info:
                logger.debug("Bot未配置onboarding信息")
                return None, []
                
            # 获取欢迎语和推荐问题
            prologue = onboarding_info.prologue
            suggested_questions = onboarding_info.suggested_questions
            
            return prologue, suggested_questions
        except Exception as e:
            logger.error(f"获取欢迎语失败: {str(e)}")
            return None, []
            
    def get_formatted_welcome(self):
        """
        获取格式化的欢迎信息，包含欢迎语和推荐问题
        
        Returns:
            str: 格式化的欢迎信息
        """
        prologue, suggested_questions = self.get_welcome_message()
        
        # 构建欢迎语
        welcome_text = prologue if prologue else "欢迎使用南开小知！"
        
        # 添加推荐问题
        if suggested_questions and len(suggested_questions) > 0:
            welcome_text += "\n\n您可以尝试以下问题:"
            for i, question in enumerate(suggested_questions):
                welcome_text += f"\n{i+1}. {question}"
                
        return welcome_text

    def get_bot_detail(self):
        """
        获取Bot详细配置信息
        
        Returns:
            dict: Bot详细配置信息
        """
        try:
            if not self.use_sdk or not COZE_SDK_AVAILABLE:
                logger.warning("获取Bot详细信息需要使用SDK模式")
                return None
                
            # 获取Bot详细信息
            bot_info = self.get_bot_info()
            if not bot_info:
                return None
                
            # 构建详细配置信息
            bot_detail = {
                "id": bot_info.bot_id,
                "name": bot_info.name,
                "description": bot_info.description,
                "icon_url": bot_info.icon_url,
                "create_time": bot_info.create_time,
                "update_time": bot_info.update_time,
                "version": bot_info.version,
                "prompt": bot_info.prompt_info.prompt if bot_info.prompt_info else None,
                "knowledge": {
                    "dataset_ids": bot_info.knowledge.dataset_ids if bot_info.knowledge else [],
                    "auto_call": bot_info.knowledge.auto_call if bot_info.knowledge else True,
                    "search_strategy": bot_info.knowledge.search_strategy if bot_info.knowledge else 0
                },
                "bot_mode": bot_info.bot_mode,
                "model": bot_info.model_info.model_name if bot_info.model_info else None,
                "onboarding": {
                    "prologue": bot_info.onboarding_info.prologue if bot_info.onboarding_info else "",
                    "suggested_questions": bot_info.onboarding_info.suggested_questions if bot_info.onboarding_info else []
                }
            }
            
            return bot_detail
        except Exception as e:
            logger.error(f"获取Bot详细信息失败: {str(e)}")
            return None
    
    def get_suggested_questions(self):
        """
        获取Bot配置的推荐问题列表
        
        Returns:
            list: 推荐问题列表
        """
        try:
            _, suggested_questions = self.get_welcome_message()
            return suggested_questions
        except Exception as e:
            logger.error(f"获取推荐问题失败: {str(e)}")
            return []
    
    def create_conversation(self):
        """
        创建新的对话
        
        Returns:
            str: 对话ID
        """
        try:
            if not self.use_sdk or not COZE_SDK_AVAILABLE:
                logger.warning("创建对话需要使用SDK模式")
                return None
                
            # 创建新的对话
            conversation = self.client.conversations.create()
            logger.debug(f"创建新对话成功: {conversation.id}")
            
            return conversation.id
        except Exception as e:
            logger.error(f"创建对话失败: {str(e)}")
            return None
    
    def add_message_to_conversation(self, conversation_id, role, content):
        """
        向对话中添加消息
        
        Args:
            conversation_id: 对话ID
            role: 消息角色，"user"或"assistant"
            content: 消息内容
            
        Returns:
            bool: 是否添加成功
        """
        try:
            if not self.use_sdk or not COZE_SDK_AVAILABLE:
                logger.warning("添加消息需要使用SDK模式")
                return False
                
            from cozepy import MessageRole, MessageContentType
            
            # 设置消息角色
            if role.lower() == "user":
                message_role = MessageRole.USER
            elif role.lower() == "assistant":
                message_role = MessageRole.ASSISTANT
            else:
                logger.error(f"不支持的消息角色: {role}")
                return False
                
            # 添加消息
            message = self.client.conversations.messages.create(
                conversation_id=conversation_id,
                role=message_role,
                content=content,
                content_type=MessageContentType.TEXT
            )
            
            logger.debug(f"添加消息成功: {message.id}")
            return True
        except Exception as e:
            logger.error(f"添加消息失败: {str(e)}")
            return False
    
    def clear_conversation(self, conversation_id):
        """
        清空对话历史
        
        Args:
            conversation_id: 对话ID
            
        Returns:
            bool: 是否清空成功
        """
        try:
            if not self.use_sdk or not COZE_SDK_AVAILABLE:
                logger.warning("清空对话需要使用SDK模式")
                return False
                
            # 清空对话
            section = self.client.conversations.clear(conversation_id=conversation_id)
            logger.debug(f"清空对话成功: {section.section_id}")
            
            return True
        except Exception as e:
            logger.error(f"清空对话失败: {str(e)}")
            return False
    
    def get_conversation_messages(self, conversation_id):
        """
        获取对话中的所有消息
        
        Args:
            conversation_id: 对话ID
            
        Returns:
            list: 消息列表
        """
        try:
            if not self.use_sdk or not COZE_SDK_AVAILABLE:
                logger.warning("获取对话消息需要使用SDK模式")
                return []
                
            # 获取对话消息
            messages = self.client.conversations.messages.list(conversation_id=conversation_id)
            
            # 构建消息列表
            message_list = []
            for message in messages:
                message_list.append({
                    "id": message.id,
                    "role": message.role,
                    "content": message.content,
                    "content_type": message.content_type,
                    "type": message.type if hasattr(message, "type") else None,
                    "meta_data": message.meta_data
                })
            
            logger.debug(f"获取对话消息成功，共 {len(message_list)} 条")
            return message_list
        except Exception as e:
            logger.error(f"获取对话消息失败: {str(e)}")
            return []
    
    def chat_with_new_conversation(self, query, stream=True):
        """
        创建新对话并发送消息
        
        Args:
            query: 用户输入
            stream: 是否使用流式输出
            
        Returns:
            如果stream为True，则返回生成器；否则返回回复内容
        """
        try:
            if not self.use_sdk or not COZE_SDK_AVAILABLE:
                logger.warning("新对话聊天需要使用SDK模式，将使用HTTP方式")
                return self.stream_reply(query) if stream else self.reply(query)
                
            from cozepy import Message, ChatEventType, MessageContentType
            
            # 创建新对话并发送消息
            if stream:
                # 流式响应
                logger.debug(f"创建新对话并发送消息(流式): {query[:30]}...")
                events = self.client.chat.stream(
                    bot_id=self.bot_id,
                    user_id="default_user",
                    additional_messages=[
                        Message.build_user_question_text(query)
                    ]
                )
                
                # 返回内容生成器
                def content_generator():
                    for event in events:
                        if event.event == ChatEventType.CONVERSATION_MESSAGE_DELTA and event.message.content:
                            yield event.message.content
                
                return content_generator()
            else:
                # 非流式响应
                logger.debug(f"创建新对话并发送消息(非流式): {query[:30]}...")
                chat_poll = self.client.chat.create_and_poll(
                    bot_id=self.bot_id,
                    user_id="default_user",
                    additional_messages=[
                        Message.build_user_question_text(query)
                    ]
                )
                
                # 提取回复内容
                for message in chat_poll.messages:
                    if message.role == "assistant" and message.type == "answer":
                        return message.content
                
                return None
        except Exception as e:
            logger.error(f"创建新对话并发送消息失败: {str(e)}")
            if stream:
                def error_generator():
                    yield f"请求失败: {str(e)}"
                return error_generator()
            else:
                return f"请求失败: {str(e)}"

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