# RAG API接口文档

## 概述

RAG（Retrieval-Augmented Generation）检索增强生成接口用于从知识库中检索相关信息，并结合大语言模型生成回答。本接口支持多种格式输出和多表查询。

## 基础信息

- **接口地址**: `http://localhost:8000/agent/rag` 或 `https://nkuwiki.com/agent/rag`
- **请求方法**: POST
- **内容类型**: application/json
- **响应格式**: JSON

## 请求参数

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|-------|------|------|--------|------|
| query | string | 是 | - | 用户查询问题 |
| tables | array | 否 | ["wxapp_posts"] | 要检索的表名列表 |
| max_results | int | 否 | 5 | 每个表返回的最大结果数 |
| stream | bool | 否 | false | 是否流式返回 |
| format | string | 否 | "markdown" | 回复格式: markdown/text/html |
| openid | string | 否 | null | 用户唯一标识 |

### 表名说明

可用的表名列表：
- `wxapp_posts`: 小程序帖子
- `wxapp_comments`: 小程序评论
- `wxapp_users`: 小程序用户
- `wechat_nku`: 微信公众号文章
- `website_nku`: 南开网站文章
- `market_nku`: 校园集市帖子

## 响应格式

```json
{
  "response": "生成的回答内容",
  "sources": [
    {
      "id": "1",
      "type": "帖子",
      "title": "相关内容标题",
      "author": "作者名称"
    }
  ],
  "format": "markdown",
  "retrieved_count": 1,
  "response_time": 0.5
}
```

### 响应字段说明

| 字段名 | 类型 | 说明 |
|-------|------|------|
| response | string | 生成的回答内容 |
| sources | array | 引用的知识来源 |
| format | string | 返回格式类型 |
| retrieved_count | int | 检索到的结果数量 |
| response_time | float | 响应时间(秒) |

## 使用示例

### Python 示例

```python
import requests
import json

url = "http://localhost:8000/agent/rag"

payload = {
    "query": "南开大学历史",
    "tables": ["wxapp_posts"],
    "max_results": 3,
    "stream": False,
    "format": "markdown"
}

headers = {
    "Content-Type": "application/json",
    "Accept": "application/json"
}

response = requests.post(url, json=payload, headers=headers)

if response.status_code == 200:
    result = response.json()
    print(f"响应内容: {result['response']}")
    print(f"检索到的结果数量: {result['retrieved_count']}")
else:
    print(f"请求失败: {response.status_code}")
    print(f"错误信息: {response.text}")
```

### cURL 示例

```bash
curl -X POST "http://localhost:8000/agent/rag" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "南开大学历史",
    "tables": ["wxapp_posts"],
    "max_results": 3,
    "format": "markdown"
  }'
```

## 增强版RAG接口 (rag2)

南开wiki还提供了增强版RAG接口，支持查询改写和更多高级功能。

- **接口地址**: `http://localhost:8000/agent/rag2` 或 `https://nkuwiki.com/agent/rag2`
- **请求方法**: POST

### 附加请求参数

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|-------|------|------|--------|------|
| query_bot_id | string | 否 | "rewriter" | 查询改写机器人ID |
| flash_bot_id | string | 否 | "flash" | 回答生成机器人ID |

### 增强版响应格式

```json
{
  "response": "生成的回答内容",
  "sources": [
    {
      "id": "1",
      "type": "帖子",
      "title": "相关内容标题",
      "author": "作者名称"
    }
  ],
  "format": "markdown",
  "retrieved_count": 1,
  "original_query": "原始查询",
  "rewritten_query": "改写后的查询",
  "response_time": 0.5
}
```

## 状态接口

获取RAG服务状态信息。

- **接口地址**: `http://localhost:8000/agent/status` 或 `https://nkuwiki.com/agent/status`
- **请求方法**: GET

### 响应示例

```json
{
  "status": "running",
  "version": "1.0.0",
  "capabilities": ["chat", "search", "rag"],
  "formats": ["markdown", "text", "html"]
}
```

## 错误处理

接口可能返回以下错误：

| 状态码 | 说明 |
|-------|------|
| 400 | 请求参数错误 |
| 404 | 未找到资源 |
| 500 | 服务器内部错误 |

### 错误响应示例

```json
{
  "detail": "不支持的表: invalid_table，有效的表为: wxapp_posts, wxapp_comments, wxapp_users, wechat_nku, website_nku, market_nku"
}
```

## 测试环境

为了方便测试，我们还提供了一个简化版测试API：

- **接口地址**: `http://localhost:8888/rag`
- **请求方法**: POST

该测试接口实现了RAG的基本功能，但使用了模拟数据，适合前端开发和接口测试。 