# 工具模块开发指南

## 模块概述

utils 模块提供了各种通用工具函数和类，支持 ETL 流程中的各个环节。该模块包含对大语言模型、多模态模型、文本处理以及 RAG 系统的支持工具。

## 文件结构

- `__init__.py` - 模块入口，定义了导出的函数和类
- `llm_utils.py` - 大语言模型工具函数
- `mllm_utils.py` - 多模态大语言模型工具函数
- `rag.py` - RAG 系统工具函数
- `qa.py` - 问答系统工具函数
- `template.py` - 提示词模板工具
- `tokenization_qwen.py` - 千问模型分词工具
- `modeling_qwen.py` - 千问模型实现
- `gemma_model.py` - Gemma 模型实现
- `gemma_config.py` - Gemma 模型配置
- `modeling_minicpm_reranker.py` - MiniCPM 重排序模型实现
- `efficient_modeling_minicpm_reranker.py` - 高效 MiniCPM 重排序模型实现
- `configuration_minicpm_reranker.py` - MiniCPM 重排序模型配置

## 开发新工具函数

1. **创建工具函数模块**:

```python
# my_utils.py
from loguru import logger
from typing import List, Dict, Any

def process_data(data: List[Dict[str, Any]], **kwargs) -> List[Dict[str, Any]]:
    """
    处理数据的通用工具函数
    
    Args:
        data: 要处理的数据列表
        **kwargs: 其他参数
        
    Returns:
        处理后的数据列表
    """
    logger.info(f"处理 {len(data)} 条数据")
    
    # 实现数据处理逻辑
    processed_data = []
    for item in data:
        # 处理每个数据项
        processed_item = transform_item(item, **kwargs)
        processed_data.append(processed_item)
    
    return processed_data

def transform_item(item: Dict[str, Any], **kwargs) -> Dict[str, Any]:
    """内部处理单个数据项的函数"""
    # 实现处理逻辑
    return item
```

1. **在 `__init__.py` 中导出工具函数**:

```python
from etl.utils.my_utils import process_data, transform_item

__all__ = [
    "process_data",
    "transform_item"
]
```

## LLM 工具开发

使用 `llm_utils.py` 中的工具与大语言模型交互：

```python
from etl.utils.llm_utils import generate_text

# 使用 LLM 生成文本
response = generate_text(
    model="qwen",
    prompt="总结以下文本：...",
    max_tokens=500
)
```

## RAG 工具开发

使用 `rag.py` 中的工具实现 RAG 系统功能：

```python
from etl.utils.rag import enhance_query

# 使用 RAG 增强查询
enhanced_query = enhance_query(
    original_query="什么是 ETL？",
    context_documents=retrieved_documents
)
```

## 注意事项

1. **通用性**: 确保工具函数具有足够的通用性，可以被多个模块使用
1. **参数命名**: 使用清晰、一致的参数命名约定
1. **类型提示**: 使用 Python 类型提示增强代码可读性和开发体验
1. **文档字符串**: 为每个函数和类提供详细的文档字符串
1. **错误处理**: 实现适当的错误处理和异常机制

## 调试与测试

1. 单独测试工具函数:

```bash
python -m etl.utils.test_my_utils
```

1. 使用内置的日志记录功能记录关键信息:

```python
from loguru import logger
logger.debug("参数值: {}", value)
```

## 参考

- 查看现有工具函数实现了解最佳实践
- 参考 `llm_utils.py` 和 `rag.py` 了解与 LLM 和 RAG 相关的工具实现 