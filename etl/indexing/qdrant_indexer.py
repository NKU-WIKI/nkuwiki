"""
Qdrant向量索引构建器

负责从MySQL数据构建Qdrant向量检索索引。
"""

import os
import sys
import logging
import asyncio
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
import aiofiles
import aiofiles.os
from tqdm.asyncio import tqdm

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from config import Config
from etl.load import db_core
from etl.embedding.hf_embeddings import HuggingFaceEmbedding
from llama_index.core.schema import BaseNode, TextNode
from llama_index.core import VectorStoreIndex, StorageContext
from llama_index.vector_stores.qdrant import QdrantVectorStore
from qdrant_client import QdrantClient, models, AsyncQdrantClient
# 导入ETL模块的统一路径配置
from etl import QDRANT_URL, COLLECTION_NAME, VECTOR_SIZE, MODELS_PATH, RAW_PATH

logger = logging.getLogger(__name__)


class QdrantIndexer:
    """Qdrant向量索引构建器
    
    负责从MySQL数据构建Qdrant向量检索索引，支持语义嵌入和文本分块。
    """
    
    def __init__(self, config: Dict[str, Any], logger: Optional[logging.Logger] = None):
        self.config = config
        self.logger = logger or logging.getLogger(__name__)
        
        # 使用ETL模块统一配置的参数
        self.collection_name = config.get('etl.data.qdrant.collection', COLLECTION_NAME)
        self.qdrant_url = config.get('etl.data.qdrant.url', QDRANT_URL)
        self.embedding_model = config.get('etl.embedding.name', 'BAAI/bge-large-zh-v1.5')
        self.vector_size = config.get('etl.data.qdrant.vector_size', VECTOR_SIZE)
        self.chunk_size = config.get('etl.chunking.chunk_size', 512)
        self.chunk_overlap = config.get('etl.chunking.chunk_overlap', 200)
        
    async def build_indexes(self, 
                     limit: int = None, 
                     batch_size: int = 100,
                     test_mode: bool = False,
                     data_source: str = "raw_files",
                     start_batch: int = 0,
                     max_batches: int = None,
                     incremental: bool = False) -> Dict[str, Any]:
        """
        构建Qdrant向量索引
        
        Args:
            limit: 限制处理的记录数量，None表示处理所有
            batch_size: 批处理大小
            test_mode: 测试模式，不实际创建索引
            data_source: 数据源类型 ("raw_files"=混合模式, "mysql"=仅MySQL, "raw_only"=仅原始文件)
            start_batch: 从第几批开始处理（分批构建）
            max_batches: 最大批次数，None表示处理所有批次
            incremental: 是否增量构建（不删除现有集合）
            
        Returns:
            构建结果统计
        """
        self.logger.info(f"开始构建Qdrant向量索引，集合: {self.collection_name}")
        
        try:
            # 初始化嵌入模型
            embed_model = await self._init_embedding_model()
            if not embed_model:
                return {"success": False, "error": "嵌入模型初始化失败", "message": "嵌入模型初始化失败"}
            
            # 初始化异步Qdrant客户端
            qdrant_client = AsyncQdrantClient(url=self.qdrant_url)
            
            # 创建或重建集合
            if not test_mode:
                await self._setup_collection(qdrant_client, incremental=incremental)
            
            # 根据数据源类型加载数据
            if data_source == "raw_files":
                print("📁 混合模式：从原始文件+PageRank数据...")
                nodes = await self._load_nodes_hybrid(limit)
                self.logger.info(f"混合模式加载了 {len(nodes)} 个节点")
            elif data_source == "mysql":
                print("📊 从MySQL数据库加载数据...")
                nodes = await self._load_and_chunk_nodes_from_mysql(limit)
                self.logger.info(f"从MySQL加载了 {len(nodes)} 个节点")
            elif data_source == "raw_only":
                print("📁 仅从原始JSON文件加载数据...")
                nodes = await self._load_and_chunk_nodes_from_raw_files(limit)
                self.logger.info(f"从原始文件加载了 {len(nodes)} 个节点")
            else:
                print("📁 默认混合模式：从原始文件+PageRank数据...")
                nodes = await self._load_nodes_hybrid(limit)
                self.logger.info(f"混合模式加载了 {len(nodes)} 个节点")
            
            if not nodes:
                self.logger.warning("没有找到任何节点数据")
                return {"total_nodes": 0, "success": False, "message": "没有找到数据"}
            
            # 构建向量索引
            if not test_mode:
                vector_store = QdrantVectorStore(
                    aclient=qdrant_client,
                    collection_name=self.collection_name
                )
                
                # 为节点生成嵌入（带进度条）
                print("🔮 生成向量嵌入...")
                nodes = await self._generate_embeddings_with_progress(embed_model, nodes, batch_size)

                # 异步批量添加节点到Qdrant（带进度条）
                print("📤 上传向量到Qdrant...")
                await self._upload_to_qdrant_with_progress(vector_store, nodes, batch_size)
                
                self.logger.info(f"Qdrant向量索引构建完成，集合: {self.collection_name}")
            else:
                self.logger.info("测试模式：跳过索引构建")
            
            print("✅ Qdrant向量索引构建完成!")
            return {
                "total_nodes": len(nodes),
                "success": True,
                "collection_name": self.collection_name,
                "vector_size": self.vector_size,
                "embedding_model": self.embedding_model,
                "data_source": data_source,
                "message": f"成功构建Qdrant索引，包含 {len(nodes)} 个向量"
            }
            
        except Exception as e:
            print(f"❌ 构建失败: {e}")
            self.logger.error(f"构建Qdrant索引时出错: {e}")
            return {
                "total_nodes": 0, 
                "success": False, 
                "error": str(e),
                "message": f"Qdrant索引构建失败: {str(e)}"
            }

    async def _generate_embeddings_with_progress(self, embed_model, nodes: List[BaseNode], batch_size: int) -> List[BaseNode]:
        """为节点生成嵌入并显示进度（优化内存管理）"""
        # 处理batch_size=-1的情况，表示不分批，一次性处理
        if batch_size == -1:
            batch_size = len(nodes)
        
        total_batches = (len(nodes) + batch_size - 1) // batch_size
        
        self.logger.info(f"开始生成嵌入: {len(nodes)} 个节点, 批次大小: {batch_size}, 总批次: {total_batches}")
        
        # 对于大数据集，在生成嵌入的同时进行垃圾回收以释放内存
        import gc
        
        with tqdm(total=len(nodes), desc="生成向量嵌入", unit="节点") as pbar:
            for i in range(0, len(nodes), batch_size):
                batch = nodes[i:i + batch_size]
                batch_num = i//batch_size + 1
                
                self.logger.debug(f"处理批次 {batch_num}/{total_batches}, 节点数: {len(batch)}")
                
                try:
                    # 为批次节点生成嵌入
                    batch_with_embeddings = await embed_model.acall(batch)
                    # 更新原始nodes列表
                    nodes[i:i + len(batch_with_embeddings)] = batch_with_embeddings
                    pbar.update(len(batch))
                    pbar.set_postfix({'批次': f"{batch_num}/{total_batches}"})
                    
                    self.logger.debug(f"批次 {batch_num} 完成, 处理了 {len(batch)} 个节点")
                    
                    # 每100批执行一次垃圾回收释放内存
                    if batch_num % 100 == 0:
                        gc.collect()
                        self.logger.debug(f"批次 {batch_num} 后执行垃圾回收")
                    
                except Exception as e:
                    self.logger.warning(f"批次 {batch_num} 嵌入生成失败: {e}")
                    pbar.update(len(batch))
        
        self.logger.info(f"嵌入生成完成，总计处理 {len(nodes)} 个节点")
        return nodes

    async def _upload_to_qdrant_with_progress(self, vector_store, nodes: List[BaseNode], batch_size: int):
        """将节点上传到Qdrant并显示进度（优化内存管理和错误处理）"""
        # 处理batch_size=-1的情况，表示不分批，一次性处理
        if batch_size == -1:
            batch_size = len(nodes)
        
        total_batches = (len(nodes) + batch_size - 1) // batch_size
        
        self.logger.info(f"开始上传到Qdrant: {len(nodes)} 个节点, 批次大小: {batch_size}, 总批次: {total_batches}")
        
        import gc
        successful_uploads = 0
        failed_uploads = 0
        
        with tqdm(total=len(nodes), desc="上传到Qdrant", unit="节点") as pbar:
            for i in range(0, len(nodes), batch_size):
                batch = nodes[i:i + batch_size]
                batch_num = i//batch_size + 1
                
                self.logger.debug(f"上传批次 {batch_num}/{total_batches}, 节点数: {len(batch)}")
                
                try:
                    await vector_store.async_add(nodes=batch)
                    successful_uploads += len(batch)
                    pbar.update(len(batch))
                    pbar.set_postfix({
                        '批次': f"{batch_num}/{total_batches}", 
                        '成功': successful_uploads,
                        '失败': failed_uploads
                    })
                    
                    self.logger.debug(f"批次 {batch_num} 上传完成, 上传了 {len(batch)} 个节点")
                    
                    # 每50批执行一次垃圾回收
                    if batch_num % 50 == 0:
                        gc.collect()
                        self.logger.debug(f"批次 {batch_num} 后执行垃圾回收")
                    
                except Exception as e:
                    failed_uploads += len(batch)
                    self.logger.warning(f"批次 {batch_num} 上传失败: {e}")
                    pbar.update(len(batch))
                    pbar.set_postfix({
                        '批次': f"{batch_num}/{total_batches}", 
                        '成功': successful_uploads,
                        '失败': failed_uploads
                    })
        
        self.logger.info(f"Qdrant上传完成，成功上传 {successful_uploads} 个节点，失败 {failed_uploads} 个节点")

    async def _init_embedding_model(self) -> Optional[HuggingFaceEmbedding]:
        """异步初始化嵌入模型"""
        def _load_model():
            """在线程池中运行的同步加载函数"""
            try:
                # 使用ETL模块统一配置的模型路径
                models_path = str(MODELS_PATH)
                
                # 设置HuggingFace缓存目录
                os.environ['HF_HOME'] = models_path
                os.environ['TRANSFORMERS_CACHE'] = models_path
                os.environ['HF_HUB_CACHE'] = models_path
                os.environ['SENTENCE_TRANSFORMERS_HOME'] = models_path
                
                self.logger.info(f"初始化嵌入模型: {self.embedding_model}")
                embed_model = HuggingFaceEmbedding(
                    model_name=self.embedding_model,
                    device='cpu'  # 强制使用CPU
                )
                
                self.logger.info("嵌入模型初始化成功")
                return embed_model
                
            except Exception as e:
                self.logger.error(f"初始化嵌入模型失败: {e}")
                return None
        
        try:
            print("🤖 初始化嵌入模型...")
            loop = asyncio.get_running_loop()
            return await loop.run_in_executor(None, _load_model)
        except Exception as e:
            self.logger.error(f"执行嵌入模型初始化时发生错误: {e}")
            return None

    async def _setup_collection(self, client: AsyncQdrantClient, incremental: bool = False):
        """设置Qdrant集合
        
        Args:
            client: Qdrant异步客户端
            incremental: 是否增量构建（不删除现有集合）
        """
        try:
            print("🗂️  设置Qdrant集合...")
            # 检查集合是否存在
            collections = await client.get_collections()
            existing_collections = [col.name for col in collections.collections]
            
            if self.collection_name in existing_collections:
                if incremental:
                    self.logger.info(f"增量模式: 保留现有集合 {self.collection_name}")
                    # 获取现有集合信息
                    collection_info = await client.get_collection(self.collection_name)
                    current_count = collection_info.points_count
                    self.logger.info(f"现有集合包含 {current_count} 个向量")
                    print(f"📊 现有集合包含 {current_count} 个向量，将进行增量更新")
                    return current_count
                else:
                    self.logger.info(f"完全重建模式: 删除现有集合 {self.collection_name}")
                    await client.delete_collection(self.collection_name)
            
            # 创建新集合（仅在非增量模式或集合不存在时）
            if not incremental or self.collection_name not in existing_collections:
                self.logger.info(f"创建新集合: {self.collection_name}, 向量维度: {self.vector_size}")
                await client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=models.VectorParams(
                        size=self.vector_size,
                        distance=models.Distance.COSINE
                    )
                )
                return 0  # 新集合初始向量数为0
            
        except Exception as e:
            self.logger.error(f"设置Qdrant集合时出错: {e}")
            raise

    async def _load_nodes_from_raw_files(self, limit: int = None) -> List[BaseNode]:
        """从原始JSON文件加载节点数据（推荐方法）"""
        nodes = []
        
        try:
            # 定义数据源配置
            data_sources = [
                {
                    'name': 'website',
                    'path': RAW_PATH / 'website' / 'nku',
                    'platform': 'website'
                },
                {
                    'name': 'wechat', 
                    'path': RAW_PATH / 'wechat' / 'nku',
                    'platform': 'wechat'
                },
                {
                    'name': 'market',
                    'path': RAW_PATH / 'market' / 'nku', 
                    'platform': 'market'
                },
                {
                    'name': 'wxapp',
                    'path': RAW_PATH / 'wxapp',
                    'platform': 'wxapp'
                }
            ]
            
            # 统计总文件数
            total_files = 0
            source_file_counts = {}
            
            for source in data_sources:
                if source['path'].exists():
                    json_files = list(source['path'].rglob('*.json'))
                    # 过滤掉特殊文件
                    json_files = [f for f in json_files if not f.name.startswith(('scraped_', 'counter.', 'lock.'))]
                    source_file_counts[source['name']] = len(json_files)
                    total_files += len(json_files)
                else:
                    source_file_counts[source['name']] = 0
                    self.logger.warning(f"数据源路径不存在: {source['path']}")
            
            if limit:
                total_files = min(total_files, limit)
            
            self.logger.info(f"预计处理 {total_files} 个JSON文件")
            for name, count in source_file_counts.items():
                if count > 0:
                    self.logger.info(f"  {name}: {count} 个文件")
            
            processed_count = 0
            
            # 使用总体进度条
            with tqdm(total=total_files, desc="加载原始数据", unit="文件") as pbar:
                for source in data_sources:
                    if not source['path'].exists():
                        continue
                        
                    # 获取该数据源的JSON文件
                    json_files = list(source['path'].rglob('*.json'))
                    json_files = [f for f in json_files if not f.name.startswith(('scraped_', 'counter.', 'lock.'))]
                    
                    if not json_files:
                        self.logger.info(f"{source['name']} 没有找到JSON文件")
                        continue
                    
                    self.logger.info(f"处理 {source['name']} 数据源: {len(json_files)} 个文件")
                    
                    # 处理该数据源的文件
                    source_desc = f"处理{source['name']}"
                    for json_file in tqdm(json_files, desc=source_desc, unit="文件", leave=False):
                        if limit and processed_count >= limit:
                            break
                            
                        try:
                            # 读取JSON文件
                            async with aiofiles.open(json_file, 'r', encoding='utf-8') as f:
                                content_str = await f.read()
                            
                            if not content_str.strip():
                                continue
                            
                            data = json.loads(content_str)
                            
                            # 处理不同的数据格式
                            if isinstance(data, list):
                                records = data
                            elif isinstance(data, dict) and 'data' in data:
                                records = data['data'] if isinstance(data['data'], list) else [data['data']]
                            else:
                                records = [data]
                            
                            # 转换每条记录为节点
                            for record in records:
                                try:
                                    node = await self._create_node_from_record(record, source['platform'], json_file)
                                    if node:
                                        nodes.append(node)
                                        
                                except Exception as e:
                                    self.logger.warning(f"处理记录时出错 {json_file}: {e}")
                                    continue
                            
                            processed_count += 1
                            pbar.update(1)
                            
                        except Exception as e:
                            self.logger.warning(f"处理文件时出错 {json_file}: {e}")
                            pbar.update(1)
                            continue
                    
                    if limit and processed_count >= limit:
                        break
            
            self.logger.info(f"总计从原始文件加载 {len(nodes)} 个节点")
            
        except Exception as e:
            self.logger.error(f"从原始文件加载数据时出错: {e}")
        
        return nodes

    async def _create_node_from_record(self, record: Dict[str, Any], platform: str, source_file: Path) -> Optional[TextNode]:
        """从记录创建TextNode"""
        try:
            # 基本字段提取
            content = record.get('content', '')
            title = record.get('title', record.get('name', ''))
            
            # 内容验证
            if not content or not content.strip():
                return None
            
            if not title:
                title = f"文档_{record.get('id', 'unknown')}"
            
            # 合并标题和内容
            full_text = f"{title}\n{content}" if title else content
            
            # 提取其他元数据
            author = record.get('author', record.get('nickname', ''))
            url = record.get('original_url', record.get('url', record.get('link', '')))
            publish_time = record.get('publish_time', record.get('create_time', record.get('time', '')))
            
            # 生成唯一ID
            record_id = record.get('id', str(abs(hash(url + title)) % 1000000))
            source_id = f"{platform}_{record_id}"
            
            # 构造URL（如果没有）
            if not url:
                if platform == 'wxapp':
                    url = f"wxapp://post/{record_id}"
                else:
                    url = f"{platform}://item/{record_id}"
            
            # 创建TextNode
            node = TextNode(
                text=full_text,
                metadata={
                    'source_id': source_id,
                    'id': record_id,
                    'url': url,
                    'title': title,
                    'author': author,
                    'original_url': url,
                    'publish_time': str(publish_time),
                    'source': platform,
                    'platform': platform,
                    'pagerank_score': float(record.get('pagerank_score', 0.0)),
                    'source_file': str(source_file),
                    'data_source': 'raw_files'
                }
            )
            
            return node
            
        except Exception as e:
            self.logger.warning(f"创建节点时出错: {e}")
            return None

    async def _load_and_chunk_nodes_from_raw_files(self, limit: int = None) -> List[BaseNode]:
        """从原始文件加载数据并进行文本分块"""
        # 首先加载原始节点
        raw_nodes = await self._load_nodes_from_raw_files(limit)
        
        if not raw_nodes:
            return []
        
        # 进行文本分块
        return await self._chunk_nodes_with_progress(raw_nodes)

    async def _load_and_chunk_nodes_from_mysql(self, limit: int = None) -> List[BaseNode]:
        """从MySQL加载数据并进行文本分块"""
        nodes = []
        
        try:
            # 构建SQL查询
            sql = """
            SELECT id, original_url, title, content, publish_time, platform, pagerank_score, author
            FROM website_nku
            WHERE content IS NOT NULL AND content != ''
            ORDER BY id
            """
            
            if limit:
                sql += f" LIMIT {limit}"
            
            # 执行查询
            records = await db_core.execute_query(sql, fetch=True)
            
            if not records:
                self.logger.warning("MySQL中没有找到任何记录")
                return nodes
            
            # 处理每条记录，创建文档节点
            doc_nodes = []
            for record in tqdm(records, desc="处理MySQL记录", unit="条"):
                try:
                    # 构建文档内容
                    content = record.get('content', '')
                    title = record.get('title', '')
                    
                    # 合并标题和内容
                    full_text = f"{title}\n{content}" if title else content
                    
                    # 创建文档节点
                    doc_node = TextNode(
                        text=full_text,
                                        metadata={
                    'source_id': record.get('id'),
                    'id': record.get('id'),
                    'url': record.get('original_url', ''),
                    'title': title,
                    'author': record.get('author', ''),
                    'original_url': record.get('original_url', ''),
                    'publish_time': str(record.get('publish_time', '')),
                    'source': record.get('platform', ''),
                    'platform': record.get('platform', ''),
                            'pagerank_score': float(record.get('pagerank_score', 0.0)),
                            'data_source': 'mysql'
                        }
                    )
                    
                    doc_nodes.append(doc_node)
                    
                except Exception as e:
                    self.logger.warning(f"处理记录ID {record.get('id')} 时出错: {e}")
                    continue
            
            # 进行文本分块
            nodes = await self._chunk_nodes_with_progress(doc_nodes)
            
        except Exception as e:
            self.logger.error(f"从MySQL加载数据时出错: {e}")
        
        return nodes

    async def _chunk_nodes_with_progress(self, doc_nodes: List[BaseNode]) -> List[BaseNode]:
        """对文档节点进行分块并显示进度（使用缓存优化）"""
        from etl.processors.chunk_cache import chunk_documents_cached
        
        self.logger.info(f"开始分块 {len(doc_nodes)} 个文档节点...")
        
        # 使用缓存进行分块
        chunked_nodes = await chunk_documents_cached(
            doc_nodes=doc_nodes,
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            force_refresh=False,
            show_progress=True
        )
        
        self.logger.info(f"分块完成，总计 {len(chunked_nodes)} 个文本块")
        return chunked_nodes

    async def _load_nodes_hybrid(self, limit: int = None) -> List[BaseNode]:
        """混合加载方案：从原始文件加载基础数据，从MySQL补充PageRank分数（推荐）"""
        try:
            # 第一步：从原始文件加载并分块
            self.logger.info("📁 第一步：从原始JSON文件加载并分块数据...")
            raw_nodes = await self._load_and_chunk_nodes_from_raw_files(limit)
            
            if not raw_nodes:
                self.logger.warning("原始文件中没有数据，回退到MySQL模式")
                return await self._load_and_chunk_nodes_from_mysql(limit)
            
            # 第二步：从MySQL加载PageRank分数映射
            self.logger.info("📊 第二步：从MySQL加载PageRank分数...")
            pagerank_mapping = await self._load_pagerank_mapping()
            
            if pagerank_mapping:
                self.logger.info(f"成功加载 {len(pagerank_mapping)} 个PageRank分数")
                
                # 第三步：为节点补充PageRank分数
                updated_count = 0
                with tqdm(raw_nodes, desc="补充PageRank分数", unit="节点") as pbar:
                    for node in pbar:
                        url = node.metadata.get('url', '')
                        if url in pagerank_mapping:
                            node.metadata['pagerank_score'] = float(pagerank_mapping[url])
                            updated_count += 1
                        pbar.set_postfix({'已更新': updated_count})
                
                self.logger.info(f"为 {updated_count} 个节点补充了PageRank分数")
            else:
                self.logger.warning("没有找到PageRank分数，所有节点将使用默认值0.0")
            
            self.logger.info(f"混合加载完成，总计 {len(raw_nodes)} 个节点")
            return raw_nodes
            
        except Exception as e:
            self.logger.error(f"混合加载失败: {e}")
            self.logger.info("尝试回退到MySQL模式...")
            try:
                return await self._load_and_chunk_nodes_from_mysql(limit)
            except Exception as mysql_error:
                self.logger.error(f"MySQL回退也失败: {mysql_error}")
                return []

    async def _load_pagerank_mapping(self) -> Dict[str, float]:
        """从MySQL加载PageRank分数映射"""
        try:
            # 首先尝试从website_nku表获取（已整合的PageRank分数）
            query = """
            SELECT original_url, pagerank_score 
            FROM website_nku 
            WHERE pagerank_score > 0
            """
            records = await db_core.execute_query(query, fetch=True)
            
            if records:
                mapping = {record['original_url']: float(record['pagerank_score']) for record in records}
                self.logger.info(f"从website_nku表加载了 {len(mapping)} 个PageRank分数")
                return mapping
            
            # 如果website_nku表没有数据，尝试从pagerank_scores表获取
            query = """
            SELECT url, pagerank_score 
            FROM pagerank_scores
            """
            records = await db_core.execute_query(query, fetch=True)
            
            if records:
                mapping = {record['url']: float(record['pagerank_score']) for record in records}
                self.logger.info(f"从pagerank_scores表加载了 {len(mapping)} 个PageRank分数")
                return mapping
            
            self.logger.warning("两个表中都没有找到PageRank数据")
            return {}
            
        except Exception as e:
            self.logger.warning(f"加载PageRank分数时出错: {e}")
            return {}

    async def validate_index(self) -> Dict[str, Any]:
        """异步验证Qdrant索引是否存在且有效"""
        self.logger.info(f"开始验证Qdrant索引: {self.collection_name}")
        client = AsyncQdrantClient(url=self.qdrant_url)
        
        try:
            # 检查集合是否存在
            collections_response = await client.get_collections()
            collection_names = [col.name for col in collections_response.collections]

            if self.collection_name not in collection_names:
                self.logger.warning(f"集合 '{self.collection_name}' 不存在。")
                return {"status": "missing", "collection_name": self.collection_name}

            # 获取集合信息
            collection_info = await client.get_collection(collection_name=self.collection_name)
            vector_count = collection_info.vectors_count

            # 获取一些示例文档 (这里用 scroll 接口)
            scroll_response = await client.scroll(
                collection_name=self.collection_name,
                limit=5,
                with_payload=True
            )
            sample_docs = [record.payload for record in scroll_response[0]]

            self.logger.info(f"集合 '{self.collection_name}' 验证成功，包含 {vector_count} 个向量。")

            return {
                "status": "ok",
                "collection_name": self.collection_name,
                "vector_count": vector_count,
                "vector_size": collection_info.vectors_config.params.size,
                "distance_metric": collection_info.vectors_config.params.distance.name,
                "sample_documents": sample_docs,
            }
        except Exception as e:
            self.logger.error(f"验证Qdrant索引时出错: {e}")
            return {"status": "error", "error_message": str(e)}
        finally:
            await client.close()


