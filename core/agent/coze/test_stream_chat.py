#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Coze流式问答测试脚本
"""

import sys
import time
from pathlib import Path
import logging
import traceback

# 添加项目根目录到系统路径
sys.path.append(str(Path(__file__).resolve().parent.parent.parent.parent))

# 导入配置和日志模块
from core import config, logger

# 导入CozeAgent
from core.agent.coze.coze_agent import CozeAgent
from core.bridge.context import Context, ContextType
from core.bridge.reply import ReplyType

# 配置日志输出
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_stream_chat(query):
    """
    测试流式问答
    
    Args:
        query: 用户提问
    """
    # 打印分隔线
    print("\n" + "="*50)
    print(f"开始测试流式问答，问题: {query}")
    print("="*50 + "\n")
    
    try:
        # 从配置中获取bot_id
        bot_id = config.get("core.agent.coze.wx_bot_id")
        
        if not bot_id:
            print("错误: 未配置bot_id，请在config.json中设置core.agent.coze.wx_bot_id")
            return
            
        # 初始化Agent
        agent = CozeAgent()
        agent.bot_id = bot_id
        
        # 创建上下文
        context = Context(ContextType.TEXT)
        context["session_id"] = "test_stream_chat"
        
        # 开始计时
        start_time = time.time()
        
        # 获取流式回复
        print("AI回复: ", end="", flush=True)
        full_response = ""
        
        # 获取回复对象
        reply = agent.reply(query, context)
        
        if reply.type != ReplyType.STREAM:
            print("错误: 未获取到流式回复")
            return
            
        # 逐步输出回复内容
        for chunk in reply.content:
            print(chunk, end="", flush=True)
            full_response += chunk
            
        # 结束计时
        end_time = time.time()
        
        # 打印统计信息
        print("\n\n" + "-"*50)
        print(f"回复完成，用时: {end_time - start_time:.2f}秒")
        print(f"回复总长度: {len(full_response)}字符")
        print("-"*50 + "\n")
        
        # 尝试获取知识库结果
        print("获取知识库召回结果...")
        knowledge_results = agent.get_knowledge_results(query)
        
        if knowledge_results:
            print("\n知识库召回结果:")
            for i, result in enumerate(knowledge_results[:5], 1):  # 只显示前5条
                print(f"{i}. {result[:100]}..." if len(result) > 100 else f"{i}. {result}")
            
            if len(knowledge_results) > 5:
                print(f"... 共{len(knowledge_results)}条结果")
        else:
            print("未找到知识库召回结果")
            
    except Exception as e:
        print(f"\n发生错误: {e}")
        logger.exception("流式问答测试异常")

def test_normal_chat(query):
    """
    测试普通问答
    
    Args:
        query: 用户提问
    """
    # 打印分隔线
    print("\n" + "="*50)
    print(f"开始测试普通问答，问题: {query}")
    print("="*50 + "\n")
    
    try:
        # 从配置中获取bot_id
        bot_id = config.get("core.agent.coze.wx_bot_id")
        
        if not bot_id:
            print("错误: 未配置bot_id，请在config.json中设置core.agent.coze.wx_bot_id")
            return
            
        # 初始化Agent
        agent = CozeAgent()
        agent.bot_id = bot_id
        
        # 创建上下文
        context = Context(ContextType.TEXT)
        context["session_id"] = "test_normal_chat"
        
        # 开始计时
        start_time = time.time()
        
        # 获取回复
        print("正在获取回复...")
        reply = agent.reply(query, context)
        
        # 结束计时
        end_time = time.time()
        
        if reply.type == ReplyType.STREAM:
            # 从流中获取完整回复
            response = ""
            for chunk in reply.content:
                response += chunk
                
            print("\nAI回复:\n")
            print(response)
            
            # 打印统计信息
            print("\n" + "-"*50)
            print(f"回复完成，用时: {end_time - start_time:.2f}秒")
            print(f"回复总长度: {len(response)}字符")
            print("-"*50 + "\n")
        else:
            print("未收到有效回复")
            
    except Exception as e:
        print(f"\n发生错误: {e}")
        logger.exception("普通问答测试异常")

def test_http_vs_sdk(query):
    """
    测试HTTP和SDK模式的性能差异
    """
    try:
        bot_id = config.get("core.agent.coze.flash_bot_id", "")
        if not bot_id:
            logger.error("未配置 flash_bot_id，请检查配置")
            return
            
        # 创建上下文
        context = Context(ContextType.TEXT)
        context["session_id"] = "test_http_vs_sdk"
        
        # 使用CozeAgent测试
        logger.info("初始化 CozeAgent")
        agent = CozeAgent()
        agent.bot_id = bot_id
        
        # SDK模式测试
        logger.info(f"SDK模式测试，查询: {query}")
        sdk_start = time.time()
        sdk_reply = agent.reply(query, context)
        sdk_end = time.time()
        
        if sdk_reply.type != ReplyType.STREAM:
            logger.error("SDK模式未获取到流式回复")
            return
            
        # 获取完整响应
        sdk_response = ""
        sdk_chunks = 0
        for chunk in sdk_reply.content:
            sdk_chunks += 1
            sdk_response += chunk
            
        sdk_time = sdk_end - sdk_start
        logger.info(f"SDK模式完成: 耗时 {sdk_time:.2f}秒，接收 {sdk_chunks} 个片段")
        logger.info(f"SDK模式响应: {sdk_response[:200]}...")
        
        # HTTP模式测试
        logger.info("\nHTTP模式测试...")
        http_start = time.time()
        http_reply = agent.reply(query, context, use_http=True)
        http_end = time.time()
        
        if http_reply.type != ReplyType.STREAM:
            logger.error("HTTP模式未获取到流式回复")
            return
            
        # 获取完整响应
        http_response = ""
        http_chunks = 0
        for chunk in http_reply.content:
            http_chunks += 1
            http_response += chunk
            
        http_time = http_end - http_start
        logger.info(f"HTTP模式完成: 耗时 {http_time:.2f}秒，接收 {http_chunks} 个片段")
        logger.info(f"HTTP模式响应: {http_response[:200]}...")
        
        # 性能比较
        logger.info("\n性能比较:")
        logger.info(f"SDK模式: {sdk_time:.2f}秒, {sdk_chunks}个片段")
        logger.info(f"HTTP模式: {http_time:.2f}秒, {http_chunks}个片段")
        logger.info(f"时间差异: {abs(sdk_time - http_time):.2f}秒")
        logger.info(f"片段差异: {abs(sdk_chunks - http_chunks)}个")
        
    except Exception as e:
        logger.error(f"测试失败: {str(e)}")
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    # 测试问题
    test_questions = [
        "介绍南开大学的历史",
        "南开大学有哪些著名的校友？",
        "南开大学的计算机专业怎么样？",
    ]
    
    # 选择第一个问题进行测试
    test_stream_chat(test_questions[0])
    
    # 测试普通问答
    test_normal_chat(test_questions[1])
    
    # 测试HTTP vs SDK
    # test_http_vs_sdk(test_questions[2])
    
    print("\n所有测试已完成！") 