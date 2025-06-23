#!/usr/bin/env python3
"""
高级RAG（检索增强生成）管道

本模块提供了一个功能完整的RAG系统，支持多种检索策略和重排序方案的灵活组合。

## 核心特性

### 🔍 多检索器支持
- **向量检索 (Vector)**: 基于BGE语义嵌入的相似度搜索
- **BM25检索 (BM25)**: 基于TF-IDF的关键词匹配
- **混合检索 (Hybrid)**: 融合向量和BM25的RRF算法
- **Elasticsearch**: 支持通配符和复杂查询的全文检索

### 🎯 智能检索策略
- **AUTO**: 根据查询特征自动选择最优策略
- **VECTOR_ONLY**: 纯语义检索，适合概念性查询
- **BM25_ONLY**: 纯关键词检索，适合精确匹配
- **HYBRID**: 混合检索，平衡语义和关键词
- **ELASTICSEARCH_ONLY**: 全文检索，支持通配符

### ⚡ 多重排序策略
- **BGE_RERANKER**: 使用BGE重排序模型的深度语义重排
- **SENTENCE_TRANSFORMER**: 基于交叉编码器的重排序
- **PAGERANK_ONLY**: 基于页面权威性的排序
- **PERSONALIZED**: 结合用户历史的个性化排序
- **NO_RERANK**: 使用原始检索分数

### 🧠 智能路由机制
系统会根据查询特征自动选择最优策略：
- 通配符查询 (`*`, `?`) → Elasticsearch
- 长查询或问句 → 混合检索
- 短查询或专有名词 → BM25检索
- 概念性查询 → 向量检索

## 使用示例

### 基础用法
```python
from etl.rag_pipeline import RagPipeline, RetrievalStrategy, RerankStrategy

# 初始化管道
rag = RagPipeline()

# 自动策略（推荐）
result = rag.run("南开大学的校训是什么？")

# 指定策略组合
result = rag.run(
    "人工智能*算法",
    retrieval_strategy=RetrievalStrategy.ELASTICSEARCH_ONLY,
    rerank_strategy=RerankStrategy.BGE_RERANKER
)
```

### 高级用法
```python
# 个性化检索
result = rag.run(
    "计算机专业课程",
    user_id="user123",
    retrieval_strategy=RetrievalStrategy.HYBRID,
    rerank_strategy=RerankStrategy.PERSONALIZED
)

# 仅检索模式（跳过LLM生成）
result = rag.retrieve_only(
    "机器学习",
    retrieval_strategy=RetrievalStrategy.VECTOR_ONLY,
    rerank_strategy=RerankStrategy.PAGERANK_ONLY
)

# 带过滤器的检索
from qdrant_client import models
filters = models.Filter(
    must=[models.FieldCondition(
        key="metadata.source", 
        match=models.MatchValue(value="academic")
    )]
)
result = rag.run("深度学习", filters=filters)
```

### 策略性能对比
| 检索策略 | 适用场景 | 优势 | 劣势 |
|---------|---------|------|------|
| AUTO | 通用场景 | 智能选择 | 可能不是最优 |
| VECTOR_ONLY | 概念查询 | 语义理解强 | 关键词匹配弱 |
| BM25_ONLY | 精确匹配 | 关键词匹配强 | 语义理解弱 |
| HYBRID | 平衡需求 | 综合效果好 | 计算开销大 |
| ELASTICSEARCH_ONLY | 复杂查询 | 功能强大 | 需要ES服务 |

| 重排序策略 | 适用场景 | 特点 |
|-----------|---------|------|
| BGE_RERANKER | 质量优先 | 效果最佳，速度较慢 |
| SENTENCE_TRANSFORMER | 平衡选择 | 效果良好，速度适中 |
| PAGERANK_ONLY | 权威性优先 | 基于页面权威性 |
| PERSONALIZED | 个性化需求 | 结合用户历史 |
| NO_RERANK | 速度优先 | 最快，无重排开销 |

## 配置参数

在 `config.json` 中可配置以下参数：

```json
{
  "etl": {
    "retrieval": {
      "pagerank_weight": 0.1,
      "enable_es_rerank": true,
      "bm25": {
        "nodes_path": "/data/index/bm25_nodes.pkl",
        "stopwords_path": "/data/nltk/hit_stopwords.txt"
      }
    },
    "data": {
      "qdrant": {
        "url": "http://localhost:6333",
        "collection": "main_index"
      },
      "elasticsearch": {
        "host": "localhost", 
        "port": 9200,
        "index": "nkuwiki"
      }
    }
  }
}
```

## 性能优化建议

1. **缓存策略**: 启用嵌入模型缓存
2. **批处理**: 对大量查询使用批处理
3. **服务预热**: 提前加载模型和索引
4. **资源监控**: 监控内存和计算资源使用
5. **策略选择**: 根据业务需求选择合适的策略组合

## 注意事项

- 确保所有依赖服务（Qdrant, Elasticsearch, MySQL）正常运行
- 模型文件需要预先下载到指定目录
- 重排序会增加响应时间但提升结果质量
- 个性化功能需要用户搜索历史数据

作者: nkuwiki-IR-lab
版本: 2.0.0
"""

