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

## 数据导入脚本

### 通用数据导入工具 (import_data.py)

脚本用于将JSON数据文件导入到MySQL数据库中。支持wechat、website、market和wxapp等多种平台数据。

#### 使用方法

```bash
# 基本用法
python -m etl.load.import_data --platform wechat --tag nku --data-dir /data/raw/wechat

# 导入指定目录的特定文件，并在导入前重建表
python -m etl.load.import_data --platform website --tag nku --data-dir /data/raw/website --pattern "*.json" --rebuild-table

# 导入微信数据示例（使用默认配置路径）
python -m etl.load.import_data --platform wechat

# 导入网站数据示例（使用默认配置路径）
python -m etl.load.import_data --platform website

# 显示详细日志
python -m etl.load.import_data --platform market --verbose
```

#### 参数说明

- `--platform`: 必填，数据平台类型，可选值为wechat、website、market、wxapp
- `--tag`: 数据标签，默认为nku
- `--data-dir`: 数据目录路径，默认使用配置中的路径
- `--pattern`: JSON文件匹配模式，默认为*.json
- `--rebuild-table`: 导入前重建表（会清空表中原有数据）
- `--batch-size`: 批量插入大小，默认100
- `--verbose`: 显示详细日志

#### 数据格式要求

脚本支持以下两种JSON格式：

1. 直接的记录列表：
```json
[
  {"title": "标题1", "content": "内容1", "author": "作者1", ...},
  {"title": "标题2", "content": "内容2", "author": "作者2", ...}
]
```

2. 包含data字段的对象：
```json
{
  "data": [
    {"title": "标题1", "content": "内容1", "author": "作者1", ...},
    {"title": "标题2", "content": "内容2", "author": "作者2", ...}
  ]
}
```

### 数据字段

脚本会自动处理以下字段：

- `title`: 标题，缺失时设置为空字符串
- `content`: 内容，缺失时设置为空字符串
- `author`: 作者，缺失时设置为"未知作者"
- `original_url`: 原始URL，缺失时设置为空字符串
- `platform`: 平台，根据参数设置
- `publish_time`: 发布时间，支持多种日期格式
- `scrape_time`: 爬取时间，支持多种日期格式

其他字段将按原样导入。

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

