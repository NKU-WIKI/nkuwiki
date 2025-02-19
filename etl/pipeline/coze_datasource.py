import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent)) 

from fastapi import FastAPI
from contextlib import asynccontextmanager
from pydantic import BaseModel, Field
import mysql.connector
from typing import List, Dict, Any
from datetime import datetime
from config import Config
from loguru import logger


logger.add(Path(__file__).parent / "logs" / "coze_datasource.log", rotation="1 day",retention="3 months", level = "INFO")


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
    query: str = Field(..., description="用户查询的问题内容")
    top_k: int = Field(5, description="返回结果数量", ge=1, le=20)

class Document(BaseModel):
    content: str
    metadata: dict

class QueryRequest(BaseModel):
    sql: str = Field(..., example="SELECT * FROM table WHERE id = %(id)s", 
                   description="参数化SQL语句，使用%(param)s格式")
    class Config:
        extra = "allow"

class QueryResult(BaseModel):
    columns: List[str] = Field(..., example=["id", "name"], description="数据列名称")
    data: List[Dict[str, Any]] = Field(..., example=[{"id":1}], description="行数据字典列表")



@app.post("/query", response_model=QueryResult,
         summary="执行原始SQL查询",
         description="支持参数化查询，使用%(name)s占位符格式",
         response_description="包含列名和行数据的查询结果")
async def execute_query(request: QueryRequest):
    """
    通用SQL查询接口
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

@app.post("/v1/retrieve",
         summary="标准文档检索接口",
         description="基于自然语言匹配微信文章内容",
         response_description="包含文档内容和元数据的结果列表",
         response_model=Dict[str, List[Document]])
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