import os
import sys
import asyncio
import time
from pathlib import Path
import logging
from typing import List, Optional, Dict, Any
import jieba
from enum import Enum
import nest_asyncio

# LlamaIndex核心组件
from llama_index.core import Settings, QueryBundle
from llama_index.core.callbacks import CallbackManager, LlamaDebugHandler, TokenCountingHandler
from llama_index.core.schema import NodeWithScore
from llama_index.vector_stores.qdrant import QdrantVectorStore
from qdrant_client import QdrantClient, models

# 项目依赖
sys.path.append(str(Path(__file__).resolve().parent.parent))
from etl.embedding.hf_embeddings import HuggingFaceEmbedding
from etl.retrieval.rerankers import SentenceTransformerRerank, LLMRerank
from etl.retrieval.retrievers import QdrantRetriever, BM25Retriever, HybridRetriever, ElasticsearchRetriever
from config import Config
from core.utils import register_logger
from core.agent.agent_factory import get_agent

# 配置日志和全局设置
logger = register_logger(__name__)
config = Config()

# 初始化LlamaIndex全局设置
Settings.callback_manager = CallbackManager([
    LlamaDebugHandler(),
    TokenCountingHandler()
])
Settings.num_output = 512
Settings.chunk_size = config.get("etl.embedding.chunking.chunk_size", 512)
Settings.chunk_overlap = config.get("etl.embedding.chunking.chunk_overlap", 200)


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


# 移除未使用的工具函数，这些功能已集成到相应的类方法中


nest_asyncio.apply()

