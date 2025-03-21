#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
测试 Coze Agent 功能
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent.parent))
from core import config, logger as core_logger  # 重命名为core_logger避免混淆

import os
import asyncio
import time
import traceback
import logging

# 创建一个标准的Python日志记录器
log_file = os.path.join(os.path.dirname(__file__), 'log')
file_logger = logging.getLogger('coze_test')
file_logger.setLevel(logging.DEBUG)
# 清空所有处理器
file_logger.handlers = []

# 捕获标准输出和标准错误
class OutputRedirector:
    def __init__(self, file_path):
        self.file = open(file_path, 'w', encoding='utf-8')
        self.stdout = sys.stdout
        self.stderr = sys.stderr
        sys.stdout = self
        sys.stderr = self
    
    def write(self, text):
        self.file.write(text)
        self.file.flush()
    
    def flush(self):
        self.file.flush()
    
    def close(self):
        if sys.stdout is self:
            sys.stdout = self.stdout
        if sys.stderr is self:
            sys.stderr = self.stderr
        self.file.close()

# 重定向输出到文件 - 先打开文件，清空内容
redirector = OutputRedirector(log_file)

# 配置文件日志 - 使用追加模式，避免和重定向覆盖冲突
file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
file_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
file_logger.addHandler(file_handler)
file_logger.propagate = False  # 避免重复记录

# 禁止其他日志输出到终端
root_logger = logging.getLogger()
for handler in root_logger.handlers[:]:
    root_logger.removeHandler(handler)

# 需要先安装 cozepy: pip install cozepy
try:
    from cozepy import COZE_CN_BASE_URL
except ImportError:
    COZE_CN_BASE_URL = "https://api.coze.cn"

# 导入必要的类
from core.agent.coze.coze_agent import CozeAgent
from core.bridge.context import Context, ContextType
from core.bridge.reply import ReplyType

def test_stream_response():
    """测试流式响应"""
    try:
        bot_id = config.get("core.agent.coze.flash_bot_id", "")
        if not bot_id:
            file_logger.error("未配置 flash_bot_id，请检查配置")
            return
            
        file_logger.info("初始化 CozeAgent")
        agent = CozeAgent()
        agent.bot_id = bot_id
        
        query = "以南开大学为例，介绍一下中国的高等教育体系"
        file_logger.info(f"测试流式响应，查询: {query}")
        
        # 创建上下文
        context = Context(ContextType.TEXT)
        context["session_id"] = "test_stream_response"
        
        # 测试流式响应
        total_chunks = 0
        total_chars = 0
        full_response = ""
        
        file_logger.info("开始接收流式响应...")
        reply = agent.reply(query, context)
        
        if reply.type != ReplyType.STREAM:
            file_logger.error("未获取到流式回复")
            return
            
        for chunk in reply.content:
            total_chunks += 1
            total_chars += len(chunk)
            full_response += chunk
            # 只打印前10个和后10个块，减少日志量
            if total_chunks <= 10 or total_chunks % 50 == 0:
                file_logger.info(f"收到chunk {total_chunks}: {chunk}")
        
        file_logger.info(f"流式响应完成: 总接收 {total_chunks} 个片段，共 {total_chars} 个字符")
        file_logger.info(f"完整响应: {full_response}")
        
    except Exception as e:
        file_logger.error(f"测试流式响应失败: {str(e)}")
        file_logger.error(traceback.format_exc())

def test_normal_response():
    """测试普通响应"""
    try:
        bot_id = config.get("core.agent.coze.flash_bot_id", "")
        if not bot_id:
            file_logger.error("未配置 flash_bot_id，请检查配置")
            return
            
        file_logger.info("初始化 CozeAgent")
        agent = CozeAgent()
        agent.bot_id = bot_id
        
        query = "介绍一下南开大学的历史"
        file_logger.info(f"测试普通响应，查询: {query}")
        
        # 创建上下文
        context = Context(ContextType.TEXT)
        context["session_id"] = "test_normal_response"
        
        # 测试普通响应
        file_logger.info("开始请求普通响应...")
        start_time = time.time()
        reply = agent.reply(query, context)
        end_time = time.time()
        
        if reply.type == ReplyType.STREAM:
            # 从流中获取完整回复
            response = ""
            for chunk in reply.content:
                response += chunk
                
            file_logger.info(f"普通响应成功，耗时: {end_time - start_time:.2f}秒")
            # 如果响应太长，只显示前500个字符
            if len(response) > 500:
                file_logger.info(f"响应内容(前500字符): {response[:500]}...")
                file_logger.info(f"响应总长度: {len(response)}字符")
            else:
                file_logger.info(f"响应内容: {response}")
        else:
            file_logger.error("普通响应失败，未获取到内容")
            
    except Exception as e:
        file_logger.error(f"测试普通响应失败: {str(e)}")
        file_logger.error(traceback.format_exc())

