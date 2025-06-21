"""
嵌入模块，负责文档嵌入处理

本模块提供核心的嵌入模型实现：
- HuggingFaceEmbedding: HuggingFace模型嵌入
- GTE模型嵌入
- 层次化节点解析
- 上下文压缩

其他功能已迁移：
- 索引构建 → etl.indexing
- 数据加载 → etl.load
- 节点处理 → etl.utils.node_utils
"""

# 核心嵌入模型
from etl.embedding.hf_embeddings import HuggingFaceEmbedding, HFEmbeddings

__all__ = [
    'HuggingFaceEmbedding', 
    'HFEmbeddings'
]
