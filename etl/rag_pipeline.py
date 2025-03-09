from __init__ import *

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
Settings.chunk_size = CHUNK_SIZE
Settings.chunk_overlap = CHUNK_OVERLAP

from qdrant_client import models
from etl.embedding.hf_embeddings import HuggingFaceEmbedding
from etl.embedding.ingestion import (
    read_data, 
    build_pipeline, 
    build_preprocess_pipeline, 
    build_vector_store, 
    build_qdrant_filters,
    get_node_content as _get_node_content
)
from etl.retrieval.rerankers import SentenceTransformerRerank
from etl.retrieval.retrievers import QdrantRetriever, BM25Retriever, HybridRetriever
from etl.embedding.hierarchical import get_leaf_nodes
from etl.utils.template import QA_TEMPLATE, MERGE_TEMPLATE
from etl.embedding.compressors import ContextCompressor
from etl.utils.llm_utils import local_llm_generate as _local_llm_generate
from etl.utils.rag import generation as _generation
from config import Config

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
        # 使用__init__.py中的配置
        self.re_only = RE_ONLY
        self.rerank_fusion_type = RERANK_FUSION_TYPE
        self.ans_refine_type = ANS_REFINE_TYPE
      
        self.reindex = REINDEX
        self.retrieval_type = RETRIEVAL_TYPE
        self.f_topk = F_TOPK
        self.f_topk_1 = F_TOPK_1
        self.f_topk_2 = F_TOPK_2
        self.f_topk_3 = F_TOPK_3
        self.bm25_type = BM25_TYPE
        self.embedding_name = EMBEDDING_NAME

        self.r_topk = R_TOPK
        self.r_topk_1 = R_TOPK_1
        self.r_embed_bs = R_EMBED_BS
        self.reranker_name = RERANKER_NAME
        self.r_use_efficient = R_USE_EFFICIENT

        self.f_embed_type_1 = F_EMBED_TYPE_1
        self.f_embed_type_2 = F_EMBED_TYPE_2
        self.r_embed_type = R_EMBED_TYPE
        self.llm_embed_type = LLM_EMBED_TYPE
        
        # 全局的索引检查操作锁
        self.lock = asyncio.Lock()
        
        # 初始化问答模板
        self.qa_template = QA_TEMPLATE
        self.merge_template = MERGE_TEMPLATE

        self.split_type = SPLIT_TYPE
        self.chunk_size = CHUNK_SIZE
        self.chunk_overlap = CHUNK_OVERLAP
          
        # 设置路径 - 使用__init__.py中定义的路径变量
        self.raw_dir = RAW_PATH
        self.index_dir = INDEX_PATH
        self.qdrant_dir = QDRANT_PATH
        
        self.qdrant_url = QDRANT_URL
        self.collection_name = COLLECTION_NAME
        self.vector_size = VECTOR_SIZE

        self.compress_method = COMPRESS_METHOD
        self.compress_rate = COMPRESS_RATE

        self.hyde_enabled = HYDE_ENABLED
        self.hyde_merging = HYDE_MERGING

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
        """保存索引状态"""
        try:
            if not self.docstore:
                self.logger.warning("空文档存储，跳过保存")
                return
                
            # 确保文件名有效
            valid_chars = re.compile(r'[^\w\-_.]')
            version = datetime.now().strftime('%Y%m%d%H%M%S')
            version = valid_chars.sub('_', version)
            
            # 使用Path对象拼接路径
            backup_path = self.index_dir / f"docstore_{version}.json"
            
            # 确保索引目录存在
            self.index_dir.mkdir(exist_ok=True, parents=True)
            
            # 保存文档存储
            self.docstore.persist(str(backup_path))
            print(f"保存文档存储成功: {backup_path}")
            
            # 管理旧版本的docstore文件，保留最近5个
            try:
                docstore_files = sorted(list(self.index_dir.glob("docstore_*.json")))
                if len(docstore_files) > 5:
                    for old_version in docstore_files[:-5]:
                        try:
                            old_version.unlink()  # 使用Path.unlink()删除文件
                            print(f"删除旧文档存储: {old_version}")
                        except Exception as e:
                            print(f"删除旧文档存储失败: {str(e)}")
            except Exception as e:
                print(f"管理旧版本文档存储失败: {str(e)}")
                
            # 保存应急文档存储
            try:
                emergency_path = self.index_dir / "emergency.json"
                self.docstore.persist(str(emergency_path))
                print(f"保存应急文档存储成功: {emergency_path}")
            except Exception as e:
                print(f"应急存储失败: {str(e)}")
        except Exception as e:
            print(f"保存索引状态失败: {str(e)}")

    async def load_state(self):
        """加载索引状态"""
        try:
            if self.use_embeddings and not self.embeddings:
                self.logger.warning("嵌入模型未初始化，跳过加载索引状态")
                return
                
            # 检查索引目录是否存在
            if not self.index_dir.exists():
                self.logger.warning(f"索引目录不存在: {self.index_dir}")
                return
                
            # 查找所有docstore文件
            docstore_files = sorted(list(self.index_dir.glob("docstore_*.json")))
            if not docstore_files:
                self.logger.warning("未找到文档存储文件")
                return
                
            # 加载最新的文档存储
            latest = docstore_files[-1]
            try:
                self.docstore = SimpleDocumentStore.from_persist_path(str(latest))
                self.logger.info(f"加载文档存储成功: {latest}")
                
                # 如果docstore为空，尝试加载应急文档存储
                if not self.docstore.docs:
                    emergency_path = self.index_dir / "emergency.json"
                    if emergency_path.exists():
                        try:
                            self.docstore = SimpleDocumentStore.from_persist_path(str(emergency_path))
                            self.logger.info("加载应急文档存储成功")
                        except Exception as e:
                            self.logger.error(f"加载应急文档存储失败: {str(e)}")
            except Exception as e:
                self.logger.error(f"加载文档存储失败: {str(e)}")
                
                # 尝试加载应急文档存储
                emergency_path = self.index_dir / "emergency.json"
                if emergency_path.exists():
                    try:
                        self.docstore = SimpleDocumentStore.from_persist_path(str(emergency_path))
                        self.logger.info("加载应急文档存储成功")
                    except Exception as e2:
                        self.logger.error(f"加载应急文档存储失败: {str(e2)}")
        except Exception as e:
            self.logger.error(f"加载索引状态失败: {str(e)}")

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
        if self.hyde_enabled:
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
            if self.hyde_merging and self.hyde_enabled:
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