def test_knowledge_results():
    """测试知识库召回结果"""
    try:
        bot_id = config.get("core.agent.coze.flash_bot_id", "")
        if not bot_id:
            file_logger.error("未配置 flash_bot_id，请检查配置")
            return
            
        file_logger.info("初始化 CozeAgent")
        agent = CozeAgent()
        agent.bot_id = bot_id
        
        query = "南开大学有哪些专业"
        file_logger.info(f"测试知识库召回，查询: {query}")
        
        # 测试知识库召回
        file_logger.info("开始获取知识库召回结果...")
        start_time = time.time()
        results = agent.get_knowledge_results(query)
        end_time = time.time()
        
        if results:
            file_logger.info(f"知识库召回成功，耗时: {end_time - start_time:.2f}秒")
            file_logger.info(f"召回结果数量: {len(results)}")
            # 最多显示前5个结果
            for i, result in enumerate(results[:5]):
                file_logger.info(f"结果 {i+1}: {result}")
            if len(results) > 5:
                file_logger.info(f"... 还有 {len(results) - 5} 个结果未显示")
        else:
            file_logger.info("未获取到知识库召回结果")
            
    except Exception as e:
        file_logger.error(f"测试知识库召回失败: {str(e)}")
        file_logger.error(traceback.format_exc())

async def test_async_stream():
    """使用异步方式测试流式响应 (示例代码，需要使用asyncio运行)"""
    try:
        # 这里仅作为如何在异步环境中使用的示例，不会实际运行
        from cozepy import AsyncCoze, TokenAuth, Message, ChatEventType
        
        api_key = config.get("core.agent.coze.api_key", "")
        bot_id = config.get("core.agent.coze.flash_bot_id", "")
        
        # 按照官方示例初始化异步客户端
        client = AsyncCoze(
            auth=TokenAuth(token=api_key),
            base_url=COZE_CN_BASE_URL  # 使用国内API
        )
        file_logger.debug(f"使用国内API: {COZE_CN_BASE_URL}")
        
        # 创建异步流
        stream = await client.chat.stream(
            bot_id=bot_id,
            user_id="default_user",
            additional_messages=[
                Message.build_user_question_text("介绍一下南开大学")
            ]
        )
        
        # 处理异步流
        chunk_count = 0
        async for event in stream:
            if event.event == ChatEventType.CONVERSATION_MESSAGE_DELTA:
                if event.message and event.message.content:
                    chunk_count += 1
                    if chunk_count <= 10 or chunk_count % 50 == 0:
                        file_logger.info(f"异步流收到内容({chunk_count}): {event.message.content}")
        
    except Exception as e:
        file_logger.error(f"异步测试失败: {str(e)}")
        file_logger.error(traceback.format_exc())

if __name__ == "__main__":
    try:
        file_logger.info("=" * 50)
        file_logger.info("测试 Coze SDK 开始")
        file_logger.info("=" * 50)
        
        file_logger.info("\n--- 测试流式响应 ---")
        test_stream_response()
        
        file_logger.info("\n--- 测试普通响应 ---")
        test_normal_response()
        
        file_logger.info("\n--- 测试知识库召回 ---")
        test_knowledge_results()
        
        file_logger.info("=" * 50)
        file_logger.info("测试 Coze SDK 完成")
        file_logger.info("=" * 50)
        
        # 确保所有日志都写入到文件
        file_handler.flush()
    finally:
        # 关闭输出重定向
        redirector.close() 