import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent)) 

from fastapi import FastAPI
from contextlib import asynccontextmanager
from pydantic import BaseModel
import mysql.connector
from typing import List, Dict, Any
from datetime import datetime
from config import Config
from loguru import logger


logger.add(Path(__file__).parent / "logs" / "coze_integration.log", rotation="1 day",retention="3 months", level = "INFO")


def get_conn(use_database=True):
    """带容错机制的数据库连接"""
    params = {
        'host': Config().get("db_host"),
        'port': Config().get("db_port"),
        'user': Config().get("db_user"),
        'password': Config().get("db_password"),
        'charset': 'utf8mb4',
        'unix_socket': '/var/run/mysqld/mysqld.sock',
        'autocommit': True
    }
    
    if use_database:
        params['database'] = Config().get("db_name")
    
    return mysql.connector.connect(**params)

def serialize_datetime(obj):
    """处理日期时间序列化"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 服务启动时执行
    print("\n=== 已注册路由 ===")
    for route in app.routes:
        print(f"{route.path} -> {route.methods}")
    print("=================\n")
    yield

app = FastAPI(
    title="NKU知识库网关",
    description="提供安全的数据查询接口",
    version="2.0.0",
    lifespan=lifespan  # 添加生命周期管理
)

class HiAgentRequest(BaseModel):
    query: str
    top_k: int = 5

class Document(BaseModel):
    content: str
    metadata: dict

class QueryRequest(BaseModel):
    sql: str
    class Config:
        extra = "allow"  # 允许接收额外字段

class QueryResult(BaseModel):
    columns: List[str]
    data: List[Dict[str, Any]]



@app.post("/query", response_model=QueryResult)
async def execute_query(request: QueryRequest):
    """
    通用SQL查询接口（POST版）
    - 示例请求体：
    {
        "sql": "SELECT * FROM table WHERE name = %(name)s",
        "name": "value"
    }
    """
    try:
        # 提取除sql外的所有参数
        params = request.dict(exclude={'sql'})
        
        with get_conn() as conn:
            with conn.cursor(dictionary=True) as cur:
                cur.execute(request.sql, params)
                
                if cur.description:
                    columns = [col[0] for col in cur.description]
                    data = [
                        {col: row[col] for col in columns} 
                        for row in cur.fetchall()
                    ]
                else:
                    columns = []
                    data = []
                
                return QueryResult(columns=columns, data=data)
                
    except mysql.connector.Error as e:
        logger.error(f"SQL执行错误: {str(e)}")
    except Exception as e:
        logger.error(f"服务器错误: {str(e)}")

@app.post("/v1/retrieve")
async def hiagent_retrieve(request: HiAgentRequest):
    """HiAgent标准检索接口"""
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT title, content, publish_time, original_url 
                    FROM wechat_articles 
                    WHERE MATCH(title, content) AGAINST(%s IN NATURAL LANGUAGE MODE)
                    ORDER BY publish_time DESC
                    LIMIT %s
                """, (request.query, request.top_k))
                
                return {
                    "documents": [
                        {
                            "content": f"{title}\n{content}",
                            "metadata": {
                                "publish_time": publish_time.isoformat(),
                                "source": original_url
                            }
                        }
                        for title, content, publish_time, original_url in cur.fetchall()
                    ]
                }
                
    except Exception as e:
        logger.exception(f"检索失败: {str(e)}")

@app.post("/openapi.json")
async def get_openapi():
    return app.openapi()

# 启动时指定host和port
if __name__ == "__main__":
    # 打印调试信息
    logger.debug("\n=== 服务启动调试信息 ===")
    logger.debug(f"数据库端口：{Config().get('db_port')}")
    logger.debug(f"环境文件路径：{Config().get('db_host')}")

    logger.debug("\n=== 已注册路由 ===")
    for route in app.routes:
        logger.debug(f"{route.path} -> {route.methods}")
    logger.debug("===================\n")
    
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 