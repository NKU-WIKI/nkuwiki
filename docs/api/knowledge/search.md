# 知识库搜索 API

本文档详细说明了与知识库搜索相关的API接口。

---

## 1. 站内综合搜索 (推荐)

- **Endpoint**: `GET /knowledge/es-search`
- **Tags**: `knowledge`, `elasticsearch`
- **Summary**: **（推荐）** 直接调用 Elasticsearch 进行高效、精准的全文检索

### 请求参数

| 参数名               | 类型     | 位置  | 是否必需 | 默认值   | 描述                                           |
| -------------------- | -------- | ----- | -------- | -------- | ---------------------------------------------- |
| `query`              | `string` | Query | 是       | -        | 搜索关键词。                                   |
| `openid`             | `string` | Query | 是       | -        | 用户的OpenID。                                 |
| `platform`           | `string` | Query | 否       | `null`   | 平台筛选，多个用逗号分隔。                     |
| `page`               | `integer`| Query | 否       | `1`      | 分页页码。                                     |
| `page_size`          | `integer`| Query | 否       | `10`     | 每页结果数。                                   |
| `max_content_length` | `integer`| Query | 否       | `300`    | 返回内容的最大长度。                           |

### 响应

- **200 OK**:
  ```json
  {
    "code": 200,
    "message": "success",
    "data": [
      {
          "id": "es_doc_id",
          "title": "ES返回的标题",
          "content": "...",
          "relevance": 12.345
      }
    ],
    "pagination": {
        "total": 100,
        "page": 1,
        "page_size": 10
    }
  }
  ```

---

## 2. 基础数据库搜索 (不推荐)

> **[注意]** 此接口直接查询数据库，在数据量大时性能较低，且不如 `es-search` 功能强大。**不推荐**在生产环境使用。

- **Endpoint**: `GET /knowledge/search`
- **Tags**: `knowledge`
- **Summary**: (不推荐) 提供跨多个数据源的关键词搜索功能

### 请求参数

| 参数名              | 类型     | 位置  | 是否必需 | 默认值                        | 描述                                                               |
| ------------------- | -------- | ----- | -------- | ----------------------------- | ------------------------------------------------------------------ |
| `query`             | `string` | Query | 是       | -                             | 搜索关键词。                                                       |
| `openid`            | `string` | Query | 是       | -                             | 用户的OpenID，用于记录搜索历史和未来个性化。                         |
| `platform`          | `string` | Query | 否       | `wechat,website,market,wxapp` | 搜索的平台，多个用逗号分隔。                                       |
| `tag`               | `string` | Query | 否       | `null`                        | 内容标签，多个用逗号分隔。                                         |
| `max_results`       | `integer`| Query | 否       | `10`                          | **每个**数据源（表）返回的最大结果数，用于初步召回。               |
| `page`              | `integer`| Query | 否       | `1`                           | 分页页码。                                                         |
| `page_size`         | `integer`| Query | 否       | `10`                          | 每页返回的结果数量。                                               |
| `sort_by`           | `string` | Query | 否       | `relevance`                   | 排序方式。可选值: `relevance` (相关度), `time` (发布时间)。          |
| `max_content_length`| `integer`| Query | 否       | `500`                         | 返回内容的最大长度，超出的部分将被截断并以`...`结尾。            |

### 响应

- **200 OK**:
  ```json
  {
    "code": 200,
    "message": "success",
    "data": [
      {
        "id": 123,
        "title": "关于南开大学的介绍",
        "content": "南开大学（Nankai University），简称"南开"，位于天津市...",
        "author": "南开大学官网",
        "publish_time": "2023-10-01 12:00:00",
        "platform": "website",
        "original_url": "http://www.nankai.edu.cn/123.html",
        "relevance": 0.85,
        "_table": "website_nku",
        "_type": "南开网站",
        "_content_truncated": true
      }
    ],
    "pagination": {
      "total": 1,
      "page": 1,
      "page_size": 10,
      "total_pages": 1,
      "has_more": false
    }
  }
  ```

---

## 3. 高级RAG搜索 (不推荐)

> **[注意]** 此接口为内部实验性接口，会加载大模型，消耗大量内存资源，且响应较慢。**不推荐**在生产环境或内存有限的设备上使用。

- **Endpoint**: `GET /knowledge/advanced-search`
- **Tags**: `knowledge`, `rag`
- **Summary**: (不推荐) 利用RAG管道进行高级搜索，召回并重排文档

### 请求参数

| 参数名               | 类型     | 位置  | 是否必需 | 默认值        | 描述                                                                                                       |
| -------------------- | -------- | ----- | -------- | ------------- | ---------------------------------------------------------------------------------------------------------- |
| `query`              | `string` | Query | 是       | -             | 搜索关键词。                                                                                               |
| `openid`             | `string` | Query | 是       | -             | 用户的OpenID，用于获取搜索历史以进行个性化。                                                               |
| `top_k_retrieve`     | `integer`| Query | 否       | `20`          | 初始检索（召回）的文档数量。                                                                               |
| `top_k_rerank`       | `integer`| Query | 否       | `10`          | 重排（rerank）后保留的文档数量。                                                                           |
| `retrieval_strategy` | `string` | Query | 否       | `auto`        | 检索策略。可选值: `auto`, `hybrid`, `vector_only`, `bm25_only`, `es_only`。                                |
| `rerank_strategy`    | `string` | Query | 否       | `bge_reranker`| 重排策略。可选值: `no_rerank`, `bge_reranker`, `st_reranker`, `personalized`。**内存不足时建议使用 `no_rerank`**。 |

### 响应

