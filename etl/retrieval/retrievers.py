import os
from pathlib import Path
import re
import time
import json
import tempfile
from typing import List, Dict, Any, Optional, Union, Tuple, Callable, Type
import numpy as np
from abc import ABC, abstractmethod

import bm25s
from llama_index.core import QueryBundle, VectorStoreIndex
from llama_index.core.base.base_retriever import BaseRetriever
from llama_index.core.base.embeddings.base import BaseEmbedding
from llama_index.core.callbacks import CallbackManager
from llama_index.core.constants import DEFAULT_SIMILARITY_TOP_K
from llama_index.core.indices.keyword_table.utils import simple_extract_keywords
from llama_index.core.schema import NodeWithScore, BaseNode, IndexNode
from llama_index.core.storage.docstore import BaseDocumentStore
from llama_index.core.vector_stores import VectorStoreQuery
from llama_index.vector_stores.qdrant import QdrantVectorStore
from etl.processors.nodes import get_node_content
from nltk import PorterStemmer
from rank_bm25 import BM25Okapi
from pydantic import ConfigDict, BaseModel, Field
from qdrant_client import QdrantClient, models
from elasticsearch import Elasticsearch
import jieba
import pickle

from etl.retrieval import logger


class QdrantRetriever(BaseRetriever):
    def __init__(
            self,
            vector_store: QdrantVectorStore,
            embed_model: BaseEmbedding,
            similarity_top_k: int = 2,
            filters=None
    ) -> None:
        self._vector_store = vector_store
        self._embed_model = embed_model
        self._similarity_top_k = similarity_top_k
        self.filters = filters
        super().__init__()

    async def _aretrieve(self, query_bundle: QueryBundle) -> List[NodeWithScore]:
        query_embedding = self._embed_model.get_query_embedding(query_bundle.query_str)
        vector_store_query = VectorStoreQuery(
            query_embedding,
            similarity_top_k=self._similarity_top_k,
            # filters=self.filters, # qdrant 使用llama_index filter会有问题，原因未知
        )
        query_result = await self._vector_store.aquery(
            vector_store_query,
            qdrant_filters=self.filters,  # 需要查找qdrant相关用法
        )

        node_with_scores = []
        for node, similarity in zip(query_result.nodes, query_result.similarities):
            node_with_scores.append(NodeWithScore(node=node, score=similarity))
        return node_with_scores

    def _retrieve(self, query_bundle: QueryBundle) -> List[NodeWithScore]:
        # 不维护
        query_embedding = self._embed_model.get_query_embedding(query_bundle.query_str)
        vector_store_query = VectorStoreQuery(
            query_embedding,
            similarity_top_k=self._similarity_top_k,
        )
        query_result = self._vector_store.query(
            vector_store_query,
            qdrant_filters=self.filters,  # 需要查找qdrant相关用法
        )

        node_with_scores = []
        for node, similarity in zip(query_result.nodes, query_result.similarities):
            node_with_scores.append(NodeWithScore(node=node, score=similarity))
        return node_with_scores


def tokenize_and_remove_stopwords(tokenizer, text, stopwords):
    if not text or not isinstance(text, str):
        return ["dummy_token"]  # 返回一个默认token，避免空列表
    
    words = tokenizer.cut(text)
    filtered_words = [word for word in words
                      if word not in stopwords and word != ' ' and len(word.strip()) > 0]
    
    # 如果过滤后为空，返回一个默认token
    return filtered_words if filtered_words else ["dummy_token"]


