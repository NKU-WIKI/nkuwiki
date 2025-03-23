"""
嵌入模块，负责文档嵌入处理
"""
import sys
import torch
import numpy as np
from pathlib import Path
from typing import Union, Dict, List, Any
# 明确导入需要的内容
from etl import config, DATA_PATH, MODELS_PATH, etl_logger

from core.utils.logger import register_logger

# 创建模块专用日志记录器
embedding_logger = register_logger("etl.embedding")

# 嵌入配置
EMBEDDING_NAME = config.get("embedding.name", "bge-large-zh-v1.5")
VECTOR_SIZE = config.get("embedding.vector_size", 1024)
EMBED_DIM = config.get("embedding.dim", 1024)
# 嵌入类型
ASYMMETRIC_TYPE = "asymmetric"  # 非对称嵌入（查询和文档使用不同模型）
SYMMETRIC_TYPE = "symmetric"    # 对称嵌入（查询和文档使用相同模型）

# 分块配置
CHUNK_SIZE = config.get("embedding.chunk_size", 512)
CHUNK_OVERLAP = config.get("embedding.chunk_overlap", 50)
SPLIT_TYPE = config.get("embedding.split_type", "sentence")  # 按句子分割

def normalize_embedding(embedding):
    """标准化嵌入向量
    
    支持numpy数组和PyTorch张量
    
    Args:
        embedding: 嵌入向量，numpy数组或PyTorch张量
        
    Returns:
        标准化后的向量（L2范数为1）
    """
    if isinstance(embedding, np.ndarray):
        # 使用numpy标准化
        norm = np.linalg.norm(embedding)
        if norm > 0:
            return embedding / norm
        return embedding
    elif isinstance(embedding, torch.Tensor):
        # 使用PyTorch标准化
        return torch.nn.functional.normalize(embedding, p=2, dim=-1)
    return embedding

# 从子模块导入类 
from etl.embedding.hf_embeddings import HFEmbeddings
from etl.embedding.ingestion import build_pipeline as Ingestion
from etl.embedding.hierarchical import HierarchicalNodeParser

# 导出API
__all__ = [
    'embedding_logger', 
    'EMBEDDING_NAME', 'VECTOR_SIZE', 'EMBED_DIM',
    'ASYMMETRIC_TYPE', 'SYMMETRIC_TYPE',
    'CHUNK_SIZE', 'CHUNK_OVERLAP', 'SPLIT_TYPE',
    'normalize_embedding',
    'HFEmbeddings', 'Ingestion', 'HierarchicalNodeParser',
    'DATA_PATH', 'MODELS_PATH'
]
