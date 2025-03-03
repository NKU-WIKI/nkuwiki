# -*- coding: UTF-8 -*-
import os
import sys

# Add project root to PYTHONPATH
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

import uvicorn
from fastapi import FastAPI, status, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from config import Config
from etl.retrieval.pipeline import EasyRAGPipeline
from etl.utils import get_yaml_data


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


config_path = "configs/easyrag.yaml"
config = get_yaml_data(config_path)
easyrag = EasyRAGPipeline(config)

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
        config['qdrant_url'] = Config().get('qdrant_url', "http://localhost:6334")
        config['qdrant_timeout'] = Config().get('qdrant_timeout', 30.0)
        config['embedding_name'] = Config().get('embedding_name', 'BAAI/bge-base-zh')
        config['auto_fix_model'] = Config().get('auto_fix_model', True)
        
        pipeline = EasyRAGPipeline()
        response = pipeline.query(query.query, top_k=query.top_k, threshold=query.threshold)
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
