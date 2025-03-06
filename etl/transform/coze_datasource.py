import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent)) 

from fastapi import FastAPI, Request, HTTPException
from contextlib import asynccontextmanager
from pydantic import BaseModel, Field
import mysql.connector
from typing import List, Dict, Any
from datetime import datetime
from config import Config
from etl.transform import transform_logger
from fastapi.middleware.cors import CORSMiddleware
from json import JSONDecodeError
Config().load_config()

# 使用模块专用logger
transform_logger.bind(service="coze_datasource")


def get_conn(use_database=True):
    """带容错机制的数据库连接"""
    params = {
        'host': Config().get("etl.data.mysql.host"),  # 需改为数据库服务器真实IP（非localhost）
        'port': Config().get("etl.data.mysql.port"),
        'user': Config().get("etl.data.mysql.user"),  # 确认该用户有远程访问权限
        'password': Config().get("etl.data.mysql.password"),  # 确认密码正确
        'charset': 'utf8mb4',
        'autocommit': True
    }
    
    if use_database:
        params['database'] = Config().get("etl.data.mysql.name")
    
    transform_logger.debug(f"尝试连接数据库：host={Config().get('etl.data.mysql.host')} user={Config().get('etl.data.mysql.user')}")
    try:
        conn = mysql.connector.connect(**params)
        transform_logger.debug("数据库连接成功")
        return conn
    except mysql.connector.Error as e:
        transform_logger.error(f"数据库连接失败: {str(e)}")
        raise

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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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



@app.api_route("/query", methods=["POST", "GET"], response_model=QueryResult,
         summary="执行原始SQL查询",
         description="GET请求不带参数时返回服务状态，带SQL参数执行查询；POST请求执行标准查询",
         response_description="包含列名和行数据的查询结果")
async def execute_query(request: Request):
    try:
        # 处理GET无参请求（返回指定字段CSV）
        if request.method == "GET" and not request.query_params:
            with get_conn() as conn:
                with conn.cursor(dictionary=True) as cur:
                    cur.execute("""
                        SELECT title, original_url, author, publish_time 
                        FROM wechat_articles 
                        ORDER BY publish_time DESC 
                        LIMIT 100
                    """)
                    
                    from fastapi.responses import StreamingResponse
                    import io
                    import csv

                    output = io.StringIO()
                    writer = csv.writer(output)
                    # 指定字段顺序
                    columns = ["title", "original_url", "author", "publish_time"]
                    writer.writerow(columns)
                    
                    for row in cur.fetchall():
                        writer.writerow([row[col] for col in columns])
                    
                    output.seek(0)
                    return StreamingResponse(
                        iter([output.getvalue()]),
                        media_type="text/csv",
                        headers={"Content-Disposition": "attachment; filename=articles_export.csv"}
                    )
            
        # 统一处理GET/POST参数
        params = await request.json() if request.method == "POST" else dict(request.query_params)
        
        sql = params.get("sql")
        if not sql:
            raise HTTPException(status_code=422, detail="缺少必要参数: sql")
            
        # 过滤掉sql参数本身
        query_params = {k: v for k, v in params.items() if k != "sql"}

        with get_conn() as conn:
            with conn.cursor(dictionary=True) as cur:
                cur.execute(sql, query_params)
                
                # 新增CSV响应处理
                if request.method == "GET":
                    from fastapi.responses import StreamingResponse
                    import io
                    import csv

                    output = io.StringIO()
                    writer = csv.writer(output)
                    
                    # 写入列头
                    columns = [col[0] for col in cur.description] if cur.description else []
                    writer.writerow(columns)
                    
                    # 写入数据行
                    for row in cur.fetchall():
                        writer.writerow([row[col] for col in columns])
                    
                    output.seek(0)
                    return StreamingResponse(
                        iter([output.getvalue()]),
                        media_type="text/csv",
                        headers={"Content-Disposition": "attachment; filename=export.csv"}
                    )
                
                # 原有JSON响应
                columns = [col[0] for col in cur.description] if cur.description else []
                data = [dict(row) for row in cur.fetchall()] if columns else []
                
                return QueryResult(columns=columns, data=data)

    except JSONDecodeError:
        raise HTTPException(400, "请求格式错误：需要JSON格式")
    except mysql.connector.Error as e:
        transform_logger.error(f"SQL执行错误: {str(e)}")
        raise HTTPException(500, "数据库查询失败")
    except Exception as e:
        transform_logger.error(f"服务器错误: {str(e)}")
        raise HTTPException(500, "服务器内部错误")

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
                    SELECT title, original_url, author, publish_time, content 
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
                        for title, content, publish_time, original_url, author in cur.fetchall()
                    ]
                }
                
    except Exception as e:
        transform_logger.exception(f"检索失败: {str(e)}")

@app.post("/openapi.json")
async def get_openapi():
    return app.openapi()

@app.middleware("http")
async def log_requests(request: Request, call_next):
    transform_logger.info(f"收到请求: {request.method} {request.url}")
    try:
        response = await call_next(request)
    except Exception as e:
        transform_logger.error(f"请求处理失败: {str(e)}")
        raise
    transform_logger.debug(f"响应状态码: {response.status_code}")
    return response

# 启动时指定host和port
if __name__ == "__main__":
    # 打印调试信息
    transform_logger.debug("\n=== 服务启动调试信息 ===")
    transform_logger.debug(f"数据库端口：{Config().get('etl.data.mysql.port')}")
    transform_logger.debug(f"环境文件路径：{Config().get('etl.data.mysql.host')}")

    transform_logger.debug("\n=== 已注册路由 ===")
    for route in app.routes:
        transform_logger.debug(f"{route.path} -> {route.methods}")
    transform_logger.debug("===================\n")
    
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        # ssl_keyfile=Config().get("ssl_key_path", "ssl/private.key"),
        # ssl_certfile=Config().get("ssl_cert_path", "ssl/certificate.pem"),
        access_log=True,
        log_level="debug"  # 添加详细日志
    ) 