#!/usr/bin/env python3
"""
检索系统详细调试脚本
逐一排查检索器问题
"""

import sys
import os
import asyncio
from pathlib import Path
import jieba

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

async def test_bm25_retriever_debug():
    """详细测试BM25检索器"""
    print("🔍 详细测试BM25检索器...")
    
    try:
        from etl.retrieval.retrievers import BM25Retriever
        from llama_index.core import QueryBundle
        from config import Config
        
        config = Config()
        bm25_nodes_path = config.get("etl.retrieval.bm25.nodes_path", "/data/index/bm25_nodes.pkl")
        
        print(f"BM25文件路径: {bm25_nodes_path}")
        print(f"文件是否存在: {os.path.exists(bm25_nodes_path)}")
        
        if not os.path.exists(bm25_nodes_path):
            print("❌ BM25文件不存在！")
            return
        
        # 初始化BM25检索器
        print("正在初始化BM25检索器...")
        bm25_retriever = BM25Retriever.from_pickle_fast(
            nodes_path=bm25_nodes_path,
            tokenizer=jieba,
            similarity_top_k=5
        )
        
        print(f"✅ BM25检索器初始化成功")
        print(f"节点数量: {len(bm25_retriever._nodes)}")
        print(f"是否已初始化: {bm25_retriever._initialized}")
        
        # 测试分词
        test_query = "南开大学"
        print(f"\n测试分词: '{test_query}'")
        tokens = jieba.cut(test_query)
        token_list = list(tokens)
        print(f"分词结果: {token_list}")
        
        # 测试get_scores
        print(f"\n测试BM25评分...")
        scores = bm25_retriever.get_scores(test_query)
        print(f"分数数组长度: {len(scores)}")
        print(f"最大分数: {max(scores) if len(scores) > 0 else 'N/A'}")
        print(f"非零分数数量: {sum(1 for s in scores if s > 0)}")
        
        # 查看前几个最高分数
        if len(scores) > 0:
            import numpy as np
            top_indices = np.argsort(scores)[::-1][:5]
            print(f"前5个最高分数:")
            for i, idx in enumerate(top_indices):
                print(f"  {i+1}. 索引{idx}: 分数{scores[idx]:.4f}")
        
        # 测试filter方法
        print(f"\n测试filter方法...")
        filtered_nodes = bm25_retriever.filter(scores)
        print(f"过滤后节点数量: {len(filtered_nodes)}")
        
        if filtered_nodes:
            for i, node_with_score in enumerate(filtered_nodes[:3]):
                title = node_with_score.node.metadata.get('title', '无标题')[:50]
                content = node_with_score.node.text[:100] if node_with_score.node.text else '无内容'
                print(f"  结果{i+1}: 分数{node_with_score.score:.4f} - {title} - {content}...")
        
        # 完整测试_retrieve方法
        print(f"\n测试完整_retrieve方法...")
        query_bundle = QueryBundle(query_str=test_query)
        results = bm25_retriever._retrieve(query_bundle)
        print(f"_retrieve返回结果数量: {len(results)}")
        
    except Exception as e:
        print(f"❌ BM25测试失败: {e}")
        import traceback
        traceback.print_exc()

async def test_qdrant_connection():
    """测试Qdrant连接"""
    print("\n🔍 测试Qdrant连接...")
    
    try:
        from config import Config
        from qdrant_client import QdrantClient
        
        config = Config()
        qdrant_url = config.get("etl.data.qdrant.url", "http://localhost:6333")
        collection_name = config.get("etl.data.qdrant.collection_name", "main_index")
        
        print(f"Qdrant URL: {qdrant_url}")
        print(f"集合名称: {collection_name}")
        
        # 创建客户端
        client = QdrantClient(url=qdrant_url)
        
        # 测试连接
        print("测试连接...")
        try:
            # 尝试获取版本信息来测试连接
            health = client.get_collections()
            print(f"✅ Qdrant连接成功")
        except Exception as health_e:
            print(f"连接测试失败: {health_e}")
            return
        
        # 检查集合是否存在
        collections = client.get_collections()
        collection_names = [c.name for c in collections.collections]
        print(f"现有集合: {collection_names}")
        
        if collection_name in collection_names:
            print(f"✅ 集合 '{collection_name}' 存在")
            
            # 获取集合信息
            collection_info = client.get_collection(collection_name)
            print(f"集合信息: {collection_info}")
            
            # 统计文档数量
            count = client.count(collection_name)
            print(f"集合中向量数量: {count.count}")
            
            if count.count == 0:
                print("⚠️ 集合中没有向量数据！")
            else:
                # 测试简单搜索
                print("测试简单向量搜索...")
                try:
                    # 先获取一个向量作为查询示例
                    sample = client.scroll(collection_name, limit=1)[0]
                    if sample:
                        sample_vector = sample[0].vector
                        search_result = client.search(
                            collection_name=collection_name,
                            query_vector=sample_vector,
                            limit=3
                        )
                        print(f"向量搜索返回结果数量: {len(search_result)}")
                except Exception as search_e:
                    print(f"向量搜索测试失败: {search_e}")
        else:
            print(f"❌ 集合 '{collection_name}' 不存在！")
            
    except Exception as e:
        print(f"❌ Qdrant连接测试失败: {e}")

async def main():
    """主调试流程"""
    print("🚀 开始检索系统详细调试...")
    
    await test_bm25_retriever_debug()
    await test_qdrant_connection()
    
    print("\n✅ 调试完成！")

if __name__ == "__main__":
    asyncio.run(main()) 