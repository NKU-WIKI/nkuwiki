"""
API模块，提供检索和生成服务的接口
"""
import os
import sys
import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from loguru import logger
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
import asyncio
import mysql.connector
from datetime import datetime

from config import Config

# 导入配置
config = Config()
config.load_config()

# API服务配置
API_HOST = "0.0.0.0"
API_PORT = 8000

# Qdrant配置
QDRANT_URL = config.get('etl.data.qdrant.url', 'http://localhost:6333')
QDRANT_TIMEOUT = config.get('etl.data.qdrant.timeout', 30.0)
EMBEDDING_NAME = config.get('etl.embedding.name', 'BAAI/bge-base-zh')
AUTO_FIX_MODEL = config.get('etl.auto_fix_model', True)

# 数据库配置
DB_HOST = config.get('etl.data.mysql.host', '127.0.0.1')
DB_PORT = config.get('etl.data.mysql.port', 3306)
DB_USER = config.get('etl.data.mysql.user', 'root')
DB_PASSWORD = config.get('etl.data.mysql.password', '')
DB_NAME = config.get('etl.data.mysql.name', 'mysql')

# 日志设置
LOG_DIR = Path(__file__).parent / "logs"
LOG_DIR.mkdir(exist_ok=True, parents=True)

# 创建API模块专用logger
api_logger = logger.bind(module="api")
logger.add(LOG_DIR / "api.log", rotation="1 day", retention="3 months", level="INFO")

# 创建FastAPI应用
app = FastAPI(title="ETL API", description="检索和生成服务API")

# 数据库连接函数
def get_conn(use_database=True):
    """带容错机制的数据库连接"""
    params = {
        'host': DB_HOST,
        'port': DB_PORT,
        'user': DB_USER,
        'password': DB_PASSWORD,
        'charset': 'utf8mb4',
        'autocommit': True
    }
    
    if use_database:
        params['database'] = DB_NAME
    
    try:
        api_logger.debug(f"尝试连接数据库：host={DB_HOST} user={DB_USER}")
        conn = mysql.connector.connect(**params)
        return conn
    except Exception as e:
        api_logger.error(f"数据库连接失败: {str(e)}")
        raise 