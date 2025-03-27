# 智能体模块 (Agent Module)

智能体模块是nkuwiki核心功能之一，负责处理用户的自然语言查询并生成回复。该模块支持多种AI大模型接口，实现了统一的抽象层，使应用程序可以轻松切换不同的AI提供商。

## 目录结构

```text

core/agent/
├── agent.py                # 智能体基类定义
├── agent_factory.py        # 智能体工厂，负责创建智能体实例
├── session_manager.py      # 会话管理，处理上下文存储和管理
├── ali/                    # 阿里云通义千问模型
├── baidu/                  # 百度文心一言模型
├── bytedance/              # 字节跳动相关模型
├── chatgpt/                # OpenAI ChatGPT模型
├── claudeapi/              # Anthropic Claude模型
├── coze/                   # Coze平台模型
├── dashscope/              # 阿里云DashScope模型
├── deepseek/               # DeepSeek模型
├── dify/                   # Dify平台模型
├── gemini/                 # Google Gemini模型
├── hiagent/                # HiAgent平台模型
├── linkai/                 # LinkAI平台模型
├── minimax/                # MiniMax模型
├── moonshot/               # Moonshot模型
├── openai/                 # OpenAI通用接口
├── xunfei/                 # 讯飞星火模型
└── zhipuai/                # 智谱AI模型

```text

## 智能体基类 (Agent)

所有智能体都继承自`Agent`基类，该基类定义了统一的接口方法:

```python
class Agent(object):
    def reply(self, query, context=None):
        """回复用户查询
        Args:
            query: 用户输入的查询文本
            context: 上下文信息，包含会话ID等
        Returns:
            Reply对象，包含回复内容
        """
        pass

```text

## 智能体工厂 (AgentFactory)

智能体工厂负责根据配置创建相应的智能体实例:

```python
def create_agent(agent_type):
    """创建指定类型的智能体实例
    Args:
        agent_type: 智能体类型代码，参见const.py
    Returns:
        智能体实例
    """
    # 根据agent_type返回相应的智能体实例

```text

## 会话管理 (SessionManager)

会话管理器维护用户与智能体之间的对话历史:

```python
class SessionManager:
    def session_query(self, query, session_id):
        """记录用户查询并返回会话实例"""

    def session_reply(self, reply, session_id):
        """记录智能体回复"""

```text

## 支持的智能体

| 智能体类型 | 描述 | 所需依赖 |
|----------|------|--------|
| coze | Coze平台，支持多种场景 | cozepy |
| hiagent | 南开大学AI平台，基于本地部署的Coze | cozepy |
| openAI | OpenAI通用API，支持GPT-3.5/4系列 | openai |
| chatGPT | OpenAI ChatGPT模型 | openai |
| baidu | 百度文心一言模型 | 无特殊依赖 |
| xunfei | 讯飞星火模型 | websocket-client |
| claudeAPI | Anthropic Claude API | anthropic |
| qwen | 旧版通义千问模型 | broadscope_bailian |
| dashscope | 阿里通义千问DashScope | dashscope |
| gemini | Google Gemini模型 | google-generativeai |
| glm-4 | 智谱AI GLM系列模型 | zhipuai |
| moonshot | Moonshot AI模型 | 无特殊依赖 |
| minimax | MiniMax AI模型 | 无特殊依赖 |
| bytedance_coze | 字节跳动Coze平台 | 无特殊依赖 |

## 使用方法

1. 在`config.json`中配置所需使用的智能体类型:

```json
{
  "services": {
    "agent_type": "coze"  // 指定要使用的智能体类型
  },
  "core": {
    "agent": {
      "coze": {
        "api_key": "your_api_key"
      }
    }
  }
}

```text

2. 在代码中通过工厂方法创建智能体:

```python
from core.agent.agent_factory import create_agent
from core.utils.common import const

# 创建智能体实例

agent = create_agent(const.COZE)

# 使用智能体回复查询

reply = agent.reply("你好，请问南开大学的校训是什么？", context)
print(reply.content)

```text

## 添加新的智能体

要添加新的智能体支持，请按照以下步骤:

1. 在`core/agent/`下创建新的目录

2. 实现继承自`Agent`的子类

3. 在`const.py`中添加新的智能体类型常量

4. 在`agent_factory.py`中添加新的条件分支

5. 在`config.py`中添加默认配置项

示例实现:

```python

# core/agent/myagent/my_agent.py

from core.agent.agent import Agent
from core.bridge.reply import Reply
from config import Config

class MyAgent(Agent):
    def __init__(self):
        self.config = Config()
        self.api_key = self.config.get("core.agent.myagent.api_key")

    def reply(self, query, context=None):
        reply = Reply()
        # 实现回复逻辑
        reply.content = "这是一个示例回复"
        return reply

```text

## 注意事项

1. 所有API密钥等敏感信息应存储在`config.json`而非代码中

2. 使用`core.agent.xxxx`的嵌套路径格式访问配置

3. 每个智能体应负责自己的会话管理和上下文维护

4. 所有智能体都应使用单例模式，使用`@singleton_decorator`装饰

## 实现进度

以下是各模型智能体的实现进度：

