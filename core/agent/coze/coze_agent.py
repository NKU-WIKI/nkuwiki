#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
使用官方 coze-py SDK 的 CozeAgent 实现
"""
# 标准库导入
import os
import sys
import json
import time
import re
from typing import List, Dict, AsyncGenerator, Generator

# 第三方库导入
import requests
import aiohttp
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# 确保项目根目录在 sys.path 中
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if project_root not in sys.path:
    sys.path.append(project_root)

# 本地导入
from config import Config
from core.agent import Agent
from core.bridge.context import ContextType, Context
from core.bridge.reply import Reply, ReplyType
from core.utils.logger import register_logger

# 初始化日志
logger = register_logger("core.agent.coze")

# 需要先安装 cozepy: pip install cozepy
from cozepy import Coze, TokenAuth, Message, ChatEventType, COZE_CN_BASE_URL
from cozepy import MessageRole, MessageContentType

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
    
    def __init__(self, tag="default"):
        super().__init__()
        self.config = Config()
        
        # 获取API密钥
        self.api_key = self.config.get("core.agent.coze.api_key", "")
        if not self.api_key:
            raise ValueError("API 密钥未配置")
            
        # 处理 bot_id
        bot_id = self.config.get(f"core.agent.coze.{tag}_bot_id")
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
        
        # 根据配置设置API基地址
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
        
        # 初始化Coze客户端
        self.client = Coze(
            auth=TokenAuth(token=self.api_key), 
            base_url=self.base_url if self.use_cn_api else None
        )
            
        # 创建HTTP会话
        self.session = create_http_session()
        
        logger.info(f"CozeAgent 初始化完成，bot_id: {self.bot_id}, API: {'国内' if self.use_cn_api else '海外'}")

    def _get_headers(self):
        """获取HTTP请求头"""
        return {
            'Authorization': f"Bearer {self.api_key}",
            'Content-Type': 'application/json'
        }

    def reply(self, query: str, context: Context) -> Reply:
        """处理用户输入，返回回复"""
        if context.type == ContextType.TEXT:
            logger.info(f"[COZE] query={query}")
            
            session_id = context["session_id"]
            session = self.sessions.session_query(query, session_id)
            logger.debug(f"[COZE] session query={session.messages}")
            
            # 获取user_id，如果没有则使用默认值
            user_id = context.get("user_id", "default_user")
            logger.debug(f"[COZE] 使用用户ID: {user_id}")
            
            # 检查是否需要 Markdown 格式
            format_type = context.get("format", "text")
            meta_data = {"format": format_type} if format_type != "text" else None
            logger.debug(f"[COZE] 输出格式: {format_type}")
            
            # 检查是否需要流式输出
            stream_output = context.get("stream_output", False) or context.get("stream", False)
            if stream_output:
                logger.info("[COZE] 使用流式输出")
                logger.info(f"开始流式请求: {query[:30]}...")
                
                def stream_wrapper():
                    try:
                        for chunk in self.stream_reply(query, format_type, user_id):
                            yield chunk
                    except Exception as e:
                        logger.error(f"[COZE] 流式回复出错: {str(e)}")
                        yield f"\n[错误: {str(e)}]"
                
                # 处理完成后更新会话
                completion_tokens, total_tokens = self._calc_tokens(session.messages, "流式回复")
                self.sessions.session_reply("流式回复", session_id, total_tokens)
                
                return Reply(ReplyType.STREAM, stream_wrapper())
            else:
                # 非流式输出
                logger.info("[COZE] 使用非流式输出")
                try:
                    response = self.client.chat.create_and_poll(
                        bot_id=self.bot_id,
                        user_id=user_id,
                        additional_messages=[
                            Message.build_user_question_text(query, meta_data=meta_data)
                        ]
                    )
                    
                    # 提取回复内容
                    for message in response.messages:
                        if message.role == "assistant" and message.type == "answer":
                            # 处理完成后更新会话
                            completion_tokens, total_tokens = self._calc_tokens(session.messages, message.content)
                            self.sessions.session_reply(message.content, session_id, total_tokens)
                            return Reply(ReplyType.TEXT, message.content)
                    
                    return Reply(ReplyType.TEXT, "未获取到有效回复")
                except (ValueError, KeyError) as e:
                    logger.error(f"[COZE] 非流式回复客户端错误: {str(e)}")
                    return Reply(ReplyType.TEXT, f"请求参数错误: {str(e)}")
                except requests.RequestException as e:
                    logger.error(f"[COZE] 非流式回复网络错误: {str(e)}")
                    return Reply(ReplyType.TEXT, f"网络请求失败: {str(e)}")
                except Exception as e:
                    logger.error(f"[COZE] 非流式回复未知错误: {str(e)}")
                    return Reply(ReplyType.TEXT, f"请求失败: {str(e)}")
            
        elif context.type == ContextType.IMAGE_CREATE:
            return Reply(ReplyType.TEXT, "暂不支持图片生成")
        else:
            return Reply(ReplyType.TEXT, "暂不支持该类型消息")

    def _calc_tokens(self, messages, answer):
        """计算token数量"""
        completion_tokens = len(answer)
        prompt_tokens = 0
        for message in messages:
            prompt_tokens += len(message["content"])
        return completion_tokens, prompt_tokens + completion_tokens

    def stream_reply(self, query, format_type="text", user_id="default_user"):
        """
        流式返回对话响应
        
        Args:
            query: 用户输入
            format_type: 输出格式类型，如 'text', 'markdown' 等
            user_id: 用户ID
            
        Returns:
            生成器，每次迭代返回一个响应片段
        """
        try:
            logger.debug(f"开始流式请求: {query[:30]}...")
            
            # 设置元数据
            meta_data = {"format": format_type} if format_type != "text" else None
            
            # 使用SDK的流式接口
            stream = self.client.chat.stream(
                bot_id=self.bot_id,
                user_id=user_id,
                additional_messages=[
                    Message.build_user_question_text(query, meta_data=meta_data)
                ]
            )
            
            # 处理流式响应
            for event in stream:
                if event.event == ChatEventType.CONVERSATION_MESSAGE_DELTA:
                    if event.message and event.message.content:
                        yield event.message.content
                        
        except (ValueError, KeyError) as e:
            logger.error(f"流式请求参数错误: {e}")
            yield f"请求参数错误: {e}"
        except requests.RequestException as e:
            logger.error(f"流式请求网络错误: {e}")
            yield f"网络请求失败: {e}"
        except Exception as e:
            logger.exception(f"流式请求未知错误: {e}")
            yield f"请求失败: {e}"

    def get_knowledge_results(self, query, user_id="default_user"):
        """
        获取对话的知识库召回结果
        
        Args:
            query: 用户输入
            user_id: 用户ID
            
        Returns:
            知识库召回结果列表
        """
        try:
            logger.info(f"开始获取知识库召回结果，bot_id: {self.bot_id}, query: {query}")
            
            # 创建对话
            chat = self.client.chat.create(
                bot_id=self.bot_id,
                user_id=user_id,
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
                    except json.JSONDecodeError as e:
                        logger.error(f"解析知识库内容JSON错误: {str(e)}")
                    except Exception as e:
                        logger.error(f"解析知识库内容其他错误: {str(e)}")
            
            return knowledge_results
            
        except (ValueError, KeyError) as e:
            logger.error(f"获取知识库召回结果参数错误: {str(e)}")
            return []
        except requests.RequestException as e:
            logger.error(f"获取知识库召回结果网络错误: {str(e)}")
            return []
        except Exception as e:
            logger.exception(f"获取知识库召回结果未知错误: {str(e)}")
            return []

    def get_bot_info(self):
        """
        获取Bot配置信息
        
        Returns:
            Bot对象，包含Bot的配置信息
        """
        try:
            # 获取Bot信息
            bot_info = self.client.bots.retrieve(bot_id=self.bot_id)
            logger.debug(f"成功获取Bot信息: {self.bot_id}")
            return bot_info
        except (ValueError, KeyError) as e:
            logger.error(f"获取Bot信息参数错误: {str(e)}")
            return None
        except requests.RequestException as e:
            logger.error(f"获取Bot信息网络错误: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"获取Bot信息未知错误: {str(e)}")
            return None
            
    def get_welcome_message(self):
        """
        获取Bot配置的欢迎语和推荐问题
        
        Returns:
            tuple: (欢迎语, 推荐问题列表)
        """
        try:
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
        except AttributeError as e:
            logger.error(f"获取欢迎语数据结构错误: {str(e)}")
            return None, []
        except Exception as e:
            logger.error(f"获取欢迎语未知错误: {str(e)}")
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
        except AttributeError as e:
            logger.error(f"获取Bot详细信息数据结构错误: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"获取Bot详细信息未知错误: {str(e)}")
            return None
    
    def get_suggested_questions(self):
        """
        获取推荐问题列表
        
        Returns:
            list: 推荐问题列表
        """
        try:
            # 这里可以实现具体的推荐问题逻辑
            # 目前返回一些通用的问题
            return [
                "南开大学的历史是什么？",
                "南开大学有哪些著名校友？",
                "南开大学的特色专业有哪些？"
            ]
        except Exception as e:
            logger.warning(f"获取推荐问题失败: {e}")
            return []
    
    def create_conversation(self):
        """
        创建新的对话
        
        Returns:
            str: 对话ID
        """
        try:
            # 创建新的对话
            conversation = self.client.conversations.create()
            logger.debug(f"创建新对话成功: {conversation.id}")
            
            return conversation.id
        except requests.RequestException as e:
            logger.error(f"创建对话网络错误: {str(e)}")
            return None
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
        except ValueError as e:
            logger.error(f"添加消息参数错误: {str(e)}")
            return False
        except requests.RequestException as e:
            logger.error(f"添加消息网络错误: {str(e)}")
            return False
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
            # 清空对话
            section = self.client.conversations.clear(conversation_id=conversation_id)
            logger.debug(f"清空对话成功: {section.section_id}")
            
            return True
        except ValueError as e:
            logger.error(f"清空对话参数错误: {str(e)}")
            return False
        except requests.RequestException as e:
            logger.error(f"清空对话网络错误: {str(e)}")
            return False
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
        except ValueError as e:
            logger.error(f"获取对话消息参数错误: {str(e)}")
            return []
        except requests.RequestException as e:
            logger.error(f"获取对话消息网络错误: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"获取对话消息失败: {str(e)}")
            return []
    
    def chat_with_new_conversation(self, query, stream=True, user_id="default_user"):
        """
        创建新对话并发送消息
        
        Args:
            query: 用户输入
            stream: 是否使用流式输出
            user_id: 用户ID
            
        Returns:
            如果stream为True，则返回生成器；否则返回回复内容
        """
        try:
            # 创建新对话并发送消息
            if stream:
                # 流式响应
                logger.debug(f"创建新对话并发送消息(流式): {query[:30]}...")
                events = self.client.chat.stream(
                    bot_id=self.bot_id,
                    user_id=user_id,
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
                    user_id=user_id,
                    additional_messages=[
                        Message.build_user_question_text(query)
                    ]
                )
                
                # 提取回复内容
                for message in chat_poll.messages:
                    if message.role == "assistant" and message.type == "answer":
                        return message.content
                
                return None
        except (ValueError, KeyError) as e:
            logger.error(f"创建新对话并发送消息参数错误: {str(e)}")
            if stream:
                def error_generator():
                    yield f"请求参数错误: {str(e)}"
                return error_generator()
            else:
                return f"请求参数错误: {str(e)}"
        except requests.RequestException as e:
            logger.error(f"创建新对话并发送消息网络错误: {str(e)}")
            if stream:
                def error_generator():
                    yield f"网络请求失败: {str(e)}"
                return error_generator()
            else:
                return f"网络请求失败: {str(e)}"
        except Exception as e:
            logger.error(f"创建新对话并发送消息未知错误: {str(e)}")
            if stream:
                def error_generator():
                    yield f"请求失败: {str(e)}"
                return error_generator()
            else:
                return f"请求失败: {str(e)}"

    async def stream_chat(self, query: str, history: List[Dict] = None, user_id="default_user") -> AsyncGenerator[str, None]:
        """异步流式对话接口"""
        try:
            # 构建历史消息
            messages = []
            if history:
                for msg in history:
                    role = msg.get("role", "user")
                    content = msg.get("content", "")
                    if role == "user":
                        messages.append(Message.build_user_question_text(content))
                    elif role == "assistant":
                        messages.append(Message.build_assistant_answer_text(content))
            
            # 添加当前用户问题
            messages.append(Message.build_user_question_text(query))
            
            # 使用aiohttp创建异步HTTP客户端会话
            async with aiohttp.ClientSession() as session:
                # 构建请求URL和头部
                url = f"{self.http_base_url}/v3/chat"
                headers = self._get_headers()
                headers.update({
                    'Accept': 'text/event-stream',
                    'Cache-Control': 'no-cache',
                    'Connection': 'keep-alive'
                })
                
                # 构建请求体
                payload = {
                    "bot_id": self.bot_id,
                    "user_id": user_id,
                    "stream": True,
                    "additional_messages": messages
                }
                
                # 发送异步请求
                async with session.post(url, headers=headers, json=payload) as response:
                    response.raise_for_status()
                    
                    # 处理流式响应
                    buffer = b""
                    async for chunk in response.content.iter_chunked(1024):
                        if not chunk:
                            continue
                            
                        buffer += chunk
                        
                        while b'\n' in buffer:
                            line, buffer = buffer.split(b'\n', 1)
                            if not line:
                                continue
                                
                            try:
                                line = line.decode('utf-8')
                                if line.startswith('data: '):
                                    data = line[6:]
                                    if data == '[DONE]':
                                        return
                                        
                                    try:
                                        json_data = json.loads(data)
                                        if 'data' in json_data and isinstance(json_data['data'], dict):
                                            content = json_data['data'].get('content', '')
                                            if content:
                                                yield content
                                    except json.JSONDecodeError:
                                        logger.debug(f"非JSON数据: {data[:30]}...")
                            except UnicodeDecodeError as e:
                                logger.debug(f"解码错误: {str(e)}")
                                continue
                            except Exception as e:
                                logger.debug(f"处理行时出错: {str(e)}")
                                continue
                    
        except aiohttp.ClientError as e:
            logger.error(f"异步流式对话客户端错误: {str(e)}")
            yield f"网络请求失败: {str(e)}"
        except ValueError as e:
            logger.error(f"异步流式对话参数错误: {str(e)}")
            yield f"请求参数错误: {str(e)}"
        except Exception as e:
            logger.error(f"异步流式对话未知错误: {str(e)}")
            yield f"错误: {str(e)}"

    async def chat(self, messages, format="markdown"):
        """
        异步对话方法，使用Coze客户端直接发送请求
        
        Args:
            messages: 消息历史
            format: 输出格式
            
        Returns:
            对话响应对象
        """
        logger.debug(f"调用chat方法，消息数量: {len(messages)}")
        
        # 提取最后一条用户消息作为查询
        query = None
        for msg in reversed(messages):
            if msg.role == MessageRole.USER:
                query = msg.content
                break
                
        if not query:
            logger.error("没有找到用户消息")
            return {"content": "未找到有效的用户消息", "sources": [], "suggested_questions": []}
            
        # 获取用户ID
        user_id = "api_user"
        
        # 设置元数据
        meta_data = {"format": format} if format != "text" else None
        
        try:
            # 使用Coze客户端发送请求
            additional_messages = []
            for msg in messages:
                if msg.role == MessageRole.USER:
                    additional_messages.append(Message.build_user_question_text(msg.content))
                elif msg.role == MessageRole.ASSISTANT:
                    additional_messages.append(Message.build_assistant_answer_text(msg.content))
                elif msg.role == MessageRole.SYSTEM:
                    additional_messages.append(Message(role=MessageRole.SYSTEM, type=MessageContentType.TEXT, content=msg.content))
            
            # 如果additional_messages为空，则添加当前查询
            if not additional_messages:
                additional_messages.append(Message.build_user_question_text(query, meta_data=meta_data))
            
            # 发送请求
            api_response = self.client.chat.create_and_poll(
                bot_id=self.bot_id,
                user_id=user_id,
                additional_messages=additional_messages
            )
            
            # 提取回复内容
            content = ""
            for message in api_response.messages:
                if message.role == "assistant" and message.type == "answer":
                    content = message.content
                    break
            
            if not content:
                logger.warning("未从响应中获取到有效内容")
                content = "抱歉，没有获取到回答。"
            
            # 构建响应
            response = {
                "content": content,
                "sources": [],
                "suggested_questions": []
            }
            
            # 尝试获取建议问题
            try:
                suggested = self.get_suggested_questions()
                if suggested and isinstance(suggested, list):
                    response["suggested_questions"] = suggested[:3]  # 最多返回3个建议问题
            except Exception as e:
                logger.warning(f"获取建议问题失败: {str(e)}")
            
            return response
            
        except Exception as e:
            logger.error(f"chat方法出错: {str(e)}")
            return {
                "content": f"请求失败: {str(e)}",
                "sources": [],
                "suggested_questions": []
            }

    async def chat_stream(self, messages, format="markdown"):
        """
        异步流式对话方法，使用现有的stream_chat方法实现
        
        Args:
            messages: 消息历史
            format: 输出格式
            
        Returns:
            流式响应
        """
        logger.debug(f"调用chat_stream方法，消息数量: {len(messages)}")
        
        # 提取最后一条用户消息作为查询
        query = None
        for msg in reversed(messages):
            if msg.role == MessageRole.USER:
                query = msg.content
                break
                
        if not query:
            logger.error("没有找到用户消息")
            return None
            
        # 转换消息历史格式
        history = []
        for msg in messages:
            if msg.role == MessageRole.USER or msg.role == MessageRole.ASSISTANT:
                history.append({
                    "role": msg.role,
                    "content": msg.content
                })
        
        # 调用stream_chat方法
        from fastapi.responses import StreamingResponse
        
        async def generate():
            async for chunk in self.stream_chat(query, history):
                if chunk:
                    yield f"data: {chunk}\n\n"
            yield "data: [DONE]\n\n"
            
        return StreamingResponse(generate(), media_type="text/event-stream")

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