# 向后兼容的函数接口
async def build_qdrant_index(
    collection_name: str = None,
    embedding_model: str = None,
    qdrant_url: str = None,
    chunk_size: int = 512,
    chunk_overlap: int = 200,
    limit: int = None,
    batch_size: int = 100,
    data_source: str = "raw_files"
) -> Dict[str, Any]:
    """
    构建Qdrant向量索引（向后兼容接口）
    
    Args:
        data_source: 数据源类型 ("raw_files"=混合模式, "mysql"=仅MySQL, "raw_only"=仅原始文件)
    """
    config = Config()
    
    # 设置配置参数
    indexer_config = {
        'etl.data.qdrant.collection': collection_name or config.get('etl.data.qdrant.collection'),
        'etl.data.qdrant.url': qdrant_url or config.get('etl.data.qdrant.url'),
        'etl.embedding.name': embedding_model or config.get('etl.embedding.name'),
        'etl.embedding.chunking.chunk_size': chunk_size,
        'etl.embedding.chunking.chunk_overlap': chunk_overlap,
        'etl.data.base_path': config.get('etl.data.base_path'),
        'etl.data.models.path': config.get('etl.data.models.path'),
        'etl.data.qdrant.vector_size': config.get('etl.data.qdrant.vector_size')
    }
    
    # 创建索引构建器
    indexer = QdrantIndexer(indexer_config)
    
    # 构建索引
    return await indexer.build_indexes(limit=limit, batch_size=batch_size, data_source=data_source) 