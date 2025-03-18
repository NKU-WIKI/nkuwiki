# 嵌入向量模块开发指南

## 模块概述

embedding 模块负责将文本转换为向量表示，是实现语义搜索和检索的基础。该模块提供了多种向量化工具，支持不同的嵌入模型和压缩方法。

## 文件结构

- `__init__.py` - 模块入口，定义了导出的函数和类

- `ingestion.py` - 数据摄入与向量化流程

- `gte_embeddings.py` - General Text Embeddings 模型实现

- `hf_embeddings.py` - Hugging Face 模型嵌入实现

- `compressors.py` - 向量压缩工具

- `hierarchical.py` - 层次化嵌入实现

- `splitter.py` - 文本分割工具，用于将文本切分为适合编码的片段

## 开发新嵌入模型

1. **创建嵌入类**:

```python
from etl.embedding import BaseEmbedding

class MyEmbedding(BaseEmbedding):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 初始化模型
        self.model = self._load_model()

    def _load_model(self):
        # 加载模型的逻辑
        pass

    def embed(self, texts, batch_size=32):
        """
        将文本转换为向量

        Args:
            texts: 文本列表
            batch_size: 批处理大小

        Returns:
            向量列表
        """
        # 实现向量化逻辑
        pass

```text

1. **使用示例**:

```python

# 初始化嵌入模型

embedding_model = MyEmbedding(model_name="my-model")

# 向量化文本

vectors = embedding_model.embed(["这是第一段文本", "这是第二段文本"])

```text

## 向量压缩

对于大规模向量数据，压缩是提高效率的重要方法：

```python
from etl.embedding.compressors import PCACompressor

# 初始化压缩器

compressor = PCACompressor(target_dim=128)

# 训练压缩器

compressor.fit(vectors)

# 压缩向量

compressed_vectors = compressor.compress(vectors)

```text

## 数据摄入流程

使用 `ingestion.py` 中的工具进行完整的数据摄入流程：

```python
from etl.embedding.ingestion import ingest_documents

# 摄入文档并转换为向量

document_ids = ingest_documents(
    documents,
    embedding_model="gte-base",
    vector_store="qdrant",
    collection_name="my_collection"
)

```text

## 注意事项

1. **批处理**: 使用批处理提高大规模文本向量化的效率

1. **模型选择**: 根据应用场景选择合适的嵌入模型

1. **维度权衡**: 考虑向量维度与检索性能的权衡

1. **归一化**: 确保向量适当归一化，特别是使用余弦相似度时

1. **缓存机制**: 考虑实现向量缓存，避免重复计算

## 调试与测试

1. 单独运行嵌入模块进行测试:

```bash
python -m etl.embedding.test_embedding

```text

1. 评估嵌入质量:

```python
from etl.embedding import evaluate_embedding
scores = evaluate_embedding(my_embedding, test_dataset)
print(f"平均相似度: {scores['avg_similarity']}")

```text

## 参考

- 查看现有嵌入实现了解最佳实践

- 参考 `gte_embeddings.py` 和 `hf_embeddings.py` 了解模型加载和使用方法
