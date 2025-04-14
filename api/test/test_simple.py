#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
简单测试RAG接口
"""

import sys
import os
import json
import requests

# 确保项目根目录在sys.path中
current_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if current_dir not in sys.path:
    sys.path.append(current_dir)

from core.utils.logger import register_logger

logger = register_logger("test.api.agent.rag.simple")

# 服务器地址
BASE_URL = "http://localhost:8000/api"

def test_rag():
    """测试RAG接口的单个查询"""
    
    # 准备请求数据
    payload = {
        "query": "我想了解一下翔宇剧社",
        "openid": "test_user",
        "platform": "wechat,website,market,wxapp",
        "max_results": 3,
        "format": "markdown"
    }
    
    # 发送请求
    try:
        logger.info(f"发送请求: {payload}")
        response = requests.post(f"{BASE_URL}/agent/rag", json=payload)
        
        if response.status_code == 200:
            response_data = response.json()
            
            if response_data.get("code") == 200:
                logger.info("请求成功")
                logger.info(f"原始查询: {response_data['data']['original_query']}")
                logger.info(f"改写查询: {response_data['data']['rewritten_query']}")
                logger.info(f"检索结果数: {response_data['data']['retrieved_count']}")
                
                # 打印回答
                logger.info(f"回答内容:\n{'-'*50}\n{response_data['data']['response']}\n{'-'*50}")
                
                # 打印前三个来源
                if response_data['data'].get('sources'):
                    sources = response_data['data']['sources']
                    logger.info(f"检索到 {len(sources)} 个来源")
                    
                    for i, source in enumerate(sources[:3]):
                        logger.info(f"来源 {i+1}:")
                        logger.info(f"  标题: {source.get('title', '无标题')}")
                        logger.info(f"  平台: {source.get('platform', '未知平台')}")
                        content = source.get('content', '')
                        logger.info(f"  内容预览: {content[:100]}...")
                
                # 打印建议问题
                if response_data['data'].get('suggested_questions'):
                    suggestions = response_data['data']['suggested_questions']
                    logger.info(f"建议问题: {suggestions}")
            else:
                logger.error(f"请求失败: {response_data}")
        else:
            logger.error(f"HTTP错误: {response.status_code}, {response.text}")
    
    except Exception as e:
        logger.error(f"请求异常: {str(e)}")

if __name__ == "__main__":
    test_rag() 