class BM25Retriever(BaseRetriever):
    """BM25 retriever implementation with fast loading support."""
    
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        extra='allow'
    )

    # Define fields at class level
    similarity_top_k: int = Field(
        default=DEFAULT_SIMILARITY_TOP_K,
        description="Number of top results to return"
    )
    bm25_type: int = Field(
        default=0,
        description="BM25 implementation type (0: BM25Okapi, 1: BM25)"
    )
    k1: float = Field(
        default=1.5,
        description="BM25 k1 parameter"
    )
    b: float = Field(
        default=0.75,
        description="BM25 b parameter"
    )
    epsilon: float = Field(
        default=0.25,
        description="BM25 epsilon parameter"
    )
    embed_type: int = Field(
        default=0,
        description="Embedding type"
    )

    def __init__(
            self,
            nodes: List[BaseNode],
            tokenizer: Optional[Callable[[str], List[str]]],
            similarity_top_k: int = DEFAULT_SIMILARITY_TOP_K,
            callback_manager: Optional[CallbackManager] = None,
            objects: Optional[List[IndexNode]] = None,
            object_map: Optional[dict] = None,
            verbose: bool = False,
            stopwords: List[str] = [""],
            embed_type: int = 0,
            bm25_type: int = 0,
            fast_mode: bool = True,  # 新增：快速模式，跳过索引构建
            lazy_init: bool = False,  # 新增：延迟初始化
    ) -> None:
        if not nodes:
            raise ValueError("Nodes list cannot be empty")
            
        # Set instance attributes
        self.similarity_top_k = similarity_top_k
        self.bm25_type = bm25_type
        self.embed_type = embed_type
        self.k1 = 1.5
        self.b = 0.75
        self.epsilon = 0.25
            
        self._nodes = nodes
        self._tokenizer = tokenizer
        self.stopwords = stopwords
        self._corpus = None
        self.bm25 = None
        self._initialized = False
        
        # 根据模式决定是否立即初始化
        if not fast_mode and not lazy_init:
            self._build_index()
        elif fast_mode:
            logger.info("BM25Retriever使用快速模式，跳过索引构建")
            # 快速模式：延迟到第一次查询时再构建索引
            self._initialized = False
        
        self.filter_dict = None
        
        super().__init__(
            callback_manager=callback_manager,
            object_map=object_map,
            objects=objects,
            verbose=verbose,
        )
    
    def _build_index(self):
        """构建BM25索引（耗时操作）"""
        if self._initialized:
            return
            
        logger.info(f"开始构建BM25索引，节点数量: {len(self._nodes)}")
        start_time = time.time()
        
        # 处理语料库
        self._corpus = []
        for i, node in enumerate(self._nodes):
            if i % 10000 == 0:  # 每处理1万个节点显示一次进度
                logger.debug(f"已处理 {i}/{len(self._nodes)} 个节点")
            
            content = get_node_content(node, self.embed_type)
            tokens = tokenize_and_remove_stopwords(self._tokenizer, content, stopwords=self.stopwords)
            self._corpus.append(tokens)
        
        if not any(self._corpus):
            raise ValueError("All documents are empty after tokenization")
        
        # 构建BM25索引
        try:
            if self.bm25_type == 1:
                self.bm25 = bm25s.BM25(k1=self.k1, b=self.b)
                self.bm25.index(self._corpus)
            else:
                self.bm25 = BM25Okapi(
                    self._corpus,
                    k1=self.k1,
                    b=self.b,
                    epsilon=self.epsilon,
                )
        except Exception as e:
            raise ValueError(f"Failed to initialize BM25: {str(e)}")
        
        self._initialized = True
        end_time = time.time()
        logger.info(f"BM25索引构建完成，耗时: {end_time - start_time:.2f}秒")
    
    def _ensure_initialized(self):
        """确保索引已初始化"""
        if not self._initialized:
            self._build_index()
    
    @classmethod
    def from_pickle_fast(
        cls,
        nodes_path: str,
        tokenizer: Optional[Callable[[str], List[str]]] = None,
        stopwords: List[str] = None,
        similarity_top_k: int = DEFAULT_SIMILARITY_TOP_K,
        **kwargs
    ) -> "BM25Retriever":
        """
        从pickle文件快速加载BM25检索器（推荐方法）
        
        Args:
            nodes_path: BM25文件路径
            tokenizer: 分词器
            stopwords: 停用词列表
            similarity_top_k: 返回结果数量
            **kwargs: 其他参数
        """
        import pickle
        
        logger.info(f"从文件快速加载BM25数据: {nodes_path}")
        start_time = time.time()
        
        # 检查文件是否存在
        if not os.path.exists(nodes_path):
            raise FileNotFoundError(f"BM25文件不存在: {nodes_path}")
        
        # 设置默认值
        if tokenizer is None:
            import jieba
            tokenizer = jieba
        
        if stopwords is None:
            stopwords = []
        
        # 首先尝试检查文件内容类型
        try:
            with open(nodes_path, 'rb') as f:
                data = pickle.load(f)
            
            # 情况1：新格式 - 包含完整状态的字典
            if isinstance(data, dict) and 'bm25_index' in data:
                logger.info("检测到新格式BM25文件，使用快速加载...")
                end_time = time.time()
                logger.info(f"文件读取耗时: {end_time - start_time:.2f}秒")
                
                # 重新打开文件并使用load_from_pickle方法
                instance = cls.load_from_pickle(nodes_path, tokenizer)
                
                # 更新参数（如果提供的话）
                if similarity_top_k != DEFAULT_SIMILARITY_TOP_K:
                    instance.similarity_top_k = similarity_top_k
                
                return instance
                
            # 情况2：旧格式 - 完整的BM25检索器对象（已废弃，应该不会出现）
            elif isinstance(data, cls):
                logger.info(f"加载完整BM25检索器成功，节点数量: {len(data._nodes)}，耗时: {time.time() - start_time:.2f}秒")
                if similarity_top_k != DEFAULT_SIMILARITY_TOP_K:
                    data.similarity_top_k = similarity_top_k
                return data
                
            # 情况3：最旧格式 - 仅节点列表，需要重新构建索引
            elif isinstance(data, list):
                nodes = data
                end_time = time.time()
                logger.info(f"加载节点数据完成，节点数量: {len(nodes)}，耗时: {end_time - start_time:.2f}秒")
                logger.info("检测到旧格式文件（仅节点），正在构建BM25索引...")
                
                # 创建检索器实例并立即构建索引
                instance = cls(
                    nodes=nodes,
                    tokenizer=tokenizer,
                    stopwords=stopwords,
                    similarity_top_k=similarity_top_k,
                    fast_mode=False,  # 立即构建索引
                    **kwargs
                )
                
                return instance
                
            else:
                raise ValueError(f"不支持的pickle文件格式: {type(data)}")
                
        except Exception as e:
            logger.error(f"加载BM25文件失败: {e}")
            raise

    def filter(self, scores):
        top_n = scores.argsort()[::-1]
        nodes: List[NodeWithScore] = []
        for ix in top_n:
            if scores[ix] <= 0:
                break
            flag = True
            if self.filter_dict is not None:
                for key, value in self.filter_dict.items():
                    if self._nodes[ix].metadata[key] != value:
                        flag = False
                        break
            if flag:
                nodes.append(NodeWithScore(node=self._nodes[ix], score=float(scores[ix])))
            if len(nodes) == self.similarity_top_k:
                break

        # add nodes sort in BM25Retriever
        nodes = sorted(nodes, key=lambda x: x.score, reverse=True)
        return nodes

    def get_scores(self, query, docs=None):
        # 确保索引已初始化
        self._ensure_initialized()
        
        if docs is None:
            bm25 = self.bm25
        else:
            corpus = [tokenize_and_remove_stopwords(
                self._tokenizer, doc, stopwords=self.stopwords)
                for doc in docs]
            if self.bm25_type == 1:
                bm25 = bm25s.BM25(
                    k1=self.k1,
                    b=self.b,
                )
                bm25.index(corpus)
            else:
                bm25 = BM25Okapi(
                    corpus,
                    k1=self.k1,
                    b=self.b,
                    epsilon=self.epsilon,
                )
        tokenized_query = tokenize_and_remove_stopwords(self._tokenizer, query,
                                                        stopwords=self.stopwords)
        scores = bm25.get_scores(tokenized_query)
        return scores

    @classmethod
    def from_defaults(
            cls,
            index: Optional[VectorStoreIndex] = None,
            nodes: Optional[List[BaseNode]] = None,
            docstore: Optional[BaseDocumentStore] = None,
            tokenizer: Optional[Callable[[str], List[str]]] = None,
            similarity_top_k: int = DEFAULT_SIMILARITY_TOP_K,
            verbose: bool = False,
            stopwords: List[str] = [""],
            embed_type: int = 0,
            bm25_type: int = 0,  # 0-->official bm25-Okapi 1-->bm25s
    ) -> "BM25Retriever":
        # ensure only one of index, nodes, or docstore is passed
        if sum(bool(val) for val in [index, nodes, docstore]) != 1:
            raise ValueError("Please pass exactly one of index, nodes, or docstore.")

        if index is not None:
            docstore = index.docstore

        if docstore is not None:
            nodes = cast(List[BaseNode], list(docstore.docs.values()))

        assert (
                nodes is not None
        ), "Please pass exactly one of index, nodes, or docstore."

        tokenizer = tokenizer
        return cls(
            nodes=nodes,
            tokenizer=tokenizer,
            similarity_top_k=similarity_top_k,
            verbose=verbose,
            stopwords=stopwords,
            embed_type=embed_type,
            bm25_type=bm25_type,
        )

    def _retrieve(self, query_bundle: QueryBundle) -> List[NodeWithScore]:
        if query_bundle.custom_embedding_strs or query_bundle.embedding:
            logger.warning("BM25Retriever does not support embeddings, skipping...")

        query = query_bundle.query_str
        scores = self.get_scores(query)
        nodes = self.filter(scores)

        return nodes

    def save_to_pickle(self, filepath: str):
        """
        保存BM25检索器到pickle文件，排除不能序列化的对象
        """
        if not self._initialized:
            raise ValueError("BM25检索器未初始化，无法保存")
        
        # 创建可序列化的状态字典
        state = {
            'nodes': self._nodes,
            'corpus': self._corpus,
            'bm25_data': {
                'type': self.bm25_type,
                'k1': self.k1,
                'b': self.b,
                'epsilon': self.epsilon,
            },
            'stopwords': self.stopwords,
            'similarity_top_k': self.similarity_top_k,
            'embed_type': self.embed_type,
            'initialized': True
        }
        
        # 保存BM25索引数据
        if self.bm25_type == 1:
            # bm25s类型，保存其内部数据
            state['bm25_index'] = {
                'doc_freqs': self.bm25.doc_freqs,
                'idf': self.bm25.idf,
                'doc_lens': self.bm25.doc_lens,
                'avgdl': self.bm25.avgdl,
                'vocab': self.bm25.vocab,
                'corpus_size': self.bm25.corpus_size
            }
        else:
            # BM25Okapi类型，保存其内部数据
            state['bm25_index'] = {
                'doc_freqs': self.bm25.doc_freqs,
                'idf': self.bm25.idf,
                'doc_len': self.bm25.doc_len,
                'avgdl': self.bm25.avgdl,
                'corpus': self._corpus  # BM25Okapi需要原始语料库
            }
        
        import pickle
        with open(filepath, 'wb') as f:
            pickle.dump(state, f)
        
        logger.info(f"BM25检索器状态已保存到: {filepath}")

    @classmethod
    def load_from_pickle(cls, filepath: str, tokenizer=None) -> "BM25Retriever":
        """
        从pickle文件加载BM25检索器状态并重建对象
        """
        import pickle
        
        with open(filepath, 'rb') as f:
            state = pickle.load(f)
        
        # 设置默认tokenizer
        if tokenizer is None:
            import jieba
            tokenizer = jieba
        
        # 创建实例（不构建索引）
        instance = cls(
            nodes=state['nodes'],
            tokenizer=tokenizer,
            stopwords=state['stopwords'],
            similarity_top_k=state['similarity_top_k'],
            embed_type=state['embed_type'],
            bm25_type=state['bm25_data']['type'],
            fast_mode=True,  # 跳过自动构建
            lazy_init=True
        )
        
        # 设置参数
        instance.k1 = state['bm25_data']['k1']
        instance.b = state['bm25_data']['b']
        instance.epsilon = state['bm25_data']['epsilon']
        instance._corpus = state['corpus']
        
        # 重建BM25索引对象
        if state['bm25_data']['type'] == 1:
            # bm25s类型
            import bm25s
            instance.bm25 = bm25s.BM25(k1=instance.k1, b=instance.b)
            # 恢复内部状态
            bm25_data = state['bm25_index']
            instance.bm25.doc_freqs = bm25_data['doc_freqs']
            instance.bm25.idf = bm25_data['idf']
            instance.bm25.doc_lens = bm25_data['doc_lens']
            instance.bm25.avgdl = bm25_data['avgdl']
            instance.bm25.vocab = bm25_data['vocab']
            instance.bm25.corpus_size = bm25_data['corpus_size']
        else:
            # BM25Okapi类型
            from rank_bm25 import BM25Okapi
            instance.bm25 = BM25Okapi(
                state['bm25_index']['corpus'],
                k1=instance.k1,
                b=instance.b,
                epsilon=instance.epsilon
            )
        
        instance._initialized = True
        logger.info(f"BM25检索器已从 {filepath} 恢复，节点数量: {len(instance._nodes)}")
        
        return instance


