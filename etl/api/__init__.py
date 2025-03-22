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

from .data_api import register_data_api
from .wxapp_export import register_api as register_wxapp_export_api

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

def register_all_apis(app):
    """
    注册所有API到Flask应用
    
    Args:
        app: Flask应用实例
    """
    # 注册数据API
    register_data_api(app)
    
    # 注册微信小程序数据导出API
    register_wxapp_export_api(app)
    
    logger.debug("已注册所有ETL API模块")
