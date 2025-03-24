#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
微信小程序RAG接口测试
"""
import requests
import json
import time

# API基础URL，根据实际环境配置
BASE_URL = "http://127.0.0.1:8000"

def test_wxapp_rag_query():
    """测试微信小程序RAG查询接口"""
    print("\n测试微信小程序RAG查询接口...")
    
    endpoint = f"{BASE_URL}/api/wxapp/rag/query"
    payload = {
        "query": "南开大学的校训是什么？",
        "openid": "test_user_openid"
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(endpoint, json=payload, headers=headers)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"响应数据:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            
            # 处理标准响应格式
            if "code" in result and "data" in result:
                data = result["data"]
                
                if "response" in data:
                    print("\n回答内容:")
                    print(data["response"])
                    
                    print("\n原始查询: " + data["original_query"])
                    print("改写查询: " + data["rewritten_query"])
                    
                    print("\n来源:")
                    for source in data["sources"]:
                        print(f"- {source['title']} ({source['type']})")
                        
                    print("\n推荐问题:")
                    for question in data["suggested_questions"]:
                        print(f"- {question}")
                
                return True
            else:
                print("响应格式不符合预期")
                return False
        else:
            print(f"请求失败: {response.text}")
            return False
        
    except Exception as e:
        print(f"测试失败: {str(e)}")
        return False

def test_rag_help():
    """测试RAG帮助信息接口"""
    print("\n测试RAG帮助信息接口...")
    
    endpoint = f"{BASE_URL}/api/wxapp/rag/help"
    
    try:
        response = requests.get(endpoint)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"响应数据:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            
            # 处理标准响应格式
            if "code" in result and "data" in result:
                data = result["data"]
                
                if "help_text" in data:
                    print("\n帮助文本:")
                    print(data["help_text"])
                    
                    print("\n推荐问题:")
                    for question in data["suggested_questions"]:
                        print(f"- {question}")
                
                return True
            else:
                print("响应格式不符合预期")
                return False
        else:
            print(f"请求失败: {response.text}")
            return False
        
    except Exception as e:
        print(f"测试失败: {str(e)}")
        return False

if __name__ == "__main__":
    print("开始测试微信小程序RAG接口...")
    
    # 测试微信小程序RAG查询接口
    query_success = test_wxapp_rag_query()
    
    # 测试RAG帮助信息接口
    help_success = test_rag_help()
    
    # 总结测试结果
    print("\n测试结果汇总:")
    print(f"- 微信小程序RAG查询接口: {'成功' if query_success else '失败'}")
    print(f"- RAG帮助信息接口: {'成功' if help_success else '失败'}") 