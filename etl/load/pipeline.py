import os
# 设置环境变量
os.environ['NLTK_DATA'] = './data/nltk_data/'
os.environ["HF_ENDPOINT"] = "https://hf-api.gitee.com"
os.environ["HF_HOME"] = "./data/models"
os.environ["SENTENCE_TRANSFORMERS_HOME"] = "./data/models"  # sentence-transformers缓存

import sys
import pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parent.parent.parent))
import random
import asyncio
import nest_asyncio
import time
from datetime import datetime

# Initialize Settings and CallbackManager before any llama_index imports
from llama_index.core import Settings
from llama_index.core.callbacks import CallbackManager, LlamaDebugHandler, TokenCountingHandler
from llama_index.core import StorageContext, QueryBundle, PromptTemplate
from llama_index.core.retrievers import AutoMergingRetriever
from llama_index.core.storage.docstore import SimpleDocumentStore

# 初始化回调管理器和全局设置
callback_manager = CallbackManager([
    LlamaDebugHandler(),
    TokenCountingHandler()
])

Settings.callback_manager = callback_manager
Settings.num_output = 512
Settings.chunk_size = 512
Settings.chunk_overlap = 50

from qdrant_client import models
from etl.embedding.gte_embeddings import GTEEmbedding
from etl.embedding.hf_embeddings import HuggingFaceEmbedding
from etl.embedding.ingestion import (
    read_data, 
    build_pipeline, 
    build_preprocess_pipeline, 
    build_vector_store, 
    build_qdrant_filters,
    get_node_content as _get_node_content
)
from etl.retrieval.rerankers import SentenceTransformerRerank, LLMRerank
from etl.retrieval.retrievers import QdrantRetriever, BM25Retriever, HybridRetriever
from etl.embedding.hierarchical import get_leaf_nodes
from etl.utils.template import QA_TEMPLATE, MERGE_TEMPLATE
from etl.embedding.compressors import ContextCompressor
from etl.utils.llm_utils import local_llm_generate as _local_llm_generate
from etl.utils.rag import generation as _generation
from config import Config

def load_stopwords(path):
    with open(path, 'r', encoding='utf-8') as file:
        stopwords = set([line.strip() for line in file])
    return stopwords

def merge_strings(A, B):
    # 找到A的结尾和B的开头最长的匹配子串
    max_overlap = 0
    min_length = min(len(A), len(B))

    for i in range(1, min_length + 1):
        if A[-i:] == B[:i]:
            max_overlap = i

    # 合并A和B，去除重复部分
    merged_string = A + B[max_overlap:]
    return merged_string


nest_asyncio.apply()


