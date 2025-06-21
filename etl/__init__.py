"""
ETL模块，负责数据抽取、转换和加载

此模块实现了爬虫数据采集、数据处理、索引建立和检索功能。
提供了数据采集、处理、存储和检索的完整流程。

子模块:
- crawler: 实现各类数据源的爬虫
- processors: 负责数据格式转换和清洗
- load: 将数据导入到数据库和索引
- embedding: 文档处理和嵌入向量生成
- indexing: 各种索引构建（向量、BM25、Elasticsearch等）
- retrieval: 实现文档检索和重排功能
- pagerank: PageRank分数计算
- utils: 通用工具函数和类

该文件负责加载ETL流程所需的全局配置，并将其定义为可供模块内其他脚本
直接导入的常量。这种方式有助于集中管理配置，并使各模块的依赖关系更加清晰。
"""
import os
from pathlib import Path
from config import Config
from core.utils import register_logger
from typing import Optional

# 创建ETL模块专用日志器
logger = register_logger("etl")

# 加载全局配置单例
_config = Config()

# --- 基础路径配置 (必须最先定义) ---
BASE_PATH = Path(_config.get("etl.data.base_path", "/data"))

# --- 派生路径配置 ---
RAW_PATH = BASE_PATH / _config.get("etl.data.raw.path", "/raw").lstrip("/")
INDEX_PATH = BASE_PATH / _config.get("etl.data.index.path", "/index").lstrip("/")
MYSQL_PATH = BASE_PATH / _config.get("etl.data.mysql.path", "/mysql").lstrip("/")
CACHE_PATH = BASE_PATH / _config.get("etl.data.cache.path", "/cache").lstrip("/")
MODELS_PATH = BASE_PATH / _config.get("etl.data.models.path", "/models").lstrip("/")
NLTK_PATH = BASE_PATH / _config.get("etl.data.nltk.path", "/nltk").lstrip("/")
QDRANT_PATH = BASE_PATH / _config.get("etl.data.qdrant.path", "/qdrant").lstrip("/")

# --- 数据库与向量存储相关配置 ---
DB_HOST: str = _config.get('etl.data.mysql.host', 'localhost')
DB_PORT: int = _config.get('etl.data.mysql.port', 3306)
DB_USER: str = _config.get('etl.data.mysql.user', 'nkuwiki')
DB_PASSWORD: str = _config.get('etl.data.mysql.password', '')
DB_NAME: str = _config.get('etl.data.mysql.name', 'nkuwiki')

# --- 数据库连接池配置 (硬编码默认值，因为它们不应由用户频繁更改) ---
DB_POOL_RESIZE_INTERVAL: int = 60
DB_POOL_MIN_SIZE: int = 2
DB_POOL_MAX_SIZE: int = 16
DB_POOL_MAX_OVERFLOW: int = 8

REDIS_HOST: str = _config.get('etl.data.redis.host', 'localhost')
REDIS_PORT: int = _config.get('etl.data.redis.port', 6379)
REDIS_DB: int = _config.get('etl.data.redis.db', 0)
REDIS_PASSWORD: Optional[str] = _config.get('etl.data.redis.password')

QDRANT_URL: str = _config.get("etl.data.qdrant.url", "http://localhost:6333")
QDRANT_API_KEY: Optional[str] = _config.get("etl.data.qdrant.api_key", None)
QDRANT_COLLECTION: str = _config.get("etl.data.qdrant.collection", "main_index")
QDRANT_TIMEOUT: float = _config.get("etl.data.qdrant.timeout", 30.0)
QDRANT_BATCH_SIZE: int = _config.get("etl.data.qdrant.batch_size", 32)

# --- 数据处理与模型相关配置 ---
EMBEDDING_MODEL_PATH: str = _config.get("etl.embedding.name", "BAAI/bge-large-zh-v1.5")
CHUNK_SIZE: int = _config.get('etl.chunking.chunk_size', 512)
CHUNK_OVERLAP: int = _config.get('etl.chunking.chunk_overlap', 200)

# --- BM25 索引相关配置 ---
BM25_NODES_PATH: str = _config.get('etl.retrieval.bm25.nodes_path', str(INDEX_PATH / 'bm25_nodes.pkl'))
STOPWORDS_PATH: str = _config.get('etl.retrieval.bm25.stopwords_path', str(NLTK_PATH / 'hit_stopwords.txt'))
BM25_ENABLE_CHUNKING: bool = _config.get('etl.retrieval.bm25.enable_chunking', False)

