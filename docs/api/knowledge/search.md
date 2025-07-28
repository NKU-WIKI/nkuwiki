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

### 5.4 获取热门和最新帖子推荐

- **Endpoint**: `GET /knowledge/recommand`
- **Tags**: `knowledge`, `recommendation`
- **Summary**: 获取热门和最新帖子，支持AI智能推荐

#### 功能描述

从多个平台（wxapp_post, wechat_nku, website_nku, market_nku）获取推荐内容，包括：

- **最热帖子**：基于点赞、评论、收藏、浏览量计算热度分数
- **最新帖子**：最近N天内发布的帖子
- **综合推荐**：结合热度和时间的综合推荐算法
- **AI智能推荐**：基于用户行为和内容分析的个性化推荐

#### 请求参数

| 参数名                    | 类型      | 位置  | 是否必需 | 默认值  | 描述                                           |
| ------------------------- | --------- | ----- | -------- | ------- | ---------------------------------------------- |
| `limit`                   | `integer` | Query | 否       | `20`    | 每类帖子的数量限制。                           |
| `hot_weight`              | `float`   | Query | 否       | `0.7`   | 热度权重，用于综合推荐算法。                   |
| `new_weight`              | `float`   | Query | 否       | `0.3`   | 新度权重，用于综合推荐算法。                   |
| `enable_ai_recommendation`| `boolean` | Query | 否       | `true`  | 是否启用AI智能推荐。                          |
| `user_id`                 | `string`  | Query | 否       | `null`  | 用户ID，用于个性化AI推荐。                     |
| `days`                    | `integer` | Query | 否       | `7`     | 查询最近N天的数据。                           |

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
          "title": "南开大学2024年招生简章发布",
          "content": "南开大学正式发布2024年本科招生简章...",
          "author": "招生办",
          "platform": "website",
          "original_url": "http://www.nankai.edu.cn/admissions/2024",
          "tag": ["招生", "官方"],
          "hot_score": 95.8,
          "create_time": "2024-01-15T10:00:00",
          "view_count": 5432,
          "like_count": 256,
          "comment_count": 89,
          "favorite_count": 178
        }
      ],
      "new_posts": [
        {
          "id": 456,
          "title": "最新校园活动通知",
          "content": "本周末将举办校园开放日活动...",
          "author": "学生处",
          "platform": "wxapp",
          "original_url": null,
          "tag": ["活动", "通知"],
          "create_time": "2024-01-28T14:30:00",
          "view_count": 1234,
          "like_count": 67,
          "comment_count": 23,
          "favorite_count": 45
        }
      ],
      "recommended_posts": [
        {
          "id": 789,
          "title": "期末考试安排及注意事项",
          "content": "各位同学请注意，期末考试即将开始...",
          "author": "教务处",
          "platform": "wechat",
          "original_url": "https://mp.weixin.qq.com/s/xxx",
          "tag": ["考试", "教务"],
          "recommendation_score": 88.5,
          "recommendation_reason": "基于您的浏览历史和兴趣标签推荐",
          "create_time": "2024-01-25T16:00:00",
          "view_count": 3456,
          "like_count": 123,
          "comment_count": 45,
          "favorite_count": 89
        }
      ],
      "ai_recommendations": [
        {
          "id": 101,
          "title": "图书馆新书推荐",
          "content": "图书馆新到一批专业书籍...",
          "author": "图书馆",
          "platform": "market",
          "original_url": "http://library.nankai.edu.cn/newbooks",
          "tag": ["图书", "学习"],
          "ai_score": 92.3,
          "personalization_factors": ["学习兴趣", "专业相关", "历史浏览"],
          "create_time": "2024-01-26T09:00:00",
          "view_count": 876,
          "like_count": 54,
          "comment_count": 12,
          "favorite_count": 32
        }
      ],
      "statistics": {
        "total_hot_posts": 20,
        "total_new_posts": 15,
        "total_recommended_posts": 18,
        "total_ai_recommendations": 12,
        "query_time_ms": 156,
        "ai_enabled": true,
        "personalized": true
      }
    }
  }
  ```

- **500 Internal Server Error**:
  ```json
  {
    "code": 500,
    "message": "获取热门和最新帖子失败",
    "details": "服务器内部错误"
  }
  ```

#### 算法说明

1. **热度分数计算**：
   - 基于点赞数、评论数、收藏数、浏览量的加权平均
   - 考虑时间衰减因子，越新的内容权重越高

2. **综合推荐算法**：
   - 综合分数 = hot_weight × 热度分数 + new_weight × 时间分数
   - 默认热度权重0.7，新度权重0.3

3. **AI智能推荐**：
   - 基于用户历史行为分析
   - 内容相似度匹配
   - 个性化标签推荐

#### 注意事项

- 当 `enable_ai_recommendation` 为 `false` 时，将不返回 `ai_recommendations` 字段
- 未提供 `user_id` 时，AI推荐将基于通用推荐算法
- `hot_weight` 和 `new_weight` 之和建议为1.0，以获得最佳推荐效果
- 推荐结果会根据平台内容的实际情况动态调整
