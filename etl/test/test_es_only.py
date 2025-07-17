#!/usr/bin/env python3
"""
仅测试Elasticsearch检索的脚本
不使用重排序，直接返回ES结果
"""

import sys
import os
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

def test_elasticsearch_only():
    """测试仅Elasticsearch检索"""
    print("🔍 测试仅Elasticsearch检索...")
    
    try:
        from etl.retrieval.retrievers import ElasticsearchRetriever
        from llama_index.core import QueryBundle
        from config import Config
        
        config = Config()
        
        # 从配置获取ES参数
        es_host = config.get("etl.data.elasticsearch.host", "localhost")
        es_port = config.get("etl.data.elasticsearch.port", 9200)
        index_name = config.get("etl.data.elasticsearch.index_name", "nkuwiki")
        
        print(f"Elasticsearch配置:")
        print(f"  主机: {es_host}")
        print(f"  端口: {es_port}")
        print(f"  索引: {index_name}")
        
        # 初始化Elasticsearch检索器
        print("\n正在初始化Elasticsearch检索器...")
        es_retriever = ElasticsearchRetriever(
            index_name=index_name,
            es_host=es_host,
            es_port=es_port,
            similarity_top_k=5
        )
        
        if es_retriever.es_client is None:
            print("❌ Elasticsearch客户端初始化失败")
            return
        
        print("✅ Elasticsearch检索器初始化成功")
        
        # 测试查询列表
        test_queries = [
            "南开大学",           # 普通查询
            "南开*",             # 通配符查询
            "*大学",             # 后缀通配符
            "计算机学院",         # 普通查询
            "计算机*",           # 前缀通配符
            "*学院",             # 后缀通配符
        ]
        
        for query in test_queries:
            print(f"\n{'='*50}")
            print(f"测试查询: '{query}'")
            print(f"{'='*50}")
            
            try:
                # 创建查询包
                query_bundle = QueryBundle(query_str=query)
                
                # 执行检索
                results = es_retriever._retrieve(query_bundle)
                
                print(f"✅ 检索成功，返回 {len(results)} 个结果")
                
                # 显示结果
                if results:
                    for i, node_with_score in enumerate(results):
                        title = node_with_score.node.metadata.get('title', '无标题')[:60]
                        content = node_with_score.node.text[:100] if node_with_score.node.text else '无内容'
                        score = node_with_score.score
                        url = node_with_score.node.metadata.get('original_url', '无URL')[:50]
                        
                        print(f"  结果 {i+1}:")
                        print(f"    分数: {score:.4f}")
                        print(f"    标题: {title}")
                        print(f"    内容: {content}...")
                        print(f"    链接: {url}")
                        print()
                else:
                    print("  ⚠️ 未找到相关结果")
                    
            except Exception as e:
                print(f"  ❌ 查询失败: {e}")
                import traceback
                traceback.print_exc()
        
        print(f"\n{'='*50}")
        print("Elasticsearch检索测试完成！")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

def test_es_connection():
    """简单测试ES连接"""
    print("🔍 测试Elasticsearch连接...")
    
    try:
        from elasticsearch import Elasticsearch
        from config import Config
        
        config = Config()
        es_host = config.get("etl.data.elasticsearch.host", "localhost")
        es_port = config.get("etl.data.elasticsearch.port", 9200)
        index_name = config.get("etl.data.elasticsearch.index_name", "nkuwiki")
        
        # 创建ES客户端
        es_client = Elasticsearch([{'host': es_host, 'port': es_port, 'scheme': 'http'}])
        
        # 测试连接
        if not es_client.ping():
            print(f"❌ 无法连接到Elasticsearch ({es_host}:{es_port})")
            return False
        
        print(f"✅ 成功连接到Elasticsearch")
        
        # 检查索引是否存在
        if not es_client.indices.exists(index=index_name):
            print(f"❌ 索引 '{index_name}' 不存在")
            return False
        
        print(f"✅ 索引 '{index_name}' 存在")
        
        # 获取文档数量
        count_result = es_client.count(index=index_name)
        doc_count = count_result['count']
        print(f"✅ 索引中有 {doc_count} 个文档")
        
        if doc_count == 0:
            print("⚠️ 索引中没有文档数据")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ 连接测试失败: {e}")
        return False

def main():
    """主函数"""
    print("🚀 开始Elasticsearch检索测试...")
    
    # 先测试连接
    if test_es_connection():
        print()
        # 再测试检索
        test_elasticsearch_only()
    else:
        print("❌ ES连接失败，跳过检索测试")
    
    print("\n✅ 测试完成！")

if __name__ == "__main__":
    main() 