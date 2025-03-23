# RAG接口使用指南

## 什么是RAG

RAG (Retrieval-Augmented Generation，检索增强生成) 是一种结合了检索和生成能力的AI技术。它通过以下步骤工作：

1. 接收用户查询
2. 从知识库中检索相关信息
3. 将检索到的信息与用户查询一起输入到生成模型中
4. 生成一个基于检索内容的回答

南开Wiki的RAG接口让你能够利用校园知识库回答用户问题，提供更准确、更相关的信息。

## 为什么使用RAG

与纯粹的生成模型相比，RAG有以下优势：

- **减少幻觉**：基于真实检索的内容生成回答，减少捏造信息
- **提供最新信息**：能够访问最新的知识库内容
- **引用信息来源**：回答中可以提供信息的来源，增加可信度
- **支持领域特定知识**：能针对特定领域（如南开大学相关信息）提供专业回答

## 快速开始

### 基本调用

```python
import requests

url = "https://nkuwiki.com/agent/rag"  # 生产环境
# url = "http://localhost:8000/agent/rag"  # 开发环境

payload = {
    "query": "南开大学历史",
    "tables": ["wxapp_posts"],
    "max_results": 3,
    "format": "markdown"
}

headers = {
    "Content-Type": "application/json"
}

response = requests.post(url, json=payload, headers=headers)
result = response.json()

print(result["response"])  # 输出生成的回答
```

### 在微信小程序中使用

```javascript
// 在微信小程序中调用RAG接口
wx.request({
  url: 'https://nkuwiki.com/agent/rag',
  method: 'POST',
  data: {
    query: '南开大学有哪些著名校友？',
    tables: ['wxapp_posts', 'wechat_nku'],
    max_results: 5,
    format: 'markdown'
  },
  header: {
    'content-type': 'application/json'
  },
  success(res) {
    console.log(res.data.response)
    // 处理回答...
  }
})
```

## 进阶用法

### 多表查询

你可以同时查询多个知识来源：

```python
payload = {
    "query": "南开大学招生信息",
    "tables": ["wxapp_posts", "wechat_nku", "website_nku"],
    "max_results": 5
}
```

### 不同输出格式

RAG接口支持三种输出格式：

- `markdown`：适合需要富文本展示的场景
- `text`：纯文本格式，适合简单场景
- `html`：适合网页展示

```python
# HTML格式输出
payload = {
    "query": "南开大学专业设置",
    "format": "html"
}
```

### 使用增强版RAG (rag2)

增强版RAG接口支持查询改写，能够提高检索质量：

```python
url = "https://nkuwiki.com/agent/rag2"

payload = {
    "query": "怎样申请奖学金",
    "tables": ["wxapp_posts"],
    "query_bot_id": "rewriter",  # 查询改写机器人
    "flash_bot_id": "flash"      # 回答生成机器人
}

response = requests.post(url, json=payload, headers=headers)
result = response.json()

print(f"原始查询: {result['original_query']}")
print(f"改写查询: {result['rewritten_query']}")
print(result["response"])
```

## 最佳实践

1. **清晰的查询**：提供明确、具体的查询问题，以获得更精确的回答
   
2. **选择合适的表**：根据需求选择合适的知识源
   - 校园生活问题：`wxapp_posts`, `wxapp_comments`
   - 官方信息：`website_nku`, `wechat_nku`
   
3. **控制结果数量**：通过`max_results`参数控制检索结果数量，平衡速度和全面性
   
4. **错误处理**：实现完善的错误处理机制，应对可能的API异常

5. **用户体验**：使用流式响应(`stream=true`)可以提供更好的用户体验，特别是对于长回答

## 故障排除

常见问题及解决方案：

1. **404错误**：检查API路径是否正确，确认服务器是否运行
2. **400错误**：检查请求参数格式，尤其是表名是否在允许的列表中
3. **响应超时**：可能是查询太复杂或服务器负载过高，尝试简化查询或稍后重试
4. **回答不相关**：尝试调整查询表达方式或使用`rag2`接口进行查询改写

## 测试与开发

为方便开发和测试，可以使用我们提供的简化测试环境：

```
http://localhost:8888/rag
```

该环境提供与正式API相同的接口格式，但使用模拟数据，适合前端开发和接口集成测试。

## 更多资源

- [API详细文档](./rag_api.md)
- [示例代码库](https://github.com/nkuwiki/examples)
- [常见问题解答](./faq.md) 