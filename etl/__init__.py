"""
ETL模块，负责数据抽取、转换和加载
"""
import os
import re
import sys
import json
import time
import requests
import asyncio
from tqdm.auto import tqdm
from datetime import datetime, timedelta
from pathlib import Path
from loguru import logger
from typing import Dict, List, Any, Set, Tuple, Union, Optional
from collections import defaultdict
sys.path.append(str(Path(__file__).resolve().parent.parent))
from config import Config
# 导入配置
config = Config()
config.load_config()

# ---------- 全局共享配置项 ----------
# 基础路径配置
BASE_PATH = Path(config.get("etl.data.base_path", "./etl/data"))
RAW_PATH = BASE_PATH / config.get("etl.data.raw.path", "/raw").lstrip("/")
CACHE_PATH = BASE_PATH / config.get("etl.data.cache.path", "/cache").lstrip("/")
INDEX_PATH = BASE_PATH / config.get("etl.data.index.path", "/index").lstrip("/")
QDRANT_PATH = BASE_PATH / config.get("etl.data.qdrant.path", "/qdrant").lstrip("/")
NLTK_PATH = BASE_PATH / config.get("etl.data.nltk.path", "/nltk").lstrip("/")
LOG_PATH = Path(__file__).resolve().parent / "logs"
# 创建必要的目录
for path in [BASE_PATH, RAW_PATH, CACHE_PATH, INDEX_PATH, QDRANT_PATH, NLTK_PATH, LOG_PATH]:
    path.mkdir(parents=True, exist_ok=True)

# 环境变量配置
HF_ENDPOINT = config.get('etl.data.models.hf_endpoint', 'https://hf-api.gitee.com')
HF_HOME = config.get("etl.data.base_path", "./etl/data") + config.get('etl.data.models.hf_home', '/models')
SENTENCE_TRANSFORMERS_HOME = HF_HOME
NLTK_DATA_PATH = str(NLTK_PATH.absolute())

# 设置环境变量 - 必须在导入nltk前设置
os.environ["HF_ENDPOINT"] = HF_ENDPOINT
os.environ["HF_HOME"] = HF_HOME
os.environ["SENTENCE_TRANSFORMERS_HOME"] = SENTENCE_TRANSFORMERS_HOME
os.environ['NLTK_DATA'] = NLTK_DATA_PATH

# 设置日志目录
LOG_PATH.mkdir(exist_ok=True, parents=True)

logger.add(LOG_PATH / "etl.log", rotation="1 day", retention="3 months", level="INFO")

import nltk
# 检查并下载NLTK资源
try:
    resources = ['wordnet.zip', 'omw-1.4.zip', 'wordnet2022.zip']
    for resource in resources:
        try:
            nltk.data.find(f'corpora/{resource}')
            logger.debug(f"NLTK资源 {resource} 已安装")
        except LookupError:
            logger.warning(f"NLTK资源 {resource} 未找到，正在下载...")
            try:
                nltk.download(resource, download_dir=NLTK_DATA_PATH, quiet=False)
                logger.debug(f"NLTK资源 {resource} 下载成功")
            except Exception as e:
                logger.error(f"NLTK资源 {resource} 下载失败: {e}")
                logger.warning(f"请手动执行: python -m nltk.downloader {resource} -d {NLTK_DATA_PATH}")
except Exception as e:
    logger.error(f"NLTK资源检查失败: {e}")
    logger.warning(f"请确保已手动下载所需NLTK资源到: {NLTK_DATA_PATH}")

# 数据库配置
DB_HOST = config.get('etl.data.mysql.host', '127.0.0.1')
DB_PORT = config.get('etl.data.mysql.port', 3306)
DB_USER = config.get('etl.data.mysql.user', 'root')
DB_PASSWORD = config.get('etl.data.mysql.password', '')
DB_NAME = config.get('etl.data.mysql.name', 'mysql')

# Qdrant配置
QDRANT_URL = config.get('etl.data.qdrant.url', 'http://localhost:6333')
QDRANT_TIMEOUT = config.get('etl.data.qdrant.timeout', 30.0)
COLLECTION_NAME = config.get('etl.data.qdrant.collection', 'main_index')
VECTOR_SIZE = config.get('etl.data.qdrant.vector_size', 1024)

# 版本信息
__version__ = "1.0.0"

# 定义导出的符号列表 
__all__ = [
    # 基础库和工具
    'os', 'sys', 'Path', 'logger', 'config','re','json','time','datetime','Dict', 'List', 'Tuple',
    'Optional', 'Any', 'Set', 'datetime', 'timedelta','Union','requests','asyncio','tqdm','defaultdict',
    # 路径配置
    'BASE_PATH', 'RAW_PATH', 'CACHE_PATH', 'INDEX_PATH', 'QDRANT_PATH', 'LOG_PATH','NLTK_PATH',
    
    # 环境变量配置
    'HF_ENDPOINT', 'HF_HOME', 'SENTENCE_TRANSFORMERS_HOME', 'NLTK_PATH',
    
    # 数据库配置
    'DB_HOST', 'DB_PORT', 'DB_USER', 'DB_PASSWORD', 'DB_NAME',

    # Qdrant配置
    'QDRANT_URL', 'QDRANT_TIMEOUT', 'COLLECTION_NAME', 'VECTOR_SIZE'
]

# etl模块的公用配置和包
# 该模块负责数据抽取、转换和加载，提供了全局共享的配置项和工具函数。
# 包含子模块：crawler, load, transform, retrieval, embedding, api, data, utils
# 提供的全局配置包括路径配置、环境变量配置和数据库配置。