class ElasticsearchRetriever(BaseRetriever):
    """
    使用Elasticsearch进行检索，支持通配符查询。
    """
    def __init__(
        self, 
        index_name: str, 
        es_host: str = 'localhost', 
        es_port: int = 9200, 
        similarity_top_k: int = 10,
        callback_manager: Optional[CallbackManager] = None,
    ):
        """
        初始化Elasticsearch检索器。

        Args:
            index_name (str): 要查询的Elasticsearch索引名称。
            es_host (str): Elasticsearch主机名。
            es_port (int): Elasticsearch端口号。
            similarity_top_k (int): 返回结果的数量。
        """
        self.index_name = index_name
        self.similarity_top_k = similarity_top_k
        try:
            self.es_client = Elasticsearch([{'host': es_host, 'port': es_port, 'scheme': 'http'}])
            if not self.es_client.ping():
                raise ConnectionError("无法连接到Elasticsearch")
        except Exception as e:
            logger.error(f"无法连接到Elasticsearch: {e}")
            self.es_client = None

        super().__init__(callback_manager=callback_manager)

    def _retrieve(self, query_bundle: QueryBundle) -> List[NodeWithScore]:
        """
        使用通配符查询在Elasticsearch中搜索。

        Args:
            query_bundle (QueryBundle): 包含查询字符串。

        Returns:
            List[NodeWithScore]: 检索到的节点列表。
        """
        if not self.es_client:
            return []
            
        query = query_bundle.query_str
        
        # 构建通配符查询
        if '*' in query or '?' in query:
            should_queries = []
            
            # 策略1: 在keyword字段中使用通配符（用于精确匹配完整标题）
            should_queries.extend([
                {"wildcard": {"title.keyword": {"value": query, "case_insensitive": True}}},
                {"wildcard": {"content.keyword": {"value": query, "case_insensitive": True}}}
            ])
            
            # 策略2: 在text字段中使用通配符
            should_queries.extend([
                {"wildcard": {"title": {"value": query, "case_insensitive": True}}},
                {"wildcard": {"content": {"value": query, "case_insensitive": True}}}
            ])
            
            # 策略3: 对于简单的前缀后缀匹配，拆分查询
            if '*' in query:
                # 处理前缀匹配 如: "南开*"
                if query.endswith('*') and '*' not in query[:-1]:
                    prefix = query[:-1]
                    should_queries.extend([
                        {"prefix": {"title": {"value": prefix, "case_insensitive": True}}},
                        {"prefix": {"content": {"value": prefix, "case_insensitive": True}}}
                    ])
                
                # 处理后缀匹配 如: "*大学"
                elif query.startswith('*') and '*' not in query[1:]:
                    suffix = query[1:]
                    should_queries.extend([
                        {"suffix": {"title": {"value": suffix, "case_insensitive": True}}},
                        {"suffix": {"content": {"value": suffix, "case_insensitive": True}}}
                    ])
                
                # 处理中间匹配 如: "南开*大学" 
                elif query.count('*') == 1 and not query.startswith('*') and not query.endswith('*'):
                    parts = query.split('*')
                    if len(parts) == 2:
                        prefix, suffix = parts
                        # 需要同时包含前缀和后缀
                        should_queries.append({
                            "bool": {
                                "must": [
                                    {"prefix": {"title": {"value": prefix, "case_insensitive": True}}},
                                    {"suffix": {"title": {"value": suffix, "case_insensitive": True}}}
                                ]
                            }
                        })
                        should_queries.append({
                            "bool": {
                                "must": [
                                    {"prefix": {"content": {"value": prefix, "case_insensitive": True}}},
                                    {"suffix": {"content": {"value": suffix, "case_insensitive": True}}}
                                ]
                            }
                        })
            
            # 策略4: 对于?查询，转换为模糊查询或者更宽泛的匹配
            if '?' in query:
                # 将?替换为空，做包含查询作为备选
                query_without_wildcards = query.replace('?', '').replace('*', '')
                if query_without_wildcards:
                    should_queries.extend([
                        {"match": {"title": {"query": query_without_wildcards, "fuzziness": "AUTO"}}},
                        {"match": {"content": {"query": query_without_wildcards, "fuzziness": "AUTO"}}}
                    ])
            
            # 策略5: query_string作为最后的尝试
            should_queries.append({
                "query_string": {
                    "query": query,
                    "fields": ["title", "content"],
                    "allow_leading_wildcard": True,
                    "analyze_wildcard": True,
                    "lenient": True
                }
            })
            
            es_query = {
                "query": {
                    "bool": {
                        "should": should_queries,
                        "minimum_should_match": 1
                    }
                }
            }
        else:
            # 如果没有通配符，使用普通的匹配查询，指定使用ik_smart分析器
            es_query = {
                "query": {
                    "bool": {
                        "should": [
                            {"match": {"title": {"query": query, "analyzer": "ik_smart", "boost": 2.0}}},
                            {"match": {"content": {"query": query, "analyzer": "ik_smart", "boost": 1.0}}}
                        ],
                        "minimum_should_match": 1
                    }
                }
            }

        try:
            response = self.es_client.search(
                index=self.index_name,
                body=es_query,
                size=self.similarity_top_k
            )
            
            nodes_with_scores = []
            for hit in response['hits']['hits']:
                source = hit['_source']
                node = IndexNode(
                    text=source.get('content', ''),
                    index_id=hit['_id'],  # 添加必需的 index_id 字段
                    metadata={
                        'title': source.get('title', ''),
                        'original_url': source.get('original_url', ''),
                        'publish_time': source.get('publish_time'),
                        'pagerank_score': source.get('pagerank_score', 0.0),  # 添加PageRank分数
                        'platform': source.get('platform', ''),  # 添加数据源信息
                    }
                )
                nodes_with_scores.append(NodeWithScore(node=node, score=hit['_score']))
            
            return nodes_with_scores
        except Exception as e:
            logger.error(f"Elasticsearch搜索出错: {e}")
            return []


