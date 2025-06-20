#!/usr/bin/env python3
import os
import jieba
import torch
from qdrant_client import QdrantClient
from llama_index.vector_stores.qdrant import QdrantVectorStore

from config import Config
from core.utils import register_logger
from core.agent.agent_factory import get_agent
from etl.embedding.hf_embeddings import HuggingFaceEmbedding
from etl.retrieval.rerankers import SentenceTransformerRerank, LLMRerank
from etl.retrieval.retrievers import QdrantRetriever, BM25Retriever, HybridRetriever, ElasticsearchRetriever

config = Config()
logger = register_logger(__name__)


def init_llm(model_name: str = None):
    """初始化语言模型"""
    if model_name is None:
        dkv3_bot_id = config.get("core.agent.coze.dkv3_bot_id")
        if isinstance(dkv3_bot_id, list) and dkv3_bot_id:
            bot_id = dkv3_bot_id[0]
        else:
            bot_id = dkv3_bot_id
        
        if not bot_id:
            logger.error("未在配置中找到 dkv3_bot_id，无法初始化裸模型")
            return None
        
        logger.info(f"Initializing LLM with Coze (bot_id={bot_id}) for generation task.")
        try:
            return get_agent("coze", bot_id=bot_id)
        except Exception as e:
            logger.error(f"Coze LLM (bot_id={bot_id}) 初始化失败: {e}")
            return None

    logger.info(f"Initializing LLM: {model_name}")
    try:
        return get_agent(model_name)
    except Exception as e:
        logger.error(f"LLM {model_name} 初始化失败: {e}")
        return None


def init_embedding_model(model_name: str):
    logger.info(f"Initializing embedding model: {model_name}")
    base_path = config.get('etl.data.base_path', '/data')
    models_subpath = config.get('etl.data.models.path', '/models')
    models_path = base_path + models_subpath
    
    os.environ['HF_HOME'] = models_path
    os.environ['TRANSFORMERS_CACHE'] = models_path
    os.environ['HF_HUB_CACHE'] = models_path
    os.environ['SENTENCE_TRANSFORMERS_HOME'] = models_path
    os.makedirs(models_path, exist_ok=True)
    logger.info(f"Models cache directory set to: {models_path}")
    
    device = 'cpu'
    logger.info("强制使用CPU设备")
    
    logger.info(f"Loading model {model_name} from {models_path} on {device}")
    try:
        return HuggingFaceEmbedding(model_name=model_name, device=device)
    except Exception as e:
        logger.error(f"Failed to initialize embedding model: {e}")
        raise


def init_reranker(model_name: str, pagerank_weight: float):
    logger.info(f"Initializing reranker: {model_name}")
    if "bge-reranker" in model_name.lower():
        return LLMRerank(model=model_name, top_n=10, pagerank_weight=pagerank_weight)
    else:
        return SentenceTransformerRerank(model=model_name, top_n=10, pagerank_weight=pagerank_weight)


def load_stopwords():
    """加载停用词文件"""
    stopwords_path = config.get('etl.retrieval.bm25.stopwords_path')
    try:
        with open(stopwords_path, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f.readlines()]
    except FileNotFoundError:
        logger.warning(f"Stopwords file not found at {stopwords_path}. Returning empty list.")
        return []


def init_vector_retriever(collection_name: str, embed_model):
    logger.info("Initializing QdrantRetriever.")
    qdrant_url = config.get('etl.data.qdrant.url', 'http://localhost:6333')
    qdrant_client = QdrantClient(url=qdrant_url)
    vector_store = QdrantVectorStore(client=qdrant_client, collection_name=collection_name)
    return QdrantRetriever(vector_store=vector_store, embed_model=embed_model, similarity_top_k=10)


def init_bm25_retriever():
    logger.info("Initializing BM25Retriever using fast mode.")
    nodes_path = config.get('etl.retrieval.bm25.nodes_path')
    
    if not nodes_path or not os.path.exists(nodes_path):
        logger.warning(f"BM25节点文件不存在: {nodes_path}. BM25检索器将被禁用.")
        return None
    
    try:
        stopwords = load_stopwords()
        return BM25Retriever.from_pickle_fast(
            nodes_path=nodes_path,
            tokenizer=jieba,
            stopwords=stopwords,
            similarity_top_k=10
        )
    except Exception as e:
        logger.error(f"BM25检索器快速加载失败: {e}")
        return None


def init_hybrid_retriever(vector_retriever, bm25_retriever, pagerank_weight: float):
    """初始化混合检索器"""
    if vector_retriever and bm25_retriever:
        logger.info("Initializing HybridRetriever with vector and BM25 retrievers.")
        return HybridRetriever(
            dense_retriever=vector_retriever,
            sparse_retriever=bm25_retriever,
            pagerank_weight=pagerank_weight
        )
    logger.warning("Cannot initialize HybridRetriever: missing vector or BM25 retriever.")
    return None


def init_es_retriever(index_name: str):
    """初始化Elasticsearch检索器"""
    logger.info("Initializing ElasticsearchRetriever.")
    es_host = config.get('etl.data.elasticsearch.host', 'localhost')
    es_port = config.get('etl.data.elasticsearch.port', 9200)
    try:
        return ElasticsearchRetriever(
            index_name=index_name, 
            es_host=es_host, 
            es_port=es_port, 
            similarity_top_k=10
        )
    except Exception as e:
        logger.warning(f"Failed to initialize ElasticsearchRetriever: {e}. Wildcard search will be disabled.")
        return None 