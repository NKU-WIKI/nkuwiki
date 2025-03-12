# NKUWIKI API 文档

## Agent API

Agent API提供了与AI助手对话和知识库搜索的功能。所有接口都位于`/agent`前缀下。

### 1. 对话接口

与AI助手进行对话。

- **接口**: POST `/agent/chat`
- **Content-Type**: application/json

#### 请求参数

```json
{
    "query": "string",     // 必填，用户输入的问题
    "history": [          // 可选，对话历史
        {
            "role": "string",    // 发言角色，可以是"user"或"assistant"
            "content": "string"  // 发言内容
        }
    ]
}
```

#### 响应格式

```json
{
    "response": "string",  // AI助手的回答
    "sources": [          // 引用的知识来源（当前版本为空数组）
        {
            "title": "string",
            "content": "string",
            "url": "string"
        }
    ]
}
```

#### 错误码

- 400: 输入验证错误（例如：问题为空）
- 500: 服务器内部错误（例如：Agent响应失败）

#### 示例

请求：
```bash
curl -X POST "http://localhost/agent/chat" \
     -H "Content-Type: application/json" \
     -d '{"query": "南开大学的校训是什么？"}'
```

响应：
```json
{
    "response": "南开大学的校训是"允公允能，日新月异"。",
    "sources": []
}
```

### 2. 知识搜索接口

搜索知识库中的内容。

- **接口**: POST `/agent/search`
- **Content-Type**: application/json

#### 请求参数

```json
{
    "keyword": "string",  // 必填，搜索关键词
    "limit": 10          // 可选，返回结果数量上限，默认10，范围1-50
}
```

#### 响应格式

```json
[
    {
        "title": "string",      // 文档标题
        "content": "string",    // 匹配的内容片段
        "score": 0.95          // 相关度得分
    }
]
```

#### 错误码

- 400: 输入验证错误（例如：关键词为空）
- 500: 服务器内部错误

### 3. 状态检查接口

获取Agent服务的运行状态。

- **接口**: GET `/agent/status`

#### 响应格式

```json
{
    "status": "running",                  // 服务状态
    "version": "1.0.0",                  // 版本号
    "capabilities": ["chat", "search"]    // 支持的功能列表
}
```

## 开发说明

1. 所有接口都需要进行错误处理，使用统一的错误响应格式
2. 接口遵循RESTful设计规范
3. 所有请求和响应都使用JSON格式
4. 接口支持异步处理，使用FastAPI框架实现

## 环境要求

- Python 3.8+
- FastAPI
- Pydantic
- Loguru

## 配置说明

主要配置项（在config.py中）：

```python
{
    "core.agent.coze.wx_bot_id": "your_bot_id",    # Coze机器人ID
    "core.agent.coze.api_key": "your_api_key",      # Coze API密钥
    "core.agent.coze.base_url": "api_base_url"      # Coze API基础URL
}
```

## 更新历史

### v1.0.0 (2024-03-12)

- 实现基础的对话功能
- 添加知识搜索接口框架
- 添加服务状态检查接口 