# Coze 智能体后端 API 文档

## 一、调用说明

### 调用流程

1. 获取 API URL 和 {{ApiKey}}

2. 请求头设置：
   - Header 添加 `Apikey={{ApiKey}}`
   - Body 包含 `AppKey={{ApiKey}}` 和 `UserID`（1-20字符唯一标识）

3. 对话流程：
   - `CreateConversation` 创建会话
   - `ChatQuery` 进行流式对话
   - 可选操作：`StopMessage`/`QueryAgain`/`Feedback`

---

## 二、核心 API 接口

### 会话管理

#### 创建会话 `POST /create_conversation`

**请求参数**：

| 参数    | 类型               | 必填 | 说明               |
|---------|--------------------|------|--------------------|
| AppKey  | string             | ✓    | 应用 key           |
| Inputs  | map(string,string) | ✗    | 变量输入           |
| UserID  | string             | ✓    | 用户唯一标识       |

**响应参数**：

| 参数          | 类型                     | 说明       |
|---------------|--------------------------|------------|
| Conversation  | AppConversationBrief     | 会话信息   |
| BaseResp      | BaseResp                 | 状态响应   |

---

### 对话交互

#### 发起对话 `POST /chat_query`

**请求参数**：

| 参数                | 类型             | 必填 | 说明                      |
|---------------------|------------------|------|---------------------------|
| AppKey              | string           | ✓    | 应用 key                  |
| AppConversationID   | string           | ✓    | 会话 ID                   |
| Query               | string           | ✓    | 用户输入内容              |
| ResponseMode        | string           | ✓    | streaming/blocking       |
| PubAgentJump        | bool             | ✗    | 是否输出agent信息         |
| UserID              | string           | ✓    | 用户唯一标识              |

**响应**：SSE 格式数据流

#### 消息流响应格式

| 字段          | 类型             | 说明                                                                 |
|---------------|------------------|----------------------------------------------------------------------|
| event         | string           | 数据类型：text/image/audio/video/file 等                            |
| data          | object           | 包含事件类型和内容：                                                 |
| - event       | string           | 事件类型：message_start/message_end/knowledge_retrieve_start 等     |
| - docs        | object           | 当事件为知识检索结束时返回：                                         |
|   - outputList| array            | 检索结果列表，包含 output 等字段                                    |

---

#### 重新生成 `POST /query_again`

**请求参数**：

| 参数                | 类型     | 必填 | 说明              |
|---------------------|----------|------|-------------------|
| AppKey              | string   | ✓    | 应用 key          |
| AppConversationID   | string   | ✓    | 会话 ID           |
| MessageID           | string   | ✓    | 上轮消息 ID        |
| UserID              | string   | ✓    | 用户唯一标识      |

---

### 会话历史

#### 获取消息历史 `POST /get_conversation_messages`

**请求参数**：

| 参数                | 类型     | 必填 | 说明              |
|---------------------|----------|------|-------------------|
| AppKey              | string   | ✓    | 应用 key          |
| AppConversationID   | string   | ✓    | 会话 ID           |
| Limit               | i32      | ✓    | 返回条数限制       |
| UserID              | string   | ✓    | 用户唯一标识      |

**响应参数**：

| 参数          | 类型                     | 说明           |
|---------------|--------------------------|----------------|
| Messages      | list(ChatMessageInfo)    | 历史消息列表   |
| BaseResp      | BaseResp                 | 状态响应       |

---

## 三、全量 API 列表

| 接口名称                 | 方法   | 路径                      | 功能说明                 |
|--------------------------|--------|---------------------------|--------------------------|
| 获取应用配置            | POST   | /get_app_config_preview  | 获取变量配置和开场白     |
| 更新会话                | POST   | /update_conversation     | 修改会话名称和变量       |
| 删除消息                | POST   | /delete_message          | 删除指定消息             |
| 设置默认回答            | POST   | /set_message_answer_used | 设置多回答中的默认选项   |
| 工作流测试              | POST   | /run_app_workflow        | 同步测试工作流           |

---

## 四、数据结构详情

### AppConversationBrief

| 字段                | 类型   | 说明           |
|---------------------|--------|----------------|
| AppConversationID   | string | 会话 ID        |
| ConversationName    | string | 会话名称       |

### ChatMessageInfo

| 字段          | 类型               | 说明                 |
|---------------|--------------------|----------------------|
| QueryID       | string             | 询问 ID              |
| AnswerInfo    | MessageAnswerInfo  | 主回答信息           |
| OtherAnswers  | list(MessageAnswerInfo) | 其他备选回答       |
| QueryExtends  | QueryExtendsInfo   | 附件文件信息         |

### MessageAnswerInfo

| 字段           | 类型         | 说明                |
|----------------|--------------|---------------------|
| MessageID      | string       | 消息唯一 ID         |
| TotalTokens    | i32          | 消耗 token 总数     |
| Latency        | double       | 响应耗时（秒）      |
| TracingJsonStr | string       | 调试追踪信息        |

### MessageStreamResponse

| 字段   | 类型   | 说明                                                                 |
|--------|--------|----------------------------------------------------------------------|
| event  | string | 数据类型：text/image/audio/video/file 等                            |
| data   | object | 包含事件类型和内容：                                                 |
| - event| string | 事件类型：message_start/message_end/knowledge_retrieve_start 等     |
| - docs | object | 当事件为 knowledge_retrieve_end 或 qa_retrieve_end 时返回：         |
|   - OutputList | array | 检索结果列表，每个元素包含 output 字段                              |

---

## 五、枚举类型

### LikeType

| 值       | 说明       |
|----------|------------|
| -1       | 踩         |
| 0        | 默认       |
| 1        | 赞         |

### VariableType

| 值         | 说明       |
|------------|------------|
| Text       | 文本类型   |
| Enum       | 枚举类型   |
| Paragraph  | 段落类型   |

---

注：保留全部技术参数，优化表格展示和层级结构，修正格式问题，关键字段用**加粗**突出显示。

