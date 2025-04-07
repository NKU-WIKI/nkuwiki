#!/usr/bin/env python3
"""
知识库搜索API测试脚本
"""
import requests
import json
import time
from datetime import datetime

# 服务器地址
BASE_URL = "http://localhost:8000"

# 测试用openid
TEST_OPENID = "test_openid_" + datetime.now().strftime("%Y%m%d%H%M%S")

def print_response(response, title="响应"):
    """打印响应内容"""
    print(f"\n=== {title} ===")
    print(f"状态码: {response.status_code}")
    try:
        data = response.json()
        print(f"响应体: {json.dumps(data, ensure_ascii=False, indent=2)}")
    except:
        print(f"响应体: {response.text[:200]}...")
    print("="*50)

def test_health():
    """测试健康检查接口"""
    url = f"{BASE_URL}/api/health"
    response = requests.get(url)
    print_response(response, "健康检查接口")
    return response.status_code == 200

def test_knowledge_search():
    """测试知识库搜索接口"""
    url = f"{BASE_URL}/api/knowledge/search"
    params = {
        "query": "南开大学", 
        "openid": TEST_OPENID,
        "platform": "website",  # 可选：wechat/website/market/wxapp
        "page": 1,
        "page_size": 5,
        "sort_by": "relevance"  # 可选：relevance/time
    }
    
    print(f"\n测试知识库搜索接口 - 参数: {json.dumps(params, ensure_ascii=False)}")
    response = requests.get(url, params=params)
    print_response(response, "知识库搜索接口")
    
    # 测试不带平台参数
    params.pop("platform", None)
    print(f"\n测试知识库搜索接口(不指定平台) - 参数: {json.dumps(params, ensure_ascii=False)}")
    response = requests.get(url, params=params)
    print_response(response, "知识库搜索接口(不指定平台)")
    
    return response.status_code == 200

def test_wxapp_search():
    """测试小程序搜索接口"""
    url = f"{BASE_URL}/api/knowledge/search-wxapp"
    params = {
        "keyword": "南开大学",
        "search_type": "all",  # 可选：all/post/user
        "page": 1,
        "limit": 5
    }
    
    print(f"\n测试小程序搜索接口 - 参数: {json.dumps(params, ensure_ascii=False)}")
    response = requests.get(url, params=params)
    print_response(response, "小程序搜索接口")
    
    # 测试仅搜索帖子
    params["search_type"] = "post"
    print(f"\n测试小程序搜索接口(仅帖子) - 参数: {json.dumps(params, ensure_ascii=False)}")
    response = requests.get(url, params=params)
    print_response(response, "小程序搜索接口(仅帖子)")
    
    return response.status_code == 200

def main():
    """主函数"""
    print(f"开始测试知识库API - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 先测试健康检查
    if not test_health():
        print("健康检查失败，服务可能未正常运行")
        return False
    
    # 测试各个接口
    tests = [
        ("知识库搜索接口", test_knowledge_search),
        ("小程序搜索接口", test_wxapp_search)
    ]
    
    results = []
    for name, test_func in tests:
        print(f"\n开始测试: {name}")
        try:
            start_time = time.time()
            success = test_func()
            elapsed = time.time() - start_time
            results.append((name, success, elapsed))
        except Exception as e:
            print(f"测试出错: {e}")
            results.append((name, False, 0))
    
    # 打印测试结果摘要
    print("\n\n测试结果摘要:")
    print("-" * 50)
    print(f"{'接口名称':<20} {'结果':<10} {'耗时(秒)':<10}")
    print("-" * 50)
    for name, success, elapsed in results:
        result = "✅ 成功" if success else "❌ 失败"
        print(f"{name:<20} {result:<10} {elapsed:.3f}")
    print("-" * 50)

if __name__ == "__main__":
    main() 