"""
API模块，提供检索和生成服务的接口
"""
# 从根模块导入共享配置
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from etl import *

import uvicorn
from fastapi import FastAPI, APIRouter, Path, Query, Body, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from etl.load import *

# API服务配置
API_HOST = "0.0.0.0"
API_PORT = 8000

# 创建api模块专用logger
api_logger = logger.bind(module="api")
log_path = LOG_PATH / 'api.log'
log_format = "{time:YYYY-MM-DD HH:mm:ss} | {level} | {module} | {message}"
logger.configure(
    handlers=[
        {"sink": sys.stdout, "format": log_format},
        {"sink": log_path, "format": log_format, "rotation": "1 day", "retention": "3 months", "level": "INFO"},
    ]
)

__all__ = [
    'json','time','tqdm','asyncio','Path',
    'Dict','List','Tuple','Optional','Any','Union',
    'api_logger', 'API_HOST', 'API_PORT', 'FastAPI','uvicorn','datetime','BaseModel','Field',
    'APIRouter','Path','Query','Body','HTTPException','CORSMiddleware',
    'EasyRAGPipeline','get_node_content'
]