- **200 OK**:
  ```json
  {
    "code": 200,
    "message": "success",
    "data": [
      {
        "id": "doc_id_1",
        "text": "南开大学的详细介绍...",
        "metadata": {
          "title": "关于南开大学",
          "author": "教务处",
          "platform": "website"
        },
        "score": 0.92
      }
    ],
    "details": {
      "message": "高级检索成功",
      "query": "南开大学",
      "retrieval_strategy": "hybrid",
      "rerank_strategy": "bge_reranker",
      "documents_retrieved": 20,
      "documents_reranked": 10,
      "response_time": 5.43
    }
  }
  ```

---

## 4. 搜索建议与历史

### 4.1 获取搜索建议

- **Endpoint**: `GET /knowledge/suggestion`
- **Tags**: `knowledge`
- **Summary**: 根据用户输入提供搜索建议

#### 请求参数

| 参数名      | 类型      | 位置  | 是否必需 | 默认值 | 描述           |
| ----------- | --------- | ----- | -------- | ------ | -------------- |
| `query`     | `string`  | Query | 是       | -      | 用户输入的关键词。 |
| `openid`    | `string`  | Query | 是       | -      | 用户的OpenID。   |
| `page_size` | `integer` | Query | 否       | `5`    | 返回建议的数量。 |

#### 响应

- **200 OK**:
  ```json
  {
      "code": 200,
      "message": "success",
      "data": [
          "南开大学",
          "南开大学校史",
          "南开大学周恩来政府管理学院"
      ]
  }
  ```

### 4.2 获取搜索历史

- **Endpoint**: `GET /knowledge/history`
- **Tags**: `knowledge`, `user`
- **Summary**: 获取指定用户的搜索历史记录

#### 请求参数

| 参数名      | 类型      | 位置  | 是否必需 | 默认值 | 描述           |
| ----------- | --------- | ----- | -------- | ------ | -------------- |
| `openid`    | `string`  | Query | 是       | -      | 用户的OpenID。   |
| `page_size` | `integer` | Query | 否       | `10`   | 返回记录的数量。 |

#### 响应

- **200 OK**:
  ```json
  {
      "code": 200,
      "message": "success",
      "data": [
          {
              "id": 1,
              "query": "四六级",
              "search_time": "2023-10-28 10:00:00"
          }
      ]
  }
  ```

### 4.3 清空搜索历史

- **Endpoint**: `POST /knowledge/history/clear`
- **Tags**: `knowledge`, `user`
- **Summary**: 清空指定用户的搜索历史

#### 请求体

```json
{
    "openid": "user_openid_string"
}
```

#### 响应

- **200 OK**:
  ```json
  {
      "code": 200,
      "message": "success",
      "data": {
          "message": "历史记录已清空"
      }
  }
  ```

---

## 5. 其他搜索相关接口

### 5.1 小程序内搜索

- **Endpoint**: `GET /knowledge/search-wxapp`
- **Tags**: `knowledge`, `wxapp`
- **Summary**: 专门用于小程序内的内容搜索

#### 请求参数

| 参数名        | 类型     | 位置  | 是否必需 | 默认值  | 描述                                                       |
| ------------- | -------- | ----- | -------- | ------- | ---------------------------------------------------------- |
| `query`       | `string` | Query | 是       | -       | 搜索关键词。                                               |
| `search_type` | `string` | Query | 否       | `all`   | 搜索类型。可选值: `all` (全部), `post` (帖子), `user` (用户)。 |
| `page`        | `integer`| Query | 否       | `1`     | 页码。                                                     |
| `page_size`   | `integer`| Query | 否       | `10`    | 每页数量。                                                 |
| `sort_by`     | `string` | Query | 否       | `time`  | 排序方式。可选值: `time` (时间), `relevance` (相关度)。    |

#### 响应

- **200 OK**:
  ```json
  {
    "code": 200,
    "message": "success",
    "data": {
      "posts": {
        "data": [],
        "pagination": { "total": 0, "page": 1, "page_size": 10, "has_more": false }
      },
      "users": {
        "data": [],
        "pagination": { "total": 0, "page": 1, "page_size": 10, "has_more": false }
      }
    },
    "pagination": {
        "page": 1,
        "page_size": 10
    }
  }
  ```

### 5.2 获取热门搜索

- **Endpoint**: `GET /knowledge/hot`
- **Tags**: `knowledge`
- **Summary**: 获取热门搜索词条列表

#### 请求参数

| 参数名      | 类型      | 位置  | 是否必需 | 默认值 | 描述           |
| ----------- | --------- | ----- | -------- | ------ | -------------- |
| `page_size` | `integer` | Query | 否       | `10`   | 返回词条的数量。 |

#### 响应

- **200 OK**:
  ```json
  {
      "code": 200,
      "message": "success",
      "data": [
          {
              "query": "校历",
              "search_count": 150
          }
      ]
  }
  ```

### 5.3 获取网页快照

- **Endpoint**: `GET /knowledge/snapshot`
- **Tags**: `knowledge`, `utils`
- **Summary**: 获取指定 URL 的网页快照

#### 请求参数

| 参数名 | 类型     | 位置  | 是否必需 | 默认值 | 描述             |
| ------ | -------- | ----- | -------- | ------ | ---------------- |
| `url`  | `string` | Query | 是       | -      | 要获取快照的原始URL。 |

#### 响应

- **200 OK**:
  ```json
  {
      "code": 200,
      "message": "success",
      "data": {
          "content": "<html>...</html>",
          "snapshot_time": "2023-10-28 11:00:00"
      }
  }
  ```
- **404 Not Found**:
  ```json
  {
      "code": 404,
      "message": "error",
      "details": "快照不存在"
  }
  ``` 