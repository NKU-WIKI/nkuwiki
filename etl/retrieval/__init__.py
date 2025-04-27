"""
检索模块，实现文档检索和重排功能
"""

from etl import (
    config, DATA_PATH, COLLECTION_NAME, VECTOR_SIZE, 
    QDRANT_URL, QDRANT_TIMEOUT
)

from core.utils.logger import register_logger

# 创建模块专用日志记录器
logger = register_logger("etl.retrieval")

# ---------- 检索配置 ----------
# 是否只使用检索进行回答
RE_ONLY = True

# 混合检索的融合方式
# 'reciprocal_rank_fusion' - 倒数排名融合
# 'merge' - 简单合并
RERANK_FUSION_TYPE = "reciprocal_rank_fusion"

# 答案精炼方式
# 'refine' - 逐步精炼
# 'compact' - 紧凑精炼
# 'tree_summarize' - 树状总结
ANS_REFINE_TYPE = "refine"

# 是否重建索引
REINDEX = False

# 检索类型
# 'dense_retriever' - 稠密检索
# 'hybrid_retriever' - 混合检索
# 'sparse_retriever' - 稀疏检索
RETRIEVAL_TYPE = "hybrid_retriever"

# 检索TopK配置（不同召回器）
F_TOPK_SPARSE = 6  # sparse召回数量
F_TOPK_DENSE = 15  # dense召回数量
F_TOPK_HYBRID = 15 # hybrid召回数量

# ---------- 重排配置 ----------
# 重排TopK
R_TOPK = 5
# 重排嵌入批大小
R_EMBED_BS = 32
# 重排模型名称（可选值：bge-reranker-large, bge-reranker-base, BAAI/bge-reranker-v2.5-large）
RERANKER_NAME = "bge-reranker-base"

# 本地LLM配置
LOCAL_LLM_NAME = "mistral-7b-instruct-v0.2.Q4_K_M"
LOCAL_LLM_PATH = "" # config.get("retrieval.local_llm_path", "")

# 从子模块导入
from etl.retrieval.retrievers import (
    QdrantRetriever, BM25Retriever, HybridRetriever
)
from etl.retrieval.rerankers import (
    SentenceTransformerRerank, LLMRerank
)

# 导出API
__all__ = [
    'logger',
    'COLLECTION_NAME', 'VECTOR_SIZE', 'QDRANT_URL', 'QDRANT_TIMEOUT',
    'RE_ONLY', 'RERANK_FUSION_TYPE', 'ANS_REFINE_TYPE', 'REINDEX', 'RETRIEVAL_TYPE',
    'F_TOPK_SPARSE', 'F_TOPK_DENSE', 'F_TOPK_HYBRID',
    'R_TOPK', 'R_EMBED_BS', 'RERANKER_NAME',
    'LOCAL_LLM_NAME', 'LOCAL_LLM_PATH',
    'QdrantRetriever', 'BM25Retriever', 'HybridRetriever',
    'SentenceTransformerRerank', 'LLMRerank',
] 