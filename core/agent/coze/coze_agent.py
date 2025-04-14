#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
使用官方 coze-py SDK 的 CozeAgent 精简实现
"""

import json
import os
import sys
import re
from typing import List, Dict, Generator
import time
from loguru import logger
import uuid

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

try:
    from cozepy import Coze, TokenAuth, Message, ChatEventType, COZE_CN_BASE_URL, MessageRole, MessageContentType, ChatStatus
    COZE_SDK_AVAILABLE = True
except ImportError:
    COZE_SDK_AVAILABLE = False
    logger.error("需要先安装 cozepy: pip install cozepy")
    raise

config = Config()
class CozeAgent(Agent):
    """CozeAgent类，使用官方 coze-py SDK 的精简实现"""
    
    def __init__(self, tag="default"):
        """初始化Coze智能体"""
        super().__init__()
        self.sessions = SessionManager(ChatGPTSession, model=config.get("model") or "coze")
        
        # 获取API密钥
        self.api_key = config.get("core.agent.coze.api_key", "")
        if not self.api_key:
            raise ValueError("API 密钥未配置")
        

        bot_id_list = config.get(f"core.agent.coze.{tag}_bot_id")
        
        if(isinstance(bot_id_list, list)):
            self.bot_id = bot_id_list[0]
        else:
            self.bot_id = bot_id_list

        logger.info(f"CozeAgent初始化，输入tag: {tag},bot_id: {self.bot_id}")

        # 初始化Coze客户端
        self.client = Coze(
            auth=TokenAuth(token=self.api_key), 
            base_url=COZE_CN_BASE_URL  # 默认使用国内API
        )
        
        logger.info(f"CozeAgent 初始化完成，tag={tag}, bot_id={self.bot_id}")

    def reply(self, query: str, context: Context) -> Reply:
        """处理用户输入，返回回复"""
        if context.type == ContextType.TEXT:
            logger.info("[COZE] query={}".format(query))
            
            session_id = context["session_id"]
            session = self.sessions.session_query(query, session_id)
            
            # 获取openid，如果没有则使用默认值
            openid = context.get("openid", "default_user")
            
            # 检查是否需要 Markdown 格式
            format_type = context.get("format", "text")
            meta_data = {"format": format_type} if format_type != "text" else None
            
            # 检查是否需要流式输出
            if context.get("stream", False):
                logger.info("[COZE] 使用流式输出")
                
                def stream_wrapper():
                    chunk_count = 0
                    total_chars = 0
                    wrapper_start = time.time()
                    logger.info(f"[COZE] 启动流式输出包装器，openid={openid}")
                    
                    try:
                        for chunk in self._stream_reply(query, format_type, openid):
                            chunk_count += 1
                            total_chars += len(chunk)
                            
                            # 记录一些关键点的状态
                            if chunk_count == 1:
                                logger.debug(f"[COZE] 转发首个响应块: '{chunk[:20]}...'")
                            elif chunk_count % 50 == 0:  # 每50个块记录一次
                                time_elapsed = time.time() - wrapper_start
                                logger.debug(f"[COZE] 已转发 {chunk_count} 个块，总字符数: {total_chars}，运行时间: {time_elapsed:.2f}秒")
                                
                            yield chunk
                            
                        # 记录完成信息
                        wrapper_time = time.time() - wrapper_start
                        logger.info(f"[COZE] 流式输出完成: {chunk_count} 个块，{total_chars} 字符，耗时: {wrapper_time:.2f}秒")
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
                max_retries = 3
                retry_count = 0
                
                while retry_count < max_retries:
                    try:
                        logger.debug(f"开始非流式请求，尝试次数: {retry_count + 1}")
                        response = self.client.chat.create_and_poll(
                            bot_id=self.bot_id,
                            user_id=openid,
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
                        
                    except Exception as e:
                        retry_count += 1
                        error_msg = str(e)
                        logger.warning(f"非流式请求失败 (尝试 {retry_count}/{max_retries}): {error_msg}")
                        
                        # 如果是网络断开错误，尝试重试
                        if "RemoteProtocolError" in error_msg or "Server disconnected" in error_msg:
                            if retry_count < max_retries:
                                wait_time = retry_count * 2  # 指数退避
                                logger.info(f"等待 {wait_time} 秒后重试...")
                                time.sleep(wait_time)
                                continue
                        
                        # 达到最大重试次数或其他错误
                        if retry_count >= max_retries:
                            return Reply(ReplyType.TEXT, f"请求失败 (尝试 {retry_count}/{max_retries}): {error_msg}")
                        
                return Reply(ReplyType.TEXT, "请求过程中发生未知错误")
            
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

    def _stream_reply(self, query, format_type="text", openid="default_user"):
        """流式返回对话响应"""
        max_retries = 3
        retry_count = 0
        chunk_count = 0
        total_chars = 0
        start_time = time.time()
        
        logger.info(f"开始流式会话: query={query[:30]}..., format={format_type}, openid={openid}")
        
        while retry_count < max_retries:
            try:
                logger.debug(f"开始流式请求: {query[:30]}...，尝试次数: {retry_count + 1}")
                request_time = time.time()
                
                # 设置元数据
                meta_data = {"format": format_type} if format_type != "text" else None
                
                # 使用SDK的流式接口
                stream = self.client.chat.stream(
                    bot_id=self.bot_id,
                    user_id=openid,
                    additional_messages=[
                        Message.build_user_question_text(query, meta_data=meta_data)
                    ]
                )
                
                logger.debug(f"已连接到流，等待响应...")
                first_chunk_received = False
                
                # 处理流式响应
                for event in stream:
                    if event.event == ChatEventType.CONVERSATION_MESSAGE_DELTA:
                        if event.message and event.message.content:
                            chunk = event.message.content
                            chunk_count += 1
                            total_chars += len(chunk)
                            
                            # 只记录首个响应块
                            if not first_chunk_received:
                                first_chunk_received = True
                                time_to_first = time.time() - request_time
                                logger.debug(f"收到首个响应: 耗时={time_to_first:.2f}秒")
                            
                            yield chunk
                
                # 如果成功完成，记录完成信息并跳出循环
                total_time = time.time() - start_time
                logger.info(f"流式请求完成: 共 {chunk_count} 个响应块，{total_chars} 字符，总耗时: {total_time:.2f}秒")
                break
                        
            except Exception as e:
                retry_count += 1
                error_msg = str(e)
                error_time = time.time() - start_time
                logger.warning(f"流式请求失败 (尝试 {retry_count}/{max_retries}): {error_msg}, 耗时: {error_time:.2f}秒")
                
                # 如果是网络断开错误，尝试重试
                if "RemoteProtocolError" in error_msg or "Server disconnected" in error_msg:
                    if retry_count < max_retries:
                        wait_time = retry_count * 2  # 指数退避
                        logger.info(f"等待 {wait_time} 秒后重试...")
                        time.sleep(wait_time)
                        continue
                
                # 达到最大重试次数或其他错误，返回错误消息
                logger.error(f"流式请求最终失败，已尝试 {retry_count} 次，返回错误消息")
                yield f"请求失败 (尝试 {retry_count}/{max_retries}): {error_msg}"
                break

    def get_knowledge_results(self, query, openid="default_user"):
        """获取对话的知识库召回结果"""
        try:
            logger.info(f"开始获取知识库召回结果，bot_id: {self.bot_id}, query: {query}")
            
            # 创建对话
            chat = self.client.chat.create(
                bot_id=self.bot_id,
                user_id=openid,
                additional_messages=[
                    Message.build_user_question_text(query)
                ]
            )
            
            # 获取会话ID和聊天ID
            conversation_id = chat.conversation_id
            chat_id = chat.id
            
            # 等待对话完成
            for _ in range(30):
                time.sleep(0.3)
                
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
            logger.exception(f"获取知识库召回结果失败: {str(e)}")
            return []

    def get_welcome_message(self):
        """获取Bot配置的欢迎语和推荐问题"""
        try:
            # 获取Bot信息
            bot_info = self.client.bots.retrieve(bot_id=self.bot_id)
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
        """获取格式化的欢迎信息，包含欢迎语和推荐问题"""
        prologue, suggested_questions = self.get_welcome_message()
        
        # 构建欢迎语
        welcome_text = prologue if prologue else "欢迎使用南开小知！"
        
        # 添加推荐问题
        if suggested_questions and len(suggested_questions) > 0:
            welcome_text += "\n\n您可以尝试以下问题:"
            for i, question in enumerate(suggested_questions):
                welcome_text += f"\n{i+1}. {question}"
                
        return welcome_text
    
    def create_conversation(self):
        """创建新的对话"""
        try:
            conversation = self.client.conversations.create()
            logger.debug(f"创建新对话成功: {conversation.id}")
            return conversation.id
        except Exception as e:
            logger.error(f"创建对话失败: {str(e)}")
            return None
    
    def add_message_to_conversation(self, conversation_id, role, content):
        """向对话中添加消息"""
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
        except Exception as e:
            logger.error(f"添加消息失败: {str(e)}")
            return False
    
    def clear_conversation(self, conversation_id):
        """清空对话历史"""
        try:
            section = self.client.conversations.clear(conversation_id=conversation_id)
            logger.debug(f"清空对话成功: {section.section_id}")
            return True
        except Exception as e:
            logger.error(f"清空对话失败: {str(e)}")
            return False
    
    def get_conversation_messages(self, conversation_id):
        """获取对话中的所有消息"""
        try:
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
    
    def chat_with_new_conversation(self, query, stream=True, openid="default_user"):
        """创建新对话并发送消息"""
        try:
            # 流式响应
            if stream:
                logger.debug(f"创建新对话并发送消息(流式): {query[:30]}...")
                events = self.client.chat.stream(
                    bot_id=self.bot_id,
                    user_id=openid,
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
                    user_id=openid,
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
    url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    url = re.search(url_pattern, content)
    return url.group() if url else False 