"""
Elasticsearch索引构建器

负责从MySQL数据构建Elasticsearch全文检索索引。
"""

import sys
import loguru
import asyncio
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import aiofiles
import aiofiles.os
from tqdm.asyncio import tqdm
from elasticsearch import Elasticsearch, helpers, AsyncElasticsearch
import os
import loguru

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from config import Config
from etl.load import db_core
# 导入ETL模块的统一路径配置
from etl import (RAW_PATH, ES_INDEX_NAME, ES_HOST, ES_PORT, ES_ENABLE_CHUNKING, CHUNK_SIZE, CHUNK_OVERLAP)

class ElasticsearchIndexer:
    """Elasticsearch索引构建器
    
    负责从MySQL数据构建Elasticsearch全文检索索引，支持通配符查询和复杂文本匹配。
    """
    
    def __init__(self, logger):
        self.logger = logger
        
        # 从ETL模块统一配置获取参数
        self.index_name = ES_INDEX_NAME
        self.es_host = ES_HOST
        self.es_port = ES_PORT
        
        # 分块参数
        self.enable_chunking = ES_ENABLE_CHUNKING
        self.chunk_size = CHUNK_SIZE
        self.chunk_overlap = CHUNK_OVERLAP
        
        self.es_client: Optional[AsyncElasticsearch] = None
        self.logger.info(f"ElasticsearchIndexer 初始化完成。连接目标: http://{self.es_host}:{self.es_port}")
        
    async def build_indexes(self, 
                     limit: int = None, 
                     batch_size: int = 50,
                     recreate_index: bool = True,
                     test_mode: bool = False,
                     data_source: str = "raw_files",
                     start_batch: int = 0,
                     max_batches: int = None) -> Dict[str, Any]:
        """
        构建Elasticsearch索引
        
        Args:
            limit: 限制处理的记录数量，None表示处理所有
            batch_size: 批处理大小
            recreate_index: 是否重新创建索引
            test_mode: 测试模式，不实际创建索引
            data_source: 数据源类型 ("raw_files"=混合模式, "mysql"=仅MySQL, "raw_only"=仅原始文件)
            start_batch: 从第几批开始处理（分批构建）
            max_batches: 最大批次数，None表示处理所有批次
            
        Returns:
            构建结果统计
        """
        self.logger.info(f"开始构建Elasticsearch索引: {self.index_name}")
        
        try:
            # 初始化Elasticsearch客户端
            es_client = await self._init_es_client()
            if not es_client:
                if test_mode:
                    # 测试模式下，无法连接ES时返回成功的模拟结果
                    return {
                        "total_records": 0,
                        "success": True,
                        "indexed": 0,
                        "errors": 0,
                        "data_source": data_source,
                        "message": "测试模式：Elasticsearch服务不可用，跳过索引构建"
                    }
                else:
                    return {
                        "success": False, 
                        "error": "无法连接到Elasticsearch", 
                        "message": "Elasticsearch连接失败"
                    }
            
            # 设置索引
            if not test_mode and recreate_index:
                await self._setup_index(es_client)
            
            # 根据数据源类型加载数据并建立索引
            try:
                if not test_mode:
                    result = await self._index_documents_from_source(es_client, limit, batch_size, data_source)
                else:
                    # 测试模式：只加载数据不索引
                    result = await self._test_data_loading_from_source(limit, data_source)
                    
                result['data_source'] = data_source
                self.logger.info(f"Elasticsearch索引构建完成: {result}")
                return result
            finally:
                # 确保客户端连接被正确关闭
                if es_client:
                    try:
                        await es_client.close()
                    except Exception as e:
                        self.logger.debug(f"关闭ES客户端时出错: {e}")
            
        except Exception as e:
            print(f"❌ 构建失败: {e}")
            self.logger.error(f"构建Elasticsearch索引时出错: {e}")
            return {
                "success": False, 
                "error": str(e),
                "message": f"Elasticsearch索引构建失败: {str(e)}"
            }

    async def build_from_nodes(self, nodes: List[Dict[str, Any]], batch_size: int = 500) -> Dict[str, Any]:
        """
        从预加载的节点列表构建Elasticsearch索引。
        
        Args:
            nodes: 从文件处理阶段传入的TextNode列表
            batch_size: 批处理大小
            
        Returns:
            构建结果统计
        """
        self.logger.info(f"开始从 {len(nodes)} 个预加载节点构建Elasticsearch索引...")
        es_client = await self._init_es_client()
        if not es_client:
            return {"success": False, "error": "无法连接到Elasticsearch"}

        try:
            # 1. 将 TextNode 转换为 Elasticsearch 需要的字典格式
            actions = []
            for node in nodes:
                # 从 metadata 提取所需字段
                doc = {
                    "url": node.metadata.get("url", ""),
                    "title": node.metadata.get("title", ""),
                    "content": node.text,  # content 来自 node.text
                    "publish_time": node.metadata.get("publish_time"),
                    "platform": node.metadata.get("platform", ""),
                    "pagerank_score": float(node.metadata.get("pagerank_score", 0.0))
                }
                
                # 移除空值字段，以避免ES索引错误
                doc = {k: v for k, v in doc.items() if v is not None}
                
                actions.append({
                    "_index": self.index_name,
                    "_id": node.metadata.get("source_id", node.id_),
                    "_source": doc
                })

            if not actions:
                self.logger.warning("没有可供索引的有效节点。")
                return {"success": True, "indexed": 0, "errors": 0}

            # 2. 使用 helpers.async_bulk 批量索引
            indexed, errors = await helpers.async_bulk(es_client, actions, chunk_size=batch_size)
            
            result = {
                "success": True,
                "indexed": indexed,
                "errors": len(errors),
                "message": f"成功索引 {indexed} 个文档，失败 {len(errors)} 个。"
            }
            self.logger.info(f"Elasticsearch索引构建完成: {result}")
            return result
            
        except Exception as e:
            self.logger.error(f"从节点构建Elasticsearch索引时出错: {e}")
            return {"success": False, "error": str(e)}
        finally:
            if es_client:
                await es_client.close()

    async def _init_es_client(self) -> Optional[AsyncElasticsearch]:
        """初始化Elasticsearch客户端"""
        if self.es_client and await self.es_client.ping():
            return self.es_client
            
        try:
            self.logger.info("🔍 正在初始化或重新初始化Elasticsearch异步客户端...")
            
            # 使用在 __init__ 中已经设置好的主机和端口
            es_url = f"http://{self.es_host}:{self.es_port}"
            
            self.es_client = AsyncElasticsearch(
                hosts=[es_url],
                verify_certs=False,
                http_compress=True,
                request_timeout=30,
                max_retries=3, 
                retry_on_timeout=True
            )
            
           # 测试连接（设置较短超时）
            try:
                ping_result = await asyncio.wait_for(self.es_client.ping(), timeout=5.0)
                if not ping_result:
                    await self.es_client.close() 
                    self.logger.debug("Elasticsearch服务器ping失败")
                    return None
            except asyncio.TimeoutError:
                await self.es_client.close()
                self.logger.debug("Elasticsearch连接超时")
                return None
            
            self.logger.info(f"成功连接到Elasticsearch: {es_url}")
            return self.es_client
                
        except Exception as e:
            self.logger.error(f"❌ 初始化Elasticsearch客户端时发生异常: {e}")
            if self.es_client:
                await self.es_client.close()
            self.es_client = None
            return None

    async def _setup_index(self, es_client: AsyncElasticsearch):
        """设置Elasticsearch索引"""
        try:
            print("🗂️  设置Elasticsearch索引...")
            # 删除现有索引
            if await es_client.indices.exists(index=self.index_name):
                self.logger.info(f"删除现有索引: {self.index_name}")
                await es_client.indices.delete(index=self.index_name)
            
            # 使用IK分析器进行中文分词
            self.logger.info("使用IK分析器进行中文分词")
            
            mapping = {
                "mappings": {
                    "properties": {
                        "url": {
                            "type": "keyword",
                            "index": True
                        },
                        "title": {
                            "type": "text",
                            "analyzer": "ik_max_word",
                            "search_analyzer": "ik_smart"
                        },
                        "content": {
                            "type": "text",
                            "analyzer": "ik_max_word",
                            "search_analyzer": "ik_smart"
                        },
                        "publish_time": {
                            "type": "date",
                            "format": "yyyy-MM-dd||yyyy-MM-dd HH:mm:ss||epoch_millis"
                        },
                        "platform": {
                            "type": "keyword",
                            "index": True
                        },
                        "pagerank_score": {
                            "type": "float"
                        }
                    }
                },
                "settings": {
                    "number_of_shards": 1,
                    "number_of_replicas": 0,
                    "analysis": {
                        "analyzer": {
                            "default": {
                                "type": "ik_max_word"
                            }
                        }
                    }
                }
            }
            
            # 创建索引
            self.logger.info(f"创建新索引: {self.index_name}")
            await es_client.indices.create(index=self.index_name, body=mapping)
            
        except Exception as e:
            self.logger.error(f"设置Elasticsearch索引时出错: {e}")
            raise

    async def _load_records_from_raw_files(self, limit: int = None) -> List[Dict[str, Any]]:
        """从原始JSON文件加载记录数据"""
        records = []
        
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
                    self.logger.debug(f"数据源路径不存在: {source['path']}")
            
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
                                file_records = data
                            elif isinstance(data, dict) and 'data' in data:
                                file_records = data['data'] if isinstance(data['data'], list) else [data['data']]
                            else:
                                file_records = [data]
                            
                            # 转换每条记录
                            for record in file_records:
                                try:
                                    converted_record = await self._convert_record_from_raw(record, source['platform'], json_file)
                                    if converted_record:
                                        records.append(converted_record)
                                        
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
            
            self.logger.info(f"总计从原始文件加载 {len(records)} 条记录")
            
        except Exception as e:
            self.logger.error(f"从原始文件加载数据时出错: {e}")
        
        return records

    async def _convert_record_from_raw(self, record: Dict[str, Any], platform: str, source_file: Path) -> Optional[Dict[str, Any]]:
        """从原始记录转换为Elasticsearch记录格式"""
        try:
            # 基本字段提取
            content = record.get('content', '')
            title = record.get('title', record.get('name', ''))
            
            # 内容验证
            if not content or not content.strip():
                return None
            
            if not title:
                title = f"文档_{record.get('id', 'unknown')}"
            
            # 提取其他元数据
            author = record.get('author', record.get('nickname', ''))
            url = record.get('original_url', record.get('url', record.get('link', '')))
            publish_time = record.get('publish_time', record.get('create_time', record.get('time', '')))
            
            # 生成唯一ID
            record_id = record.get('id', str(abs(hash(url + title)) % 1000000))
            
            # 构造URL（如果没有）
            if not url:
                if platform == 'wxapp':
                    url = f"wxapp://post/{record_id}"
                else:
                    url = f"{platform}://item/{record_id}"
            
            # 处理发布时间
            if publish_time and not self._is_valid_date(str(publish_time)):
                publish_time = None
            
            # 创建ES记录
            es_record = {
                'id': record_id,
                'source_id': f"{platform}_{record_id}",
                'original_url': url,
                'title': title,
                'content': content,
                'author': author,
                'publish_time': publish_time,
                'platform': platform,
                'pagerank_score': float(record.get('pagerank_score', 0.0)),
                'source_file': str(source_file),
                'data_source': 'raw_files'
            }
            
            return es_record
            
        except Exception as e:
            self.logger.warning(f"转换记录时出错: {e}")
            return None

    async def _load_records_from_mysql(self, limit: int = None) -> List[Dict[str, Any]]:
        """从MySQL加载记录数据"""
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
                return []
            
            # 转换记录格式，添加数据源标记
            converted_records = []
            for record in tqdm(records, desc="处理MySQL记录", unit="条"):
                try:
                    # 处理发布时间
                    publish_time = record.get('publish_time')
                    if publish_time and not self._is_valid_date(str(publish_time)):
                        publish_time = None
                    
                    converted_record = {
                        'id': record.get('id'),
                        'source_id': record.get('id'),
                        'original_url': record.get('original_url', ''),
                        'title': record.get('title', ''),
                        'content': record.get('content', ''),
                        'author': record.get('author', ''),
                        'publish_time': publish_time,
                        'platform': record.get('platform', ''),
                        'pagerank_score': float(record.get('pagerank_score', 0.0)),
                        'data_source': 'mysql'
                    }
                    converted_records.append(converted_record)
                    
                except Exception as e:
                    self.logger.warning(f"处理MySQL记录时出错: {e}")
                    continue
            
            self.logger.info(f"从MySQL加载了 {len(converted_records)} 条记录")
            return converted_records
            
        except Exception as e:
            self.logger.error(f"从MySQL加载数据时出错: {e}")
            return []

    async def _load_records_hybrid(self, limit: int = None) -> List[Dict[str, Any]]:
        """混合加载方案：从原始文件加载基础数据，从MySQL补充PageRank分数（推荐）"""
        try:
            # 第一步：从原始文件加载基础数据
            self.logger.info("📁 第一步：从原始JSON文件加载基础数据...")
            raw_records = await self._load_records_from_raw_files(limit)
            
            if not raw_records:
                self.logger.debug("原始文件中没有数据，回退到MySQL模式")
                return await self._load_records_from_mysql(limit)
            
            # 第二步：从MySQL加载PageRank分数映射
            self.logger.info("📊 第二步：从MySQL加载PageRank分数...")
            pagerank_mapping = await self._load_pagerank_mapping()
            
            if pagerank_mapping:
                self.logger.info(f"成功加载 {len(pagerank_mapping)} 个PageRank分数")
                
                # 第三步：为记录补充PageRank分数
                updated_count = 0
                with tqdm(raw_records, desc="补充PageRank分数", unit="记录") as pbar:
                    for record in pbar:
                        url = record.get('original_url', '')
                        if url in pagerank_mapping:
                            record['pagerank_score'] = float(pagerank_mapping[url])
                            updated_count += 1
                        pbar.set_postfix({'已更新': updated_count})
                
                self.logger.info(f"为 {updated_count} 条记录补充了PageRank分数")
            else:
                self.logger.warning("没有找到PageRank分数，所有记录将使用默认值0.0")
            
            self.logger.info(f"混合加载完成，总计 {len(raw_records)} 条记录")
            return raw_records
            
        except Exception as e:
            self.logger.error(f"混合加载失败: {e}")
            self.logger.info("尝试回退到MySQL模式...")
            try:
                return await self._load_records_from_mysql(limit)
            except Exception as mysql_error:
                self.logger.error(f"MySQL回退也失败: {mysql_error}")
                return []

    async def _load_pagerank_mapping(self) -> Dict[str, float]:
        """从MySQL加载PageRank分数"""
        pagerank_map = {}
        query = "SELECT original_url, pagerank_score FROM link_graph"
        try:
            # 使用正确的函数名 execute_custom_query
            records = await db_core.execute_custom_query(query, fetch='all')
            if records:
                pagerank_map = {rec['original_url']: rec['pagerank_score'] for rec in records}
            self.logger.info(f"✅ 成功从MySQL加载 {len(pagerank_map)} 条PageRank记录")
            return pagerank_map
            
        except Exception as e:
            self.logger.warning(f"加载PageRank分数时出错: {e}")
            return {}

    async def _chunk_documents_if_enabled(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """可选的文档分块功能"""
        if not self.enable_chunking or not records:
            return records
        
        print("📄 进行文档分块...")
        self.logger.info(f"开始分块 {len(records)} 个文档...")
        
        from etl.processors.chunk_cache import chunk_documents_cached
        from llama_index.core.schema import TextNode
        
        # 将记录转换为TextNode
        doc_nodes = []
        for record in records:
            content = record.get('content', '')
            title = record.get('title', '')
            full_text = f"{title}\n{content}" if title else content
            
            node = TextNode(
                text=full_text,
                metadata=record
            )
            doc_nodes.append(node)
        
        # 使用缓存进行分块
        chunked_nodes = await chunk_documents_cached(
            doc_nodes=doc_nodes,
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            force_refresh=False,
            show_progress=True
        )
        
        # 将分块节点转换回记录格式
        chunked_records = []
        for i, node in enumerate(chunked_nodes):
            record = node.metadata.copy()
            record['content'] = node.text  # 使用分块后的文本
            # 为分块创建唯一ID
            original_id = record.get('id', i)
            record['id'] = f"{original_id}_chunk_{i}"
            record['chunk_id'] = i  # 添加分块标识
            record['original_id'] = original_id  # 保留原始ID
            chunked_records.append(record)
        
        self.logger.info(f"分块完成，从 {len(records)} 个文档生成 {len(chunked_records)} 个分块")
        return chunked_records

    async def _index_documents_from_source(self, es_client: AsyncElasticsearch, limit: int = None, batch_size: int = 1000, data_source: str = "raw_files") -> Dict[str, Any]:
        """根据数据源索引文档到Elasticsearch"""
        try:
            # 根据数据源类型加载数据
            if data_source == "raw_files":
                print("📁 混合模式：从原始文件+PageRank数据...")
                records = await self._load_records_hybrid(limit)
            elif data_source == "mysql":
                print("📊 从MySQL数据库加载数据...")
                records = await self._load_records_from_mysql(limit)
            elif data_source == "raw_only":
                print("📁 仅从原始JSON文件加载数据...")
                records = await self._load_records_from_raw_files(limit)
            else:
                print("📁 默认混合模式：从原始文件+PageRank数据...")
                records = await self._load_records_hybrid(limit)
            
            if not records:
                return {"total_records": 0, "success": True, "indexed": 0, "errors": 0, "message": "没有找到数据"}
            
            # 可选的文档分块
            records = await self._chunk_documents_if_enabled(records)
            
            self.logger.info(f"准备索引 {len(records)} 条记录")
            
            # 批量索引（带进度条）
            print("📤 索引文档到Elasticsearch...")
            success_count = 0
            error_count = 0
            
            async def async_doc_generator():
                """异步文档生成器，用于批量索引"""
                for record in records:
                    try:
                        doc = {
                            "_index": self.index_name,
                            "_id": record.get('id'),
                            "_source": {
                                "source_id": record.get('source_id'),
                                "id": record.get('id'),
                                "original_url": record.get('original_url', ''),
                                "title": record.get('title', ''),
                                "content": record.get('content', ''),
                                "author": record.get('author', ''),
                                "publish_time": record.get('publish_time'),
                                "platform": record.get('platform', ''),
                                "pagerank_score": record.get('pagerank_score', 0.0)
                            }
                        }
                        yield doc
                        
                    except Exception as e:
                        self.logger.warning(f"处理记录时出错: {e}")
                        continue
            
            # 执行异步批量索引（带进度条和性能优化）
            with tqdm(total=len(records), desc="索引到ES", unit="文档") as pbar:
                async for ok, action_result in helpers.async_streaming_bulk(
                    es_client, 
                    async_doc_generator(), 
                    chunk_size=min(batch_size, 100),  # 限制批大小，避免过载
                    max_chunk_bytes=10*1024*1024,     # 10MB最大块大小
                    request_timeout=60,                # 增加请求超时
                    max_retries=3,                     # 增加重试次数
                    initial_backoff=1,                 # 初始退避时间
                    max_backoff=60,                    # 最大退避时间
                    raise_on_error=False,
                    raise_on_exception=False
                ):
                    if ok:
                        success_count += 1
                    else:
                        error_count += 1
                        # 记录具体错误信息（但不记录太多）
                        if error_count <= 10:
                            self.logger.debug(f"索引错误: {action_result}")
                    pbar.update(1)
                    pbar.set_postfix({'成功': success_count, '失败': error_count})
                    
                    # 添加短暂延迟以减少ES压力
                    if (success_count + error_count) % 1000 == 0:
                        await asyncio.sleep(0.1)

            self.logger.info(f"索引完成: {success_count} 成功, {error_count} 失败")
            print("✅ Elasticsearch索引构建完成!")
            
            return {
                "total_records": len(records),
                "success": True,
                "indexed": success_count,
                "errors": error_count,
                "message": f"成功索引 {success_count} 条记录, {error_count} 条失败"
            }

        except Exception as e:
            self.logger.error(f"索引文档到Elasticsearch时出错: {e}")
            return {
                "total_records": 0, 
                "success": False, 
                "indexed": 0,
                "errors": 0,
                "error": str(e),
                "message": f"索引文档失败: {str(e)}"
            }

    async def _test_data_loading_from_source(self, limit: int = None, data_source: str = "raw_files") -> Dict[str, Any]:
        """测试模式下根据数据源仅加载数据，不进行索引"""
        try:
            # 根据数据源类型加载数据
            if data_source == "raw_files":
                records = await self._load_records_hybrid(limit)
            elif data_source == "mysql":
                records = await self._load_records_from_mysql(limit)
            elif data_source == "raw_only":
                records = await self._load_records_from_raw_files(limit)
            else:
                records = await self._load_records_hybrid(limit)
            
            # 可选的文档分块
            records = await self._chunk_documents_if_enabled(records)
            
            self.logger.info(f"测试模式：成功从{data_source}加载 {len(records)} 条记录")
            
            return {
                "total_records": len(records),
                "success": True,
                "indexed": 0,
                "errors": 0,
                "message": f"测试模式：成功加载 {len(records)} 条记录，跳过索引"
            }
            
        except Exception as e:
            self.logger.error(f"测试模式下加载数据失败: {e}")
            return {"total_records": 0, "success": False, "message": f"测试模式下加载数据失败: {e}"}

    async def _index_documents(self, es_client: AsyncElasticsearch, limit: int = None, batch_size: int = 1000) -> Dict[str, Any]:
        """索引文档到Elasticsearch（向后兼容方法）"""
        return await self._index_documents_from_source(es_client, limit, batch_size, "mysql")

    async def _test_data_loading(self, limit: int = None) -> Dict[str, Any]:
        """测试模式下仅加载数据，不进行索引（向后兼容方法）"""
        return await self._test_data_loading_from_source(limit, "mysql")

    def _is_valid_date(self, date_str) -> bool:
        """验证日期字符串是否有效"""
        if not date_str or not isinstance(date_str, str):
            return False
        try:
            # 尝试解析多种格式
            for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d"]:
                datetime.strptime(date_str, fmt)
            return True
        except ValueError:
            return False

    async def validate_index(self) -> Dict[str, Any]:
        """
        异步验证索引的健康状况和内容。

        Returns:
            Dict[str, Any]: 包含索引统计信息和示例文档的字典。
        """
        self.logger.info(f"开始验证Elasticsearch索引: {self.index_name}")
        es_client = await self._init_es_client()
        if not es_client:
            return {"error": "无法连接到Elasticsearch"}

        try:
            # 检查索引是否存在
            if not await es_client.indices.exists(index=self.index_name):
                self.logger.warning(f"索引 '{self.index_name}' 不存在。")
                return {"status": "missing", "index_name": self.index_name}

            # 获取文档总数
            count_response = await es_client.count(index=self.index_name)
            doc_count = count_response.get("count", 0)

            # 获取一些示例文档
            search_response = await es_client.search(
                index=self.index_name,
                body={"query": {"match_all": {}}, "size": 5}
            )
            sample_docs = [hit["_source"] for hit in search_response["hits"]["hits"]]

            self.logger.info(f"索引 '{self.index_name}' 验证成功，包含 {doc_count} 个文档。")
            
            return {
                "status": "ok",
                "index_name": self.index_name,
                "document_count": doc_count,
                "sample_documents": sample_docs,
            }
        except Exception as e:
            self.logger.error(f"验证索引时出错: {e}")
            return {"status": "error", "error_message": str(e)}
        finally:
            # 确保客户端连接被正确关闭
            if es_client:
                try:
                    await es_client.close()
                except Exception as close_error:
                    self.logger.debug(f"关闭ES客户端时出错: {close_error}")


# 向后兼容的函数接口
async def build_elasticsearch_index(
    index_name: str = None,
    es_host: str = None,
    es_port: int = None,
    limit: int = None,
    batch_size: int = 1000,
    recreate_index: bool = True,
    data_source: str = "raw_files"
) -> Dict[str, Any]:
    """
    构建Elasticsearch索引（向后兼容接口）
    
    Args:
        data_source: 数据源类型 ("raw_files"=混合模式, "mysql"=仅MySQL, "raw_only"=仅原始文件)
    """
    config = Config()
    
    # 设置配置参数
    indexer_config = {
        'etl.data.elasticsearch.index': index_name or config.get('etl.data.elasticsearch.index'),
        'etl.data.elasticsearch.host': es_host or config.get('etl.data.elasticsearch.host'),
        'etl.data.elasticsearch.port': es_port or config.get('etl.data.elasticsearch.port')
    }
    
    # 创建索引构建器
    indexer = ElasticsearchIndexer(indexer_config)
    
    # 构建索引
    return await indexer.build_indexes(limit=limit, batch_size=batch_size, recreate_index=recreate_index, data_source=data_source) 