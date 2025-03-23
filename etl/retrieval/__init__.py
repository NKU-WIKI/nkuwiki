"""
检索模块，负责文档检索和重排序
"""

# 从根模块导入共享配置
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from etl import *
from core.utils.logger import get_module_logger

import numpy as np
import torch

# 检索相关配置
RE_ONLY = config.get('etl.retrieval.re_only', False)
RERANK_FUSION_TYPE = config.get('etl.retrieval.rerank_fusion_type', 1)
ANS_REFINE_TYPE = config.get('etl.retrieval.ans_refine_type', 0)
REINDEX = config.get('etl.retrieval.reindex', False)
RETRIEVAL_TYPE = config.get('etl.retrieval.retrieval_type', 3)
F_TOPK = config.get('etl.retrieval.f_topk', 128)
F_TOPK_1 = config.get('etl.retrieval.f_topk_1', 288)
F_TOPK_2 = config.get('etl.retrieval.f_topk_2', 192)
F_TOPK_3 = config.get('etl.retrieval.f_topk_3', 6)
BM25_TYPE = config.get('etl.retrieval.bm25_type', 0)

# 重排配置
R_TOPK = config.get('etl.reranker.r_topk', 6)
R_TOPK_1 = config.get('etl.reranker.r_topk_1', 6)
R_EMBED_BS = config.get('etl.reranker.r_embed_bs', 32)
RERANKER_NAME = config.get('etl.reranker.name', "cross-encoder/stsb-distilroberta-base")
R_USE_EFFICIENT = config.get('etl.reranker.r_use_efficient', 0)

HYDE_ENABLED = config.get('etl.hyde.enabled', False)
HYDE_MERGING = config.get('etl.hyde.merging', False)

COMPRESS_METHOD = config.get('etl.compression.compress_method', "")
COMPRESS_RATE = config.get('etl.compression.compress_rate', 0.5)

# 本地LLM配置
LOCAL_LLM_NAME = config.get('etl.local_llm_name', "")

# Qdrant配置
QDRANT_URL = config.get('etl.data.qdrant.url', 'http://localhost:6333')
QDRANT_TIMEOUT = config.get('etl.data.qdrant.timeout', 30.0)
COLLECTION_NAME = config.get('etl.data.qdrant.collection', 'main_index')
VECTOR_SIZE = config.get('etl.data.qdrant.vector_size', 1024)

# 创建retrieval模块专用logger
retrieval_logger = get_module_logger("etl.retrieval")

# 定义导出的变量和函数
__all__ = [
    'os', 'sys', 'np', 'torch', 'json', 'Path', 'Dict', 'List', 'Optional', 
    'Any', 'Union', 'Tuple', 'retrieval_logger', 'asyncio', 'defaultdict', 'datetime',
    
    # 路径配置
    'BASE_PATH', 'INDEX_PATH', 'CACHE_PATH', 'QDRANT_PATH', 'LOG_PATH',
    
    # 检索配置
    'RE_ONLY', 'RERANK_FUSION_TYPE', 'ANS_REFINE_TYPE', 'REINDEX', 'RETRIEVAL_TYPE',
    'F_TOPK', 'F_TOPK_1', 'F_TOPK_2', 'F_TOPK_3', 'BM25_TYPE',
    
    # 重排配置
    'R_TOPK', 'R_TOPK_1', 'R_EMBED_BS', 'RERANKER_NAME', 'R_USE_EFFICIENT',
    
    # LLM和Qdrant配置
    'LOCAL_LLM_NAME', 'QDRANT_URL', 'QDRANT_TIMEOUT', 'COLLECTION_NAME', 'VECTOR_SIZE',
    
    # 重排配置
    'HYDE_ENABLED', 'HYDE_MERGING',
    
    # 压缩配置
    'COMPRESS_METHOD', 'COMPRESS_RATE'
] 