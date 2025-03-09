"""
加载模块，负责数据加载和索引构建
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from etl import *

import numpy as np
import torch
import pickle
from collections import defaultdict

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

# 嵌入配置
EMBEDDING_NAME = config.get('etl.embedding.name', 'BAAI/bge-large-zh-v1.5')
F_EMBED_TYPE_1 = config.get('etl.embedding.f_embed_type_1', 1)
F_EMBED_TYPE_2 = config.get('etl.embedding.f_embed_type_2', 2)
R_EMBED_TYPE = config.get('etl.embedding.r_embed_type', 1)
LLM_EMBED_TYPE = config.get('etl.embedding.llm_embed_type', 3)

# 分块配置
SPLIT_TYPE = config.get('etl.chunking.split_type', 0)
CHUNK_SIZE = config.get('etl.chunking.chunk_size', 512)
CHUNK_OVERLAP = config.get('etl.chunking.chunk_overlap', 200)

# 压缩配置
COMPRESS_METHOD = config.get('etl.compression.compress_method', "")
COMPRESS_RATE = config.get('etl.compression.compress_rate', 0.5)

# HYDE配置
HYDE_ENABLED = config.get('etl.hyde.enabled', False)
HYDE_MERGING = config.get('etl.hyde.merging', False)

# Qdrant配置
QDRANT_URL = config.get('etl.data.qdrant.url', 'http://localhost:6333')
COLLECTION_NAME = config.get('etl.data.qdrant.collection', 'main_index')
VECTOR_SIZE = config.get('etl.data.qdrant.vector_size', 1024)


# 创建加载模块专用logger
load_logger = logger.bind(module="load")
log_path = LOG_PATH + "/load.log"
log_format = "{time:YYYY-MM-DD HH:mm:ss} | {level} | {module} | {message}"
logger.configure(
    handlers=[
        {"sink": sys.stdout, "format": log_format},
        {"sink": log_path, "format": log_format, "rotation": "1 day", "retention": "3 months", "level": "INFO"},
    ]
)

# 常用模板
QA_TEMPLATE = """问题: {query}

回答应基于以下信息:
{context}

回答:"""

MERGE_TEMPLATE = """基于以下信息:
{context}

以及以下参考答案:
{answer}

生成一个综合性的更好的回答:"""

# 通用函数
def load_stopwords(path):
    """加载停用词列表"""
    with open(path, 'r', encoding='utf-8') as f:
        return set([line.strip() for line in f.readlines()])

# 定义导出的变量和函数
__all__ = [
    'os', 'sys', 'json', 'time', 'asyncio', 'np', 'torch', 'Path', 'Dict', 'List',
    'Optional', 'Any', 'Union', 'Tuple', 'load_logger', 'datetime', 'pickle', 're',
    'defaultdict', 'load_stopwords', 'QA_TEMPLATE', 'MERGE_TEMPLATE',
    
    # 路径配置
    'BASE_PATH', 'RAW_PATH', 'INDEX_PATH', 'CACHE_PATH', 'QDRANT_PATH', 'LOG_PATH',
    
    # 环境变量
    'HF_ENDPOINT', 'HF_HOME', 'SENTENCE_TRANSFORMERS_HOME', 'NLTK_DATA',
    
    # 检索配置
    'RE_ONLY', 'RERANK_FUSION_TYPE', 'ANS_REFINE_TYPE', 'REINDEX', 'RETRIEVAL_TYPE',
    'F_TOPK', 'F_TOPK_1', 'F_TOPK_2', 'F_TOPK_3', 'BM25_TYPE',
    
    # 重排配置
    'R_TOPK', 'R_TOPK_1', 'R_EMBED_BS', 'RERANKER_NAME', 'R_USE_EFFICIENT',
    
    # 嵌入配置
    'EMBEDDING_NAME', 'F_EMBED_TYPE_1', 'F_EMBED_TYPE_2', 'R_EMBED_TYPE', 'LLM_EMBED_TYPE',
    
    # 分块配置
    'SPLIT_TYPE', 'CHUNK_SIZE', 'CHUNK_OVERLAP',
    
    # 其他配置
    'COMPRESS_METHOD', 'COMPRESS_RATE', 'HYDE_ENABLED', 'HYDE_MERGING',
    'QDRANT_URL', 'COLLECTION_NAME', 'VECTOR_SIZE',
    'DB_HOST', 'DB_PORT', 'DB_USER', 'DB_PASSWORD', 'DB_NAME'
]