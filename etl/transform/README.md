# 数据转换模块开发指南

## 模块概述

transform 模块负责对原始数据进行清洗、转换和处理，是 ETL 流程中的"Transform"环节。该模块提供了多种转换工具，用于将原始数据处理成结构化的、标准化的数据格式。

## 文件结构

- `__init__.py` - 模块入口，定义了导出的函数和类
- `splitter.py` - 文本分割工具，用于将长文本分割成适合处理的片段
- `transformation.py` - 通用数据转换工具
- `merge_json.py` - JSON数据合并工具
- `preprocess_zedx.py` - ZedX数据预处理工具
- `get_ocr_data.py` - OCR数据处理工具
- `wechatmp2markdown/` - 微信公众号文章转换为Markdown的工具

## 开发新转换器

1. **创建转换类**:

```python
from etl.transform import BaseTransformer

class MyTransformer:
    def __init__(self, **kwargs):
        # 初始化配置
        self.config = kwargs
    
    def transform(self, data):
        # 实现数据转换逻辑
        transformed_data = self._process(data)
        return transformed_data
    
    def _process(self, data):
        # 内部处理方法
        pass
```

1. **使用示例**:

```python
# 初始化转换器
transformer = MyTransformer(option1=True, option2="value")
# 加载数据
raw_data = load_data_from_path("./etl/data/raw/my_data.json")
# 执行转换
transformed_data = transformer.transform(raw_data)
# 保存转换后的数据
save_data(transformed_data, "./etl/data/cache/transformed_data.json")
```

## 文本分割

文本分割是数据处理的重要步骤，特别是对于需要进行向量化的文本：

```python
from etl.transform.splitter import TextSplitter

# 初始化分割器
splitter = TextSplitter(chunk_size=1000, chunk_overlap=200)
# 分割文本
chunks = splitter.split_text(long_text)
```

## 注意事项

1. **数据清洗**: 确保移除无用的标记、格式和噪声数据
2. **格式标准化**: 遵循项目定义的数据格式标准
3. **性能考虑**: 对于大数据量，考虑使用批处理和流处理
4. **中间结果**: 转换后的中间结果应保存在 `etl/data/cache/` 目录下
5. **错误处理**: 妥善处理格式错误、转换异常等情况

## 调试与测试

1. 单独运行转换模块进行测试:

```bash
python -m etl.transform.your_transformer
```

1. 使用内置的日志记录功能记录关键信息:

```python
from loguru import logger
logger.info("处理进度: {}/{}".format(current, total))
```

## 参考

- 查看现有转换器实现了解最佳实践
- 使用 `transformation.py` 中的通用工具函数
