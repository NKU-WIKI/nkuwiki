#!/usr/bin/env python3
from enum import Enum


class RetrievalStrategy(Enum):
    """检索策略枚举"""
    VECTOR_ONLY = "vector_only"           # 仅向量检索
    BM25_ONLY = "bm25_only"              # 仅BM25检索
    HYBRID = "hybrid"                     # 混合检索（向量+BM25）
    ELASTICSEARCH_ONLY = "es_only"        # 仅Elasticsearch检索
    AUTO = "auto"                         # 自动选择（基于查询特征）


class RerankStrategy(Enum):
    """重排序策略枚举"""
    NO_RERANK = "no_rerank"              # 不重排序
    BGE_RERANKER = "bge_reranker"        # BGE重排序器
    SENTENCE_TRANSFORMER = "st_reranker" # SentenceTransformer重排序器
    PAGERANK_ONLY = "pagerank_only"      # 仅PageRank排序
    PERSONALIZED = "personalized"        # 个性化排序 