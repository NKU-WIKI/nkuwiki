# nkuwiki 开源·共治·普惠的南开百科

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)[![Version](https://img.shields.io/badge/version-0.0.1-blue.svg)](https://github.com/your-org/nkuwiki/releases)

## 目录

- [nkuwiki 开源·共治·普惠的南开百科](#nkuwiki-开源共治普惠的南开百科)
  - [目录](#目录)
  - [🎯 愿景与目标](#-愿景与目标)
  - [🤝 如何参与](#-如何参与)
  - [🏗 系统架构图](#-系统架构图)
  - [📅 演进路线](#-演进路线)
  - [💻 技术实现](#-技术实现)
    - [项目结构树](#项目结构树)
    - [技术选型表](#技术选型表)
    - [核心模块实现](#核心模块实现)
      - [爬虫混合架构实现方案](#爬虫混合架构实现方案)
      - [知识库入库流程](#知识库入库流程)
      - [用户贡献管道](#用户贡献管道)
      - [agent交互架构](#agent交互架构)
      - [web服务架构](#web服务架构)
    - [部署规范](#部署规范)
  - [📚 文档维护](#-文档维护)

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
    - 🔓 接入**南开全渠道数据源**（网站/微信公众号/校园集市/小红书/微博/抖音/B站/知乎etc.）
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
- 💎 **贡献流通系统**：
  - 🎁 **激励全周期覆盖**（采集/清洗/标注）
  - ♻️ **数字权益兑换**：
    - ⚡ 优先计算资源
    - 🎚️ 个性化知识门户
    - 🗳️ 治理代议席位

  ## 🤝 如何参与

  ⭐ **联系方式**：您可以直接添加微信 `ao_kimi` ，飞书联系 @廖望，或者联系开发团队与志愿者团队任意成员。

  🌱 **使用即贡献，贡献即治理**：您可以通过使用我们的服务，联系我们反馈您的宝贵意见，向朋友安利我们的服务，上传您认为有价值的资料，在我们的项目提issue或PR，或者直接加入开发团队与志愿者团队等多种方式为社区发展作出贡献。我们欢迎任何形式，不计大小的贡献！

现任开发团队

- [@aokimi0](https://github.com/aokimi0)
- [@LiaojunChen](https://github.com/LiaojunChen)
- [@hht421](https://github.com/hht421)
- [@ym-guan](https://github.com/ym-guan)

现任志愿者团队

- [@aokimi0](https://github.com/aokimi0)
- [@hht421](https://github.com/hht421)

## 🏗 系统架构图

![系统架构图](./docs/assets/系统架构图.png)

## 📅 演进路线

| 阶段             | 关键里程碑                          | 技术栈与架构决策                     | 交付产物                          |
|------------------|-------------------------------------|--------------------------------------|-----------------------------------|
| **MVP启动期**    | ✅ 核心服务上线                      | 🛠 FastAPI（API网关）                | 📦 容器化核心服务                 |
| (0-3月)          | ▪ 微信公众号智能问答MVP             | 🤖 Coze（智能Agent）                  | 📚 部署指南+运维手册              |
|                  | ▪ 动态爬虫框架1.0                   | 🕷 Playwright（自动化爬虫） | 🔍 知识库检索API文档              |
|                  | ▪ 重点平台数据接入（官网/公众号）     |                                      |                                   |
|                  | ▪ 知识库基础检索功能                 |                                      |                                   |
| **生态构建期**   | 🚀 核心系统扩展                      | 🕸 Scrapy（分布式爬虫）             | 🧩 可插拔爬虫框架                |
| (4-6月)          | ▪ 全平台爬虫覆盖                    | 📊 Prometheus+Granfana（监控）      | 📈 质量评估系统                  |
|                  | ▪ 数据质量看板1.0                   | 🔐 JWT+RBAC（权限控制）             | 🪙 Token激励原型系统             |
|                  | ▪ 用户贡献系统原型                  |                                      |                                   |
|                  | ▪ 反爬策略增强                      |                                      |                                   |
| **体系升级期**   | 🌟 系统架构演进                      | ☁ Spring Cloud Alibaba（微服务）   | 🔄 积分系统微服务集群            |
| (7-9月)          | ▪ 微服务化改造                      | 📦 ELK（日志分析）                  | 👁️ 系统健康看板                 |
|                  | ▪ 分布式积分系统                    | 🧠 Milvus（向量检索）               | 🎨 多模态处理SDK                |
|                  | ▪ 全链路监控体系                    |                                      |                                   |
|                  | ▪ 多模态知识引擎                    |                                      |                                   |

**小团队演进策略**：

1. 🎯 功能优先级：采用「剃刀原则」聚焦核心场景，首期仅保留问答/检索/基础爬虫功能
2. 🧪 验证驱动：Token机制先实现简单积分发放，二期再引入兑换/消费闭环
3. 📶 渐进接入：平台接入按「官网→公众号→校园集市→社交平台」顺序分阶段实施
4. 🚧 架构演进：从单体→模块化→微服务渐进式改造，避免早期过度设计

## 💻 技术实现

### 项目结构树

```plaintext
nkuwiki/
├── core/               # 核心基础设施
│   ├── auth/          # 统一认证服务
│   │   ├── duckdb_operator.py
│   │   ├── seaweedfs_client.py
│   │   └── redis_manager.py
│   ├── agent/         # Agent核心模块
│   │   ├── coze_integration.py    # Coze平台交互
│   │   ├── other_platform_integration.py # 其他平台交互
│   │   └── plugin_manager.py # 插件管理系统
│   └── utils/         # 公共工具库
│       ├── anti_spider/  # 反反爬工具
│       └── quality/      # 质量评估工具
│
├── etl/
│   ├── crawler/       # 爬虫统一管理（extraction）
│   │   ├── base_crawler.py # 爬虫基类
│   │   ├── website.py      # 网站爬虫
│   │   ├── wechat.py        # 微信公众号爬虫
│   │   ├── campus_market.py  # 校园集市爬虫
│   │   ├── xiaohongshu.py    # 小红书爬虫
│   │   ├── weibo.py          # 微博爬虫
│   │   ├── douyin.py         # 抖音爬虫
│   │   ├── bilibili.py       # B站爬虫
│   │   └── zhihu.py          # 知乎爬虫
│   └── pipelines/     # 处理管道（transformation+loading）
│       ├── quality_control/ # 质量管控
│       └── data_export/    # 数据导出
│
├── services/
│   ├── wechat/        # 微信公众号服务
│   │   ├── message_router.py # 消息路由
│   │   ├── celery_app.py  # 使用Celery替代Prefect
│   │   ├── contrib_task.py # 用户贡献处理
│   │   ├── task_manager.py # 任务调度
│   │   ├── task_processor.py # 任务处理
│   │   └── admin.py # 管理后台
│   └── website/       # 网站服务
│       └── website_service.py # 网站服务
│
└── infra/
    ├── deploy/        # 部署配置
    │   └── docker-compose.yml
    └── monitoring/    # 监控体系
        ├── loki/      # 日志管理
        └── pyroscope/ # 持续性能分析


/data/                  # 服务器根目录独立存储
├── raw/                # 原始数据
│   ├── website/        # 网站
│   ├── wechat/         # 微信公众号
│   ├── campus_market/  # 校园集市
│   ├── xiaohongshu/    # 小红书
│   ├── weibo/          # 微博
│   ├── douyin/         # 抖音
│   ├── bilibili/       # B站
│   ├── zhihu/          # 知乎
│   ├── volunteer/      # 志愿者团队贡献
│   ├── user/           # 用户贡献数据
└── processed/ 
    ├── structured/    # 结构化数据（DuckDB）
    └── vector/       # 向量数据（Coze同步）
```

### 技术选型表

| 模块           | 子模块              | 技术栈                                | 版本     | 选型依据                          |
|----------------|-------------------|-------------------------------------|---------|---------------------------------|
| **爬虫引擎**    | 混合采集架构       | Playwright + Selenium              | 1.42.0 / 4.18.0 | 双引擎覆盖现代SPA与传统网页场景，Playwright处理复杂DOM性能提升40% |
|                | 反爬解决方案       | Browserless + mitmproxy            | 2.7.0 / 10.1.0 | 分布式浏览器指纹混淆 + 公众号API流量镜像捕获能力 |
| **数据清洗**    | 数据清洗           | Pandera + DuckDB                  | 0.11.0 / 0.9.2 | 声明式数据验证框架 + 列式存储实时处理能力 |
| **消息队列**    | 用户贡献处理       | RabbitMQ                           | 3.13.0  | 支持AMQP 1.0协议，消息持久化与死信队列保障数据完整性 |
| **存储层**      | 对象存储           | SeaweedFS                          | 3.64    | 对象存储与文件系统统一接口，自动纠删码机制 |
|                | 元数据存储         | DuckDB                            | 0.9.2   | 支持Python原生OLAP查询，向量化执行引擎加速 |
| **任务调度**    | 分布式任务         | Celery + Redis                     | 5.3.6 / 7.2.4 | 支持优先级队列与任务状态追踪，Redis Streams保障消息可靠性 |
| **监控体系**    | 链路追踪          | OpenTelemetry                     | 1.24.0  | 统一观测数据标准，支持Metrics/Logs/Traces三支柱 |
| **核心组件**    | API网关           | Apache APISIX                     | 3.8.0   | 动态插件架构支持JWT鉴权/限流/熔断等策略热更新 |
| **Agent模块**  | API交互层         | FastAPI + HTTPX                    | 0.110.0 | 异步HTTP客户端支持SSE/WebSocket长连接 |
|                | 多模态处理        | Coze Multi-Modal API             | 2024.2  | 支持文生图/图生文多模态联合推理 |
| **微信服务**    | 消息路由          | FastAPI WebSocket                | 0.110.0 | 支持万人级并发消息推送，消息压缩率60%+ |
|                | 任务调度          | Celery                           | 5.3.6   | 支持定时任务与工作流编排，任务失败自动重试 |
| **基础设施**    | 容器编排          | Docker Compose                   | 2.24.5  | 支持服务依赖管理，开发-生产环境一致性保障 |
|                | 日志管理          | Loki + Promtail                  | 2.9.4   | 支持日志标签化索引，存储空间节省70% |

### 核心模块实现

#### 爬虫混合架构实现方案

![爬虫混合架构方案](./docs/assets/爬虫混合架构方案.png)

说明：

1. **复杂登录场景**：使用Selenium处理南开教务系统等需要模拟完整登录流程的系统（[BrowserStack指南](https://www.browserstack.com/guide/web-scraping-using-selenium-python)）。
2. **混合抓包模式**：结合Mitmproxy+Selenium Wire实现公众号API请求捕获（[Scrape-it案例](https://scrape-it.cloud/blog/web-scraping-using-selenium-python)）。
3. **反反爬策略**：通过Browserless集群实现IP轮换和浏览器指纹混淆。
4. **性能平衡**：Playwright处理现代Web应用（B站/小红书），Selenium专注复杂传统系统。

#### 知识库入库流程

![知识库入库流程](./docs/assets/知识库入库流程.png)

#### 用户贡献管道

![用户贡献管道](./docs/assets/用户贡献管道.png)

#### agent交互架构

![agent交互架构](./docs/assets/agent交互架构.png)

#### web服务架构

![web服务架构](./docs/assets/web服务架构.png)

### 部署规范

```yaml
version: '3.8'

services:
  apisix:
    image: apache/apisix:3.8.0-alpine
    ports:
      - "9080:9080"
      - "9180:9180"
    volumes:
      - ./apisix/config.yaml:/usr/local/apisix/conf/config.yaml
    networks:
      - nkuwiki-net
    depends_on:
      redis:
        condition: service_healthy
      rabbitmq:
        condition: service_healthy

  web:
    image: nkuwiki/web:v1.2
    env_file: .env
    networks:
      - nkuwiki-net
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  celery_worker:
    image: nkuwiki/worker:v1.1
    env_file: .env
    command: celery -A services.wechat.celery_app worker --loglevel=info
    depends_on:
      redis:
        condition: service_healthy
      rabbitmq:
        condition: service_healthy

  redis:
    image: redis:7.2.4-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s

  rabbitmq:
    image: rabbitmq:3.13.0-management-alpine
    environment:
      RABBITMQ_DEFAULT_USER: ${RABBITMQ_USER}
      RABBITMQ_DEFAULT_PASS: ${RABBITMQ_PASS}
    ports:
      - "5672:5672"
      - "15672:15672"
    volumes:
      - rabbitmq_data:/var/lib/rabbitmq
    healthcheck:
      test: ["CMD", "rabbitmq-diagnostics", "check_running"]
      interval: 30s

  seaweedfs:
    image: chrislusf/seaweedfs:3.64
    ports:
      - "9333:9333"  # Master
      - "8080:8080"  # Volume
    command: "server -dir=/data"
    volumes:
      - seaweedfs_data:/data

  otel_collector:
    image: otel/opentelemetry-collector-contrib:0.96.0
    volumes:
      - ./infrastructure/monitoring/otel-config.yaml:/etc/otelcol/config.yaml
    ports:
      - "4317:4317" # OTLP gRPC
      - "4318:4318" # OTLP HTTP

volumes:
  redis_data:
  rabbitmq_data:
  seaweedfs_data:

networks:
  nkuwiki-net:
    driver: bridge
    attachable: true

# 反向代理配置（可选）
# traefik:
#   image: traefik:v2.11
#   ports:
#     - "80:80"
#     - "443:443"
#   volumes:
#     - /var/run/docker.sock:/var/run/docker.sock:ro
```

**部署说明**：

1. 使用`env_file`管理敏感配置（需创建.env文件）。
2. 健康检查机制保障服务启动顺序。
3. 独立存储卷实现数据持久化。
4. OpenTelemetry Collector实现统一监控。

## 📚 文档维护

| 版本 | 日期       | 修改人   | 变更描述               |
|------|------------|----------|-----------------------|
| 1.0  | 2025-02-03 | aokimi   | 初稿       |
| 1.1  | 2025-02-05 | aokimi   | 团队更新|