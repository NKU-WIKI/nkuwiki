# ETL 模块

## 模块概述

ETL模块是nkuwiki平台的数据处理模块，负责数据抽取(Extract)、转换(Transform)和加载(Load)。该模块实现了爬虫数据采集、数据转换处理、索引建立和检索功能。

## 子模块

### 1. api - API接口

提供数据访问的API接口，如MySQL数据库访问。

- **mysql_api.py** - MySQL数据库API实现
- **mysql_api.md** - API接口文档

### 2. crawler - 爬虫模块

负责从各种数据源抓取数据。

- **base_crawler.py** - 基础爬虫类
- 其他特定爬虫实现（网站、微信等）

### 3. transform - 转换模块

负责数据格式转换、处理和清洗。

- **transformation.py** - 转换工具

### 4. load - 加载模块

将原始数据导出到索引数据、关系数据库和向量数据库。

- **mysql_tables/** - MySQL建表语句
- **json2mysql.py** - JSON数据导入MySQL
- **pipieline.py** - 文档索引流程

### 5. embedding - 嵌入处理

文档处理和嵌入向量生成。

- **hierarchical.py** - 文档处理成节点树，建立索引
- **ingestion.py** - 文档分块、嵌入
- **hf_embeddings.py** - 嵌入模型

### 6. retrieval - 检索模块

实现文档检索和重排功能。

- **retrivers.py** - 稀疏/稠密/混合检索器
- **rerankders.py** - 重排器

### 7. utils - 工具函数

通用工具函数和类库。

### 8. data - 数据存储

数据持久化存储目录（通常为gitignore）。

- **cache/** - 缓存目录
- **index/** - 索引目录
- **models/** - 模型目录
- **mysql/** - MySQL数据目录
- **qdrant/** - Qdrant向量数据库目录
- **nltk/** - NLTK数据目录
- **raw/** - 原始数据目录

## 配置

ETL模块的配置项存储在config.json文件中，路径前缀为`etl`：

```json
{
  "etl": {
    "data": {
      "base_path": "./etl/data",
      "raw": {"path": "/raw"},
      "cache": {"path": "/cache"},
      "index": {"path": "/index"},
      "qdrant": {
        "path": "/qdrant",
        "url": "http://localhost:6333",
        "timeout": 30.0,
        "collection": "main_index",
        "vector_size": 1024
      },
      "mysql": {
        "host": "127.0.0.1",
        "port": 3306,
        "user": "root",
        "password": "",
        "name": "nkuwiki"
      },
      "models": {
        "hf_endpoint": "https://hf-api.gitee.com",
        "hf_home": "/models"
      }
    }
  }
}
```

## 使用方法

### 导入ETL模块

```python
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))
from etl import logger, config, BASE_PATH
```

### 使用爬虫采集数据

```python
from etl.crawler.base_crawler import BaseCrawler

class MyCrawler(BaseCrawler):
    def crawl(self):
        # 爬虫实现
        pass

crawler = MyCrawler()
data = crawler.crawl()
```

### 使用检索功能

```python
from etl.rag_pipeline import RAGPipeline

pipeline = RAGPipeline()
results = pipeline.search("南开大学的校训是什么？")
print(results)
```

## 日志

使用debug级别记录详细信息，info级别记录重要信息。
