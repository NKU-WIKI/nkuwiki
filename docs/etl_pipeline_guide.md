# NKUWiki ETL 开发规范

本文档为 `nkuwiki` 项目的ETL（数据提取、转换、加载）系统开发提供指导规范，旨在确保代码的一致性、模块化和可维护性。

## 1. ETL 核心设计理念

项目ETL流程遵循**阶段式解耦**的设计原则，主要分为三个独立阶段：

1.  **数据采集 (Crawling)**: 从不同数据源（网站、公众号、校园集市等）抓取原始信息，并以标准化的JSON格式存入统一的数据湖。
2.  **数据处理与索引 (Processing & Indexing)**: 对原始数据进行转换、分块、向量化，并加载到Qdrant向量数据库和Elasticsearch全文索引中。
3.  **洞察生成与应用 (Insight & Application)**: 基于新增数据，利用大语言模型生成结构化的分析洞察，并存入MySQL数据库，为上层应用提供数据支持。

`etl/daily_pipeline.py` 是驱动阶段2和3的核心任务编排器。

---

## 2. 阶段一：数据采集 (`etl/crawler/`)

### 任务与职责
- 从指定的数据源抓取原始数据。
- 将抓取到的数据处理成**标准JSON格式**。
- 将JSON文件存储到统一的数据湖 `/data/raw/`。

### 开发新爬虫的步骤

1.  **创建爬虫脚本**:
    - 在 `etl/crawler/` 下为新数据源创建一个独立的`py`文件，例如 `etl/crawler/bilibili_spider.py`。
    - 爬虫逻辑应包含错误处理、重试机制，并记录详细日志。

2.  **标准化输出**:
    - 爬虫的最终输出**必须**是一个或多个 `.json` 文件。
    - 每个JSON文件应包含单个数据单元（如一篇文章、一个帖子）的完整信息。
    - JSON文件必须包含以下核心字段，以确保下游处理流程可以正确识别：
      ```json
      {
        "id": "数据唯一标识，建议使用URL的MD5哈希",
        "title": "标题",
        "content": "正文内容",
        "url": "原始链接",
        "platform": "平台标识 (例如: 'website', 'wechat', 'market')",
        "tag": "具体来源标签 (例如: 'nkunews', 'nkuyouth', 'market_sell')",
        "publish_time": "发布时间 (ISO 8601格式, e.g., '2023-10-27T10:00:00+08:00')"
      }
      ```

3.  **统一存储**:
    - 所有生成的 `.json` 文件必须存放到 `/data/raw/` 目录。
    - 存储路径应遵循规范：`/data/raw/{platform}/{tag}/{year}{month}/{article_id}.json`。其中 `article_id` 通常是文件内容的md5。

---

## 3. 阶段二 & 三：任务编排 (`etl/daily_pipeline.py`)

`