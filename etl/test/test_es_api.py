#!/usr/bin/env python3
"""
测试新的ES API接口
"""

import requests
import json

def test_es_api():
    """测试ES API接口"""
    base_url = "http://localhost:8000/api/knowledge"
    
    test_cases = [
        {
            "query": "原神",
            "description": "普通查询"
        },
        {
            "query": "原神*",
            "description": "前缀通配符查询"
        },
        {
            "query": "*集美",
            "description": "后缀通配符查询"
        },
        {
            "query": "nkuwiki",
            "description": "英文查询"
        },
        {
            "query": "抽象",
            "description": "另一个普通查询"
        }
    ]
    
    for test_case in test_cases:
        print(f"\n{'='*60}")
        print(f"测试: {test_case['description']} - '{test_case['query']}'")
        print(f"{'='*60}")
        
        try:
            # 构建请求URL
            url = f"{base_url}/es-search"
            params = {
                "query": test_case["query"],
                "openid": "test_user_123",
                "page": 1,
                "page_size": 5,
                "max_content_length": 200
            }
            
            # 发送请求
            response = requests.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                print(f"✅ 请求成功")
                print(f"状态码: {response.status_code}")
                print(f"响应时间: {data.get('details', {}).get('response_time', 'N/A')}秒")
                
                # 分页信息
                pagination = data.get('pagination', {})
                print(f"分页信息: 总数={pagination.get('total', 0)}, 页码={pagination.get('page', 1)}, 总页数={pagination.get('total_pages', 0)}")
                
                # 结果
                results = data.get('data', [])
                print(f"返回结果数: {len(results)}")
                
                for i, result in enumerate(results[:3]):  # 只显示前3个结果
                    print(f"\n  结果 {i+1}:")
                    print(f"    标题: {result.get('title', '无标题')[:50]}")
                    print(f"    内容: {result.get('content', '无内容')[:80]}...")
                    print(f"    链接: {result.get('url', '无链接')[:50]}")
                    print(f"    分数: {result.get('score', 0):.2f}")
                    print(f"    PageRank: {result.get('pagerank_score', 0):.4f}")
                    print(f"    是否截断: {result.get('is_truncated', False)}")
                
            else:
                print(f"❌ 请求失败")
                print(f"状态码: {response.status_code}")
                print(f"响应: {response.text}")
                
        except Exception as e:
            print(f"❌ 请求异常: {e}")

if __name__ == "__main__":
    print("🚀 开始测试ES API接口...")
    test_es_api()
    print("\n✅ 测试完成！") 