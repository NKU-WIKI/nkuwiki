# 检索模块开发指南

## 模块概述

retrieval 模块负责从数据库、索引或其他存储介质中检索数据。它是实现 RAG (检索增强生成) 系统的核心组件，提供高效、准确的数据检索能力。

## 文件结构

- `__init__.py` - 模块入口，定义了导出的函数和类
- `retrievers.py` - 实现了多种检索器，用于从不同数据源检索数据
- `rerankers.py` - 实现了多种重排序器，用于对检索结果进行重新排序

## 开发新检索器

1. **创建检索器类**:

```python
from etl.retrieval.retrievers import BaseRetriever

class MyRetriever(BaseRetriever):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 初始化配置
        
    def retrieve(self, query, top_k=5, **kwargs):
        """
        根据查询检索相关文档
        
        Args:
            query: 查询文本
            top_k: 返回结果数量
            
        Returns:
            检索到的文档列表
        """
        # 实现检索逻辑
        pass
```

1. **使用示例**:

```python
# 初始化检索器
retriever = MyRetriever(index_path="./etl/data/index/my_index")
# 执行检索
results = retriever.retrieve("查询问题", top_k=10)
```

## 开发新重排序器

1. **创建重排序器类**:

```python
from etl.retrieval.rerankers import BaseReranker

class MyReranker(BaseReranker):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 初始化配置
        
    def rerank(self, query, documents, top_k=None):
        """
        对检索结果进行重排序
        
        Args:
            query: 查询文本
            documents: 检索到的文档列表
            top_k: 返回结果数量
            
        Returns:
            重排序后的文档列表
        """
        # 实现重排序逻辑
        pass
```

1. **使用示例**:

```python
# 初始化重排序器
reranker = MyReranker()
# 执行重排序
reranked_results = reranker.rerank("查询问题", retriever_results)
```

## 注意事项

1. **性能优化**: 检索操作需要注重效率，特别是对于大规模数据
1. **相关性评分**: 确保相关性评分方法合理，能够准确反映文档与查询的相关度
1. **多样性**: 考虑结果的多样性，避免返回过于相似的文档
1. **缓存策略**: 对于常见查询，考虑实现缓存机制
1. **日志记录**: 记录关键检索信息，便于调试和性能分析

## 调试与测试

1. 单独运行检索模块进行测试:

```bash
python -m etl.retrieval.test_retriever
```

1. 评估检索性能:

```python
from etl.retrieval import evaluate_retriever
scores = evaluate_retriever(my_retriever, test_dataset)
print(f"Precision@5: {scores['precision@5']}")
```

## 参考

- 查看现有检索器实现了解最佳实践
- 参考 `retrievers.py` 和 `rerankers.py` 中的通用工具函数
