# 项目日志使用指南

本项目使用 [Loguru](https://github.com/Delgan/loguru) 库进行日志管理。为了保持一致性和便于查找问题，我们在每个模块的 `__init__.py` 文件中创建了专用的 logger 实例，供该模块内的所有文件共享使用。

## 日志实例

每个模块都有自己专用的 logger 实例，命名格式为 `{module_name}_logger`：

| 模块 | Logger 实例 | 日志文件 |
| --- | --- | --- |
| crawler | `crawler_logger` | `logs/crawler.log` |
| embedding | `embedding_logger` | `logs/embedding.log` |
| load | `load_logger` | `logs/load.log` |
| transform | `transform_logger` | `logs/transform.log` |
| retrieval | `retrieval_logger` | `logs/retrieval.log` |

## 在模块中使用日志

### 导入模块 logger

```python
# 在模块文件中导入
from etl.crawler import crawler_logger

def my_function():
    crawler_logger.info("这是一条信息日志")
    crawler_logger.error("这是一条错误日志")
```

### 自定义上下文信息

```python
# 添加上下文信息创建特定实例
class MyCrawler:
    def __init__(self, name):
        self.logger = crawler_logger.bind(crawler=name)
        
    def process(self):
        self.logger.info("处理中...")  # 日志会包含crawler=name的上下文
```

## 日志级别

支持的日志级别（从低到高）：

- `DEBUG`: 调试信息，用于开发阶段
- `INFO`: 一般信息，记录程序正常运行状态
- `SUCCESS`: 成功信息，表示任务成功完成
- `WARNING`: 警告信息，不影响程序运行但需要注意
- `ERROR`: 错误信息，表示发生了错误但不会导致程序崩溃
- `CRITICAL`: 严重错误，可能导致程序崩溃

## 日志格式

所有日志采用统一格式：

```
{time:YYYY-MM-DD HH:mm:ss} | {level} | {module} | {message}
```

## 最佳实践

1. **始终使用模块级别的日志实例**，不要创建新的 logger 实例
2. **适当使用日志级别**，避免过多的 DEBUG 日志进入生产环境
3. **使用 bind() 添加上下文**，便于日志分析和问题排查
4. **添加有意义的日志信息**，包括操作对象、关键参数等
5. **异常处理中记录详细信息**，包括异常类型、错误消息和关键变量

## 示例

### 基本用法

```python
from etl.retrieval import retrieval_logger

retrieval_logger.info("开始检索")
retrieval_logger.debug(f"参数设置: topk={topk}")

try:
    # 业务逻辑
    result = perform_retrieval()
    retrieval_logger.success(f"检索成功: 找到 {len(result)} 条记录")
except Exception as e:
    retrieval_logger.error(f"检索失败: {str(e)}")
```

### 在类中使用

```python
from etl.load import load_logger

class DataLoader:
    def __init__(self, source):
        self.source = source
        self.logger = load_logger.bind(source=source)
    
    def load(self):
        self.logger.info(f"开始加载数据")
        # ...处理逻辑
        self.logger.success("数据加载完成")
``` 