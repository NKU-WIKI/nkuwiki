#!/usr/bin/env python3
"""
最简化的Elasticsearch检索测试
直接测试ES检索器，不依赖其他组件
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

def test_es_direct():
    """直接测试ES检索"""
    print("🔍 直接测试Elasticsearch检索...")
    
    try:
        from elasticsearch import Elasticsearch
        
        # ES配置
        es_host = "localhost"
        es_port = 9200
        index_name = "nkuwiki"
        
        print(f"连接ES: {es_host}:{es_port}")
        
        # 创建ES客户端
        es_client = Elasticsearch([{'host': es_host, 'port': es_port, 'scheme': 'http'}])
        
        # 测试连接
        if not es_client.ping():
            print("❌ 无法连接到Elasticsearch")
            return
        
        print("✅ ES连接成功")
        
        # 检查索引
        if not es_client.indices.exists(index=index_name):
            print(f"❌ 索引 '{index_name}' 不存在")
            return
        
        # 获取文档数量
        count_result = es_client.count(index=index_name)
        doc_count = count_result['count']
        print(f"✅ 索引中有 {doc_count} 个文档")
        
        if doc_count == 0:
            print("⚠️ 索引为空")
            return
        
        # 测试查询
        test_queries = [
            "原神",
            "集美",
            "抽象",
            "nkuwiki"
        ]
        
        for query in test_queries:
            print(f"\n测试查询: '{query}'")
            
            # 构建查询
            if '*' in query:
                # 通配符查询
                es_query = {
                    "query": {
                        "bool": {
                            "should": [
                                {"wildcard": {"title": {"value": query, "case_insensitive": True}}},
                                {"wildcard": {"content": {"value": query, "case_insensitive": True}}}
                            ],
                            "minimum_should_match": 1
                        }
                    }
                }
            else:
                # 普通匹配查询
                es_query = {
                    "query": {
                        "bool": {
                            "should": [
                                {"match": {"title": query}},
                                {"match": {"content": query}}
                            ],
                            "minimum_should_match": 1
                        }
                    }
                }
            
            try:
                # 执行搜索
                response = es_client.search(
                    index=index_name,
                    body=es_query,
                    size=5
                )
                
                hits = response['hits']['hits']
                print(f"  ✅ 返回 {len(hits)} 个结果")
                
                # 显示结果
                for i, hit in enumerate(hits):
                    source = hit['_source']
                    title = source.get('title', '无标题')[:50]
                    content = source.get('content', '无内容')[:80]
                    score = hit['_score']
                    
                    print(f"    结果{i+1}: 分数{score:.2f} - {title}")
                    print(f"            {content}...")
                
            except Exception as e:
                print(f"  ❌ 查询失败: {e}")
        
        print("\n✅ ES检索测试完成")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_es_direct() 