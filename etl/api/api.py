# -*- coding: UTF-8 -*-
import os

import uvicorn
from fastapi import FastAPI, status, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from config import Config
from etl.retrieval.pipeline import EasyRAGPipeline


class QueryRequest(BaseModel):
    query: str = ""
    document: str = ""


class QueryResponse(BaseModel):
    answer: str = ""
    contexts: list[str] = []


def create_app() -> FastAPI:
    app = FastAPI()

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    return app


# 直接初始化EasyRAGPipeline
easyrag = EasyRAGPipeline()

app = create_app()


@app.get("/test")
def test():
    return "hello rag"


@app.post("/v1/rag", status_code=status.HTTP_200_OK)
async def rag(request: QueryRequest):
    # query对象: {"query":"Daisyseed安装软件从哪里获取", "document":"director"}
    query = {"query": request.query, "document": request.document}
    res = easyrag.run(query)
    result = {
        "answer": res["answer"],
        "contexts": res["contexts"],
    }
    return result


class Query(BaseModel):
    query: str
    top_k: int = 5
    threshold: float = 0.5


@app.post("/query")
async def query(query: Query):
    try:
        # 从Config获取配置
        config = {}
        config['qdrant_url'] = Config().get('etl.data.qdrant.url', "http://localhost:6334")
        config['qdrant_timeout'] = Config().get('etl.data.qdrant.timeout', 30.0)
        config['embedding_name'] = Config().get('etl.embedding.name', 'BAAI/bge-base-zh')
        config['auto_fix_model'] = Config().get('etl.auto_fix_model', True)
        
        pipeline = EasyRAGPipeline()
        response = pipeline.query(query.query, top_k=query.top_k, threshold=query.threshold)
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
