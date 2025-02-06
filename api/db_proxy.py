from fastapi import FastAPI, Security, HTTPException, Query
from fastapi.security import APIKeyHeader
from pydantic import BaseModel
import mysql.connector
from typing import Optional, List
import os
import json

app = FastAPI(
    title="NKU知识库网关",
    description="为HiAgent提供结构化数据访问接口",
    version="1.0.0"
)
api_key_header = APIKeyHeader(name="Authorization")

class HiAgentRequest(BaseModel):
    query: str
    top_k: int = 5

class Document(BaseModel):
    content: str
    metadata: dict

def get_conn():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        charset='utf8mb4'
    )

@app.post("/v1/retrieve")
async def hiagent_retrieve(
    request: HiAgentRequest,
    api_key: str = Security(api_key_header)
):
    """HiAgent标准检索接口"""
    if api_key != f"Bearer {os.getenv('HIAGENT_API_KEY')}":
        raise HTTPException(401, "Invalid credentials")
    
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
        raise HTTPException(500, f"检索失败: {str(e)}")

@app.get("/openapi.json")
async def get_openapi():
    return app.openapi() 