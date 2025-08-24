# nkuwiki 开源·共治·普惠的南开百科

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)[![Version](https://img.shields.io/badge/version-0.3.0-blue.svg)](https://github.com/your-org/nkuwiki/releases)[![DeepWiki](https://img.shields.io/badge/DeepWiki-documentation-blue)](https://deepwiki.com/NKU-WIKI/nkuwiki)

<img src="./docs/assets/logo-lc-green.png" width="400" alt="nkuwiki logo" />

## demo

![demo](./docs/assets/wxapp.gif)

## 🚀 立即体验

- 🔗 [Coze](https://www.coze.cn/store/agent/7473464038963036186?bot_id=true&bid=6ffcvvj3k6g0j)
- 🔗 [Hiagent](https://coze.nankai.edu.cn/product/llm/chat/cuh2gospkp8br093l2eg)
- 🤖 企微机器人参考[三步将nkuwiki bot添加到你的群](https://nankai.feishu.cn/wiki/UT4EwiPxmisBdOk3d1ycnGR2nve?from=from_copylink)
- 🔎 微信服务号：nkuwiki知识社区（无限制，用户体验更好）
- 🗝️ 微信订阅号 nkuwiki（有消极回复限制）
- 🔥 微信小程序：nku元智wiki
  
![微信小程序码](https://raw.githubusercontent.com/aokimi0/image-hosting-platform/main/img/2ed4dd7258abda2204b768c7e1017cf.jpg)

## 🎯 愿景与目标

我们致力于构建**南开知识共同体**，践行 **开源·共治·普惠** 三位一体价值体系
（🔓 技术开源透明 + 🤝 社区协同共治 + 🆓 服务永久普惠），实现：

- 🚀 **消除南开学子信息差距**
- 💡 **开放知识资源免费获取**
- 🌱 **构建可持续的互助社区**

**项目亮点**：

- 🤖 **开源知识中枢**
  - 🧠 双擎驱动：**RAG**框架 + **SOTA**模型推理
  - 🔄 **动态知识图谱**
    - 🔓 接入**南开全渠道数据源**（网站/微信公众号/校园集市/小红书/微博/抖音/B站/知乎etc.，详见[数据源重点实体清单](https://nankai.feishu.cn/wiki/OEuGw04XXiqJnekbawcc9XsQnUf)）
    - 🤝 **社区共治**：志愿者团队与用户协同维护
    - 🛡️ **开源评估框架**（贡献者透明审计）
  - 🔍 多模态和丰富插件支持
    - 支持文本/语音/图像/视频全感官知识获取
    - 丰富插件支持：搜索引擎、创意生图、数据分析etc.

- 👥 **普惠共治机制**
  - 三维协同架构：
    - 💻 **技术层**：开源社区维护核心栈
    - ⚖️ **治理层**：DAO式内容审核委员会
    - 👤 **应用层**：贡献即治理（1Token=1投票权）

## ⚡ 快速开始

1. **克隆项目**
```bash
git clone https://github.com/NKU-WIKI/nkuwiki.git
cd nkuwiki
git submodule update --init --recursive
```

2. **环境准备 (推荐)**
    - 确保你已安装 Python 3.10+。
    - 为了避免依赖冲突，强烈建议在 Python 虚拟环境中安装项目。

    <details>
    <summary>点击查看如何创建虚拟环境</summary>

    **方法一: 使用 venv (Python自带)**
    ```bash
    # 在项目根目录创建名为 .venv 的虚拟环境
    python3 -m venv .venv

    # 激活虚拟环境
    # Linux/MacOS
    source .venv/bin/activate 
    # Windows
    .venv\\Scripts\\activate
    ```

    **方法二: 使用 conda**
    ```bash
    # 创建名为 nkuwiki 的环境
    conda create -n nkuwiki python=3.10 -y

    # 激活环境
    conda activate nkuwiki
    ```
    </details>

3. **安装依赖**
```bash
pip install -r requirements.txt

# 安装 Playwright 的浏览器依赖
playwright install chromium
```

4. **配置项目**
    - 在项目根目录创建 `config.json` 文件，并填入必要的配置，例如你的大模型API Key。
    - 更多详细信息，请参考 `docs/configuration_guide.md`。

5. **启动问答服务**

    本项目支持多种渠道与用户交互，核心启动命令是 `python app.py`。

    **a. 终端模式 (默认)**

    直接在命令行中与智能体进行对话，适合开发和快速测试。

    ```bash
    python app.py
    ```
    ![终端模式效果](./docs/assets/terminal-qa.png)

    **b. API服务模式**

    将问答能力封装为RESTful API，供前端或其他服务调用。

    ```bash
    # 启动API服务，监听在8000端口
    python app.py --api --port 8000

    # 检查服务健康状态
    curl -X GET "http://localhost:8000/api/health"
    ```

6.  **运行ETL与爬虫**

    ETL（数据提取、转换、加载）是保证知识库持续更新的核心。

    ```bash
    # 运行ETL全流程（扫描、索引、洞察），处理过去24小时的数据
    python etl/daily_pipeline.py

    # 仅运行微信公众号爬虫
    python -m etl.crawler.wechat

    # 仅运行校园集市爬虫
    python -m etl.crawler.market
    ```
    - 更多关于ETL和爬虫的使用说明，请参考 [ETL流程指南](./docs/etl_pipeline_guide.md) 和 [爬虫开发指南](./docs/crawler_guide.md)。

## 🏗 系统架构

![系统架构图](./docs/assets/系统架构图.png)

项目采用模块化设计，主要包含以下模块：

- **core/**: 核心功能模块
  - agent/: 智能体对话实现
  - utils/: 通用工具

- **etl/**: 数据处理模块
  - crawler/: 数据采集 (详见 [爬虫模块使用指南](./docs/crawler_guide.md))
  - transform/: 数据转换
  - load/: 数据加载
  - embedding/: 向量嵌入
  - retrieval/: 知识检索

- **api/**: API服务模块
  - models/: 数据模型
  - routes/: 路由处理
  - common/: 通用工具

- **services/**: 多渠道服务
  - app/: 微信小程序
  - wechatmp/: 微信公众号
  - wework/: 微信机器人
  - website/: 网站
  - terminal/: 终端服务

## 💻 技术实现

### 技术选型

| 模块 | 子模块 | 技术栈 | 版本 | 选型依据 |
| --- | --- | --- | --- | --- |
| **爬虫引擎** | 混合采集架构 | Playwright + Selenium | 1.42.0 / 4.18.0 | 双引擎覆盖现代SPA与传统网页场景，Playwright处理复杂DOM性能提升40% |
| **数据清洗** | 数据清洗 | Pandera + DuckDB | 0.11.0 / 0.9.2 | 声明式数据验证框架 + 列式存储实时处理能力 |
| **存储层** | 对象存储 | SeaweedFS | 3.64 | 对象存储与文件系统统一接口，自动纠删码机制 |
| **Agent模块** | API交互层 | FastAPI + HTTPX | 0.110.0 | 异步HTTP客户端支持SSE/WebSocket长连接 |
| **微信服务** | 消息路由 | FastAPI WebSocket | 0.110.0 | 支持万人级并发消息推送，消息压缩率60%+ |
| **基础设施** | 容器编排 | Docker Compose | 2.24.5 | 支持服务依赖管理，开发-生产环境一致性保障 |

### 核心模块实现

#### 爬虫混合架构实现方案

![爬虫混合架构方案](./docs/assets/爬虫混合架构方案.png)

说明：

1. **复杂登录场景**：使用Selenium处理南开教务系统等需要模拟完整登录流程的系统
2. **混合抓包模式**：结合Mitmproxy+Selenium Wire实现公众号API请求捕获
3. **反反爬策略**：通过Browserless集群实现IP轮换和浏览器指纹混淆
4. **性能平衡**：Playwright处理现代Web应用（B站/小红书），Selenium专注复杂传统系统

#### 知识库入库流程

![知识库入库流程](./docs/assets/知识库入库流程.png)

#### agent交互架构

![agent交互架构](./docs/assets/agent交互架构.png)

## 📁 项目目录结构

```
nkuwiki/
├── api/                  # FastAPI 后端API模块
│   ├── models/           # Pydantic 数据模型
│   └── routes/           # API 路由处理
├── core/                 # 核心共享模块
│   ├── agent/            # RAG 与多智能体核心逻辑
│   └── utils/            # 通用工具（日志、缓存等）
├── data/                 # 数据持久化目录 (Git忽略)
│   ├── mysql/            # MySQL 数据文件
│   ├── qdrant/           # Qdrant 向量数据
│   ├── raw/              # 爬虫抓取的原始数据
│   └── models/           # 下载的AI模型
├── docs/                 # 项目文档和资产
│   └── assets/           # 文档中引用的图片
├── etl/                  # 数据提取、转换、加载 (ETL) 管道
│   ├── crawler/          # 各类爬虫实现
│   ├── load/             # 数据加载到数据库的逻辑
│   └── daily_pipeline.py # 每日运行的ETL任务编排器
├── infra/                # 基础设施与部署配置
│   └── monitoring/       # 监控相关配置
├── services/             # 多渠道服务接口
│   ├── wechatmp/         # 微信公众号服务
│   └── terminal/         # 终端交互服务
├── app.py                # ✅ 应用主入口，用于启动服务
├── config.py             # ⚙️ 全局配置加载与管理
├── config.json           # 🔒 配置文件 (私密，需自行创建)
├── Dockerfile            # 📦 应用服务的 Docker 镜像定义
├── docker-compose.yml    # 🐳 应用服务 (api) 的 Docker Compose 文件
├── docker-compose.infra.yml # 🏗️ 基础设施 (DB, Redis等) 的 Docker Compose 文件
├── nkuwiki_service_manager.sh # 🚀 自动化部署与管理脚本
└── requirements.txt      # Python 依赖列表
```

### 核心目录职责

-   **`api/`**: 负责对外提供标准的 RESTful API。它是前后端分离的核心，定义了所有的数据接口和数据模型。
-   **`core/`**: 包含项目中最核心的业务逻辑，特别是 `agent` 模块，它实现了完整的 RAG (检索增强生成) 流程和多智能体协作。
-   **`etl/`**: 项目的数据中枢。所有外部数据的抓取、清洗、处理、索引、入库都在此模块完成，是保证知识库新鲜、准确的关键。
-   **`services/`**: 面向终端用户的服务层。它将 `core` 模块的核心能力封装成不同的服务形式，如微信公众号、终端命令行等。
-   **`infra/`**: 存放所有与部署、运维、监控相关的配置，如 `docker-compose` 文件、`Dockerfile` 和 `Nginx` 配置。

## 📅 演进路线

| 阶段 | 关键里程碑 | 技术栈与架构决策 | 交付产物 |
| --- | --- | --- | --- |
| **MVP启动期** | ✅ 核心服务上线 | 🛠 FastAPI（API网关） | 📦 容器化核心服务 |
| (0-3月) | ▪ 微信公众号智能问答MVP | 🤖 Coze（智能Agent） | 📚 部署指南+运维手册 |
| **生态构建期** | 🚀 核心系统扩展 | 🕸 Scrapy（分布式爬虫） | 🧩 可插拔爬虫框架 |
| (4-6月) | ▪ 全平台爬虫覆盖 | 📊 Prometheus+Grafana（监控） | 📈 质量评估系统 |
| **体系升级期** | 🌟 系统架构演进 | ☁ Spring Cloud Alibaba（微服务） | 🔄 积分系统微服务集群 |
| (7-9月) | ▪ 微服务化改造 | 📦 ELK（日志分析） | 👁️ 系统健康看板 |

## 🔧 开发指南

- **API文档**: [API Documentation](./docs/api_docs.md)
- **ETL流程**: [ETL Pipeline Guide](./docs/etl_pipeline_guide.md)
- **爬虫开发**: [Crawler Development Guide](./docs/crawler_guide.md)
- **RAG架构**: [RAG Strategy](./docs/rag.md)
- **详细配置**: [Configuration Guide](./docs/configuration_guide.md)

或参考完整的[飞书开发文档](https://nankai.feishu.cn/wiki/U3hSweEsUiJDHKkQtVycuNSMnMe)。

## 🔩 部署指南 (Docker & Systemd)

本项目提供了一套基于 Docker 和 `systemd` 的自动化部署方案，通过 `nkuwiki_service_manager.sh` 脚本可以方便地在同一台服务器上管理 `main` (生产) 和 `dev` (开发) 两个环境。

### 1. 环境要求

在开始之前，请确保您的服务器（推荐 Ubuntu 22.04+）满足以下条件：
- `root` 用户权限。
- 已安装 [Git](https://git-scm.com/downloads)。
- 已安装 [Docker](https://docs.docker.com/engine/install/ubuntu/) 和 [Docker Compose](https://docs.docker.com/compose/install/)。
- 已安装 [Nginx](https://www.digitalocean.com/community/tutorials/how-to-install-nginx-on-ubuntu-22-04)。

### 2. 部署步骤

所有部署操作都通过 `nkuwiki_service_manager.sh` 脚本完成，该脚本需要以 `root` 权限运行。

```bash
sudo ./nkuwiki_service_manager.sh [命令] [参数]
```

#### **第一步：启动基础设施服务 (仅需一次)**

基础设施（数据库、缓存等）是所有分支共享的。首次部署时，需要先启动它们。

```bash
sudo ./nkuwiki_service_manager.sh start-infra
```
此命令会使用 `docker-compose.infra.yml` 在后台启动 `MySQL`, `Redis`, `Qdrant` 和 `Elasticsearch` 容器。

#### **第二步：部署应用分支 (main/dev)**

您可以独立部署 `main` 或 `dev` 分支的应用。

- **部署 `main` 分支 (生产环境)**
  ```bash
  sudo ./nkuwiki_service_manager.sh start main
  ```
  该命令会自动完成以下工作：
  1. 构建 `api` 服务的 Docker 镜像。
  2. 启动一个名为 `nkuwiki_main` 的容器，API 服务监听在 **8000** 端口。
  3. 更新 Nginx 配置，将流量导向该容器。
  4. 创建并启用 `systemd` 服务 `nkuwiki@main.service`，实现开机自启。

- **部署 `dev` 分支 (开发环境)**
  ```bash
  sudo ./nkuwiki_service_manager.sh start dev
  ```
  与部署 `main` 分支类似，但 `api` 服务将监听在 **8001** 端口，容器名为 `nkuwiki_dev`，`systemd` 服务为 `nkuwiki@dev.service`。

#### **第三步：验证部署**

部署完成后，您可以通过 `status` 命令检查服务状态：

```bash
# 查看 main 分支状态
sudo ./nkuwiki_service_manager.sh status main

# 查看 dev 分支状态
sudo ./nkuwiki_service_manager.sh status dev

# 查看共享的基础设施状态
sudo ./nkuwiki_service_manager.sh status-infra
```

### 3. 服务管理

使用管理脚本可以方便地对服务进行日常维护。

- **停止服务**: `sudo ./nkuwiki_service_manager.sh stop [main|dev]`
- **重启服务**: `sudo ./nkuwiki_service_manager.sh restart [main|dev]`
- **查看日志**: `sudo ./nkuwiki_service_manager.sh logs [main|dev]`

### 4. Nginx 路由机制：如何切换 main/dev 环境

Nginx 作为反向代理，可以根据客户端请求的 HTTP 头动态地将 API 请求转发到 `main` 或 `dev` 环境。

- **切换机制**: 通过 `X-Branch` 请求头来切换。
  - `X-Branch: dev`: 请求将被转发到 `dev` 环境 (8001端口)。
  - `X-Branch: main` 或 **不提供此请求头**: 请求将被转发到 `main` 环境 (8000端口)。

- **前端应用须知**:
  如果前端应用需要连接到 `dev` 环境进行测试，开发者必须在发起 API 请求时，手动添加 `X-Branch: dev` 这个 HTTP Header。

  示例 (使用 `curl`):
  ```bash
  # 请求将发送到 main 环境
  curl http://your-domain.com/api/some-endpoint

  # 请求将发送到 dev 环境
  curl -H "X-Branch: dev" http://your-domain.com/api/some-endpoint
  ```

### 5. 开机自启 (Systemd)

`start` 命令会自动为您创建 `systemd` 服务，使应用能够在服务器重启后自动运行。

您也可以使用标准的 `systemctl` 命令来手动管理这些服务：
```bash
# 管理 main 分支服务
sudo systemctl [start|stop|status|restart] nkuwiki@main.service

# 管理 dev 分支服务
sudo systemctl [start|stop|status|restart] nkuwiki@dev.service
```

## 🤝 如何参与

⭐ **联系方式**：您可以直接添加微信 `ao_kimi` ，飞书联系 @廖望，或者联系开发团队与志愿者团队任意成员。

🌱 **使用即贡献，贡献即治理**：您可以通过使用我们的服务，联系我们反馈您的宝贵意见，向朋友安利我们的服务，上传您认为有价值的资料，在我们的项目提issue或PR，或者直接加入开发团队与志愿者团队等多种方式为社区发展作出贡献。我们欢迎任何形式，不计大小的贡献！

现任开发团队：

- [@aokimi0](https://github.com/aokimi0)
- [@client2233](https://github.com/client2233)
- [@Frederick2313072](https://github.com/Frederick2313072)
- [@Because66666](https://github.com/Because66666)
- [@ghost233lism](https://github.com/ghost233lism)
- [@hht421](https://github.com/hht421)


现任志愿者团队：
- [@aokimi0](https://github.com/aokimi0)
- [@hht421](https://github.com/hht421)
- [@hengdaoye50](https://github.com/hengdaoye50)
- [@Because66666](https://github.com/Because66666)