class RagPipeline:
    """
    高级RAG（检索增强生成）管道，支持多种检索策略组合。
    
    检索策略：
    - VECTOR_ONLY: 纯语义向量检索，适合概念性查询
    - BM25_ONLY: 纯关键词检索，适合精确匹配
    - HYBRID: 混合检索，融合语义和关键词，适合大多数场景
    - ELASTICSEARCH_ONLY: 全文检索，适合复杂查询和通配符
    - AUTO: 自动选择最优策略
    
    重排序策略：
    - NO_RERANK: 使用原始检索分数
    - BGE_RERANKER: 使用BGE重排序模型
    - SENTENCE_TRANSFORMER: 使用SentenceTransformer重排序
    - PAGERANK_ONLY: 仅基于页面权威性排序
    - PERSONALIZED: 结合用户历史的个性化排序
    """
    
    def __init__(self,
                 llm_model_name: str = "deepseek-chat",
                 embedding_model_name: str = "BAAI/bge-large-zh-v1.5",
                 rerank_model_name: str = "BAAI/bge-reranker-base",
                 collection_name: str = None,
                 es_index_name: str = None,
                 pagerank_weight: float = None,
                 enable_es_rerank: bool = None,
                 default_retrieval_strategy: RetrievalStrategy = RetrievalStrategy.AUTO,
                 default_rerank_strategy: RerankStrategy = RerankStrategy.BGE_RERANKER
                 ):
        """
        初始化RAG管道。
        
        Args:
            llm_model_name: 语言模型名称
            embedding_model_name: 嵌入模型名称
            rerank_model_name: 重排序模型名称
            collection_name: Qdrant集合名称
            es_index_name: Elasticsearch索引名称
            pagerank_weight: PageRank权重
            enable_es_rerank: 是否对ES结果重排序
            default_retrieval_strategy: 默认检索策略
            default_rerank_strategy: 默认重排序策略
        """
        logger.info("Initializing RAG pipeline...")
        self.collection_name = collection_name or config.get('etl.data.qdrant.collection', 'website_nku')
        self.es_index_name = es_index_name or config.get('etl.data.elasticsearch.index', 'nkuwiki')
        
        # 策略配置
        self.default_retrieval_strategy = default_retrieval_strategy
        self.default_rerank_strategy = default_rerank_strategy
        
        # PageRank和重排序配置
        self.pagerank_weight = pagerank_weight if pagerank_weight is not None else config.get('etl.retrieval.pagerank_weight', 0.1)
        self.enable_es_rerank = enable_es_rerank if enable_es_rerank is not None else config.get('etl.retrieval.enable_es_rerank', True)
        
        logger.info(f"Default retrieval strategy: {self.default_retrieval_strategy.value}")
        logger.info(f"Default rerank strategy: {self.default_rerank_strategy.value}")
        logger.info(f"PageRank weight: {self.pagerank_weight}, ES rerank enabled: {self.enable_es_rerank}")

        # 1. 初始化语言模型 (LLM)
        self.llm = self._init_llm(llm_model_name)
        
        # 2. 初始化嵌入模型 (Embedding)
        self.embed_model = self._init_embedding_model(embedding_model_name)
        Settings.embed_model = self.embed_model

        # 3. 初始化重排模型 (Reranker)
        self.reranker = self._init_reranker(rerank_model_name)

        # 4. 初始化检索器 (Retrievers)
        self.vector_retriever = self._init_vector_retriever()
        self.bm25_retriever = self._init_bm25_retriever()
        self.hybrid_retriever = self._init_hybrid_retriever()
        self.es_retriever = self._init_es_retriever()
        
        # 5. 记录可用的检索器
        self.available_retrievers = self._check_available_retrievers()
        logger.info(f"Available retrievers: {list(self.available_retrievers.keys())}")
        
        logger.info("RAG pipeline initialized successfully.")

    def _init_llm(self, model_name: str):
        logger.info(f"Initializing LLM: {model_name}")
        # 使用coze agent替代llama-index的OpenAI LLM，指定使用answerGenerate_bot_id
        return get_agent("coze", tag="answerGenerate")

    def _init_embedding_model(self, model_name: str):
        logger.info(f"Initializing embedding model: {model_name}")
        # 根据配置文件逻辑：base_path + models.path
        import os
        base_path = config.get('etl.data.base_path', '/data')
        models_subpath = config.get('etl.data.models.path', '/models')
        models_path = base_path + models_subpath
        
        # 全局设置HuggingFace缓存目录
        os.environ['HF_HOME'] = models_path
        os.environ['TRANSFORMERS_CACHE'] = models_path
        os.environ['HF_HUB_CACHE'] = models_path
        os.environ['SENTENCE_TRANSFORMERS_HOME'] = models_path
        # 确保目录存在
        os.makedirs(models_path, exist_ok=True)
        logger.info(f"Models cache directory set to: {models_path}")
        
        # 使用项目的 HuggingFaceEmbedding 类，它已经继承自 BaseEmbedding
        from etl.embedding.hf_embeddings import HuggingFaceEmbedding
        import torch
        
        # 强制使用CPU以避免内存不足问题
        device = 'cpu'
        logger.info("强制使用CPU设备")
        
        logger.info(f"Loading model {model_name} from {models_path} on {device}")
        try:
            return HuggingFaceEmbedding(
                model_name=model_name,
                device=device
            )
        except Exception as e:
            logger.error(f"Failed to initialize embedding model: {e}")
            raise

    def _init_reranker(self, model_name: str):
        logger.info(f"Initializing reranker: {model_name}")
        # 根据模型名称选择合适的重排序器
        if "bge-reranker" in model_name.lower():
            return LLMRerank(model=model_name, top_n=10, pagerank_weight=self.pagerank_weight)
        else:
            return SentenceTransformerRerank(model=model_name, top_n=10, pagerank_weight=self.pagerank_weight)

    def _load_stopwords(self):
        """加载停用词文件"""
        stopwords_path = config.get('etl.retrieval.bm25.stopwords_path')
        try:
            with open(stopwords_path, 'r', encoding='utf-8') as f:
                return [line.strip() for line in f.readlines()]
        except FileNotFoundError:
            logger.warning(f"Stopwords file not found at {stopwords_path}. Returning empty list.")
            return []

    def _init_vector_retriever(self):
        logger.info("Initializing QdrantRetriever.")
        qdrant_url = config.get('etl.data.qdrant.url', 'http://localhost:6333')
        qdrant_client = QdrantClient(url=qdrant_url)
        vector_store = QdrantVectorStore(client=qdrant_client, collection_name=self.collection_name)
        return QdrantRetriever(vector_store=vector_store, embed_model=self.embed_model, similarity_top_k=10)

    def _init_bm25_retriever(self):
        logger.info("Initializing BM25Retriever using fast mode.")
        nodes_path = config.get('etl.retrieval.bm25.nodes_path')
        
        # 检查预构建的节点文件是否存在
        if not nodes_path or not os.path.exists(nodes_path):
            logger.warning(f"BM25节点文件不存在: {nodes_path}. BM25检索器将被禁用.")
            return None
        
        try:
            # 使用快速加载方法
            stopwords = self._load_stopwords()
            return BM25Retriever.from_pickle_fast(
                nodes_path=nodes_path,
                tokenizer=jieba,
                stopwords=stopwords,
                similarity_top_k=10
            )
        except Exception as e:
            logger.error(f"BM25检索器快速加载失败: {e}")
            return None

    def _init_hybrid_retriever(self):
        """初始化混合检索器"""
        if self.vector_retriever and self.bm25_retriever:
            logger.info("Initializing HybridRetriever with vector and BM25 retrievers.")
            return HybridRetriever(
                dense_retriever=self.vector_retriever,
                sparse_retriever=self.bm25_retriever,
                pagerank_weight=self.pagerank_weight
            )
        logger.warning("Cannot initialize HybridRetriever: missing vector or BM25 retriever.")
        return None

    def _init_es_retriever(self):
        """初始化Elasticsearch检索器"""
        logger.info("Initializing ElasticsearchRetriever.")
        es_host = config.get('etl.data.elasticsearch.host', 'localhost')
        es_port = config.get('etl.data.elasticsearch.port', 9200)
        try:
            return ElasticsearchRetriever(
                index_name=self.es_index_name, 
                es_host=es_host, 
                es_port=es_port, 
                similarity_top_k=10
            )
        except Exception as e:
            logger.warning(f"Failed to initialize ElasticsearchRetriever: {e}. Wildcard search will be disabled.")
            return None

    def _check_available_retrievers(self) -> Dict[str, bool]:
        """检查可用的检索器"""
        return {
            "vector": self.vector_retriever is not None,
            "bm25": self.bm25_retriever is not None,
            "hybrid": self.hybrid_retriever is not None,
            "elasticsearch": self.es_retriever is not None
        }

    def _determine_retrieval_strategy(self, query: str) -> RetrievalStrategy:
        """根据查询内容自动确定最优检索策略"""
        # 通配符查询 -> Elasticsearch
        if '*' in query or '?' in query:
            if self.available_retrievers.get("elasticsearch"):
                return RetrievalStrategy.ELASTICSEARCH_ONLY
        
        # 长查询（>20字符）或包含问句 -> 混合检索
        if len(query) > 20 or any(char in query for char in ['？', '?', '如何', '什么', '为什么', '怎么']):
            if self.available_retrievers.get("hybrid"):
                return RetrievalStrategy.HYBRID
            elif self.available_retrievers.get("vector"):
                return RetrievalStrategy.VECTOR_ONLY
        
        # 短查询或专有名词 -> BM25
        if len(query) <= 10:
            if self.available_retrievers.get("bm25"):
                return RetrievalStrategy.BM25_ONLY
        
        # 默认使用混合检索
        if self.available_retrievers.get("hybrid"):
            return RetrievalStrategy.HYBRID
        elif self.available_retrievers.get("vector"):
            return RetrievalStrategy.VECTOR_ONLY
        elif self.available_retrievers.get("bm25"):
            return RetrievalStrategy.BM25_ONLY
        else:
            return RetrievalStrategy.ELASTICSEARCH_ONLY

    def retrieve(self, 
                query: str, 
                top_k: int = 10, 
                filters=None,
                strategy: Optional[RetrievalStrategy] = None) -> List[NodeWithScore]:
        """
        根据指定策略或自动选择检索器进行检索。
        
        Args:
            query: 查询字符串
            top_k: 返回结果数量
            filters: Qdrant过滤器
            strategy: 检索策略，None时使用默认策略或自动选择
        """
        # 确定检索策略
        if strategy is None:
            strategy = self.default_retrieval_strategy
        
        if strategy == RetrievalStrategy.AUTO:
            strategy = self._determine_retrieval_strategy(query)
        
        logger.info(f"Using retrieval strategy: {strategy.value} for query: '{query}'")
        
        query_bundle = QueryBundle(query_str=query)
        
        # 执行检索
        if strategy == RetrievalStrategy.VECTOR_ONLY:
            if not self.vector_retriever:
                logger.error("Vector retriever not available")
                return []
            if filters and hasattr(self.vector_retriever, 'filters'):
                self.vector_retriever.filters = filters
            retrieved_nodes = self.vector_retriever._retrieve(query_bundle)
            
        elif strategy == RetrievalStrategy.BM25_ONLY:
            if not self.bm25_retriever:
                logger.error("BM25 retriever not available")
                return []
            retrieved_nodes = self.bm25_retriever._retrieve(query_bundle)
            
        elif strategy == RetrievalStrategy.HYBRID:
            if not self.hybrid_retriever:
                logger.error("Hybrid retriever not available")
                return []
            if filters and self.vector_retriever and hasattr(self.vector_retriever, 'filters'):
                self.vector_retriever.filters = filters
            retrieved_nodes = self.hybrid_retriever._retrieve(query_bundle)
            
        elif strategy == RetrievalStrategy.ELASTICSEARCH_ONLY:
            if not self.es_retriever:
                logger.error("Elasticsearch retriever not available")
                return []
            retrieved_nodes = self.es_retriever._retrieve(query_bundle)
            
        else:
            logger.error(f"Unknown retrieval strategy: {strategy}")
            return []
        
        logger.info(f"Retrieved {len(retrieved_nodes)} documents using {strategy.value}")
        return retrieved_nodes[:top_k]

    def rerank(self, 
              query: str, 
              retrieved_nodes: List[NodeWithScore], 
              top_n: int = 5,
              search_history: List[str] = None,
              strategy: Optional[RerankStrategy] = None,
              is_elasticsearch: bool = False) -> List[NodeWithScore]:
        """
        根据指定策略对检索结果进行重排序。
        
        Args:
            query: 查询字符串
            retrieved_nodes: 检索到的节点
            top_n: 返回的节点数量
            search_history: 用户搜索历史
            strategy: 重排序策略
            is_elasticsearch: 是否为Elasticsearch结果
        """
        if strategy is None:
            strategy = self.default_rerank_strategy
        
        logger.info(f"Using rerank strategy: {strategy.value}")
        
        # 特殊处理：Elasticsearch结果且配置为不重排序
        if is_elasticsearch and not self.enable_es_rerank and strategy != RerankStrategy.NO_RERANK:
            logger.info("Elasticsearch结果跳过重排序，仅应用个性化提权")
            strategy = RerankStrategy.PERSONALIZED
        
        # 执行重排序
        if strategy == RerankStrategy.NO_RERANK:
            # 仅按原始分数排序
            sorted_nodes = sorted(retrieved_nodes, key=lambda x: float(x.score or 0), reverse=True)
            return sorted_nodes[:top_n]
            
        elif strategy == RerankStrategy.PAGERANK_ONLY:
            # 仅按PageRank分数排序
            for node_with_score in retrieved_nodes:
                metadata = node_with_score.node.metadata if hasattr(node_with_score.node, 'metadata') else {}
                pagerank_score = metadata.get('pagerank_score', 0.0)
                node_with_score.score = float(pagerank_score)
            sorted_nodes = sorted(retrieved_nodes, key=lambda x: float(x.score or 0), reverse=True)
            return sorted_nodes[:top_n]
            
        elif strategy == RerankStrategy.PERSONALIZED:
            # 仅应用个性化提权
            if search_history:
                logger.info("应用个性化提权...")
                history_keywords = set(search_history)
                for node_with_score in retrieved_nodes:
                    content = node_with_score.get_content().lower()
                    if any(keyword.lower() in content for keyword in history_keywords):
                        boost = 0.1
                        node_with_score.score += boost
                        logger.debug(f"节点 {node_with_score.node.node_id} 因匹配历史记录而被提权 {boost}")
            sorted_nodes = sorted(retrieved_nodes, key=lambda x: float(x.score or 0), reverse=True)
            return sorted_nodes[:top_n]
            
        elif strategy in [RerankStrategy.BGE_RERANKER, RerankStrategy.SENTENCE_TRANSFORMER]:
            # 使用重排序模型
            if not self.reranker:
                logger.warning("Reranker not initialized, falling back to no rerank")
                return self.rerank(query, retrieved_nodes, top_n, search_history, RerankStrategy.NO_RERANK, is_elasticsearch)
            
            # 先应用个性化提权
            if search_history:
                logger.info("应用个性化提权...")
                history_keywords = set(search_history)
                for node_with_score in retrieved_nodes:
                    content = node_with_score.get_content().lower()
                    if any(keyword.lower() in content for keyword in history_keywords):
                        boost = 0.1
                        node_with_score.score += boost
                        logger.debug(f"节点 {node_with_score.node.node_id} 因匹配历史记录而被提权 {boost}")
            
            # 再使用重排序模型
            reranked_nodes = self.reranker.postprocess_nodes(retrieved_nodes, query_bundle=QueryBundle(query_str=query))
            return reranked_nodes[:top_n]
        
        else:
            logger.error(f"Unknown rerank strategy: {strategy}")
            return retrieved_nodes[:top_n]

    def generate(self, query: str, context_nodes: List[NodeWithScore]) -> str:
        """
        根据上下文节点生成最终答案。
        """
        logger.info("Generating final answer.")
        
        # 构建参考资料文本，格式与rag.py保持一致
        sources_text = ""
        for i, node in enumerate(context_nodes):
            try:
                # 获取节点的元数据
                metadata = node.node.metadata if hasattr(node.node, 'metadata') else {}
                title = metadata.get('title', '未知标题')
                platform = metadata.get('source', '未知平台')
                content = node.get_content()
                
                # 精简内容，最多保留200个字符
                if len(content) > 200:
                    content = content[:200] + "..."
                
                # 使用与rag.py相同的格式
                sources_text += f"[{i+1}] 标题：{title}\n来源：{platform}\n内容：{content}\n\n"
            except Exception as e:
                logger.error(f"处理context_node[{i}]失败: {str(e)}")
                sources_text += f"[{i+1}] 无法处理的来源\n\n"
        
        # 使用与rag.py相同的提示词格式
        prompt = f"用户问题：{query}\n\n参考资料：\n{sources_text}"
        
        try:
            # 使用与rag.py相同的调用方式，添加超时控制
            import asyncio
            
            async def _generate_with_timeout():
                loop = asyncio.get_event_loop()
                return await loop.run_in_executor(
                    None, 
                    lambda: self.llm.chat_with_new_conversation(
                        query=prompt,
                        stream=False,
                        openid=f"rag_user_{int(time.time())}"
                    )
                )
            
            # 设置30秒超时
            try:
                result = asyncio.run(asyncio.wait_for(_generate_with_timeout(), timeout=30.0))
            except asyncio.TimeoutError:
                logger.warning("生成答案超时（>30秒），返回基于上下文的摘要")
                if context_nodes:
                    return f"根据找到的相关信息：{sources_text[:300]}..."
                return "抱歉，回答生成超时，请稍后再试。"
            
            if isinstance(result, dict) and "response" in result:
                answer = result.get("response", "")
                
                # 处理可能的格式化前缀，与rag.py保持一致
                if answer and (answer.startswith("回答：") or answer.startswith("回答:")):
                    answer = answer[3:].strip()
                    
                return answer or "抱歉，未能生成有效回答。"
            else:
                logger.warning("Coze返回的结果格式不正确")
                return "抱歉，回答格式出现问题。"
        except Exception as e:
            logger.error(f"生成答案时出错: {e}")
            # 如果LLM失败，返回基于上下文的简单摘要
            if context_nodes:
                return f"根据找到的相关信息，{sources_text[:300]}..."
            return f"抱歉，在生成答案时遇到了问题: {str(e)}"

    async def _get_user_search_history(self, user_id: str, limit: int = 10) -> List[str]:
        """从数据库获取用户的最近搜索历史记录 (同步版本)。"""
        if not user_id:
            return []
        try:
            # 使用正确的表名 wxapp_search_history 和字段 keyword
            sql = "SELECT DISTINCT keyword FROM wxapp_search_history WHERE openid = %s ORDER BY search_time DESC LIMIT %s"
            from etl.load import db_core
            # 假设 db_core 有一个同步执行函数
            records = await db_core.execute_query(sql, (user_id, limit), fetch=True)
            if records:
                history = [record['keyword'] for record in records]
                logger.info(f"成功获取用户 {user_id} 的 {len(history)} 条搜索历史。")
                return history
            return []
        except Exception as e:
            logger.error(f"获取用户 {user_id} 的搜索历史失败: {e}")
            return []

    def run(self, 
           query: str, 
           top_k_retrieve: int = 20, 
           top_k_rerank: int = 5, 
           user_id: Optional[str] = None,
           skip_generation: bool = False,
           retrieval_strategy: Optional[RetrievalStrategy] = None,
           rerank_strategy: Optional[RerankStrategy] = None,
           filters=None) -> dict:
        """
        执行完整的RAG流程：检索 -> 重排 -> 生成。
        
        Args:
            query: 查询字符串
            top_k_retrieve: 检索数量
            top_k_rerank: 重排后保留数量
            user_id: 用户ID，用于个性化
            skip_generation: 是否跳过LLM生成步骤
            retrieval_strategy: 检索策略
            rerank_strategy: 重排序策略
            filters: Qdrant过滤器
        """
        logger.info(f"--- Running RAG pipeline for query: '{query}' for user: {user_id} ---")
        logger.info(f"Retrieval strategy: {retrieval_strategy or 'default'}, Rerank strategy: {rerank_strategy or 'default'}")

        # 1. 获取用户历史（用于个性化）
        search_history = []
        if user_id:
            try:
                import asyncio
                search_history = asyncio.run(self._get_user_search_history(user_id))
            except Exception as e:
                logger.warning(f"获取用户搜索历史失败: {e}")
                search_history = []
        
        # 2. 检索
        retrieved_nodes = self.retrieve(
            query=query, 
            top_k=top_k_retrieve, 
            filters=filters,
            strategy=retrieval_strategy
        )
        
        if not retrieved_nodes:
            return {"answer": "抱歉，未能找到相关信息。", "contexts": [], "retrieved_texts": []}

        # 判断是否使用了Elasticsearch检索
        used_strategy = retrieval_strategy or self.default_retrieval_strategy
        if used_strategy == RetrievalStrategy.AUTO:
            used_strategy = self._determine_retrieval_strategy(query)
        is_elasticsearch = used_strategy == RetrievalStrategy.ELASTICSEARCH_ONLY
        
        # 3. 重排序
        reranked_nodes = self.rerank(
            query=query,
            retrieved_nodes=retrieved_nodes,
            top_n=top_k_rerank,
            search_history=search_history,
            strategy=rerank_strategy,
            is_elasticsearch=is_elasticsearch
        )
        
        # 提取召回文本
        retrieved_texts = []
        for i, node in enumerate(reranked_nodes, 1):
            content = node.get_content()
            score = getattr(node, 'score', 0.0)
            metadata = node.node.metadata if hasattr(node.node, 'metadata') else {}
            retrieved_texts.append({
                "rank": i,
                "content": content,
                "score": score,
                "title": metadata.get('title', ''),
                "url": metadata.get('url', ''),
                "source": metadata.get('source', '')
            })
        
        # 如果跳过生成步骤，直接返回召回文本
        if skip_generation:
            logger.info("--- RAG pipeline finished (generation skipped) ---")
            return {
                "answer": "检索完成，已跳过答案生成。", 
                "contexts": reranked_nodes,
                "retrieved_texts": retrieved_texts,
                "used_retrieval_strategy": used_strategy.value,
                "used_rerank_strategy": (rerank_strategy or self.default_rerank_strategy).value
            }
        
        # 4. 生成
        answer = self.generate(query, reranked_nodes)
        
        logger.info(f"--- RAG pipeline finished ---")
        return {
            "answer": answer, 
            "contexts": reranked_nodes,
            "retrieved_texts": retrieved_texts,
            "used_retrieval_strategy": used_strategy.value,
            "used_rerank_strategy": (rerank_strategy or self.default_rerank_strategy).value
        }

    def retrieve_only(self, 
                     query: str, 
                     top_k_retrieve: int = 20, 
                     top_k_rerank: int = 5, 
                     user_id: Optional[str] = None,
                     retrieval_strategy: Optional[RetrievalStrategy] = None,
                     rerank_strategy: Optional[RerankStrategy] = None,
                     filters=None) -> dict:
        """
        只执行检索和重排，跳过LLM生成步骤。
        """
        return self.run(
            query=query, 
            top_k_retrieve=top_k_retrieve, 
            top_k_rerank=top_k_rerank, 
            user_id=user_id, 
            skip_generation=True,
            retrieval_strategy=retrieval_strategy,
            rerank_strategy=rerank_strategy,
            filters=filters
        )

    def get_strategy_combinations(self) -> Dict[str, List[str]]:
        """获取所有可用的策略组合"""
        available_retrieval = []
        for strategy in RetrievalStrategy:
            if strategy == RetrievalStrategy.AUTO:
                available_retrieval.append(strategy.value)
            elif strategy == RetrievalStrategy.VECTOR_ONLY and self.available_retrievers.get("vector"):
                available_retrieval.append(strategy.value)
            elif strategy == RetrievalStrategy.BM25_ONLY and self.available_retrievers.get("bm25"):
                available_retrieval.append(strategy.value)
            elif strategy == RetrievalStrategy.HYBRID and self.available_retrievers.get("hybrid"):
                available_retrieval.append(strategy.value)
            elif strategy == RetrievalStrategy.ELASTICSEARCH_ONLY and self.available_retrievers.get("elasticsearch"):
                available_retrieval.append(strategy.value)
        
        available_rerank = [strategy.value for strategy in RerankStrategy]
        
        return {
            "retrieval_strategies": available_retrieval,
            "rerank_strategies": available_rerank,
            "available_retrievers": self.available_retrievers
        }


