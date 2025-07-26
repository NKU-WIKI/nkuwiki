"""
向量数据库相关API功能

使用新的索引构建架构：
- 索引构建 → etl.indexing
- 数据加载 → etl.load
- 检索功能 → etl.retrieval
"""

from typing import List, Dict, Any, Optional
import logging
from loguru import logger

# 导入etl检索模块
from etl.retrieval.retrievers import QdrantRetriever, BM25Retriever, HybridRetriever
from llama_index.core import QueryBundle
from llama_index.core.schema import NodeWithScore
from etl.embedding.hf_embeddings import HuggingFaceEmbedding as HFEmbedding
from llama_index.vector_stores.qdrant import QdrantVectorStore
from qdrant_client import AsyncQdrantClient

# 设置日志记录器
api_logger = logging.getLogger("api.database.vector")

# 缓存已创建的检索器实例
_retriever_cache = {}

def get_retriever(retriever_type: str = "hybrid"):
    """获取检索器实例
    
    Args:
        retriever_type: 检索器类型，可选值：qdrant, bm25, hybrid
        
    Returns:
        检索器实例
    """
    if retriever_type in _retriever_cache:
        return _retriever_cache[retriever_type]
    
    try:
        # 创建embedding模型
        embed_model = HFEmbedding()
        
        # 初始化QdrantVectorStore
        client = AsyncQdrantClient(url="http://localhost:6333")
        vector_store = QdrantVectorStore(
            aclient=client, 
            collection_name="main_index"
        )
        
        # 创建稠密检索器
        dense_retriever = QdrantRetriever(
            vector_store=vector_store,
            embed_model=embed_model,
            similarity_top_k=5
        )
        
        # 创建稀疏检索器
        from jieba import lcut
        sparse_retriever = BM25Retriever(
            nodes=[],
            tokenizer=lcut,
            similarity_top_k=5
        )
        
        if retriever_type == "qdrant":
            retriever = dense_retriever
        elif retriever_type == "bm25":
            retriever = sparse_retriever
        else:  # hybrid
            retriever = HybridRetriever(
                dense_retriever=dense_retriever,
                sparse_retriever=sparse_retriever,
                retrieval_type=1
            )
        
        _retriever_cache[retriever_type] = retriever
        return retriever
    except Exception as e:
        logger.error(f"创建检索器失败: {str(e)}")
        
        class DummyRetriever:
            async def _aretrieve(self, query_bundle):
                return []
            def retrieve(self, query_bundle, limit=10):
                return []
                
        return DummyRetriever()

async def search_documents(
    query: str,
    limit: int = 10,
    retriever_type: str = "hybrid",
    collection_name: Optional[str] = None
) -> List[Dict[str, Any]]:
    """搜索文档
    
    Args:
        query: 搜索查询
        limit: 返回结果数量限制
        retriever_type: 检索器类型
        collection_name: 集合名称，可选
        
    Returns:
        List[Dict[str, Any]]: 搜索结果列表
    """
    api_logger.debug(f"搜索文档: query={query}, limit={limit}, retriever_type={retriever_type}")
    
    retriever = get_retriever(retriever_type)
    query_bundle = QueryBundle(query)
    
    try:
        nodes = retriever.retrieve(query_bundle, limit=limit)
        results = []
        
        for node in nodes:
            result = {
                "id": node.node.node_id,
                "score": node.score,
                "content": node.node.text,
                "metadata": node.node.metadata,
                "platform": node.node.metadata.get("platform", "未知来源"),
                "title": node.node.metadata.get("title", "未知标题")
            }
            results.append(result)
        
        return results
    except Exception as e:
        logger.error(f"搜索文档失败: {str(e)}")
        return []

async def retrieve_from_qdrant(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """从Qdrant检索文档（稠密检索）"""
    return await search_documents(query, limit, "qdrant")

async def retrieve_hybrid(query: str, limit: int = 10, collection_name: Optional[str] = None) -> List[Dict[str, Any]]:
    """使用混合检索策略检索文档"""
    return await search_documents(query, limit, "hybrid", collection_name=collection_name) 