# Core 模块

## 模块概述

Core模块是nkuwiki平台的核心模块，负责智能体对话、贡献激励、平台治理等算法应用。它提供了智能体管理、会话处理和身份验证等核心功能。

## 子模块

### 1. agent - 智能体应用

智能体管理模块，支持多种类型的AI对话引擎。

- **coze** - Coze平台对接
- **session_manager.py** - 会话管理器
- **agent_factory.py** - 智能体工厂

### 2. api - API接口

提供智能体相关的API接口，包括对话和知识搜索。

- **agent_api.py** - 智能体API接口实现
- **agent_api.md** - API接口文档

### 3. auth - 认证授权

处理用户认证和授权相关功能。

### 4. bridge - 桥接服务

连接各种服务与智能体。

### 5. utils - 工具函数和类

通用工具函数和类库。

- **plugins** - 插件管理系统
- **common** - 通用工具库
- **voice** - 语音处理
- **translate** - 翻译工具

## 配置

Core模块的配置项存储在config.json文件中，路径前缀为`core`：

```json
{
  "core": {
    "agent": {
      "type": "coze",
      "coze": {
        "wx_bot_id": "your_bot_id",
        "api_key": "your_api_key",
        "base_url": "api_base_url"
      }
    }
  }
}
```

## 使用方法

### 导入core模块

```python
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))
from core import logger, config
```

### 使用智能体

```python
from core.agent.agent_factory import create_agent

# 创建智能体
agent = create_agent()

# 对话
response = agent.chat("你好，请问南开大学的校训是什么？")
print(response)
```

## 日志

使用debug级别记录详细信息，info级别记录重要信息。

Core模块的日志文件位于`core/logs/core.log`，使用loguru库记录日志。
