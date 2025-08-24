# ETL 模块

## 模块概述

ETL模块是nkuwiki平台的数据处理模块，负责数据抽取(Extract)、转换(Transform)和加载(Load)。该模块实现了爬虫数据采集、数据处理、索引建立和检索功能。

## 架构设计

### 核心子模块

#### 1. crawler - 爬虫模块

负责从各种数据源抓取数据。

- **base_crawler.py** - 基础爬虫类
- **wechat.py** - 微信公众号爬虫
- **webpage_spider/** - 网页爬虫（Scrapy框架）
- **xhs_spider/** - 小红书爬虫
- **douyin_spider/** - 抖音爬虫

#### 2. processors - 数据处理模块

负责数据格式转换、处理和清洗。

- **document.py** - 文档处理器
- **text.py** - 文本分割和层次化处理
- **compress.py** - 上下文压缩
- **wechat.py** - 微信数据处理
- **abstract.py** - 摘要生成
- **summarize.py** - 批量摘要工具
- **utils.py** - 通用数据处理工具

#### 3. load - 加载模块

将原始数据导出到索引数据、关系数据库和向量数据库。

- **mysql_tables/** - MySQL建表语句
- **db_core.py** - 数据库核心操作
- **db_pool_manager.py** - 数据库连接池管理
- **table_manager.py** - 表管理工具

#### 4. indexing - 索引构建

各种索引构建的统一接口。

- **mysql_indexer.py** - MySQL索引构建
- **bm25_indexer.py** - BM25索引构建
- **qdrant_indexer.py** - 向量索引构建
- **elasticsearch_indexer.py** - Elasticsearch索引构建

#### 5. embedding - 嵌入处理

文档处理和嵌入向量生成。

- **hf_embeddings.py** - HuggingFace嵌入模型
- **gte_embeddings.py** - GTE嵌入模型

#### 6. retrieval - 检索模块

实现文档检索和重排功能。

- **retrievers.py** - 稀疏/稠密/混合检索器
- **rerankers.py** - 重排器

#### 7. pagerank - PageRank计算

计算网页权威性分数。

- **calculate_pagerank_mysql.py** - 基于MySQL的PageRank计算

#### 8. utils - 工具函数

通用工具函数和常量定义。

- **const.py** - 统一常量定义（所有ETL模块常量）
- **text.py** - 文本工具
- **file.py** - 文件工具
- **date.py** - 日期工具
- **model.py** - 模型工具
- **scan.py** - 扫描工具

### 数据存储

数据持久化存储目录（通常为gitignore）：

- **cache/** - 缓存目录
- **index/** - 索引目录
- **models/** - 模型目录
- **mysql/** - MySQL数据目录
- **qdrant/** - Qdrant向量数据库目录
- **nltk/** - NLTK数据目录
- **raw/** - 原始数据目录

## 常量管理

所有ETL模块相关的常量都统一定义在 `etl/utils/const.py` 中：

### 南开大学相关常量
- 域名映射 (`domain_source_map`)
- 网站URL映射 (`nankai_url_maps`)
- 种子URL (`additional_seed_urls`, `nankai_start_urls`)

### 微信公众号分类
- 大学官方账号 (`university_official_accounts`)
- 学院官方账号 (`school_official_accounts`)
- 社团账号 (`club_official_accounts`)
- 公司账号 (`company_accounts`)
- 非官方账号 (`unofficial_accounts`)

### 爬虫相关常量
- 用户代理 (`DEFAULT_USER_AGENTS`, `USER_AGENTS`)
- 时区和语言 (`DEFAULT_TIMEZONE`, `DEFAULT_LOCALE`)

### 招聘相关常量
- 招聘关键词 (`recruitment_keywords`)

### 数据处理常量
- 文本处理模式 (`HTML_TAGS_PATTERN`, `SPECIAL_CHARS_PATTERN`)
- 长度限制 (`MAX_TEXT_LENGTH`, `MIN_TEXT_LENGTH`)
- 批处理大小 (`DEFAULT_BATCH_SIZE`, `MAX_BATCH_SIZE`)

## 配置

ETL模块的配置项存储在config.json文件中，路径前缀为`etl`：

```json
{
  "etl": {
    "data": {
      "base_path": "/data",
      "raw": {"path": "/raw"},
      "cache": {"path": "/cache"},
      "index": {"path": "/index"},
      "qdrant": {
        "path": "/qdrant",
        "url": "http://localhost:6333",
        "collection": "main_index",
        "vector_size": 1024
      },
      "mysql": {
        "path": "/mysql",
        "host": "127.0.0.1",
        "port": 3306,
        "user": "nkuwiki",
        "password": "",
        "name": "nkuwiki"
      },
      "nltk": {"path": "/nltk"},
      "models": {
        "hf_home": "/models",
        "hf_endpoint": "https://hf-api.gitee.com"
      }
    },
    "crawler": {
      "proxy_pool": "http://127.0.0.1:7897",
      "market_token": ""
    },
    "pagerank": {
      "alpha": 0.85,
      "max_iter": 100,
      "tolerance": 1e-6
    },
    "retrieval": {
      "pagerank_weight": 0.1,
      "enable_es_rerank": true
    }
  }
}
```

## 主要功能脚本

### 数据导入
```bash
# 导入微信数据
python -m etl.load.import_data --platform wechat --tag nku

# 导入网站数据  
python -m etl.load.import_data --platform website --tag nku

# 重建表并导入
python -m etl.load.import_data --platform wechat --rebuild-table
```

### 索引构建
```bash
# 构建所有索引
python -m etl.build_all_indexes

# 单独构建特定索引
python -m etl.indexing.bm25_indexer
python -m etl.indexing.qdrant_indexer
```

### PageRank计算
```bash
python -m etl.pagerank.calculate_pagerank_mysql
```

### 定时任务
```bash
# 招聘信息收集（每日18:00）
python -m etl.job_pipeline

# 校园活动信息收集
python -m etl.act_pipeline
```

## 日志与调试

- 日志使用 `core.utils.logger.register_logger` 方法注册
- 默认使用 debug 级别，重要信息用 info 级别
- 各子模块都有独立的logger实例

## 最佳实践

1. **常量使用**: 所有常量从 `etl.utils.const` 导入
2. **路径配置**: 使用 `etl` 模块导出的路径常量
3. **数据库操作**: 使用 `etl.load.db_core` 的方法
4. **批量处理**: 使用适当的批处理大小
5. **异步编程**: I/O密集型操作使用异步方法
6. **错误处理**: 添加适当的异常处理和日志记录

## 版本信息

当前版本: 2.0.0

## 依赖关系

- MySQL: 关系数据存储
- Qdrant: 向量数据库
- Elasticsearch: 全文检索
- Redis: 缓存
- Scrapy: 网页爬虫
- NLTK: 自然语言处理
- Transformers: 机器学习模型
- NetworkX: 图分析（PageRank）
