# nkuwiki 配置指南

本文档为 `nkuwiki` 项目提供详细的配置说明，旨在帮助您快速、准确地完成项目设置。

## 核心概念

项目的配置系统设计简洁，核心逻辑如下：

1.  **内置默认配置**: 项目在 `config.py` 文件中预定义了一套完整的默认配置 `available_setting`。这保证了即使没有外部配置文件，项目也能以基础模式运行。
2.  **`config.json` 覆盖**: 您可以通过在项目根目录下创建一个 `config.json` 文件来自定义配置。项目启动时会自动加载此文件，并将其中的设置覆盖到默认配置上。

**简单来说，您只需要在 `config.json` 中指定您想修改的配置项即可。**

## 快速开始：创建您的 `config.json`

1.  **复制模板**: 项目在 `docs/config-template/` 目录下提供了多种场景的配置模板（如 `config-terminal.json`, `config-wechatmp.json` 等）。请根据您的需求，选择一个模板并将其复制到项目**根目录**，然后重命名为 `config.json`。

    例如，如果您想在终端中运行，可以执行：
    ```bash
    cp docs/config-template/config-terminal.json ./config.json
    ```

2.  **修改配置**: 打开根目录下的 `config.json` 文件，填入必要的敏感信息，例如 `api_key`、`bot_id`、数据库密码等。

    一个最小化的 `config.json` 示例可能如下：
    ```json
    {
      "core": {
        "agent": {
          "coze": {
            "api_key": "your_coze_api_key_here",
            "bot_id": ["your_bot_id_here"]
          }
        }
      },
      "etl": {
        "data": {
          "mysql": {
            "password": "your_database_password"
          }
        }
      }
    }
    ```

## 主要配置项说明

配置文件主要分为三大块：`core`, `services`, `etl`。

### 1. `core`: 核心与智能体配置

-   `core.agent`: 集中配置所有第三方大模型（LLM）的 API 信息。
    -   `coze`, `openai`, `zhipu`, `gemini` 等都配置在此处。
    -   **关键字段**: `api_key`, `base_url`, `bot_id` (部分模型需要)。

    ```json
    "core": {
      "agent": {
        "coze": {
          "api_key": "YOUR_API_KEY",
          "bot_id": ["YOUR_BOT_ID"]
        },
        "openai": {
          "api_key": "YOUR_OPENAI_KEY",
          "model": "gpt-4-turbo"
        }
      }
    }
    ```

### 2. `services`: 服务通道配置

-   `services.channel_type`: 指定项目启动时运行的服务类型，例如 `terminal`, `wechatmp`, `website`。
-   `services.agent_type`: 指定服务默认使用的智能体类型，例如 `coze`, `openai`。
-   每个通道的专属配置也在这里，如 `terminal` 的欢迎语，`wechatmp_service` 的 `token` 和 `app_id` 等。

    ```json
    "services": {
      "channel_type": "terminal",
      "agent_type": "coze",
      "terminal": {
        "stream_output": true,
        "welcome_message": "欢迎使用 NKU Wiki 智能助手!"
      }
    }
    ```

### 3. `etl`: 数据处理管道配置

-   `etl.data`: 配置数据存储相关的连接信息。
    -   `base_path`: 数据文件的根目录，默认为 `./data`。
    -   `mysql`: MySQL 数据库连接信息 (`host`, `port`, `user`, `password`, `name`)。
    -   `qdrant`: Qdrant 向量数据库的 URL 和集合名称。
    -   `redis`: Redis 连接信息。
    -   `elasticsearch`: Elasticsearch 连接信息。
-   `etl.embedding`: 配置文本嵌入模型的名称或路径。
-   `etl.retrieval`: 配置检索策略相关的参数。

    ```json
    "etl": {
      "data": {
        "base_path": "./data",
        "mysql": {
          "host": "127.0.0.1",
          "port": 3306,
          "user": "root",
          "password": "your_password",
          "name": "nkuwiki"
        },
        "qdrant": {
          "url": "http://localhost:6333"
        }
      },
      "embedding": {
        "name": "BAAI/bge-large-zh-v1.5"
      }
    }
    ```

## 高级技巧

-   **点分路径访问**: 在代码中，您可以使用点分路径（dot notation）来方便地获取嵌套的配置项，例如：
    ```python
    from config import Config
    config = Config()
    api_key = config.get("core.agent.coze.api_key")
    ```
-   **查看完整配置**: 要了解所有可用的配置项及其默认值，请直接查阅 `config.py` 文件中的 `available_setting` 字典。

---

配置完成后，您就可以根据 [安装指南](./installation_guide.md) 启动项目了。 