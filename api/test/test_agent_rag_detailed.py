#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
详细测试api/agent/rag接口的各种情况
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

logger = register_logger("test.api.agent.rag.detailed")

# 服务器地址
BASE_URL = "http://localhost:8000/api"

async def test_missing_parameters():
    """测试缺少必要参数的情况"""
    logger.info("测试缺少必要参数的情况")
    
    async with aiohttp.ClientSession() as session:
        # 测试缺少query参数
        payload = {
            "openid": "test_user"
        }
        async with session.post(urljoin(BASE_URL, "/agent/rag"), json=payload) as response:
            response_data = await response.json()
            logger.info(f"缺少query参数 - 响应状态: {response.status}, 响应: {response_data}")
        
        # 测试缺少openid参数
        payload = {
            "query": "南开大学的校训是什么"
        }
        async with session.post(urljoin(BASE_URL, "/agent/rag"), json=payload) as response:
            response_data = await response.json()
            logger.info(f"缺少openid参数 - 响应状态: {response.status}, 响应: {response_data}")
        
        # 测试参数为空字符串
        payload = {
            "query": "",
            "openid": "test_user"
        }
        async with session.post(urljoin(BASE_URL, "/agent/rag"), json=payload) as response:
            response_data = await response.json()
            logger.info(f"query为空字符串 - 响应状态: {response.status}, 响应: {response_data}")

async def test_platform_parameter():
    """测试platform参数的各种情况"""
    logger.info("测试platform参数的各种情况")
    
    test_payload = {
        "query": "南开大学的校训是什么",
        "openid": "test_user"
    }
    
    async with aiohttp.ClientSession() as session:
        # 测试不同的platform组合
        platforms = [
            None,  # 默认所有平台
            "wechat",
            "website",
            "market",
            "wxapp",
            "wechat,website",
            "wechat,market,wxapp",
            "invalid_platform"  # 无效平台
        ]
        
        for platform in platforms:
            payload = test_payload.copy()
            if platform:
                payload["platform"] = platform
                
            logger.info(f"测试platform参数: {platform}")
            start_time = time.time()
            
            try:
                async with session.post(urljoin(BASE_URL, "/agent/rag"), json=payload) as response:
                    response_data = await response.json()
                    elapsed = time.time() - start_time
                    
                    if response.status == 200 and response_data.get("code") == 0:
                        logger.info(f"测试成功 - 响应状态: {response.status}, 耗时: {elapsed:.2f}秒")
                        logger.info(f"检索结果数: {response_data['data']['retrieved_count']}")
                    else:
                        logger.warning(f"测试有问题 - 响应状态: {response.status}, 错误信息: {response_data}")
            except Exception as e:
                logger.error(f"请求异常: {str(e)}")
            
            # 每次请求之间间隔2秒
            await asyncio.sleep(2)

async def test_max_results_parameter():
    """测试max_results参数的各种情况"""
    logger.info("测试max_results参数的各种情况")
    
    base_payload = {
        "query": "南开大学的历史",
        "openid": "test_user"
    }
    
    max_results_values = [1, 5, 10, 20, 50]
    
    async with aiohttp.ClientSession() as session:
        for max_results in max_results_values:
            payload = base_payload.copy()
            payload["max_results"] = max_results
            
            logger.info(f"测试max_results参数: {max_results}")
            start_time = time.time()
            
            try:
                async with session.post(urljoin(BASE_URL, "/agent/rag"), json=payload) as response:
                    response_data = await response.json()
                    elapsed = time.time() - start_time
                    
                    if response.status == 200 and response_data.get("code") == 0:
                        logger.info(f"测试成功 - 响应状态: {response.status}, 耗时: {elapsed:.2f}秒")
                        logger.info(f"检索结果数: {response_data['data']['retrieved_count']}")
                    else:
                        logger.warning(f"测试有问题 - 响应状态: {response.status}, 错误信息: {response_data}")
            except Exception as e:
                logger.error(f"请求异常: {str(e)}")
            
            # 每次请求之间间隔2秒
            await asyncio.sleep(2)

async def test_format_parameter():
    """测试format参数的各种情况"""
    logger.info("测试format参数的各种情况")
    
    base_payload = {
        "query": "南开大学的录取分数线",
        "openid": "test_user"
    }
    
    formats = ["text", "markdown", "html", "invalid_format"]
    
    async with aiohttp.ClientSession() as session:
        for format_type in formats:
            payload = base_payload.copy()
            payload["format"] = format_type
            
            logger.info(f"测试format参数: {format_type}")
            start_time = time.time()
            
            try:
                async with session.post(urljoin(BASE_URL, "/agent/rag"), json=payload) as response:
                    response_data = await response.json()
                    elapsed = time.time() - start_time
                    
                    if response.status == 200 and response_data.get("code") == 0:
                        logger.info(f"测试成功 - 响应状态: {response.status}, 耗时: {elapsed:.2f}秒")
                        # 检查返回的格式是否符合预期
                        if format_type == "markdown":
                            has_markdown = "**" in response_data['data']['response'] or "#" in response_data['data']['response']
                            logger.info(f"返回格式是否含有Markdown标记: {has_markdown}")
                    else:
                        logger.warning(f"测试有问题 - 响应状态: {response.status}, 错误信息: {response_data}")
            except Exception as e:
                logger.error(f"请求异常: {str(e)}")
            
            # 每次请求之间间隔2秒
            await asyncio.sleep(2)

