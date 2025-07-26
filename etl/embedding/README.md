# ETL Embedding 模块

## ⚠️ 重要说明

本模块正在重构中，部分功能已迁移到其他模块：

### 已迁移的功能 ✅

- **`get_node_content`** → 迁移到 `etl.utils.node_utils`
- **`merge_strings`** → 迁移到 `etl.utils.node_utils`  
- **索引构建功能** → 由 `etl.indexing` 模块统一处理
- **数据加载功能** → 由 `etl.load` 模块统一处理

### 保留的功能 📌

- **`hf_embeddings.py`** - HuggingFace嵌入模型实现
- **`gte_embeddings.py`** - GTE嵌入模型实现

### 已迁移的功能 ✅ (更新)

- **`hierarchical.py`** → 迁移到 `etl.transform.hierarchical`
- **`compressors.py`** → 迁移到 `etl.utils.compressors`
- **`get_node_content`** → 迁移到 `etl.utils.node_utils`
- **`merge_strings`** → 迁移到 `etl.utils.node_utils`  
- **索引构建功能** → 由 `etl.indexing` 模块统一处理
- **数据加载功能** → 由 `etl.load` 模块统一处理

### 已删除的功能 🗑️

- **`ingestion.py`** - 功能重复，已删除

## 使用建议

1. **对于节点内容提取**：
   ```python
   # 旧方式 (不推荐)
   from etl.embedding.ingestion import get_node_content
   
   # 新方式 (推荐)
   from etl.utils.node_utils import get_node_content
   ```

2. **对于层次化解析**：
   ```python
   # 旧方式 (不推荐)
   from etl.embedding.hierarchical import HierarchicalNodeParser
   
   # 新方式 (推荐)
   from etl.transform.hierarchical import HierarchicalNodeParser
   ```

3. **对于上下文压缩**：
   ```python
   # 旧方式 (不推荐)
   from etl.embedding.compressors import ContextCompressor
   
   # 新方式 (推荐)
   from etl.utils.compressors import ContextCompressor
   ```

4. **对于索引构建**：
   ```python
   # 使用etl.indexing模块
   from etl.indexing import build_qdrant_index, build_bm25_index
   ```

5. **对于数据加载**：
   ```python
   # 使用etl.load模块
   from etl.load import execute_query, query_records
   ```

## 版本变更

- **v2.0**: 功能重构，移除重复代码，模块职责更清晰
- **v1.x**: 原始实现，包含大量重复功能

如有疑问，请参考 `etl/README.md` 了解整体架构设计。

## 目录结构

```
etl/embedding/
├── README.md              # 本文档
├── hf_embeddings.py       # HuggingFace嵌入模型封装
├── gte_embeddings.py      # GTE嵌入模型封装
├── test_simple_pipeline.py # 服务连接测试
└── test_embedding_small.py # 小规模嵌入测试
```

## 核心组件

### 1. 数据摄取 (`ingestion.py`)

提供从各种数据源加载文档并构建向量存储的功能：

```python
from etl.embedding.ingestion import load_data_from_mysql, build_vector_store

# 从MySQL加载文档
documents = load_data_from_mysql(table_name="website_nku")

# 构建向量存储
client, vector_store = await build_vector_store(
    qdrant_url="http://localhost:6333",
    collection_name="main_index",
    vector_size=1024
)
```

### 2. 嵌入模型 (`hf_embeddings.py`, `gte_embeddings.py`)

提供多种嵌入模型的统一接口：

```python
from etl.embedding.hf_embeddings import HuggingFaceEmbedding
from etl.embedding.gte_embeddings import GTEEmbedding

# HuggingFace模型
hf_embed = HuggingFaceEmbedding(model_name="BAAI/bge-large-zh-v1.5")

# GTE模型  
gte_embed = GTEEmbedding(model_path="/data/models/gte-large-zh")
```

### 3. 文档处理 (`compressors.py`, `hierarchical.py`)

提供文档压缩和层次化处理功能：

```python
from etl.embedding.compressors import DocumentCompressor
from etl.embedding.hierarchical import HierarchicalProcessor

# 文档压缩
compressor = DocumentCompressor()
compressed_docs = compressor.compress(documents)

# 层次化处理
processor = HierarchicalProcessor()
hierarchical_docs = processor.process(documents)
```

## 测试工具

### 服务连接测试

验证Qdrant、Elasticsearch、MySQL等服务的连接性：

```bash
python etl/embedding/test_simple_pipeline.py
```

### 小规模嵌入测试

测试嵌入功能和性能：

```bash
python etl/embedding/test_embedding_small.py
```

## 迁移指南

### 从旧版本迁移

如果你之前使用 `build_retrieval_indexes.py`（已删除），请改用新的统一接口：

**旧方式（已废弃）：**
```bash
python etl/embedding/build_retrieval_indexes.py
```

**新方式：**
```bash
# 完整的索引构建流程
python etl/import_and_index.py --all --data-dir /data/crawler/website

# 仅构建检索索引
python etl/import_and_index.py --qdrant --bm25 --elasticsearch
```

### 配置迁移

嵌入相关配置现在统一在 `config.json` 中管理：

```json
{
  "etl": {
    "embedding": {
      "model_path": "/data/models",
      "model_name": "bge-large-zh-v1.5",
      "batch_size": 32,
      "chunk_size": 512,
      "chunk_overlap": 50
    },
    "data": {
      "qdrant": {
        "url": "http://localhost:6333",
        "collection": "main_index",
        "vector_size": 1024
      }
    }
  }
}
```

## 开发指南

### 添加新的嵌入模型

1. 在相应的嵌入模型文件中添加新的类
2. 实现 `embed_documents()` 和 `embed_query()` 方法
3. 更新配置文件中的模型选项

### 扩展数据源

1. 在 `ingestion.py` 中添加新的 `load_data_from_*()` 函数
2. 确保返回的文档格式与现有接口兼容
3. 更新相关的索引构建器

## 注意事项

- 嵌入模型需要大量GPU内存，建议在生产环境中使用GPU加速
- 向量索引构建可能耗时较长，建议使用批处理模式
- 确保Qdrant服务在索引构建前已正确启动
- 定期备份向量索引以防数据丢失
