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
- **认证**: `可选` - 提供有效的JWT Token时，会记录用户搜索历史并启用个性化功能。

### 请求参数

| 参数名              | 类型     | 位置  | 是否必需 | 默认值                        | 描述                                                               |
| ------------------- | -------- | ----- | -------- | ----------------------------- | ------------------------------------------------------------------ |
| `query`             | `string` | Query | 是       | -                             | 搜索关键词。                                                       |
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
        "content": "南开大学（Nankai University），简称“南开”，位于天津市...",
        "author": "南开大学官网",
        "platform": "website",
        "original_url": "http://www.nankai.edu.cn/123.html",
        "tag": ["官方", "新闻"],
        "relevance": 0.85,
        "is_truncated": true,
        "create_time": "2023-10-01T12:00:00",
        "update_time": "2023-10-01T12:00:00",
        "is_official": true,
        "view_count": 1024,
        "like_count": 128
      }
    ],
    "pagination": {
      "total": 100,
      "page": 1,
      "page_size": 10,
      "total_pages": 10,
      "has_more": true
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

### 4.4 清空搜索历史

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

## 5. 热门搜索与网页快照

### 5.1 获取热门搜索

- **Endpoint**: `GET /knowledge/hot`
- **Tags**: `knowledge`
- **Summary**: 获取热门搜索词条列表

#### 请求参数

| 参数名      | 类型      | 位置  | 是否必需 | 默认值 | 描述           |
| ----------- | --------- | ----- | -------- | ------ | -------------- |
| `days`      | `integer` | Query | 否       | `7`    | 统计最近几天的热门搜索。 |
| `page_size` | `integer` | Query | 否       | `10`   | 返回热门搜索词条的数量。 |

#### 响应

- **200 OK**:
  ```json
  {
      "code": 200,
      "message": "success",
      "data": [
          {
              "search_query": "校历",
              "search_count": 150
          }
      ]
  }
  ```

### 5.2 小程序内搜索

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
### 5.4 获取热门和最新帖子

- **Endpoint**: `GET /knowledge/hot_and_new`
- **Tags**: `knowledge`
- **Summary**: 获取热门和最新帖子推荐

#### 功能说明

此接口从多个平台（wxapp_post、wechat_nku、website_nku、market_nku）获取推荐内容，提供三种类型的数据：

- **最热帖子**：基于点赞、评论、收藏、浏览量等指标计算热度分数的热门内容
- **最新帖子**：最近7天内发布的最新内容
- **综合推荐**：结合热度和时间因素的综合推荐算法排序

#### 请求参数

| 参数名       | 类型    | 位置  | 是否必需 | 默认值 | 描述                                     |
| ------------ | ------- | ----- | -------- | ------ | ---------------------------------------- |
| `limit`      | `integer` | Query | 否       | `20`   | 每类帖子的数量限制。                     |
| `hot_weight` | `float`   | Query | 否       | `0.7`  | 热度权重，用于综合推荐算法，取值范围0-1。 |
| `new_weight` | `float`   | Query | 否       | `0.3`  | 新度权重，用于综合推荐算法，取值范围0-1。 |

#### 响应

- **200 OK**:
  ```json
  {
    "code": 200,
    "message": "success",
    "data": {
      "hot_posts": [
        {
          "id": 123,
          "title": "南开大学2024年春季学期课程安排",
          "content": "根据学校安排，2024年春季学期将于...",
          "author": "教务处",
          "platform": "website_nku",
          "original_url": "http://www.nankai.edu.cn/news/123",
          "tag": ["官方", "课程"],
          "hot_score": 0.92,
          "create_time": "2024-01-15T10:00:00",
          "update_time": "2024-01-15T10:00:00",
          "view_count": 2048,
          "like_count": 256,
          "comment_count": 128,
          "favorite_count": 64
        }
      ],
      "new_posts": [
        {
          "id": 456,
          "title": "最新：图书馆开放时间调整通知",
          "content": "为更好地服务师生，图书馆开放时间调整为...",
          "author": "图书馆",
          "platform": "wechat_nku",
          "original_url": "https://mp.weixin.qq.com/s/abc123",
          "tag": ["通知", "图书馆"],
          "create_time": "2024-01-20T15:30:00",
          "update_time": "2024-01-20T15:30:00",
          "view_count": 512,
          "like_count": 32,
          "comment_count": 8,
          "favorite_count": 16
        }
      ],
      "recommended_posts": [
        {
          "id": 789,
          "title": "南开大学校园文化节精彩回顾",
          "content": "本次校园文化节汇聚了各学院的精彩表演...",
          "author": "学生会",
          "platform": "wxapp_post",
          "original_url": null,
          "tag": ["文化", "活动"],
          "composite_score": 0.85,
          "hot_score": 0.78,
          "time_score": 0.95,
          "create_time": "2024-01-18T20:00:00",
          "update_time": "2024-01-18T20:00:00",
          "view_count": 1024,
          "like_count": 128,
          "comment_count": 64,
          "favorite_count": 32
        }
      ],
      "statistics": {
        "total_hot_posts": 50,
        "total_new_posts": 35,
        "total_recommended_posts": 100,
        "data_sources": ["wxapp_post", "wechat_nku", "website_nku", "market_nku"],
        "time_range": "2024-01-14 to 2024-01-21",
        "hot_weight": 0.7,
        "new_weight": 0.3
      }
    }
  }
  ```

- **500 Internal Server Error**:
  ```json
  {
    "code": 500,
    "message": "error",
    "details": "获取热门和最新帖子失败"
  }
  ```

#### 算法说明

**热度分数计算**：
- 基于点赞数、评论数、收藏数、浏览量等指标
- 考虑内容发布时间的衰减因子
- 不同平台数据进行归一化处理

**综合推荐算法**：
- `composite_score = hot_weight × hot_score + new_weight × time_score`
- `hot_score`：内容的热度分数（0-1）
- `time_score`：基于发布时间的新鲜度分数（0-1）
- 权重可通过参数调整，满足不同场景需求

#### 使用建议

- **首页推荐**：使用默认参数获取均衡的热门和最新内容
- **热门优先**：设置较高的 `hot_weight`（如0.8-0.9）
- **最新优先**：设置较高的 `new_weight`（如0.8-0.9）
- **性能考虑**：建议 `limit` 参数不要设置过大（建议≤50）
