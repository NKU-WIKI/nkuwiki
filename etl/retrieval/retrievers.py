import os
from pathlib import Path
import re
import time
import json
import tempfile
from typing import List, Dict, Any, Optional, Union, Tuple, Callable, Type
import numpy as np
from abc import ABC, abstractmethod
from core.utils.logger import get_module_logger

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
from etl.embedding.ingestion import get_node_content
from nltk import PorterStemmer
from rank_bm25 import BM25Okapi
from pydantic import ConfigDict, BaseModel, Field

logger = get_module_logger(__name__)


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
    """BM25 retriever implementation."""
    
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
        
        # 处理语料库
        self._corpus = []
        for node in self._nodes:
            content = get_node_content(node, self.embed_type)
            tokens = tokenize_and_remove_stopwords(self._tokenizer, content, stopwords=stopwords)
            self._corpus.append(tokens)
            
        if not any(self._corpus):  # 检查是否所有文档都是空的
            raise ValueError("All documents are empty after tokenization")
            
        try:
            if self.bm25_type == 1:
                self.bm25 = bm25s.BM25(
                    k1=self.k1,
                    b=self.b,
                )
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
            
        self.filter_dict = None
        
        super().__init__(
            callback_manager=callback_manager,
            object_map=object_map,
            objects=objects,
            verbose=verbose,
        )

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


class HybridRetriever(BaseRetriever):
    def __init__(
            self,
            dense_retriever: QdrantRetriever,
            sparse_retriever: BM25Retriever,
            retrieval_type=1,
            topk=256,
    ):
        self.dense_retriever = dense_retriever
        self.sparse_retriever = sparse_retriever
        self.retrieval_type = retrieval_type  # 1:dense only 2:sparse only 3:hybrid
        self.filters = None
        self.filter_dict = None
        self.topk = topk
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
    def reciprocal_rank_fusion(cls, list_of_list_ranks_system, K=60, topk=256):
        """Reciprocal rank fusion method."""
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
                rrf_scores[content] += 1 / (rank + K)

        # 按RRF分数排序
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
                topk=self.topk
            )
            
            return all_nodes
            
        except Exception as e:
            print(f"Error in hybrid retrieval: {str(e)}")
            # 返回空列表而不是失败
            return []

    def _retrieve(self, query_bundle: QueryBundle) -> List[NodeWithScore]:
        """Synchronous version - not maintained."""
        raise NotImplementedError("Synchronous retrieval is not supported. Please use aretrieve instead.")