async def test_stream_parameter():
    """测试流式响应的详细情况"""
    logger.info("测试流式响应的详细情况")
    
    payload = {
        "query": "南开大学的招生政策",
        "openid": "test_user",
        "stream": True
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            start_time = time.time()
            async with session.post(urljoin(BASE_URL, "/agent/rag"), json=payload) as response:
                if response.status == 200:
                    logger.info(f"流式测试 - 连接成功")
                    
                    # 详细记录SSE事件
                    event_count = 0
                    chunks_count = 0
                    content_chunks = []
                    query_received = False
                    sources_received = False
                    suggestions_received = False
                    end_received = False
                    
                    async for line in response.content:
                        line = line.decode('utf-8').strip()
                        if line.startswith('data: '):
                            event_count += 1
                            try:
                                event_data = json.loads(line[6:])
                                event_type = event_data.get('type')
                                
                                if event_type == 'query':
                                    query_received = True
                                    logger.info(f"流式响应 - 查询事件: 原始={event_data['original']}, 改写={event_data['rewritten']}")
                                elif event_type == 'content':
                                    chunks_count += 1
                                    content_chunks.append(event_data['chunk'])
                                    if chunks_count % 10 == 0:
                                        logger.debug(f"已接收 {chunks_count} 个内容块")
                                elif event_type == 'sources':
                                    sources_received = True
                                    logger.info(f"流式响应 - 来源事件: {len(event_data['sources'])} 个来源")
                                    # 打印前两个来源的详细信息
                                    for i, source in enumerate(event_data['sources'][:2]):
                                        logger.info(f"来源 {i+1}: 标题={source.get('title', '无标题')}, 平台={source.get('platform', '未知')}")
                                elif event_type == 'suggestions':
                                    suggestions_received = True
                                    logger.info(f"流式响应 - 建议问题事件: {len(event_data['suggestions'])} 个建议")
                                    logger.info(f"建议问题: {event_data['suggestions']}")
                                elif event_type == 'end':
                                    end_received = True
                                    elapsed = time.time() - start_time
                                    logger.info(f"流式响应完成，耗时: {elapsed:.2f}秒")
                                    break
                            except json.JSONDecodeError:
                                logger.error(f"解析SSE事件失败: {line}")
                    
                    # 统计分析
                    logger.info(f"流式响应统计:")
                    logger.info(f"- 总事件数: {event_count}")
                    logger.info(f"- 内容块数: {chunks_count}")
                    logger.info(f"- 总内容长度: {len(''.join(content_chunks))}")
                    logger.info(f"- 查询事件: {'✓' if query_received else '✗'}")
                    logger.info(f"- 来源事件: {'✓' if sources_received else '✗'}")
                    logger.info(f"- 建议问题事件: {'✓' if suggestions_received else '✗'}")
                    logger.info(f"- 结束事件: {'✓' if end_received else '✗'}")
                else:
                    logger.error(f"流式测试失败 - 响应状态: {response.status}")
        except Exception as e:
            logger.error(f"流式请求异常: {str(e)}")

async def test_error_handling():
    """测试错误处理情况"""
    logger.info("测试错误处理情况")
    
    # 长查询测试
    long_query = "南开大学" * 1000  # 非常长的查询
    
    payload = {
        "query": long_query,
        "openid": "test_user"
    }
    
    async with aiohttp.ClientSession() as session:
        logger.info("测试非常长的查询")
        try:
            async with session.post(urljoin(BASE_URL, "/agent/rag"), json=payload, timeout=30) as response:
                response_data = await response.json()
                logger.info(f"长查询测试 - 响应状态: {response.status}, 响应类型: {type(response_data)}")
                if isinstance(response_data, dict):
                    logger.info(f"响应码: {response_data.get('code')}")
        except Exception as e:
            logger.error(f"长查询测试异常: {str(e)}")
        
        await asyncio.sleep(2)
        
        # 特殊字符测试
        special_chars_query = "南开大学@#$%^&*()_+<>?|"
        payload = {
            "query": special_chars_query,
            "openid": "test_user"
        }
        
        logger.info("测试包含特殊字符的查询")
        try:
            async with session.post(urljoin(BASE_URL, "/agent/rag"), json=payload) as response:
                response_data = await response.json()
                logger.info(f"特殊字符测试 - 响应状态: {response.status}")
                if response.status == 200 and response_data.get("code") == 0:
                    logger.info(f"测试成功 - 查询被正确处理")
                else:
                    logger.warning(f"测试有问题 - 错误信息: {response_data}")
        except Exception as e:
            logger.error(f"特殊字符测试异常: {str(e)}")

async def main():
    """执行所有测试"""
    logger.info("======= 开始详细测试RAG接口 =======")
    
    # 测试缺少必要参数
    await test_missing_parameters()
    await asyncio.sleep(2)
    
    # 测试platform参数
    await test_platform_parameter()
    await asyncio.sleep(2)
    
    # 测试max_results参数
    await test_max_results_parameter()
    await asyncio.sleep(2)
    
    # 测试format参数
    await test_format_parameter()
    await asyncio.sleep(2)
    
    # 测试流式响应
    await test_stream_parameter()
    await asyncio.sleep(2)
    
    # 测试错误处理
    await test_error_handling()
    
    logger.info("======= 详细测试RAG接口完成 =======")

if __name__ == "__main__":
    asyncio.run(main()) 