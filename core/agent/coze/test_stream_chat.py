#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Coze流式问答测试脚本
"""

import sys
import time
from pathlib import Path
import logging

# 添加项目根目录到系统路径
sys.path.append(str(Path(__file__).resolve().parent.parent.parent.parent))

# 导入配置和日志模块
from core import config, logger

# 导入CozeAgentSDK
from core.agent.coze.coze_agent_sdk import CozeAgentSDK

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
            
        # 初始化SDK
        sdk = CozeAgentSDK(bot_id=bot_id, use_cn_api=True)
        
        # 开始计时
        start_time = time.time()
        
        # 获取流式回复
        print("AI回复: ", end="", flush=True)
        full_response = ""
        
        # 逐步输出回复内容
        for chunk in sdk.stream_reply(query):
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
        knowledge_results = sdk.get_knowledge_results(query)
        
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
            
        # 初始化SDK
        sdk = CozeAgentSDK(bot_id=bot_id, use_cn_api=True)
        
        # 开始计时
        start_time = time.time()
        
        # 获取回复
        print("正在获取回复...")
        response = sdk.reply(query)
        
        # 结束计时
        end_time = time.time()
        
        if response:
            print("\nAI回复:\n")
            print(response)
            
            # 打印统计信息
            print("\n" + "-"*50)
            print(f"回复完成，用时: {end_time - start_time:.2f}秒")
            print(f"回复总长度: {len(response)}字符")
            print("-"*50 + "\n")
        else:
            print("未收到回复")
            
    except Exception as e:
        print(f"\n发生错误: {e}")
        logger.exception("普通问答测试异常")

def test_http_vs_sdk(query):
    """
    对比HTTP和SDK模式的性能
    
    Args:
        query: 用户提问
    """
    # 打印分隔线
    print("\n" + "="*50)
    print(f"开始对比HTTP和SDK模式，问题: {query}")
    print("="*50 + "\n")
    
    try:
        # 从配置中获取bot_id
        bot_id = config.get("core.agent.coze.wx_bot_id")
        
        if not bot_id:
            print("错误: 未配置bot_id，请在config.json中设置core.agent.coze.wx_bot_id")
            return
            
        # 测试SDK模式
        print("\n[SDK模式]")
        sdk_instance = CozeAgentSDK(bot_id=bot_id, use_cn_api=True, use_sdk=True)
        
        # 开始计时
        sdk_start_time = time.time()
        
        # 获取回复
        print("正在获取回复...")
        sdk_response = sdk_instance.reply(query)
        
        # 结束计时
        sdk_end_time = time.time()
        sdk_time = sdk_end_time - sdk_start_time
        
        if sdk_response:
            print(f"回复完成，用时: {sdk_time:.2f}秒")
            print(f"回复总长度: {len(sdk_response)}字符")
        else:
            print("未收到回复")
        
        # 测试HTTP模式
        print("\n[HTTP模式]")
        http_instance = CozeAgentSDK(bot_id=bot_id, use_cn_api=True, use_sdk=False)
        
        # 开始计时
        http_start_time = time.time()
        
        # 获取回复
        print("正在获取回复...")
        http_response = http_instance.reply(query)
        
        # 结束计时
        http_end_time = time.time()
        http_time = http_end_time - http_start_time
        
        if http_response:
            print(f"回复完成，用时: {http_time:.2f}秒")
            print(f"回复总长度: {len(http_response)}字符")
        else:
            print("未收到回复")
            
        # 比较结果
        print("\n[对比结果]")
        if sdk_response and http_response:
            print(f"SDK模式用时: {sdk_time:.2f}秒")
            print(f"HTTP模式用时: {http_time:.2f}秒")
            print(f"速度差异: {'SDK更快' if sdk_time < http_time else 'HTTP更快'}, 差值: {abs(sdk_time - http_time):.2f}秒")
            
            # 内容一致性
            content_match = sdk_response == http_response
            print(f"内容一致性: {'内容完全一致' if content_match else '内容不一致'}")
            
            if not content_match:
                # 计算响应的相似程度
                common_len = len([i for i, j in zip(sdk_response, http_response) if i == j])
                similarity = common_len / max(len(sdk_response), len(http_response)) * 100
                print(f"内容相似度: {similarity:.2f}%")
            
    except Exception as e:
        print(f"\n发生错误: {e}")
        logger.exception("模式对比测试异常")

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