class EasyRAGPipeline:
    @classmethod
    async def create(cls):
        """工厂方法创建并初始化管道"""
        pipeline = cls()
        await pipeline.async_init()
        return pipeline

    def __init__(self):
        # 直接使用Config类的get_rag_config方法
        self.config = Config().get_rag_config()
        # 也可以直接从Config()获取单个配置项
        # self.embedding_name = Config().get("embedding_name", "BAAI/bge-large-zh-v1.5")
        
        # Initialize callback manager first
        if Settings.callback_manager is None:
            Settings.callback_manager = callback_manager
        
        self.re_only = self.config.get('re_only', False)
        self.rerank_fusion_type = self.config.get('rerank_fusion_type', 1)
        self.ans_refine_type = self.config.get('ans_refine_type', 0)
      
        self.reindex = self.config.get('reindex', False)
        self.retrieval_type = self.config.get('retrieval_type', 3)
        self.f_topk = self.config.get('f_topk', 128)
        self.f_topk_1 = self.config.get('f_topk_1', 128)
        self.f_topk_2 = self.config.get('f_topk_2', 288)
        self.f_topk_3 = self.config.get('f_topk_3', 6)
        self.bm25_type = self.config.get('bm25_type', 1)
        self.embedding_name = self.config.get('embedding_name', 'BAAI/bge-large-zh-v1.5')

        self.r_topk = self.config.get('r_topk', 6)
        self.r_topk_1 = self.config.get('r_topk_1', 6)
        self.r_embed_bs = self.config.get('r_embed_bs', 32)
        self.reranker_name = self.config.get('reranker_name', "cross-encoder/stsb-distilroberta-base")

        self.f_embed_type_1 = self.config.get('f_embed_type_1', 1)
        self.f_embed_type_2 = self.config.get('f_embed_type_2', 2)
        self.r_embed_type = self.config.get('r_embed_type', 1)
        
        # 初始化问答模板
        self.qa_template = QA_TEMPLATE
        self.merge_template = MERGE_TEMPLATE

        self.split_type = self.config.get('split_type', 0)
        self.chunk_size = self.config.get('chunk_size', 512)
        self.chunk_overlap = self.config.get('chunk_overlap', 200)
          
        # 从配置文件获取存储路径
        data_config = self.config.get('data', {})
        
        # 设置原始数据路径
        raw_config = data_config.get('raw', {})
        self.raw_dir = os.path.abspath(raw_config.get('path', 'data/raw'))
        
        # 设置索引数据路径
        index_config = data_config.get('index', {})
        self.index_dir = os.path.abspath(index_config.get('path', 'data/index'))
        
        # 设置Qdrant存储路径
        qdrant_config = data_config.get('qdrant', {})
        self.qdrant_url = qdrant_config.get('url')
        self.qdrant_dir = os.path.abspath(qdrant_config.get('path', 'data/qdrant'))
        self.collection_name = qdrant_config.get('collection', 'main_index')
        self.vector_size = qdrant_config.get('vector_size', 1024)

        self.compress_method = self.config.get('compress_method', "")
        self.compress_rate = self.config.get('compress_rate', 0.5)

        self.hyde = self.config.get('hyde', False)
        self.hyde_merging = self.config.get('hyde_merging', False)

        self.qdrant_client = None

    async def __aenter__(self):
        """异步上下文管理器入口"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口，确保资源正确关闭"""
        if self.qdrant_client is not None:
            await self.qdrant_client.close()
            self.qdrant_client = None

    async def save_state(self):
        """双持久化存储：保存Qdrant快照和文档存储"""
        try:
            # 确保索引目录存在
            os.makedirs(self.index_dir, exist_ok=True)
            
            # Qdrant原生快照
            if hasattr(self, 'qdrant_client') and self.qdrant_client is not None:
                try:
                    # 创建带时间戳的快照名称
                    snapshot_name = f"snapshot_{datetime.now().strftime('%Y%m%d%H%M%S')}"
                    await self.qdrant_client.create_snapshot(
                        collection_name=self.collection_name,
                        snapshot_name=snapshot_name
                    )
                    print(f"创建Qdrant快照成功: {snapshot_name}")
                    
                    # 管理快照数量，保留最近3个
                    try:
                        snapshots = await self.qdrant_client.list_snapshots(collection_name=self.collection_name)
                        if len(snapshots) > 3:
                            for old_snapshot in snapshots[:-3]:
                                try:
                                    await self.qdrant_client.delete_snapshot(
                                        collection_name=self.collection_name,
                                        snapshot_name=old_snapshot.name
                                    )
                                    print(f"删除旧快照: {old_snapshot.name}")
                                except Exception as e:
                                    print(f"删除旧快照失败: {str(e)}")
                    except Exception as e:
                        print(f"管理Qdrant快照失败: {str(e)}")
                except Exception as e:
                    print(f"创建Qdrant快照失败: {str(e)}")
            
            # 文档存储版本控制
            if hasattr(self, 'docstore') and self.docstore is not None:
                # 仅当docstore非空时才保存
                if len(self.docstore.docs) > 0:
                    version = datetime.now().strftime("%Y%m%d%H%M%S")
                    backup_path = os.path.join(self.index_dir, f"docstore_{version}.json")
                    try:
                        # 确保索引目录存在
                        os.makedirs(os.path.dirname(backup_path), exist_ok=True)
                        print(f"正在保存文档存储到{backup_path}...")
                        
                        # 检查docstore.apersist方法是否存在
                        if hasattr(self.docstore, 'apersist'):
                            await self.docstore.apersist(backup_path)
                        elif hasattr(self.docstore, 'persist'):
                            # 如果没有异步方法，回退到同步方法
                            self.docstore.persist(backup_path)
                        else:
                            print("警告：文档存储没有persist或apersist方法")
                            # 实现简单的JSON序列化
                            import json
                            try:
                                # 尝试简单序列化文档ID和内容
                                doc_dict = {node_id: node.to_dict() for node_id, node in self.docstore.docs.items()}
                                with open(backup_path, 'w', encoding='utf-8') as f:
                                    json.dump(doc_dict, f, ensure_ascii=False, indent=2)
                            except Exception as e:
                                print(f"简单序列化文档存储失败: {str(e)}")
                                raise
                                
                        print(f"文档存储已保存到{backup_path}，包含{len(self.docstore.docs)}个文档")
                        
                        # 维护最近3个版本
                        versions = sorted([f for f in os.listdir(self.index_dir) 
                                        if f.startswith("docstore_")])
                        for old_version in versions[:-3]:
                            try:
                                os.remove(os.path.join(self.index_dir, old_version))
                                print(f"删除旧版本{old_version}")
                            except Exception as e:
                                print(f"删除旧版本{old_version}失败: {str(e)}")
                    except Exception as e:
                        print(f"保存文档存储失败: {str(e)}")
                        # 应急存储
                        emergency_path = os.path.join(self.index_dir, "emergency.json")
                        try:
                            if hasattr(self.docstore, 'apersist'):
                                await self.docstore.apersist(emergency_path)
                            elif hasattr(self.docstore, 'persist'):
                                self.docstore.persist(emergency_path)
                            else:
                                # 简单序列化
                                import json
                                doc_dict = {node_id: node.to_dict() for node_id, node in self.docstore.docs.items()}
                                with open(emergency_path, 'w', encoding='utf-8') as f:
                                    json.dump(doc_dict, f, ensure_ascii=False, indent=2)
                            print(f"应急存储已保存到{emergency_path}")
                        except Exception as e:
                            print(f"应急存储失败: {str(e)}")
                else:
                    print("文档存储为空，跳过保存")
            else:
                print("文档存储不可用，跳过保存")

        except Exception as e:
            print(f"持久化失败: {str(e)}")

    async def load_state(self):
        """状态加载"""
        try:
            # 确保索引目录存在
            os.makedirs(self.index_dir, exist_ok=True)
            
            # 加载最新索引存储
            versions = []
            if os.path.exists(self.index_dir):
                versions = [f for f in os.listdir(self.index_dir) 
                           if f.startswith("docstore_")]
                
            if versions:
                try:
                    latest = sorted(versions)[-1]
                    latest_path = os.path.join(self.index_dir, latest)
                    print(f"尝试从{latest_path}加载索引存储...")
                    
                    # 尝试使用SimpleDocumentStore.from_persist_path方法
                    try:
                        self.docstore = SimpleDocumentStore.from_persist_path(
                            latest_path
                        )
                        print(f"从{latest}加载索引存储成功，包含{len(self.docstore.docs)}个文档")
                    except (ImportError, AttributeError) as e:
                        print(f"通过from_persist_path加载失败: {str(e)}")
                        # 尝试手动解析JSON文件
                        try:
                            import json
                            from llama_index.core.schema import TextNode
                            
                            with open(latest_path, 'r', encoding='utf-8') as f:
                                docs_data = json.load(f)
                            
                            self.docstore = SimpleDocumentStore()
                            
                            # 检查数据格式并相应处理
                            if isinstance(docs_data, dict):
                                for node_id, node_data in docs_data.items():
                                    try:
                                        if isinstance(node_data, dict):
                                            # 尝试从字典创建TextNode
                                            node = TextNode.from_dict(node_data)
                                            self.docstore.add_documents([node])
                                        else:
                                            print(f"警告：节点数据格式不正确: {type(node_data)}")
                                    except Exception as node_e:
                                        print(f"加载节点{node_id}失败: {str(node_e)}")
                            else:
                                print(f"警告：文档存储格式不正确: {type(docs_data)}")
                                
                            print(f"通过手动解析从{latest}加载索引存储成功，包含{len(self.docstore.docs)}个文档")
                        except Exception as json_e:
                            print(f"手动解析JSON失败: {str(json_e)}")
                            raise
                except Exception as e:
                    print(f"加载最新索引存储失败: {str(e)}")
                    # 尝试加载应急备份
                    emergency_path = os.path.join(self.index_dir, "emergency.json")
                    if os.path.exists(emergency_path):
                        try:
                            # 尝试标准加载
                            try:
                                self.docstore = SimpleDocumentStore.from_persist_path(emergency_path)
                                print(f"从应急备份加载索引存储成功，包含{len(self.docstore.docs)}个文档")
                            except Exception:
                                # 尝试手动解析
                                import json
                                from llama_index.core.schema import TextNode
                                
                                with open(emergency_path, 'r', encoding='utf-8') as f:
                                    docs_data = json.load(f)
                                
                                self.docstore = SimpleDocumentStore()
                                
                                if isinstance(docs_data, dict):
                                    for node_id, node_data in docs_data.items():
                                        try:
                                            if isinstance(node_data, dict):
                                                node = TextNode.from_dict(node_data)
                                                self.docstore.add_documents([node])
                                        except Exception as node_e:
                                            print(f"加载应急节点{node_id}失败: {str(node_e)}")
                                
                                print(f"通过手动解析从应急备份加载索引存储成功，包含{len(self.docstore.docs)}个文档")
                        except Exception as e:
                            print(f"加载应急备份失败: {str(e)}")
                            print("初始化空索引存储")
                            self.docstore = SimpleDocumentStore()
                    else:
                        print("没有找到应急备份，初始化空索引存储")
                        self.docstore = SimpleDocumentStore()
            else:
                print("没有找到索引存储文件，初始化空索引存储")
                self.docstore = SimpleDocumentStore()
                
            # 尝试加载Qdrant快照(如果可用)
            if hasattr(self, 'qdrant_client') and self.qdrant_client is not None:
                try:
                    snapshots = await self.qdrant_client.list_snapshots(collection_name=self.collection_name)
                    if snapshots:
                        # 不自动恢复快照，只提示存在
                        print(f"Qdrant有{len(snapshots)}个可用快照，最新的是{snapshots[-1].name}")
                except Exception as e:
                    print(f"查询Qdrant快照失败: {str(e)}")
                    
        except Exception as e:
            print(f"状态加载失败: {str(e)}")
            print("初始化空索引存储")
            self.docstore = SimpleDocumentStore()

    async def async_init(self):
        # Initialize callback manager
        if Settings.callback_manager is None:
            Settings.callback_manager = callback_manager
            
        # 初始化 docstore
        self.docstore = SimpleDocumentStore()
            
        # Load existing state
        await self.load_state()
        
        self.embedding = HuggingFaceEmbedding(
            model_name=self.embedding_name,
            embed_batch_size=128,
            embed_type=self.f_embed_type_1
        )
        Settings.embed_model = self.embedding

        # 文档预处理成节点
        documents = read_data(self.raw_dir)

        print(f"文档读入完成，一共有{len(documents)}个文档")
        vector_store = None

        client, vector_store = await build_vector_store(
            qdrant_url=self.qdrant_url,
            reindex=self.reindex,
            collection_name=self.collection_name,
            vector_size=self.vector_size,
        )
        
        # 保存 qdrant_client 用于后续持久化
        self.qdrant_client = client

        collection_info = await client.get_collection(
            collection_name=self.collection_name,
        )
        self.llm = None
        
        # 初始化密集检索器 - 无论集合是否为空都需要初始化
        if self.embedding is not None:
            f_topk_1 = self.f_topk_1
            self.dense_retriever = QdrantRetriever(vector_store, self.embedding, similarity_top_k=f_topk_1)
            print(f"创建{self.embedding_name}密集检索器成功")
        
        if collection_info.points_count == 0:
            pipeline = build_pipeline(
                self.llm, 
                self.embedding, 
                vector_store=vector_store, 
                data_path=self.raw_dir,
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap,
                callback_manager=callback_manager
            )
            # 暂时停止实时索引
            await client.update_collection(
                collection_name=self.collection_name,
                optimizer_config=models.OptimizersConfigDiff(indexing_threshold=0),
            )
            nodes = await pipeline.arun(documents=documents, show_progress=True, num_workers=1)
            # 恢复实时索引
            await client.update_collection(
                collection_name=self.collection_name,
                optimizer_config=models.OptimizersConfigDiff(indexing_threshold=20000),
            )
            print(f"索引建立完成，一共有{len(nodes)}个节点")

            preprocess_pipeline = build_preprocess_pipeline(
                self.raw_dir,
                self.chunk_size,
                self.chunk_overlap,
                self.split_type,
                callback_manager=callback_manager
            )
            nodes_ = await preprocess_pipeline.arun(documents=documents, show_progress=True, num_workers=1)
            print(f"索引已建立，一共有{len(nodes_)}个节点")

            # 加载稀疏检索
            self.stp_words = load_stopwords("./data/hit_stopwords.txt")
            import jieba
            self.sparse_tk = jieba.Tokenizer()
            if self.split_type == 1:
                self.nodes = get_leaf_nodes(nodes_)
                print("叶子节点数量:", len(self.nodes))
                self.docstore = SimpleDocumentStore()
                self.docstore.add_documents(self.nodes)
                storage_context = StorageContext.from_defaults(docstore=self.docstore)
            else:
                self.nodes = nodes_
                self.docstore.add_documents(self.nodes)
            
            # 保存初始化的docstore
            os.makedirs(self.index_dir, exist_ok=True)
            await self.save_state()
            
            self.sparse_retriever = BM25Retriever.from_defaults(
                nodes=self.nodes,
                tokenizer=self.sparse_tk,
                similarity_top_k=self.f_topk_2,
                stopwords=self.stp_words,
                embed_type=self.f_embed_type_2,
                bm25_type=self.bm25_type,
            )

            if self.f_topk_3 != 0:
                self.path_retriever = BM25Retriever.from_defaults(
                    nodes=self.nodes,
                    tokenizer=self.sparse_tk,
                    similarity_top_k=self.f_topk_3,
                    stopwords=self.stp_words,
                    embed_type=5,  # 4-->file_path 5-->know_path
                    bm25_type=self.bm25_type,
                )
            else:
                self.path_retriever = None

            if self.split_type == 1:
                self.sparse_retriever = AutoMergingRetriever(
                    self.sparse_retriever,
                    storage_context,
                    simple_ratio_thresh=0.4
                )
            print("创建BM25稀疏检索器成功")

            # 创建node快速索引
            self.nodeid2idx = dict()
            for i, node in enumerate(self.nodes):
                self.nodeid2idx[node.node_id] = i

            # 创建检索器
            if self.retrieval_type == 1:
                self.retriever = self.dense_retriever
            elif self.retrieval_type == 2:
                self.retriever = self.sparse_retriever
            elif self.retrieval_type == 3:
                f_topk = self.f_topk
                self.retriever = HybridRetriever(
                    dense_retriever=self.dense_retriever,
                    sparse_retriever=self.sparse_retriever,
                    retrieval_type=self.retrieval_type,  # 1-dense 2-sparse 3-hybrid
                    topk=f_topk,
                )
                print("创建混合检索器成功")
        else:
            # 如果集合已存在，需要从存储加载相关数据
            # 加载稀疏检索所需数据
            self.stp_words = load_stopwords("./data/hit_stopwords.txt")
            import jieba
            self.sparse_tk = jieba.Tokenizer()
            
            # 使用docstore中的节点
            if hasattr(self, 'docstore') and self.docstore is not None:
                self.nodes = list(self.docstore.docs.values())
                print(f"从docstore加载了{len(self.nodes)}个节点")
                
                # 只有当有节点时才创建检索器
                if len(self.nodes) > 0:
                    # 创建node快速索引
                    self.nodeid2idx = dict()
                    for i, node in enumerate(self.nodes):
                        self.nodeid2idx[node.node_id] = i
                    
                    # 初始化检索器
                    self.sparse_retriever = BM25Retriever.from_defaults(
                        nodes=self.nodes,
                        tokenizer=self.sparse_tk,
                        similarity_top_k=self.f_topk_2,
                        stopwords=self.stp_words,
                        embed_type=self.f_embed_type_2,
                        bm25_type=self.bm25_type,
                    )
                    print("创建BM25稀疏检索器成功")
                    
                    if self.f_topk_3 != 0:
                        self.path_retriever = BM25Retriever.from_defaults(
                            nodes=self.nodes,
                            tokenizer=self.sparse_tk,
                            similarity_top_k=self.f_topk_3,
                            stopwords=self.stp_words,
                            embed_type=5,
                            bm25_type=self.bm25_type,
                        )
                    else:
                        self.path_retriever = None
                    
                    if self.split_type == 1:
                        storage_context = StorageContext.from_defaults(docstore=self.docstore)
                        self.sparse_retriever = AutoMergingRetriever(
                            self.sparse_retriever,
                            storage_context,
                            simple_ratio_thresh=0.4
                        )
                    
                    # 创建检索器
                    if self.retrieval_type == 1:
                        self.retriever = self.dense_retriever
                    elif self.retrieval_type == 2:
                        self.retriever = self.sparse_retriever
                    elif self.retrieval_type == 3:
                        f_topk = self.f_topk
                        self.retriever = HybridRetriever(
                            dense_retriever=self.dense_retriever,
                            sparse_retriever=self.sparse_retriever,
                            retrieval_type=self.retrieval_type,
                            topk=f_topk,
                        )
                        print("创建混合检索器成功")
                else:
                    print("docstore中没有节点，将重新生成节点和检索器")
                    
                    # 在docstore为空但collection已存在的情况下，重新生成节点
                    if collection_info.points_count > 0 and len(documents) > 0:
                        print(f"集合中有{collection_info.points_count}个点，但docstore为空，重新生成节点")
                        
                        # 重新创建节点
                        preprocess_pipeline = build_preprocess_pipeline(
                            self.raw_dir,
                            self.chunk_size,
                            self.chunk_overlap,
                            self.split_type,
                            callback_manager=callback_manager
                        )
                        nodes_ = await preprocess_pipeline.arun(documents=documents, show_progress=True, num_workers=1)
                        print(f"重新生成了{len(nodes_)}个节点")
                        
                        # 加载稀疏检索
                        self.stp_words = load_stopwords("./data/hit_stopwords.txt")
                        import jieba
                        self.sparse_tk = jieba.Tokenizer()
                        
                        if self.split_type == 1:
                            self.nodes = get_leaf_nodes(nodes_)
                            print("叶子节点数量:", len(self.nodes))
                            self.docstore = SimpleDocumentStore()
                            self.docstore.add_documents(self.nodes)
                            storage_context = StorageContext.from_defaults(docstore=self.docstore)
                        else:
                            self.nodes = nodes_
                            self.docstore.add_documents(self.nodes)
                        
                        # 保存初始化的docstore
                        os.makedirs(self.index_dir, exist_ok=True)
                        await self.save_state()
                        print(f"成功保存了docstore，包含{len(self.docstore.docs)}个文档")
                        
                        # 创建node快速索引
                        self.nodeid2idx = dict()
                        for i, node in enumerate(self.nodes):
                            self.nodeid2idx[node.node_id] = i
                        
                        # 初始化检索器
                        self.sparse_retriever = BM25Retriever.from_defaults(
                            nodes=self.nodes,
                            tokenizer=self.sparse_tk,
                            similarity_top_k=self.f_topk_2,
                            stopwords=self.stp_words,
                            embed_type=self.f_embed_type_2,
                            bm25_type=self.bm25_type,
                        )
                        print("创建BM25稀疏检索器成功")
                        
                        if self.f_topk_3 != 0:
                            self.path_retriever = BM25Retriever.from_defaults(
                                nodes=self.nodes,
                                tokenizer=self.sparse_tk,
                                similarity_top_k=self.f_topk_3,
                                stopwords=self.stp_words,
                                embed_type=5,
                                bm25_type=self.bm25_type,
                            )
                        else:
                            self.path_retriever = None
                        
                        if self.split_type == 1:
                            self.sparse_retriever = AutoMergingRetriever(
                                self.sparse_retriever,
                                storage_context,
                                simple_ratio_thresh=0.4
                            )
                        
                        # 创建检索器
                        if self.retrieval_type == 1:
                            self.retriever = self.dense_retriever
                        elif self.retrieval_type == 2:
                            self.retriever = self.sparse_retriever
                        elif self.retrieval_type == 3:
                            f_topk = self.f_topk
                            self.retriever = HybridRetriever(
                                dense_retriever=self.dense_retriever,
                                sparse_retriever=self.sparse_retriever,
                                retrieval_type=self.retrieval_type,
                                topk=f_topk,
                            )
                            print("创建混合检索器成功")
                    else:
                        print("docstore中没有节点，将使用默认密集检索器")
                        self.nodes = []
                        self.retriever = self.dense_retriever
                        self.sparse_retriever = None
                        self.path_retriever = None
            else:
                print("警告：docstore不可用，将使用默认密集检索器")
                self.nodes = []
                self.retriever = self.dense_retriever
                self.sparse_retriever = None
                self.path_retriever = None

        # 创建重排器
        self.reranker = None
       
        if(self.reranker_name): 
            self.reranker = SentenceTransformerRerank(
                top_n=self.r_topk,
                model=self.reranker_name,
            )
            print(f"创建{self.reranker_name}重排器成功")
     
        if self.compress_method:
            self.compressor = ContextCompressor(
                self.compress_method,
                self.compress_rate,
                self.sparse_retriever,
            )
        else:
            self.compressor = None

        print("EasyRAGPipeline 初始化完成".center(60, "="))
        
        return self

    def build_query_bundle(self, query_str):
        query_bundle = QueryBundle(query_str=query_str)
        return query_bundle

    def build_prompt_template(self, qa_template):
        return PromptTemplate(qa_template)

    def build_filters(self, query):
        filters = None
        filter_dict = None
        if "document" in query and query["document"] != "":
            dir = query['document']
            filters = build_qdrant_filters(
                dir=dir
            )
            filter_dict = {
                "dir": dir
            }
        return filters, filter_dict

    async def generation(self, llm, fmt_qa_prompt):
        # 如果llm为None，返回默认响应
        if llm is None:
            from llama_index.core.llms import CompletionResponse
            return CompletionResponse(text="仅检索模式，未配置LLM")
        return await _generation(llm, fmt_qa_prompt)

    def get_node_content(self, node) -> str:
        return _get_node_content(node, embed_type=self.r_embed_type, nodes=self.nodes, nodeid2idx=self.nodeid2idx)

    def local_llm_generate(self, query):
        return _local_llm_generate(query, self.local_llm_model, self.local_llm_tokenizer)

    async def run(self, query: dict) -> dict:
        '''
        "query":"问题" #必填
        "document": "所属路径" #用于过滤文档，可选
        '''
        if self.hyde:
            hyde_query = self.hyde_transform(query["query"])
            query["hyde_query"] = hyde_query.custom_embedding_strs[0]
        self.filters, self.filter_dict = self.build_filters(query)
        
        # 检查是否有可用的检索器
        if not hasattr(self, 'retriever') or self.retriever is None:
            return {"answer": "系统尚未准备好，请先添加一些文档。", "nodes": [], "contexts": []}
        
        # 设置re_only参数，如果配置为True，则仅检索不生成答案
        original_re_only = self.re_only
        if self.re_only:
            # 无需修改self.re_only，直接在generation方法中使用
            print("仅检索模式，不生成答案")
        
        if self.rerank_fusion_type == 0:
            self.retriever.filters = self.filters
            self.retriever.filter_dict = self.filter_dict
            res = await self.generation_with_knowledge_retrieval(
                query_str=query["query"],
                hyde_query=query.get("hyde_query", "")
            )
        else:
            # 设置密集检索器的过滤器
            if hasattr(self, 'dense_retriever') and self.dense_retriever is not None:
                self.dense_retriever.filters = self.filters
            
            # 设置稀疏检索器的过滤器字典（如果存在）
            if hasattr(self, 'sparse_retriever') and self.sparse_retriever is not None:
                self.sparse_retriever.filter_dict = self.filter_dict
                # 使用融合重排
                res = await self.generation_with_rerank_fusion(
                    query_str=query["query"],
                )
            else:
                # 如果稀疏检索器不可用，使用密集检索器
                print("稀疏检索器不可用，使用密集检索")
                self.retriever = self.dense_retriever
                res = await self.generation_with_knowledge_retrieval(
                    query_str=query["query"],
                    hyde_query=query.get("hyde_query", "")
                )
        
        # 恢复原始re_only设置
        self.re_only = original_re_only
        
        return res

    def sort_by_retrieval(self, nodes):
        new_nodes = sorted(nodes, key=lambda x: -x.node.metadata['retrieval_score'] if x.score else 0)
        return new_nodes

    async def generation_with_knowledge_retrieval(
            self,
            query_str: str,
            hyde_query: str=""
    ):
        query_bundle = self.build_query_bundle(query_str+hyde_query)
        
        # 添加对sparse_retriever是否为None的检查
        if self.sparse_retriever is None:
            # 如果sparse_retriever不可用，使用dense_retriever
            node_with_scores = await self.dense_retriever.aretrieve(query_bundle)
        else:
            node_with_scores = await self.sparse_retriever.aretrieve(query_bundle)
            
        if self.path_retriever is not None:
            node_with_scores_path = await self.path_retriever.aretrieve(query_bundle)
        else:
            node_with_scores_path = []
            
        # 只有在有内容时才进行融合，否则直接使用已有结果
        if node_with_scores_path:
            node_with_scores = HybridRetriever.fusion([
                node_with_scores,
                node_with_scores_path,
            ])
        # 如果path_retriever为空，则不需要融合直接使用node_with_scores
        if self.reranker and node_with_scores and len(node_with_scores) > 0:
            if self.hyde_merging and self.hyde:
                hyde_query_top1_chunk = f'问题：{query_str},\n 可能有用的提示文档:{hyde_query},\n ' \
                                        f'检索得到的相关上下文：{self.get_node_content(node_with_scores[0])}'
                hyde_merging_query_bundle = self.hyde_transform_merging(hyde_query_top1_chunk)
                query_bundle = self.build_query_bundle(query_str + "\n" + hyde_merging_query_bundle.custom_embedding_strs[0])

            node_with_scores = self.reranker.postprocess_nodes(node_with_scores, query_bundle)
            
        if not node_with_scores:
            return {"answer": "未找到相关文档", "nodes": [], "contexts": []}
            
        contents = [self.get_node_content(node=node) for node in node_with_scores]
        
        # 检查contents是否为空
        if not contents:
            return {"answer": "未找到相关内容", "nodes": node_with_scores, "contexts": []}
            
        context_str = "\n\n".join(
            [f"### 文档{i}: {content}" for i, content in enumerate(contents)]
        )
        if self.re_only:
            return {"answer": "", "nodes": node_with_scores, "contexts": contents}
        fmt_qa_prompt = self.qa_template.format(
            context_str=context_str, query_str=query_str
        )
        ret = await self.generation(self.llm, fmt_qa_prompt)
        if self.ans_refine_type == 1:
            fmt_merge_prompt = self.merge_template.format(
                context_str=contents[0], query_str=query_str, answer_str=ret.text
            )
            ret = await self.generation(self.llm, fmt_merge_prompt)
        elif self.ans_refine_type == 2:
            ret.text = ret.text + "\n\n" + contents[0]
        return {"answer": ret.text, "nodes": node_with_scores, "contexts": contents}

    async def generation_with_rerank_fusion(
            self,
            query_str: str,
    ):
        query_bundle = self.build_query_bundle(query_str)
        
        # 检查稀疏检索器是否可用
        if self.sparse_retriever is None:
            # 如果不可用，只使用密集检索器
            dense_node_with_scores = await self.dense_retriever.aretrieve(query_bundle)
            if self.reranker:
                # 使用正确的postprocess_nodes方法
                dense_node_with_scores = self.reranker.postprocess_nodes(dense_node_with_scores, query_bundle)
            # 当稀疏检索器不可用时，设置空的稀疏结果
            sparse_node_with_scores = []
            # 所有处理都使用密集检索结果
            node_with_scores = dense_node_with_scores
        else:
            # 原有的融合重排逻辑
            dense_node_with_scores = await self.dense_retriever.aretrieve(query_bundle)
            sparse_node_with_scores = await self.sparse_retriever.aretrieve(query_bundle)
            if self.path_retriever is not None:
                path_node_with_scores = await self.path_retriever.aretrieve(query_bundle)
            else:
                path_node_with_scores = []
            
            # 融合检索结果
            # 过滤掉空列表，防止融合出错
            retrievers_results = []
            if len(dense_node_with_scores) > 0:
                retrievers_results.append(dense_node_with_scores)
            if len(sparse_node_with_scores) > 0:
                retrievers_results.append(sparse_node_with_scores)
            if len(path_node_with_scores) > 0:
                retrievers_results.append(path_node_with_scores)
                
            if len(retrievers_results) > 1:
                # 只有当有多个非空结果时才进行融合
                node_with_scores = HybridRetriever.fusion(retrievers_results)
            elif len(retrievers_results) == 1:
                # 如果只有一个非空结果，直接使用
                node_with_scores = retrievers_results[0]
            else:
                # 所有结果都为空，返回空列表
                node_with_scores = []
                
            # 应用重排器
            if self.reranker and node_with_scores and len(node_with_scores) > 0:
                # 使用正确的postprocess_nodes方法
                node_with_scores = self.reranker.postprocess_nodes(node_with_scores, query_bundle)

        if not node_with_scores:
            return {"answer": "未找到相关文档", "nodes": [], "contexts": []}
            
        contents = [self.get_node_content(node) for node in node_with_scores]
        if not contents:
            return {"answer": "未找到相关内容", "nodes": node_with_scores, "contexts": []}

        # 如果是仅检索模式，直接返回结果而不生成答案
        if self.re_only:
            return {"answer": "", "nodes": node_with_scores, "contexts": contents}
            
        # 以下是生成答案的逻辑
        if self.rerank_fusion_type == 1:
            # 使用融合后的结果生成答案
            context_str = "\n\n".join(
                [f"### 文档{i}: {content}" for i, content in enumerate(contents)]
            )
            fmt_qa_prompt = self.qa_template.format(
                context_str=context_str, query_str=query_str
            )
            ret = await self.generation(self.llm, fmt_qa_prompt)
        else:
            # 分别使用稀疏和密集检索结果生成答案
            # 如果稀疏检索结果为空（稀疏检索器为None的情况），使用空列表
            if not sparse_node_with_scores:
                contents_sparse = []
                context_str_sparse = "没有相关稀疏检索结果"
                fmt_qa_prompt_sparse = self.qa_template.format(
                    context_str=context_str_sparse, query_str=query_str
                )
                # 创建一个简单的响应对象，模拟llm生成的结果
                class SimpleResponse:
                    def __init__(self, text):
                        self.text = text
                    
                    def __add__(self, other):
                        # 支持与其他响应对象相加
                        result = SimpleResponse(self.text + "\n\n" + other.text)
                        return result
                
                ret_sparse = SimpleResponse("没有相关稀疏检索结果")
            else:
                contents_sparse = [self.get_node_content(node) for node in sparse_node_with_scores]
                if not contents_sparse:
                    contents_sparse = []
                    context_str_sparse = "无法获取稀疏检索结果内容"
                else:
                    context_str_sparse = "\n\n".join(
                        [f"### 文档{i}: {content}" for i, content in enumerate(contents_sparse)]
                    )
                fmt_qa_prompt_sparse = self.qa_template.format(
                    context_str=context_str_sparse, query_str=query_str
                )
                ret_sparse = await self.generation(self.llm, fmt_qa_prompt_sparse)

            contents_dense = [self.get_node_content(node) for node in dense_node_with_scores]
            if not contents_dense:
                contents_dense = []
                context_str_dense = "无法获取密集检索结果内容"
            else:
                context_str_dense = "\n\n".join(
                    [f"### 文档{i}: {content}" for i, content in enumerate(contents_dense)]
                )
            fmt_qa_prompt_dense = self.qa_template.format(
                context_str=context_str_dense, query_str=query_str
            )
            ret_dense = await self.generation(self.llm, fmt_qa_prompt_dense)

            if self.rerank_fusion_type == 2:
                # 选择较长的回答
                ret = ret_dense if len(ret_dense.text) >= len(ret_sparse.text) else ret_sparse
                contents = contents_dense if len(ret_dense.text) >= len(ret_sparse.text) else contents_sparse
            else:
                # 合并两个回答
                ret = ret_sparse + ret_dense
                contents = contents_sparse + contents_dense

        return {"answer": ret.text, "nodes": node_with_scores, "contexts": contents}


