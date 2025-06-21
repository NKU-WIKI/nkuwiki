#!/usr/bin/env python3
"""
简单的Qdrant连接测试
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

def test_qdrant_simple():
    """简单测试Qdrant连接"""
    print("🔍 测试Qdrant连接...")
    
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
            collections = client.get_collections()
            print(f"✅ Qdrant连接成功")
            
            collection_names = [c.name for c in collections.collections]
            print(f"现有集合: {collection_names}")
            
            if collection_name in collection_names:
                print(f"✅ 集合 '{collection_name}' 存在")
                
                # 统计文档数量
                count = client.count(collection_name)
                print(f"集合中向量数量: {count.count}")
                
                if count.count == 0:
                    print("⚠️ 集合中没有向量数据！这就是问题所在！")
                    return False
                else:
                    print(f"✅ 集合中有 {count.count} 个向量")
                    return True
            else:
                print(f"❌ 集合 '{collection_name}' 不存在！这就是问题所在！")
                return False
                
        except Exception as conn_e:
            print(f"❌ Qdrant连接失败: {conn_e}")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

if __name__ == "__main__":
    result = test_qdrant_simple()
    if not result:
        print("\n💡 诊断结果: Qdrant向量数据库有问题，这就是为什么混合检索返回0结果的原因！")
        print("   - BM25检索器工作正常")
        print("   - 但是向量检索失败，导致混合检索无法工作")
        print("   - 需要检查Qdrant服务或重新构建向量索引") 