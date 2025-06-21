#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
测试api/agent/rag接口
"""

import sys
import os
import json
import asyncio
import time
import aiohttp
import requests
from urllib.parse import urljoin

# 确保项目根目录在sys.path中
current_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if current_dir not in sys.path:
    sys.path.append(current_dir)

from core.utils.logger import register_logger

logger = register_logger("test.api.agent.rag")

# 服务器地址
BASE_URL = "http://localhost:8000/api"

# 测试OpenID
TEST_OPENID = f"test_user_{int(time.time())}"

# 测试查询
TEST_QUERIES = [
    "南开大学的校训是什么",
    "南开大学有哪些学院",
    "南开大学的图书馆位置",
    "南开大学的历史",
    "南开大学的校长是谁"
]

async def test_rag_async():
    """异步测试RAG接口"""
    logger.info("开始异步测试RAG接口")
    
    async with aiohttp.ClientSession() as session:
        for query in TEST_QUERIES:
            logger.info(f"测试查询: {query}")
            
            # 准备请求数据
            payload = {
                "query": query,
                "openid": TEST_OPENID,
                "platform": "wechat,website,market,wxapp",
                "max_results": 10,
                "format": "markdown"
            }
            
            # 测试普通RAG请求
            start_time = time.time()
            async with session.post(urljoin(BASE_URL, "/agent/rag"), json=payload) as response:
                response_data = await response.json()
                elapsed = time.time() - start_time
                
                logger.info(f"响应耗时: {elapsed:.2f}秒")
                if response.status == 200 and response_data.get("code") == 0:
                    logger.info(f"测试成功 - 响应状态: {response.status}")
                    logger.info(f"原始查询: {response_data['data']['original_query']}")
                    logger.info(f"改写查询: {response_data['data']['rewritten_query']}")
                    logger.info(f"检索结果数: {response_data['data']['retrieved_count']}")
                    logger.info(f"回答长度: {len(response_data['data']['response'])}")
                    if response_data['data'].get("suggested_questions"):
                        logger.info(f"建议问题: {response_data['data']['suggested_questions']}")
                else:
                    logger.error(f"测试失败 - 响应状态: {response.status}, 错误信息: {response_data}")
            
            # 测试流式RAG请求
            logger.info(f"测试流式请求: {query}")
            payload["stream"] = True
            
            start_time = time.time()
            try:
                async with session.post(urljoin(BASE_URL, "/agent/rag"), json=payload) as response:
                    if response.status == 200:
                        logger.info(f"流式测试 - 连接成功")
                        
                        # 读取SSE事件流
                        async for line in response.content:
                            line = line.decode('utf-8').strip()
                            if line.startswith('data: '):
                                try:
                                    event_data = json.loads(line[6:])
                                    event_type = event_data.get('type')
                                    
                                    if event_type == 'query':
                                        logger.info(f"流式响应 - 查询: 原始={event_data['original']}, 改写={event_data['rewritten']}")
                                    elif event_type == 'content':
                                        logger.debug(f"流式响应 - 内容块: {event_data['chunk']}")
                                    elif event_type == 'sources':
                                        logger.info(f"流式响应 - 来源数: {len(event_data['sources'])}")
                                    elif event_type == 'suggestions':
                                        logger.info(f"流式响应 - 建议问题: {event_data['suggestions']}")
                                    elif event_type == 'end':
                                        elapsed = time.time() - start_time
                                        logger.info(f"流式响应完成，耗时: {elapsed:.2f}秒")
                                        break
                                    elif event_type == 'error':
                                        logger.error(f"流式响应错误: {event_data['message']}")
                                except json.JSONDecodeError:
                                    logger.error(f"解析SSE事件失败: {line}")
                    else:
                        logger.error(f"流式测试失败 - 响应状态: {response.status}")
            except Exception as e:
                logger.error(f"流式请求异常: {str(e)}")
            
            # 每次请求之间间隔2秒
            await asyncio.sleep(2)
    
    logger.info("异步测试完成")

def test_rag_sync():
    """同步测试RAG接口"""
    logger.info("开始同步测试RAG接口")
    
    for query in TEST_QUERIES:
        logger.info(f"测试查询: {query}")
        
        # 准备请求数据
        payload = {
            "query": query,
            "openid": TEST_OPENID,
            "platform": "wechat,website,market,wxapp",
            "max_results": 10,
            "format": "markdown"
        }
        
        # 发送请求
        try:
            start_time = time.time()
            response = requests.post(urljoin(BASE_URL, "/agent/rag"), json=payload)
            elapsed = time.time() - start_time
            
            logger.info(f"响应耗时: {elapsed:.2f}秒")
            
            if response.status_code == 200:
                response_data = response.json()
                if response_data.get("code") == 0:
                    logger.info(f"测试成功 - 响应状态: {response.status_code}")
                    logger.info(f"原始查询: {response_data['data']['original_query']}")
                    logger.info(f"改写查询: {response_data['data']['rewritten_query']}")
                    logger.info(f"检索结果数: {response_data['data']['retrieved_count']}")
                    logger.info(f"回答长度: {len(response_data['data']['response'])}")
                    if response_data['data'].get("suggested_questions"):
                        logger.info(f"建议问题: {response_data['data']['suggested_questions']}")
                else:
                    logger.error(f"测试失败 - 错误信息: {response_data}")
            else:
                logger.error(f"测试失败 - 响应状态: {response.status_code}, 错误: {response.text}")
        except Exception as e:
            logger.error(f"请求异常: {str(e)}")
        
        # 每次请求之间间隔2秒
        time.sleep(2)
    
    logger.info("同步测试完成")

if __name__ == "__main__":
    logger.info("RAG接口测试脚本启动")
    
    # 执行同步测试
    test_rag_sync()
    
    # 执行异步测试
    asyncio.run(test_rag_async()) 