# API模块开发指南

## 模块概述

api 模块提供了对外的服务接口，用于将 ETL 处理后的数据以 API 的形式提供给其他系统使用。包括 RESTful API 接口和 WebUI 界面。

## 文件结构

- `__init__.py` - 模块入口，定义了导出的函数和类
- `api.py` - RESTful API 实现
- `webui.py` - Web 用户界面实现
- `coze_datasource.py` - Coze 数据源集成

## 开发新 API 端点

1. **创建新端点**:

```python
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

# 定义请求模型
class SearchRequest(BaseModel):
    query: str
    top_k: int = 5

# 创建路由
router = APIRouter()

@router.post("/search")
async def search_endpoint(request: SearchRequest):
    """
    搜索接口
    """
    try:
        # 实现搜索逻辑
        results = perform_search(request.query, request.top_k)
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

1. **集成到主 API 应用**:

```python
from fastapi import FastAPI
from etl.api.my_endpoints import router as my_router

app = FastAPI(title="ETL API")
app.include_router(my_router, prefix="/my-api", tags=["My API"])
```

## WebUI 开发

为数据可视化和交互添加 WebUI 组件：

```python
import streamlit as st

def create_search_page():
    st.title("搜索界面")
    
    # 用户输入
    query = st.text_input("请输入搜索词")
    top_k = st.slider("返回结果数量", 1, 20, 5)
    
    if st.button("搜索"):
        # 调用 API
        results = call_search_api(query, top_k)
        
        # 显示结果
        for i, result in enumerate(results):
            st.subheader(f"结果 {i+1}")
            st.write(result["content"])
            st.write(f"相关度: {result['score']}")
```

## Coze 数据源集成

使用 `coze_datasource.py` 将数据集成到 Coze 平台：

```python
from etl.api.coze_datasource import CozeDatasource

# 创建 Coze 数据源
datasource = CozeDatasource(
    name="我的数据源",
    description="ETL 处理后的数据",
    vector_store="qdrant",
    collection_name="my_collection"
)