class HybridRetriever(BaseRetriever):
    def __init__(
            self,
            dense_retriever: QdrantRetriever,
            sparse_retriever: BM25Retriever,
            retrieval_type=1,
            topk=256,
            pagerank_weight=0.1,
    ):
        self.dense_retriever = dense_retriever
        self.sparse_retriever = sparse_retriever
        self.retrieval_type = retrieval_type  # 1:dense only 2:sparse only 3:hybrid
        self.filters = None
        self.filter_dict = None
        self.topk = topk
        self.pagerank_weight = pagerank_weight
        super().__init__()

    @classmethod
    def fusion(cls, list_of_list_ranks_system, topk=256):
        """Simple fusion method that removes duplicates and sorts by score."""
        all_nodes = []
        seen_contents = set()
        
        for nodes in list_of_list_ranks_system:
            if not nodes:  # 跳过空列表
                continue
            for node in nodes:
                content = node.node.get_content()
                if content not in seen_contents:
                    all_nodes.append(node)
                    seen_contents.add(content)
                    
        # 确保所有节点都有有效的分数
        for node in all_nodes:
            if node.score is None:
                node.score = 0.0
                
        all_nodes = sorted(all_nodes, key=lambda x: float(x.score), reverse=True)
        return all_nodes[:min(topk, len(all_nodes))]

    @classmethod
    def reciprocal_rank_fusion(cls, list_of_list_ranks_system, K=60, topk=256, pagerank_weight=0.1):
        """Reciprocal rank fusion method with PageRank integration."""
        from collections import defaultdict
        
        if not list_of_list_ranks_system or all(not lst for lst in list_of_list_ranks_system):
            return []
            
        rrf_scores = defaultdict(float)
        content_to_node = {}
        
        for rank_list in list_of_list_ranks_system:
            if not rank_list:  # 跳过空列表
                continue
            for rank, item in enumerate(rank_list, 1):
                content = item.node.get_content()
                content_to_node[content] = item
                
                # 计算RRF分数
                rrf_score = 1 / (rank + K)
                
                # 获取PageRank分数
                pagerank_score = item.node.metadata.get('pagerank_score', 0.0)
                
                # 结合RRF和PageRank分数（使用配置的权重）
                final_score = rrf_score + pagerank_weight * float(pagerank_score)
                rrf_scores[content] += final_score

        # 按最终分数排序
        sorted_items = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
        
        # 构建结果列表
        reranked_nodes = []
        for content, score in sorted_items:
            node = content_to_node[content]
            node.score = float(score)  # 确保分数是float类型
            reranked_nodes.append(node)
            
        return reranked_nodes[:min(topk, len(reranked_nodes))]

    async def _aretrieve(self, query_bundle: QueryBundle) -> List[NodeWithScore]:
        try:
            if self.retrieval_type == 2:
                self.sparse_retriever.filter_dict = self.filter_dict
                sparse_nodes = await self.sparse_retriever.aretrieve(query_bundle)
                return sparse_nodes
                
            if self.retrieval_type == 1:
                self.dense_retriever.filters = self.filters
                dense_nodes = await self.dense_retriever.aretrieve(query_bundle)
                return dense_nodes

            # Hybrid retrieval (type 3)
            self.sparse_retriever.filter_dict = self.filter_dict
            self.dense_retriever.filters = self.filters
            
            # 并行执行两个检索
            sparse_nodes = await self.sparse_retriever.aretrieve(query_bundle)
            dense_nodes = await self.dense_retriever.aretrieve(query_bundle)
            
            # 使用 reciprocal rank fusion 合并结果
            all_nodes = self.reciprocal_rank_fusion(
                [sparse_nodes, dense_nodes], 
                topk=self.topk,
                pagerank_weight=self.pagerank_weight
            )
            
            return all_nodes
            
        except Exception as e:
            print(f"Error in hybrid retrieval: {str(e)}")
            # 返回空列表而不是失败
            return []

    def _retrieve(self, query_bundle: QueryBundle) -> List[NodeWithScore]:
        """Synchronous version with intelligent fallback."""
        try:
            if self.retrieval_type == 2:
                # BM25只进行同步检索
                sparse_nodes = self.sparse_retriever._retrieve(query_bundle)
                return sparse_nodes
                
            if self.retrieval_type == 1:
                # 向量检索
                dense_nodes = self.dense_retriever._retrieve(query_bundle)
                return dense_nodes

            # Hybrid retrieval (type 3) - 智能混合检索
            # 同步执行两个检索
            sparse_nodes = self.sparse_retriever._retrieve(query_bundle)
            dense_nodes = self.dense_retriever._retrieve(query_bundle)
            
            # 智能降级策略
            if not dense_nodes and sparse_nodes:
                # 向量检索失败，降级到BM25检索
                print(f"向量检索返回0结果，降级使用BM25检索，返回{len(sparse_nodes)}个结果")
                return sparse_nodes
            elif not sparse_nodes and dense_nodes:
                # BM25检索失败，降级到向量检索
                print(f"BM25检索返回0结果，降级使用向量检索，返回{len(dense_nodes)}个结果")
                return dense_nodes
            elif not sparse_nodes and not dense_nodes:
                # 两个都失败
                print("BM25和向量检索都返回0结果")
                return []
            
            # 正常混合检索：使用 reciprocal rank fusion 合并结果
            all_nodes = self.reciprocal_rank_fusion(
                [sparse_nodes, dense_nodes], 
                topk=self.topk,
                pagerank_weight=self.pagerank_weight
            )
            
            print(f"混合检索：BM25返回{len(sparse_nodes)}个结果，向量返回{len(dense_nodes)}个结果，融合后{len(all_nodes)}个结果")
            return all_nodes
            
        except Exception as e:
            print(f"Error in hybrid retrieval: {str(e)}")
            # 尝试降级到BM25检索作为最后的备选
            try:
                fallback_nodes = self.sparse_retriever._retrieve(query_bundle)
                print(f"异常降级到BM25检索，返回{len(fallback_nodes)}个结果")
                return fallback_nodes
            except:
                return []


class VectorRetriever:
    """
    从向量数据库（如Qdrant）中检索相关文档。
    """
    def __init__(self, vector_store: QdrantVectorStore, embed_model: BaseEmbedding):
        self.vector_store = vector_store
        self.embed_model = embed_model

    def search(self, query: str) -> List[Dict[str, Any]]:
        query_embedding = self.embed_model.get_query_embedding(query)
        vector_store_query = VectorStoreQuery(
            query_embedding,
            similarity_top_k=2,
        )
        query_result = self.vector_store.query(
            vector_store_query,
        )

        results = []
        for node, similarity in zip(query_result.nodes, query_result.similarities):
            results.append({
                'node': node,
                'similarity': similarity
            })
        return results
