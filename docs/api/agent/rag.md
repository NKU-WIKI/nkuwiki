# 智能体：RAG 问答接口

本文档详细说明了与智能体 RAG (Retrieval-Augmented Generation) 问答功能相关的 API 接口。

---

## 1. 智能问答

**接口**: `POST /agent/rag`

**功能描述**:
该接口是智能问答的核心，结合了信息检索（Retrieval）和生成（Generation）两个阶段，能够根据知识库内容生成更准确、更丰富的答案。其主要流程包括：
1.  **查询理解与改写 (可选)**: 对用户的原始问题进行分析和改写，以便更好地在知识库中检索。
2.  **信息检索**: 使用改写后的查询在知识库中进行高效检索，召回最相关的文档片段。
3.  **答案生成**: 将原始问题和检索到的信息源整合后，交给大语言模型（LLM）生成最终的、自然的回答。
4.  **流式与非流式响应**: 支持一次性返回完整答案，也支持类似打字机效果的流式响应。

**认证**: 可选。
- 匿名用户可直接调用此接口。
- 如果请求时在Header中提供了有效的JWT，系统将能够记录用户偏好，为未来的个性化功能提供支持。

**请求体 (Body)**:

| 参数 | 类型 | 是否必须 | 默认值 | 描述 |
| --- | --- | --- | --- | --- |
| `query` | `string` | 是 | | 用户的原始查询问题。 |
| `stream` | `boolean` | 否 | `false` | 是否使用流式响应。`true` 为流式，`false` 为一次性返回。 |
| `platform` | `string` | 否 | `null` | 按平台筛选，支持 `wechat`, `website`, `market`, `wxapp`。多个用逗号 `,` 分隔。 |
| `max_results` | `integer`| 否 | `10` | 检索阶段从知识库召回的最大文档数量。 |
| `rewrite_query`| `boolean`| 否 | `false` | 是否启用查询改写功能。 |

**请求示例 (非流式)**:

```bash
curl -X POST "http://127.0.0.1:8000/agent/rag" \
-H "Content-Type: application/json" \
-d '{
  "query": "南开大学有哪些知名校友？",
  "stream": false
}'
```

**成功响应示例 (非流式)**:

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "original_query": "南开大学有哪些知名校友？",
    "rewritten_query": "南开大学有哪些知名校友？",
    "response": "南开大学有许多知名校友...",
    "sources": [
      {
        "title": "知名校友——潘源",
        "content": "1989级校友潘源...",
        "author": "",
        "platform": "website",
        "original_url": "...",
        "relevance": 88.43759
      }
    ],
    "suggested_questions": [],
    "format": "markdown",
    "retrieved_count": 10,
    "response_time": 21.48
  }
}
```
*为简洁起见，`response` 和 `sources` 的内容在示例中被缩短。*

**响应字段说明**:

- **data**: 核心响应数据对象。
  - `original_query`: 用户输入的原始问题。
  - `rewritten_query`: 经过系统改写后的查询，用于内部检索。
  - `response`: LLM 生成的最终文本回答。
  - `sources`: 一个对象数组，列出了生成答案所依据的参考资料。每个对象包含 `title`, `content`, `original_url` 等字段。
  - `suggested_questions`: 一个字符串数组，包含模型建议的后续问题。
  - `response_time`: 服务器处理该请求的总耗时（秒）。 