# 注册数据源
datasource.register()
```

## 注意事项

1. **安全性**: 实现适当的认证和授权机制
1. **性能优化**: 对于高频调用的 API，考虑实现缓存
1. **错误处理**: 提供清晰的错误信息和错误码
1. **版本控制**: 考虑实现 API 版本控制，确保兼容性
1. **文档生成**: 使用 FastAPI 的自动文档功能，保持文档更新

## 调试与测试

1. 运行 API 服务:

```bash
uvicorn etl.api.api:app --host 0.0.0.0 --port 8000 --reload
```

1. 运行 WebUI:

```bash
streamlit run etl/api/webui.py
```

## 参考

- 查看 `api.py` 了解 API 开发的最佳实践
- 参考 `webui.py` 了解 WebUI 实现方法

---

EasyRAG: Efficient Retrieval-Augmented Generation Framework for Automated Network Operations

[![license](https://img.shields.io/github/license/mashape/apistatus.svg?maxAge=2592000)](https://github.com/BUAADreamer/EasyRAG/blob/main/licence)
[![arxiv badge](https://img.shields.io/badge/arxiv-2410.10315-red)](https://arxiv.org/abs/2410.10315)
[![GitHub Repo stars](https://img.shields.io/github/stars/BUAADreamer/EasyRAG?style=social)](https://github.com/BUAADreamer/EasyRAG/stargazers)
[![zhihu blog](https://img.shields.io/badge/zhihu-Blog-informational)](https://zhuanlan.zhihu.com/p/7272025344)

## 目录

- [概述](#概述)
- [要求](#要求)
- [复现](#复现)
- [使用方法](#使用方法)
- [项目结构](#项目结构)
- [引用](#引用)
- [致谢](#致谢)

## 概述

本文介绍了EasyRAG，这是一个简单、轻量级且高效的检索增强生成框架，用于自动化网络运维。我们的框架有三个优势。首先是准确的问答能力。我们设计了一个直接的RAG方案，基于(1)特定的数据处理工作流(2)双路稀疏检索进行粗排(3)LLM重排序器进行重排(4)LLM答案生成和优化。这一方法在初赛中获得了GLM4赛道的第一名，在半决赛中获得了GLM4赛道的第二名。其次是简单部署。我们的方法主要由BM25检索和BGE-reranker重排组成，无需微调任何模型，占用极少的VRAM，易于部署且高度可扩展；我们提供了一个灵活的代码库，具有各种搜索和生成策略，便于自定义过程实现。最后是高效推理。我们为整个粗排、重排和生成过程设计了一个高效的推理加速方案，显著减少了RAG的推理延迟，同时保持了良好的准确度；每个加速方案都可以即插即用到RAG过程的任何组件中，持续提高RAG系统的效率。

![系统概览](assets/overview.png)

## 要求

EasyRAG需要Python3.10.14和至少1个16GB的GPU。

您需要将`src/easyrag.yaml`中的`llm_keys`更改为您的GLM密钥。

```shell
pip install -r requirements.txt
git lfs install
bash scripts/download.sh # 下载模型
bash scripts/process.sh # 处理zedx数据
```

## 复现

### 1. 直接运行

```bash
cd src
# 运行挑战问题
python3 main.py 
# 复制答案文件
cp submit_result.jsonl ../answer.jsonl
```

### 2. 使用Docker运行

```bash
chmod +x scripts/run.sh
./scripts/run.sh
```

## 使用方法

### 1. API

```bash
cd src
uvicorn api:app --host 0.0.0.0 --port 8000 --workers 1
```

### 2. WebUI

您需要先运行API

```bash
cd src
streamlit run webui.py
```

## 项目结构

仅解释半决赛中可能使用的代码。

```yaml
- src
    - custom
        - splitter.py # 自定义分块器
        - hierarchical.py # 分层分块器
        - transformation.py # 文件路径和标题提取
        - embeddings # 为GTE实现单独的嵌入类
            - ...
        - retrievers.py # 实现基于qdrant的密集检索器、中文BM25检索器、带有rrf和简单合并的融合检索器
        - rerankers.py # 为bge系列重排序器实现一些单独的类，便于自定义使用
        - template.py # QA提示模板
    - pipeline
        - ingestion.py # 数据处理流程：数据读取器、元数据提取、文档分块、文档编码、元数据过滤器、向量数据库创建
        - pipeline.py # EasyRAG管道类，包含各种数据和模型的初始化，自定义RAG管道定义
        - rag.py # 一些RAG的工具函数
        - qa.py # 读取问题文件并保存答案
    - utils # 适用于中国的hf自适应自定义llm，直接从相应模型hf链接中的代码复制而来
        - ...
    - configs
        - easyrag.yaml # 配置文件
    - data
        - nltk_data # nltk中的停用词列表和分词器数据
        - hit_stopwords.txt # 哈工大中文停用词表
        - imgmap_filtered.json # 由get_ocr_data.py处理
        - question.jsonl # 半决赛测试集
    - main.py # 主函数，入口文件
    - api.py # FastAPI服务
    - preprocess_zedx.py # zedx数据预处理
    - get_ocr_data.py # paddleocr+glm4v提取图像内容
    - submit.py # 向挑战提交结果
- requirements.txt # python依赖
- run.sh # docker运行脚本
- Dockerfile # docker配置文件
```

## 引用

```latex
@article{feng2024easyrag,
  title={EasyRAG: Efficient Retrieval-Augmented Generation Framework for Automated Network Operations},
  author={Feng, Zhangchi, Kuang Dongdong, Wang Zhongyuan, Nie Zhijie, Zheng Yaowei and Zhang, Richong},
  journal={arXiv preprint arXiv:2410.10315},
  year={2024}
}
```

## 致谢

感谢[CCF AIOps 2024挑战赛组委会](https://competition.aiops-challenge.com/home/competition/1780211530478944282)，他们提供了高质量的数据和良好的氛围。
