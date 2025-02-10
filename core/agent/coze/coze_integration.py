# from fastapi import FastAPI, HTTPException, Query, Depends
# from contextlib import asynccontextmanager
# from pydantic import BaseModel
# import mysql.connector
# from typing import Optional, List, Dict, Any
# import os
# import json
# from dotenv import load_dotenv
# from pathlib import Path
# from datetime import datetime

# # 从项目根目录加载.env文件

# # 正确加载方式：显式指定.env文件路径
# env_path = Path("/home/nkuwiki/nkuwiki/.env")  # 硬编码绝对路径
# load_dotenv(env_path)  # ✅ 在模块顶层加载

# # 在代码中添加路径验证
# print(f"正在加载环境文件：{env_path}")
# print(f"文件存在：{env_path.exists()}")
# print(f"文件内容：{env_path.read_text()}")

# # 在加载环境变量后立即验证
# print(f"验证环境变量：DB_PORT={os.getenv('DB_PORT')}")

# # 在环境变量加载后添加验证
# print(f"\n=== 环境变量验证 ===")
# print(f"DB_HOST: {os.getenv('DB_HOST')}")
# print(f"DB_PORT: {os.getenv('DB_PORT')}")
# print(f"DB_USER: {os.getenv('DB_USER')}")
# print(f"DB_NAME: {os.getenv('DB_NAME')}")
# print("==================\n")

# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     # 服务启动时执行
#     print("\n=== 已注册路由 ===")
#     for route in app.routes:
#         print(f"{route.path} -> {route.methods}")
#     print("=================\n")
#     yield

# app = FastAPI(
#     title="NKU知识库网关",
#     description="提供安全的数据查询接口",
#     version="2.0.0",
#     lifespan=lifespan  # 添加生命周期管理
# )

# class HiAgentRequest(BaseModel):
#     query: str
#     top_k: int = 5

# class Document(BaseModel):
#     content: str
#     metadata: dict

# class QueryRequest(BaseModel):
#     sql: str
#     class Config:
#         extra = "allow"  # 允许接收额外字段

# class QueryResult(BaseModel):
#     columns: List[str]
#     data: List[Dict[str, Any]]

# def get_conn():
#     """数据库连接池"""
#     # 使用标准logging模块
#     import logging
#     logger = logging.getLogger(__name__)
    
#     logger.debug(f"""
#     [DEBUG] 数据库连接配置：
#     HOST: {os.getenv('DB_HOST')}
#     PORT: {os.getenv('DB_PORT')}
#     USER: {os.getenv('DB_USER')}
#     DB: {os.getenv('DB_NAME')}
#     """)
    
#     return mysql.connector.connect(
#         host=os.getenv("DB_HOST"),
#         port=3306,  # 硬编码测试
#         user=os.getenv("DB_USER"),
#         password=os.getenv("DB_PASSWORD"),
#         database=os.getenv("DB_NAME"),
#         charset='utf8mb4'
#     )

# def serialize_datetime(obj):
#     """处理日期时间序列化"""
#     if isinstance(obj, datetime):
#         return obj.isoformat()
#     raise TypeError(f"Type {type(obj)} not serializable")

# @app.post("/query", response_model=QueryResult)
# async def execute_query(request: QueryRequest):
#     """
#     通用SQL查询接口（POST版）
#     - 示例请求体：
#     {
#         "sql": "SELECT * FROM table WHERE name = %(name)s",
#         "name": "value"
#     }
#     """
#     try:
#         # 提取除sql外的所有参数
#         params = request.dict(exclude={'sql'})
        
#         with get_conn() as conn:
#             with conn.cursor(dictionary=True) as cur:
#                 cur.execute(request.sql, params)
                
#                 if cur.description:
#                     columns = [col[0] for col in cur.description]
#                     data = [
#                         {col: row[col] for col in columns} 
#                         for row in cur.fetchall()
#                     ]
#                 else:
#                     columns = []
#                     data = []
                
#                 return QueryResult(columns=columns, data=data)
                
#     except mysql.connector.Error as e:
#         raise HTTPException(400, f"SQL执行错误: {str(e)}")
#     except Exception as e:
#         raise HTTPException(500, f"服务器错误: {str(e)}")

# @app.post("/v1/retrieve")
# async def hiagent_retrieve(request: HiAgentRequest):
#     """HiAgent标准检索接口"""
#     try:
#         with get_conn() as conn:
#             with conn.cursor() as cur:
#                 cur.execute("""
#                     SELECT title, content, publish_time, original_url 
#                     FROM wechat_articles 
#                     WHERE MATCH(title, content) AGAINST(%s IN NATURAL LANGUAGE MODE)
#                     ORDER BY publish_time DESC
#                     LIMIT %s
#                 """, (request.query, request.top_k))
                
#                 return {
#                     "documents": [
#                         {
#                             "content": f"{title}\n{content}",
#                             "metadata": {
#                                 "publish_time": publish_time.isoformat(),
#                                 "source": original_url
#                             }
#                         }
#                         for title, content, publish_time, original_url in cur.fetchall()
#                     ]
#                 }
                
#     except Exception as e:
#         raise HTTPException(500, f"检索失败: {str(e)}")

# @app.get("/openapi.json")
# async def get_openapi():
#     return app.openapi()

# # 启动时指定host和port
# if __name__ == "__main__":
#     # 打印调试信息
#     print("\n=== 服务启动调试信息 ===")
#     print(f"数据库端口：{os.getenv('DB_PORT')}")
#     print(f"环境文件路径：{env_path}")
    
#     print("\n=== 已注册路由 ===")
#     for route in app.routes:
#         print(f"{route.path} -> {route.methods}")
#     print("===================\n")
    
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8000) 