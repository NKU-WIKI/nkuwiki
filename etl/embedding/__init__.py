"""
嵌入模块，负责文本向量化
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from etl import *

import torch
import numpy as np
from sentence_transformers import SentenceTransformer
from llama_index.core.base.embeddings.base import DEFAULT_EMBED_BATCH_SIZE, BaseEmbedding
from llama_index.core.bridge.pydantic import Field, ConfigDict
from llama_index.core.schema import BaseNode, Document, MetadataMode, TextNode, NodeWithScore
from llama_index.core import SimpleDirectoryReader
from llama_index.core.schema import TransformComponent
from etl.transform.splitter import SentenceSplitter

# 嵌入配置
EMBEDDING_NAME = config.get('etl.embedding.name', 'BAAI/bge-large-zh-v1.5')
VECTOR_SIZE = config.get('etl.embedding.vector_size', 1024)
EMBED_DIM = config.get('etl.embedding.embed_dim', 1024)
F_EMBED_TYPE_1 = config.get('etl.embedding.f_embed_type_1', 1)
F_EMBED_TYPE_2 = config.get('etl.embedding.f_embed_type_2', 2)
R_EMBED_TYPE = config.get('etl.embedding.r_embed_type', 1)
LLM_EMBED_TYPE = config.get('etl.embedding.llm_embed_type', 3)

# 分块配置
CHUNK_SIZE = config.get('chunk_size', 1024)
CHUNK_OVERLAP = config.get('chunk_overlap', 50)
SPLIT_TYPE = config.get('split_type', 0)  # 0-->Sentence 1-->Hierarchical

# 创建嵌入模块专用logger
embedding_logger = logger.bind(module="embedding")
log_path = LOG_PATH / "embedding.log"
log_format = "{time:YYYY-MM-DD HH:mm:ss} | {level} | {module} | {message}"
logger.configure(
    handlers=[
        {"sink": sys.stdout, "format": log_format},
        {"sink": log_path, "format": log_format, "rotation": "1 day", "retention": "3 months", "level": "INFO"},
    ]
)

# 常用嵌入函数
def normalize_embedding(embedding):
    """标准化嵌入向量"""
    if isinstance(embedding, np.ndarray):
        norm = np.linalg.norm(embedding)
        if norm > 0:
            return embedding / norm
        return embedding
    elif isinstance(embedding, torch.Tensor):
        return torch.nn.functional.normalize(embedding, p=2, dim=-1)
    else:
        raise TypeError("Embedding must be either numpy.ndarray or torch.Tensor")

# 定义导出
__all__ = [
    'os', 'sys', 'torch', 'np', 'asyncio', 'Path', 'Dict', 'List', 'Optional',
    'Any', 'Union', 'Tuple', 'embedding_logger', 'SentenceTransformer', 'normalize_embedding',
    'DEFAULT_EMBED_BATCH_SIZE', 'BaseEmbedding', 'Field', 'ConfigDict', 'BaseNode', 
    'Document', 'MetadataMode', 'TextNode', 'NodeWithScore', 'SimpleDirectoryReader', 
    'SentenceSplitter', 'TransformComponent',
    # 路径配置
    'BASE_PATH', 'CACHE_PATH', 'INDEX_PATH', 'RAW_PATH', 'LOG_PATH', 'NLTK_PATH',
    
    # 环境变量配置
    'HF_ENDPOINT', 'HF_HOME', 'SENTENCE_TRANSFORMERS_HOME',
    
    # 嵌入配置
    'EMBEDDING_NAME', 'VECTOR_SIZE', 'EMBED_DIM', 'F_EMBED_TYPE_1', 'F_EMBED_TYPE_2',
    'R_EMBED_TYPE', 'LLM_EMBED_TYPE',
    
    # 分块配置
    'CHUNK_SIZE', 'CHUNK_OVERLAP', 'SPLIT_TYPE'
]
