"""
BM25索引构建器

负责从MySQL数据构建BM25文本检索索引。
"""

import os
import sys
import pickle
import logging
import asyncio
from pathlib import Path
from typing import List, Dict, Any, Optional
import jieba
import aiofiles
import aiofiles.os
from tqdm.asyncio import tqdm
import json

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from config import Config
from etl.load import db_core
from etl.retrieval.retrievers import BM25Retriever
from llama_index.core.schema import BaseNode, TextNode
# 导入ETL模块的统一路径配置
from etl import INDEX_PATH, NLTK_PATH, RAW_PATH

logger = logging.getLogger(__name__)


class BM25Indexer:
    """BM25索引构建器
    
    负责从MySQL数据构建BM25文本检索索引，支持中文分词和停用词过滤。
    """
    
    def __init__(self, config: Dict[str, Any], logger: Optional[logging.Logger] = None):
        self.config = config
        self.logger = logger or logging.getLogger(__name__)
        
        # 使用ETL模块统一配置的路径
        self.output_path = config.get('etl.retrieval.bm25.nodes_path', 
                                     str(INDEX_PATH / 'bm25_nodes.pkl'))
        self.stopwords_path = config.get('etl.retrieval.bm25.stopwords_path', 
                                        str(NLTK_PATH / 'hit_stopwords.txt'))
        
        # 分块参数（可选，用于支持长文档）
        self.enable_chunking = config.get('etl.retrieval.bm25.enable_chunking', False)
        self.chunk_size = config.get('etl.chunking.chunk_size', 512)
        self.chunk_overlap = config.get('etl.chunking.chunk_overlap', 200)
        
    async def build_indexes(self, 
                     limit: int = None, 
                     bm25_type: int = 0,
                     test_mode: bool = False,
                     data_source: str = "raw_files",
                     batch_size: int = -1,
                     start_batch: int = 0,
                     max_batches: int = None) -> Dict[str, Any]:
        """
        构建BM25索引
        
        Args:
            limit: 限制处理的记录数量，None表示处理所有
            bm25_type: BM25算法类型 (0: BM25Okapi, 1: BM25)
            test_mode: 测试模式，不实际保存文件
            data_source: 数据源类型 ("raw_files"=混合模式, "mysql"=仅MySQL, "raw_only"=仅原始文件)
            batch_size: 每批处理的记录数量，-1表示不分批
            start_batch: 从第几批开始处理（分批构建）
            max_batches: 最大批次数，None表示处理所有批次
            
        Returns:
            构建结果统计
        """
        self.logger.info(f"开始构建BM25索引，输出路径: {self.output_path}")
        
        try:
            # 确保输出目录存在
            if not test_mode:
                await aiofiles.os.makedirs(os.path.dirname(self.output_path), exist_ok=True)
            
            # 加载停用词
            print("🔍 加载停用词...")
            stopwords = await self._load_stopwords()
            self.logger.info(f"加载了 {len(stopwords)} 个停用词")
            
            # 根据数据源类型加载数据
            if data_source == "raw_files":
                print("📁 混合模式：从原始文件+PageRank数据...")
                nodes = await self._load_nodes_hybrid(limit)
                self.logger.info(f"混合模式加载了 {len(nodes)} 个节点")
            elif data_source == "mysql":
                print("📊 从MySQL数据库加载数据...")
                nodes = await self._load_nodes_from_mysql(limit)
                self.logger.info(f"从MySQL加载了 {len(nodes)} 个节点")
            elif data_source == "raw_only":
                print("📁 仅从原始JSON文件加载数据...")
                nodes = await self._load_nodes_from_raw_files(limit)
                self.logger.info(f"从原始文件加载了 {len(nodes)} 个节点")
            else:
                print("📁 默认混合模式：从原始文件+PageRank数据...")
                nodes = await self._load_nodes_hybrid(limit)
                self.logger.info(f"混合模式加载了 {len(nodes)} 个节点")
            
            if not nodes:
                self.logger.warning("没有找到任何节点数据")
                return {"total_nodes": 0, "success": False, "message": "没有找到数据"}
            
            # 可选的文档分块（用于支持长文档）
            if self.enable_chunking:
                print("📄 进行文档分块...")
                nodes = await self._chunk_nodes_with_cache(nodes)
                self.logger.info(f"分块后总计 {len(nodes)} 个节点")
            
            # 创建jieba分词器对象（具有cut方法）
            import jieba
            
            # 构建BM25索引（详细进度显示）
            print("🔧 构建BM25检索器...")
            bm25_retriever = await self._build_bm25_retriever_with_progress(
                nodes, jieba, stopwords, bm25_type
            )
            
            # 保存索引
            if not test_mode:
                print("💾 保存索引文件...")
                with tqdm(total=1, desc="保存索引", unit="文件") as pbar:
                    # 使用BM25检索器的自定义保存方法
                    bm25_retriever.save_to_pickle(self.output_path)
                    pbar.update(1)
                self.logger.info(f"BM25检索器已保存到: {self.output_path}")
            else:
                self.logger.info("测试模式：跳过文件保存")
            
            print("✅ BM25索引构建完成!")
            return {
                "total_nodes": len(nodes),
                "success": True,
                "output_path": self.output_path,
                "bm25_type": bm25_type,
                "message": f"成功构建BM25索引，包含 {len(nodes)} 个节点"
            }
            
        except Exception as e:
            print(f"❌ 构建失败: {e}")
            self.logger.error(f"构建BM25索引时出错: {e}")
            return {
                "total_nodes": 0, 
                "success": False, 
                "error": str(e),
                "message": f"BM25索引构建失败: {str(e)}"
            }
    
    async def _load_stopwords(self) -> List[str]:
        """异步加载停用词"""
        stopwords = []
        
        try:
            exists = False
            try:
                await aiofiles.os.stat(self.stopwords_path)
                exists = True
            except FileNotFoundError:
                exists = False

            if not exists:
                self.logger.warning(f"停用词文件不存在: {self.stopwords_path}")
                return stopwords
            
            async with aiofiles.open(self.stopwords_path, 'r', encoding='utf-8') as f:
                stopwords = [line.strip() for line in await f.readlines() if line.strip()]
            self.logger.info(f"成功加载 {len(stopwords)} 个停用词")
        except Exception as e:
            self.logger.error(f"加载停用词时出错: {e}")
        
        return stopwords

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

    async def _load_nodes_from_mysql(self, limit: int = None) -> List[BaseNode]:
        """从MySQL加载节点数据（支持多表：website_nku, wechat_nku, wxapp_post）"""
        nodes = []
        
        try:
            # 定义表配置，统一字段映射
            table_configs = [
                {
                    'table': 'website_nku',
                    'fields': {
                        'id': 'id',
                        'url': 'original_url', 
                        'title': 'title',
                        'content': 'content',
                        'author': 'author',
                        'publish_time': 'publish_time',
                        'platform': 'platform',
                        'pagerank_score': 'pagerank_score'
                    },
                    'platform_name': 'website'
                },
                {
                    'table': 'wechat_nku',
                    'fields': {
                        'id': 'id',
                        'url': 'original_url',
                        'title': 'title', 
                        'content': 'content',
                        'author': 'author',
                        'publish_time': 'publish_time',
                        'platform': 'platform',
                        'pagerank_score': 'COALESCE(0.0, 0.0)'  # wechat表没有pagerank_score字段，设为默认值
                    },
                    'platform_name': 'wechat'
                },
                {
                    'table': 'wxapp_post',
                    'fields': {
                        'id': 'id',
                        'url': 'CONCAT("wxapp://post/", id)',  # wxapp没有URL，构造一个
                        'title': 'title',
                        'content': 'content', 
                        'author': 'nickname',
                        'publish_time': 'create_time',  # wxapp使用create_time
                        'platform': '"wxapp"',  # 固定值
                        'pagerank_score': 'COALESCE(0.0, 0.0)'  # wxapp表没有pagerank_score字段，设为默认值
                    },
                    'where_clause': 'status = 1 AND is_deleted = 0',  # wxapp特有的筛选条件
                    'platform_name': 'wxapp'
                }
            ]
            
            # 先获取各表的总数量，用于进度条
            table_counts = {}
            for config in table_configs:
                try:
                    count_sql = f"""
                    SELECT COUNT(*) as total
                    FROM {config['table']}
                    WHERE content IS NOT NULL AND content != ''
                    """
                    if 'where_clause' in config:
                        count_sql += f" AND {config['where_clause']}"
                    
                    count_result = await db_core.execute_query(count_sql, fetch=True)
                    table_counts[config['table']] = count_result[0]['total'] if count_result else 0
                except Exception as e:
                    self.logger.warning(f"获取{config['table']}数量时出错: {e}")
                    table_counts[config['table']] = 0
            
            total_expected = sum(table_counts.values())
            if limit:
                total_expected = min(total_expected, limit * len(table_configs))
            
            self.logger.info(f"预计从{len(table_configs)}个表加载约{total_expected}条记录")
            
            # 使用总体进度条
            with tqdm(total=total_expected, desc="加载MySQL数据", unit="条") as pbar:
                # 从每个表加载数据
                for config in table_configs:
                    try:
                        # 构建字段选择
                        field_selections = []
                        for alias, field_expr in config['fields'].items():
                            field_selections.append(f"{field_expr} as {alias}")
                        
                        # 构建SQL查询
                        sql = f"""
                        SELECT {', '.join(field_selections)}
                        FROM {config['table']}
                        WHERE content IS NOT NULL AND content != ''
                        """
                        
                        # 添加表特定的WHERE条件
                        if 'where_clause' in config:
                            sql += f" AND {config['where_clause']}"
                        
                        sql += " ORDER BY id"
                        
                        # 应用限制（如果指定）
                        table_limit = limit if limit else None
                        if table_limit:
                            sql += f" LIMIT {table_limit}"
                        
                        self.logger.debug(f"查询{config['table']}表")
                        
                        # 执行查询
                        records = await db_core.execute_query(sql, fetch=True)
                        
                        if not records:
                            self.logger.info(f"{config['table']}中没有找到任何记录")
                            continue
                        
                        self.logger.info(f"从{config['table']}加载了 {len(records)} 条记录")
                        
                        # 转换为TextNode（带进度条）
                        table_desc = f"处理{config['table']}"
                        for record in tqdm(records, desc=table_desc, unit="条", leave=False):
                            try:
                                # 构建节点文本内容
                                content = record.get('content', '')
                                title = record.get('title', '')
                                
                                # 合并标题和内容
                                full_text = f"{title}\n{content}" if title else content
                                
                                # 创建TextNode（使用统一的元数据映射）
                                node = TextNode(
                                    text=full_text,
                                    metadata={
                                        'source_id': f"{config['platform_name']}_{record.get('id')}",  # 唯一标识
                                        'id': record.get('id'),
                                        'title': title,
                                        'author': record.get('author', ''),
                                        'original_url': record.get('original_url', ''),
                                        'publish_time': str(record.get('publish_time', '')),
                                        'platform': config['platform_name'],
                                        'pagerank_score': float(record.get('pagerank_score', 0.0)),
                                        'table_name': config['table']  # 标记来源表
                                    }
                                )
                                
                                nodes.append(node)
                                pbar.update(1)  # 更新总体进度
                                
                            except Exception as e:
                                self.logger.warning(f"处理{config['table']}记录时出错: {e}")
                                continue
                    
                    except Exception as e:
                        self.logger.error(f"从{config['table']}加载数据时出错: {e}")
                        continue
            
            self.logger.info(f"总计成功加载 {len(nodes)} 个节点")
            
        except Exception as e:
            self.logger.error(f"从MySQL加载数据时出错: {e}")
        
        return nodes
    
    async def _build_bm25_retriever_with_progress(self, nodes: List[BaseNode], tokenizer, stopwords: List[str], bm25_type: int) -> 'BM25Retriever':
        """构建BM25检索器并显示详细进度"""
        from etl.processors.nodes import get_node_content
        from etl.retrieval.retrievers import tokenize_and_remove_stopwords
        
        def _build_bm25():
            """在线程池中运行的同步构建函数"""
            # 步骤1: 预处理文本和分词
            corpus = []
            
            with tqdm(nodes, desc="分词处理", unit="文档") as pbar:
                for node in pbar:
                    try:
                        # 获取节点内容
                        content = get_node_content(node, embed_type=0)
                        # 分词并去除停用词
                        tokens = tokenize_and_remove_stopwords(tokenizer, content, stopwords=stopwords)
                        corpus.append(tokens)
                        pbar.set_postfix({'已处理': len(corpus)})
                    except Exception as e:
                        self.logger.warning(f"分词处理节点失败: {e}")
                        corpus.append([])  # 添加空列表避免索引错误
            
            if not any(corpus):
                raise ValueError("所有文档在分词后都为空")
            
            # 步骤2: 构建BM25索引
            with tqdm(total=1, desc="构建BM25索引", unit="索引") as pbar:
                try:
                    if bm25_type == 1:
                        import bm25s
                        bm25_instance = bm25s.BM25(k1=1.5, b=0.75)
                        bm25_instance.index(corpus)
                    else:
                        from rank_bm25 import BM25Okapi
                        bm25_instance = BM25Okapi(corpus, k1=1.5, b=0.75, epsilon=0.25)
                    pbar.update(1)
                    pbar.set_postfix({'状态': '完成'})
                except Exception as e:
                    raise ValueError(f"BM25索引构建失败: {str(e)}")
            
            # 步骤3: 创建检索器
            with tqdm(total=1, desc="初始化检索器", unit="检索器") as pbar:
                retriever = BM25Retriever(
                    nodes=nodes,
                    tokenizer=tokenizer,
                    stopwords=stopwords,
                    bm25_type=bm25_type,
                    fast_mode=False,  # 确保立即初始化
                    verbose=True
                )
                # 手动设置已构建的BM25索引和语料库
                retriever._corpus = corpus
                retriever.bm25 = bm25_instance
                retriever._initialized = True
                
                pbar.update(1)
                pbar.set_postfix({'状态': '完成'})
            
            return retriever
        
        # 在线程池中运行构建过程
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, _build_bm25)

    async def _chunk_nodes_with_cache(self, doc_nodes: List[BaseNode]) -> List[BaseNode]:
        """使用缓存对文档节点进行分块"""
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

    def _chinese_tokenizer(self, text: str) -> List[str]:
        """中文分词器"""
        try:
            import jieba
            # 使用jieba进行中文分词
            tokens = list(jieba.cut(text))
            # 过滤掉空白和单字符token
            tokens = [token.strip() for token in tokens if len(token.strip()) > 1]
            return tokens
        except Exception as e:
            self.logger.warning(f"分词时出错: {e}")
            return text.split()  # 降级到简单空格分割
    
    async def validate_index(self) -> Dict[str, Any]:
        """异步验证索引文件是否存在且有效"""
        exists = False
        try:
            await aiofiles.os.stat(self.output_path)
            exists = True
        except FileNotFoundError:
            exists = False

        if not exists:
            return {
                "valid": False,
                "message": f"索引文件不存在: {self.output_path}"
            }
        
        def _load_pickle(data: bytes) -> Any:
            return pickle.loads(data)

        try:
            async with aiofiles.open(self.output_path, 'rb') as f:
                data = await f.read()
            
            loop = asyncio.get_running_loop()
            nodes = await loop.run_in_executor(None, _load_pickle, data)
            
            if not isinstance(nodes, list) or len(nodes) == 0:
                return {
                    "valid": False,
                    "message": "索引文件格式不正确或为空"
                }
            
            return {
                "valid": True,
                "message": f"索引文件有效，包含 {len(nodes)} 个节点",
                "node_count": len(nodes)
            }
            
        except Exception as e:
            return {
                "valid": False,
                "message": f"读取索引文件时出错: {str(e)}"
            }

    async def _load_nodes_hybrid(self, limit: int = None) -> List[BaseNode]:
        """混合加载方案：从原始文件加载基础数据，从MySQL补充PageRank分数（推荐）"""
        nodes = []
        
        try:
            # 第一步：从原始文件加载基础数据
            self.logger.info("📁 第一步：从原始JSON文件加载基础数据...")
            raw_nodes = await self._load_nodes_from_raw_files(limit)
            
            if not raw_nodes:
                self.logger.warning("原始文件中没有数据，回退到MySQL模式")
                return await self._load_nodes_from_mysql(limit)
            
            # 第二步：从MySQL加载PageRank分数映射
            self.logger.info("📊 第二步：从MySQL加载PageRank分数...")
            pagerank_mapping = await self._load_pagerank_mapping()
            
            if pagerank_mapping:
                self.logger.info(f"成功加载 {len(pagerank_mapping)} 个PageRank分数")
                
                # 第三步：为节点补充PageRank分数
                updated_count = 0
                with tqdm(raw_nodes, desc="补充PageRank分数", unit="节点") as pbar:
                    for node in pbar:
                        url = node.metadata.get('original_url', '')
                        if url in pagerank_mapping:
                            node.metadata['pagerank_score'] = float(pagerank_mapping[url])
                            updated_count += 1
                        pbar.set_postfix({'已更新': updated_count})
                
                self.logger.info(f"为 {updated_count} 个节点补充了PageRank分数")
            else:
                self.logger.warning("没有找到PageRank分数，所有节点将使用默认值0.0")
            
            nodes = raw_nodes
            self.logger.info(f"混合加载完成，总计 {len(nodes)} 个节点")
            
        except Exception as e:
            self.logger.error(f"混合加载失败: {e}")
            self.logger.info("尝试回退到MySQL模式...")
            try:
                nodes = await self._load_nodes_from_mysql(limit)
            except Exception as mysql_error:
                self.logger.error(f"MySQL回退也失败: {mysql_error}")
                nodes = []
        
        return nodes

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


# 向后兼容的函数接口
def build_bm25_index(
    output_path: str = None,
    stopwords_path: str = None,
    bm25_type: int = 0,
    limit: int = None,
    data_source: str = "raw_files"
) -> Dict[str, Any]:
    """
    构建BM25索引（向后兼容接口）
    
    Args:
        output_path: 索引输出路径
        stopwords_path: 停用词文件路径
        bm25_type: BM25算法类型 (0: BM25Okapi, 1: BM25)
        limit: 限制处理的记录数量，None表示处理所有
        data_source: 数据源类型 ("raw_files"=混合模式, "mysql"=仅MySQL, "raw_only"=仅原始文件)
        
    Returns:
        构建结果统计
    """
    config = Config()
    
    # 设置配置参数
    indexer_config = {
        'etl.retrieval.bm25.nodes_path': output_path or config.get('etl.retrieval.bm25.nodes_path'),
        'etl.retrieval.bm25.stopwords_path': stopwords_path or config.get('etl.retrieval.bm25.stopwords_path')
    }
    
    # 创建索引构建器
    indexer = BM25Indexer(indexer_config)
    
    # 构建索引
    return asyncio.run(indexer.build_indexes(limit=limit, bm25_type=bm25_type, data_source=data_source)) 