| 模型                  | 状态       | 文件                                              |
|-----------------------|------------|---------------------------------------------------|
| 百度文心一言          | 已完成     | `core/agent/baidu/baidu_wenxin.py`                |
| ChatGPT               | 已完成     | `core/agent/chatgpt/chat_gpt_agent.py`            |
| OpenAI                | 已完成     | `core/agent/openai/open_ai_agent.py`              |
| Azure ChatGPT         | 已完成     | `core/agent/chatgpt/chat_gpt_agent.py`            |
| LinkAI                | 已完成     | `core/agent/linkai/link_ai_agent.py`              |
| 讯飞星火              | 已完成     | `core/agent/xunfei/xunfei_spark_agent.py`         |
| Claude API            | 已完成     | `core/agent/claudeapi/claude_api_agent.py`        |
| Google Gemini         | 已完成     | `core/agent/gemini/google_gemini_agent.py`        |
| DeepSeek              | 已完成     | `core/agent/deepseek/deepseek_agent.py`           |
| 字节跳动Coze          | 已完成     | `core/agent/bytedance/bytedance_coze_agent.py`    |
| 阿里云通义千问        | 已完成     | `core/agent/ali/ali_qwen_agent.py`                |
| 阿里云DashScope       | 已完成     | `core/agent/dashscope/dashscope_agent.py`         |
| 智谱AI                | 已完成     | `core/agent/zhipuai/zhipuai_agent.py`             |
| Moonshot              | 已完成     | `core/agent/moonshot/moonshot_agent.py`           |
| Minimax               | 已完成     | `core/agent/minimax/minimax_agent.py`             |
| Dify                  | 已完成     | `core/agent/dify/dify_agent.py`                   |
| HiAgent               | 已完成     | `core/agent/hiagent/hiagent_agent.py`             |

### 升级说明

本项目正在从原基于bot的架构升级到基于agent的架构。升级过程包括：

1. 将类名从`XxxBot`更改为`XxxAgent`

2. 确保正确使用`Config`实例

3. 统一日志格式和错误处理方式

4. 优化代码结构，改进注释和文档

未完成的工作：

1. ~~完成剩余模型的实现~~ (已全部完成)

2. 进行全面测试，确保所有模型可正常工作

3. 优化配置项，确保配置路径一致性

### 配置说明

所有智能体的配置项均遵循`core.agent.<模型名>.<配置项>`的格式，例如：

```json
{
  "core.agent.gemini.api_key": "YOUR_API_KEY",
  "core.agent.gemini.model": "gemini-1.5-pro",
  "core.agent.gemini.temperature": 0.7
}

```text

请在`config.json`文件中配置相应的参数。

# 南开Wiki智能助手模块

本模块实现了南开Wiki的智能助手功能，支持多种大语言模型(LLM)，提供对话、知识检索等能力。

## 主要功能

1. 提供统一Agent接口，支持多种智能体实现
2. 会话状态管理，维护用户对话历史
3. 流式输出支持，减少响应延迟
4. 知识库检索增强，提高回答准确性

## 使用方法

### 智能体工厂

使用工厂方法获取智能体实例：

```python
from core.agent.agent_factory import get_agent

# 获取默认智能体
agent = get_agent()

# 获取指定类型智能体
agent = get_agent("coze")  # 使用Coze智能体

# 获取指定类型和标签的智能体
agent = get_agent("coze", tag="rewrite")  # 使用特定bot_id的Coze智能体
```

### 基本对话

```python
from core.bridge.context import Context, ContextType
from core.bridge.reply import Reply, ReplyType

# 创建上下文
context = Context()
context.type = ContextType.TEXT
context["session_id"] = "user_session_123"
context["stream"] = False  # 是否流式输出

# 发送请求并获取回复
reply = agent.reply("南开大学有什么特色专业？", context)

# 处理回复
if reply.type == ReplyType.TEXT:
    print(reply.content)
```

### 流式对话

```python
# 开启流式输出
context["stream"] = True

# 发送请求并获取流式回复
reply = agent.reply("南开大学有什么特色专业？", context)

# 处理流式回复
if reply.type == ReplyType.STREAM:
    for chunk in reply.content:
        print(chunk, end="", flush=True)
```

### CozeAgent特性

Coze智能体是基于Coze官方API的实现，支持多个机器人(bot)，通过标签区分：

```python
# 引入CozeAgent
from core.agent.coze.coze_agent import CozeAgent

# 使用默认bot
agent = CozeAgent()

# 使用指定标签的bot
agent = CozeAgent(tag="knowledge")  # 使用knowledge标签的bot
```

#### 配置说明

CozeAgent的配置位于config.json中：

```json
{
  "core": {
    "agent": {
      "coze": {
        "api_key": "your_coze_api_key",
        "default_bot_id": "default_bot_id",
        "knowledge_bot_id": "knowledge_bot_id",
        "rewrite_bot_id": "rewrite_bot_id"
      }
    }
  }
}
```

即可通过标签引用特定bot：

```python
agent = CozeAgent(tag="knowledge")
# 使用config中的knowledge_bot_id
```

## 开发指南

### 添加新的智能体

1. 创建新的智能体类，继承自`Agent`基类
2. 实现`reply`方法
3. 在`agent_factory.py`中注册新的智能体

```python
# 示例：实现新的智能体
from core.agent import Agent
from core.bridge.context import Context
from core.bridge.reply import Reply, ReplyType

class MyNewAgent(Agent):
    def __init__(self):
        super().__init__()
        # 初始化代码...
        
    def reply(self, query: str, context: Context) -> Reply:
        # 实现回复逻辑...
        return Reply(ReplyType.TEXT, "回复内容")
```

### 优化与改进

当前优先事项：
- 改进知识库检索质量
- 优化流式输出性能
- 增强对话上下文管理
