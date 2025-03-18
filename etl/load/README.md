# 数据加载模块开发指南

## 模块概述

load 模块负责将转换后的数据加载到目标存储系统中，是 ETL 流程中的"Load"环节。该模块提供了多种数据加载工具，支持向数据库、向量库等多种存储系统的数据写入。

## 文件结构

- `__init__.py` - 模块入口，定义了导出的函数和类

- `pipeline.py` - 完整的数据处理和加载流水线

- `json2mysql.py` - 将 JSON 数据加载到 MySQL 数据库

- `mysql_tables/` - MySQL 表结构定义

## 开发新加载器

1. **创建加载器类**:

```python
from etl.load import BaseLoader

class MyLoader(BaseLoader):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 初始化配置
        self.connection = self._create_connection()

    def _create_connection(self):
        # 创建与目标系统的连接
        pass

    def load(self, data, **kwargs):
        """
        将数据加载到目标系统

        Args:
            data: 要加载的数据

        Returns:
            加载结果或状态
        """
        # 实现数据加载逻辑
        pass

    def close(self):
        # 关闭连接
        if self.connection:
            self.connection.close()

```text

1. **使用示例**:

```python

# 初始化加载器

loader = MyLoader(host="localhost", port=5432)

# 加载数据

result = loader.load(transformed_data)

# 关闭加载器

loader.close()

```text

## 数据库加载

使用 `json2mysql.py` 将 JSON 数据加载到 MySQL 数据库：

```python
from etl.load.json2mysql import JSONToMySQL

# 初始化加载器

loader = JSONToMySQL(
    host="localhost",
    user="root",
    password="password",
    database="my_db"
)

# 加载数据

loader.load_json_to_table(json_data, "my_table")

```text

## 完整流水线

使用 `pipeline.py` 中的工具创建完整的数据处理流水线：

```python
from etl.load.pipeline import ETLPipeline

# 创建流水线

pipeline = ETLPipeline(
    crawler="wechat",
    transformer="text_splitter",
    loader="mysql"
)

# 执行流水线

pipeline.run(source="公众号名称")

```text

## 注意事项

1. **批处理**: 对于大规模数据，使用批处理进行加载

1. **事务处理**: 实现适当的事务机制，确保数据一致性

1. **错误处理**: 妥善处理加载过程中的错误，实现回滚或重试机制

1. **连接池**: 对于频繁的数据加载，考虑使用连接池

1. **监控记录**: 记录数据加载过程中的关键指标，便于后续分析

## 调试与测试

1. 单独运行加载模块进行测试:

```bash
python -m etl.load.test_loader

```text

1. 使用内置的日志记录功能记录关键信息:

```python
from loguru import logger
logger.info("已加载 {} 条记录到 {}", len(data), target)

```text

## 参考

- 查看 `json2mysql.py` 了解数据库加载最佳实践

- 参考 `pipeline.py` 了解完整 ETL 流程的实现