if __name__ == "__main__":
    import asyncio
    
    async def main():
        try:
            print("正在初始化EasyRAG Pipeline...")
            async with await EasyRAGPipeline.create() as pipeline:  # 使用异步上下文管理器
                print(f"初始化完成，RAG系统状态:")
                print(f"- 是否存在稀疏检索器: {hasattr(pipeline, 'sparse_retriever') and pipeline.sparse_retriever is not None}")
                print(f"- 是否存在密集检索器: {hasattr(pipeline, 'dense_retriever') and pipeline.dense_retriever is not None}")
                print(f"- docstore中节点数: {len(pipeline.docstore.docs) if hasattr(pipeline, 'docstore') and pipeline.docstore is not None else 0}")
                print(f"- 使用的检索器类型: {type(pipeline.retriever).__name__ if hasattr(pipeline, 'retriever') else '无'}")
                
                query = {
                    "query": "2月的文章"
                }
                print(f"\n正在处理查询: '{query['query']}'")
                res = await pipeline.run(query)
                
                # 打印结果
                print("\n查询结果:")
                print(f"找到的上下文数量: {len(res.get('contexts', []))}")
                
                # 输出检索到的文档内容
                contexts = res.get('contexts', [])
                if contexts:
                    print("\n检索到的文档内容:")
                    for i, content in enumerate(contexts):
                        print(f"\n--- 文档 {i+1} ---")
                        print(content)
                else:
                    print("未检索到相关文档")
                
                print(f"\n答案: {res.get('answer', '无答案')}")
                
        except Exception as e:
            import traceback
            print(f"运行中出现错误: {str(e)}")
            traceback.print_exc()
    
    try:
        # 处理Windows上asyncio的异常
        if hasattr(asyncio, 'WindowsSelectorEventLoopPolicy'):
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n程序被用户中断")
    except Exception as e:
        import traceback
        print(f"主线程错误: {str(e)}")
        traceback.print_exc()