if __name__ == "__main__":
    # 使用示例：展示不同的策略组合
    rag_pipeline = RagPipeline()
    
    print("=== 可用策略组合 ===")
    strategies = rag_pipeline.get_strategy_combinations()
    print("检索策略:", strategies["retrieval_strategies"])
    print("重排序策略:", strategies["rerank_strategies"])
    print("可用检索器:", strategies["available_retrievers"])
    print()
    
    # 示例1: 自动策略（默认）
    print("=== 示例1: 自动策略 ===")
    query1 = "南开大学的校训是什么？"
    result1 = rag_pipeline.run(query=query1)
    print(f"查询: {query1}")
    print(f"使用的检索策略: {result1['used_retrieval_strategy']}")
    print(f"使用的重排序策略: {result1['used_rerank_strategy']}")
    print(f"答案: {result1['answer'][:100]}...")
    print()

    # 示例2: 指定策略组合
    print("=== 示例2: 指定策略组合 ===")
    query2 = "南开大学*学院"
    result2 = rag_pipeline.run(
        query=query2,
        retrieval_strategy=RetrievalStrategy.ELASTICSEARCH_ONLY,
        rerank_strategy=RerankStrategy.PAGERANK_ONLY
    )
    print(f"查询: {query2}")
    print(f"使用的检索策略: {result2['used_retrieval_strategy']}")
    print(f"使用的重排序策略: {result2['used_rerank_strategy']}")
    print()

    # 示例3: 仅检索模式
    print("=== 示例3: 仅检索模式 ===")
    query3 = "人工智能"
    result3 = rag_pipeline.retrieve_only(
        query=query3,
        retrieval_strategy=RetrievalStrategy.HYBRID,
        rerank_strategy=RerankStrategy.BGE_RERANKER
    )
    print(f"查询: {query3}")
    print(f"检索到的文档数量: {len(result3['retrieved_texts'])}")
    print(f"使用的检索策略: {result3['used_retrieval_strategy']}")
    print()

    # 示例4: 个性化检索
    print("=== 示例4: 个性化检索 ===")
    query4 = "计算机专业"
    result4 = rag_pipeline.run(
        query=query4,
        user_id="test_user_123",
        retrieval_strategy=RetrievalStrategy.VECTOR_ONLY,
        rerank_strategy=RerankStrategy.PERSONALIZED
    )
    print(f"查询: {query4}")
    print(f"使用的检索策略: {result4['used_retrieval_strategy']}")
    print(f"使用的重排序策略: {result4['used_rerank_strategy']}")
    print()
