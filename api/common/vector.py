"""
向量数据库访问层
提供向量数据库的检索和存储功能，复用etl/retrieval中的函数
"""
from typing import List, Dict, Any, Optional, Union
import logging
from loguru import logger

# 导入etl检索模块中的函数
from etl.retrieval.retrievers import (
    QdrantRetriever, BM25Retriever, HybridRetriever
)
from etl.embedding.ingestion import embed_and_store_document
from llama_index.core import QueryBundle
from llama_index.core.schema import NodeWithScore
from etl.embedding.hf_embeddings import HuggingFaceEmbedding as HFEmbedding
from llama_index.vector_stores.qdrant import QdrantVectorStore

# 设置日志记录器
api_logger = logging.getLogger("api.database.vector")

# 缓存已创建的检索器实例
_retriever_cache = {}

def get_retriever(retriever_type: str = "hybrid"):
    """
    获取检索器实例
    
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
        
        # 初始化QdrantVectorStore（稠密检索器需要）
        from etl.embedding.ingestion import build_vector_store
        import asyncio
        
        loop = asyncio.get_event_loop()
        client, vector_store = loop.run_until_complete(
            build_vector_store(collection_name="wxapp_posts")
        )
        
        # 创建稠密检索器
        dense_retriever = QdrantRetriever(
            vector_store=vector_store,
            embed_model=embed_model,
            similarity_top_k=5
        )
        
        # 创建稀疏检索器（暂时使用空节点列表初始化，后续可改进）
        from jieba import lcut
        sparse_retriever = BM25Retriever(
            nodes=[],  # 空节点列表
            tokenizer=lcut,
            similarity_top_k=5
        )
        
        if retriever_type == "qdrant":
            retriever = dense_retriever
        elif retriever_type == "bm25":
            retriever = sparse_retriever
        else:  # 默认使用混合检索
            retriever = HybridRetriever(
                dense_retriever=dense_retriever,
                sparse_retriever=sparse_retriever,
                retrieval_type=1  # 1: 只使用稠密检索，因为稀疏检索暂时未正确初始化
            )
        
        _retriever_cache[retriever_type] = retriever
        return retriever
    except Exception as e:
        logger.error(f"创建检索器失败: {str(e)}")
        # 返回一个简单的检索器
        class DummyRetriever(HybridRetriever):
            def __init__(self):
                pass
                
            async def _aretrieve(self, query_bundle):
                return []
                
        return DummyRetriever()

async def index_document(
    file_path: str,
    file_name: str,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    将文档索引到向量数据库
    
    Args:
        file_path: 文档路径
        file_name: 文档名称
        metadata: 文档元数据
        
    Returns:
        Dict[str, Any]: 索引结果
    """
    api_logger.debug(f"索引文档: {file_path}")
    
    try:
        # 嵌入并存储文档
        doc_id = embed_and_store_document(
            file_path=file_path,
            doc_name=file_name,
            metadata=metadata or {}
        )
        
        return {
            "success": True,
            "document_id": doc_id,
            "message": "文档已成功索引"
        }
    except Exception as e:
        logger.error(f"索引文档失败: {str(e)}")
        return {
            "success": False,
            "message": f"索引文档失败: {str(e)}"
        }

async def search_documents(
    query: str,
    limit: int = 10,
    retriever_type: str = "hybrid",
    collection_name: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    搜索文档
    
    Args:
        query: 搜索查询
        limit: 返回结果数量限制
        retriever_type: 检索器类型
        collection_name: 集合名称，可选
        
    Returns:
        List[Dict[str, Any]]: 搜索结果列表
    """
    api_logger.debug(f"搜索文档: query={query}, limit={limit}, retriever_type={retriever_type}, collection_name={collection_name}")
    
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
                "source": node.node.metadata.get("source", "未知来源"),
                "title": node.node.metadata.get("title", "未知标题")
            }
            results.append(result)
        
        return results
    except Exception as e:
        logger.error(f"搜索文档失败: {str(e)}")
        return []

async def retrieve_from_qdrant(
    query: str,
    limit: int = 10
) -> List[Dict[str, Any]]:
    """
    从Qdrant检索文档（稠密检索）
    
    Args:
        query: 搜索查询
        limit: 返回结果数量限制
        
    Returns:
        List[Dict[str, Any]]: 搜索结果列表
    """
    return await search_documents(query, limit, "qdrant")

async def retrieve_hybrid(
    query: str,
    limit: int = 10,
    collection_name: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    使用混合检索策略检索文档
    
    Args:
        query: 搜索查询
        limit: 返回结果数量限制
        collection_name: 集合名称，可选
        
    Returns:
        List[Dict[str, Any]]: 搜索结果列表
    """
    return await search_documents(query, limit, "hybrid", collection_name=collection_name) 