# --- Elasticsearch 索引相关配置 ---
ES_HOST: str = _config.get('etl.data.elasticsearch.host', 'localhost')
ES_PORT: int = _config.get('etl.data.elasticsearch.port', 9200)
ES_INDEX_NAME: str = _config.get('etl.data.elasticsearch.index', 'nkuwiki')
ES_ENABLE_CHUNKING: bool = _config.get('etl.data.elasticsearch.enable_chunking', False)

# --- 环境变量配置 ---
HF_ENDPOINT = _config.get('etl.data.models.hf_endpoint', 'https://hf-api.gitee.com')
HF_HOME = str(MODELS_PATH)
SENTENCE_TRANSFORMERS_HOME = HF_HOME
os.environ['HF_ENDPOINT'] = HF_ENDPOINT
os.environ['HF_HOME'] = HF_HOME
os.environ['SENTENCE_TRANSFORMERS_HOME'] = SENTENCE_TRANSFORMERS_HOME

# 创建必要的目录
for path in [BASE_PATH, RAW_PATH, CACHE_PATH, INDEX_PATH, QDRANT_PATH, MYSQL_PATH, NLTK_PATH, MODELS_PATH]:
    path.mkdir(parents=True, exist_ok=True)

# 导入nltk并设置下载路径
import nltk
nltk.data.path.append(str(NLTK_PATH.absolute()))

# 检查并下载NLTK资源
try:
    resources = ['wordnet', 'omw-1.4', 'wordnet2022', 'punkt', 'stopwords']
    for resource in resources:
        try:
            # 检查资源是否存在
            if resource == 'punkt':
                resource_path = NLTK_PATH / 'tokenizers' / resource
            else:
                resource_path = NLTK_PATH / 'corpora' / resource
            
            # 直接检查目录是否存在，而不是使用nltk.data.find
            if resource_path.exists():
                logger.debug(f"NLTK资源 {resource} 已存在: {resource_path}")
                continue
            
            # 如果不存在，尝试下载
            logger.warning(f"NLTK资源 {resource} 未找到，正在下载...")
            try:
                nltk.download(resource, download_dir=str(NLTK_PATH.absolute()), quiet=False)
                logger.debug(f"NLTK资源 {resource} 下载成功")
            except Exception as e:
                logger.error(f"NLTK资源 {resource} 下载失败: {e}")
                logger.warning(f"请手动执行: python -m nltk.downloader {resource} -d {str(NLTK_PATH.absolute())}")
        except Exception as e:
            logger.error(f"检查NLTK资源 {resource} 时出错: {e}")
except Exception as e:
    logger.error(f"NLTK资源检查失败: {e}")
    logger.warning(f"请确保已手动下载所需NLTK资源到: {str(NLTK_PATH.absolute())}")

# Qdrant配置
VECTOR_SIZE = _config.get('etl.data.qdrant.vector_size', 1024)

# --- 爬虫相关配置 ---
PROXY_POOL: str = _config.get("etl.crawler.proxy_pool", "http://127.0.0.1:7897")
MARKET_TOKEN: str = _config.get("etl.crawler.market_token", "")

# 版本信息
__version__ = "2.0.0"

# 定义导出的符号列表 
__all__ = [
    # 路径配置
    'BASE_PATH', 'RAW_PATH', 'CACHE_PATH', 'INDEX_PATH', 'QDRANT_PATH', 'MYSQL_PATH', 'NLTK_PATH',
    'MODELS_PATH',
    
    # 环境变量配置
    'HF_ENDPOINT', 'HF_HOME', 'SENTENCE_TRANSFORMERS_HOME',
    
    # 数据库配置
    'DB_HOST', 'DB_PORT', 'DB_USER', 'DB_PASSWORD', 'DB_NAME',
    'DB_POOL_RESIZE_INTERVAL', 'DB_POOL_MIN_SIZE', 'DB_POOL_MAX_SIZE', 'DB_POOL_MAX_OVERFLOW',

    # Qdrant配置
    'QDRANT_URL', 'QDRANT_TIMEOUT', 'QDRANT_API_KEY', 'QDRANT_COLLECTION', 'QDRANT_BATCH_SIZE', 'VECTOR_SIZE',
    
    # 爬虫配置
    'PROXY_POOL', 'MARKET_TOKEN',

    # 版本信息
    '__version__'
]

# ETL模块主要功能：
# 1. 数据抽取：通过crawler子模块实现各类数据源的爬取
# 2. 数据处理：通过processors子模块实现数据清洗和格式转换
# 3. 数据加载：通过load子模块实现数据的存储和索引
# 4. 索引构建：通过indexing子模块构建各种类型的索引
# 5. 数据检索：通过retrieval子模块实现文档的检索与排序
# 6. 嵌入计算：通过embedding子模块实现文档的向量化
# 7. PageRank计算：通过pagerank子模块计算网页权威性分数

# 可以在此处添加更多ETL相关的配置常量...
