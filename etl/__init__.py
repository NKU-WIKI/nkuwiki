"""
ETL模块，负责数据抽取、转换和加载
"""
import os
import re
import sys
import json
import time
import requests
from datetime import datetime, timedelta
from pathlib import Path
from loguru import logger
from typing import Dict, List, Any, Set, Union, Optional
sys.path.append(str(Path(__file__).resolve().parent.parent))
from config import Config
# 导入配置
config = Config()
config.load_config()

# ---------- 全局共享配置项 ----------
# 基础路径配置
BASE_PATH = config.get("data.base_path", "./etl/data")
RAW_PATH = BASE_PATH + config.get("data.raw.path", "/raw")
CACHE_PATH = BASE_PATH + config.get("data.cache.path", "/cache")
INDEX_PATH = BASE_PATH + config.get("data.index.path", "/index")
QDRANT_PATH = BASE_PATH + config.get("data.qdrant.path", "/qdrant")
LOG_PATH = str(Path(__file__).resolve().parent) + "/logs"
# 创建必要的目录
for path in [BASE_PATH, RAW_PATH, CACHE_PATH, INDEX_PATH, QDRANT_PATH, LOG_PATH]:
    Path(path).mkdir(exist_ok=True, parents=True)

# 环境变量配置
HF_ENDPOINT = config.get('etl.data.models.hf_endpoint', 'https://hf-api.gitee.com')
HF_HOME = config.get('etl.data.models.hf_home', './etl/data/models')
SENTENCE_TRANSFORMERS_HOME = config.get('etl.data.models.sentence_transformers_home', './etl/data/models')
NLTK_DATA = config.get('etl.data.nltk.path', './etl/data/nltk_data/')

# 设置环境变量
os.environ["HF_ENDPOINT"] = HF_ENDPOINT
os.environ["HF_HOME"] = HF_HOME
os.environ["SENTENCE_TRANSFORMERS_HOME"] = SENTENCE_TRANSFORMERS_HOME
os.environ['NLTK_DATA'] = NLTK_DATA

# 设置日志
LOG_DIR = Path(LOG_PATH)
LOG_DIR.mkdir(exist_ok=True, parents=True)
logger.add(LOG_DIR / "etl.log", rotation="1 day", retention="3 months", level="INFO")

# 数据库配置
DB_HOST = config.get('mysql.host', '127.0.0.1')
DB_PORT = config.get('mysql.port', 3306)
DB_USER = config.get('mysql.user', 'root')
DB_PASSWORD = config.get('mysql.password', '')
DB_NAME = config.get('mysql.name', 'mysql')

# 版本信息
__version__ = "1.0.0"

# 定义导出的符号列表 
__all__ = [
    # 基础库和工具
    'os', 'sys', 'Path', 'logger', 'config','re','json','time','datetime','Dict', 'List', 'Optional', 'Any', 'Set', 'datetime', 'timedelta','Union','requests',

    # 路径配置
    'BASE_PATH', 'RAW_PATH', 'CACHE_PATH', 'INDEX_PATH', 'QDRANT_PATH', 'LOG_PATH',
    
    # 环境变量配置
    'HF_ENDPOINT', 'HF_HOME', 'SENTENCE_TRANSFORMERS_HOME', 'NLTK_DATA',
    
    # 数据库配置
    'DB_HOST', 'DB_PORT', 'DB_USER', 'DB_PASSWORD', 'DB_NAME'
]

# etl模块的公用配置和包
# 该模块负责数据抽取、转换和加载，提供了全局共享的配置项和工具函数。
# 包含子模块：crawler, load, transform, retrieval, embedding, api, data, utils
# 提供的全局配置包括路径配置、环境变量配置和数据库配置。
