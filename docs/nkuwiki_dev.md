# 📚nkuwiki开发文档

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

## 🏗 系统架构图

```plantuml
@startuml
!include https://raw.githubusercontent.com/plantuml-stdlib/C4-PlantUML/master/C4_Container.puml

' ==== 标题样式调整 ====
skinparam titleFontSize 20
skinparam titleFontName "Microsoft YaHei"
skinparam titleFontColor #1A237E

' ==== 布局参数 ====
skinparam nodesep 50
skinparam ranksep 150
skinparam linetype ortho
skinparam defaultFontSize 16
skinparam defaultFontName "Microsoft YaHei"
skinparam monochrome false
skinparam shadowing false
skinparam wrapWidth 150
skinparam nodeFontSize 14
skinparam defaultTextAlignment center
LAYOUT_LEFT_RIGHT()
LAYOUT_WITH_LEGEND()

title nkuwiki 系统架构全景图\n<size:18>——开源·共治·普惠的南开知识生态</size>

' ==== 核心架构 ====

Person(user, "校园用户", "多终端访问服务\n• 微信公众号\n• 网站\n• 飞书", $sprite="person2", $tags="user")
Person(volunteer, "志愿者", "知识库维护与审核", $sprite="person2", $tags="volunteer")
' ==== 核心系统层 ====
System_Boundary(nkuwiki_core, "核心系统层") {
    ContainerDb(knowledge_db, "知识库", "FAISS", "向量化存储\n1. 动态版本控制\n2. 增量更新索引\n3. 志愿者人工回滚", $tags="core_db")
    Container(msg_broker, "消息中枢", "RabbitMQ", "AMQP协议\n1. 持久化队列\n2. 消息确认机制\n3. 消息重试机制", $tags="mq")
    Container(ai_agent, "智能Agent", "Coze", "SOTA-LLM多模态交互\n1. RAG增强\n2. 工作流\n3. 插件调用", $tags="ai")

}

' ==== 系统调度层 ====
System_Boundary(infra, "系统调度层") {
    Container(apisix, "API网关", "Apache APISIX", "流量控制", $tags="infra")
    Container(otel, "监控体系", "OpenTelemetry", "全链路追踪", $tags="monitor")
    Container(celery, "任务调度", "Celery+Redis", "分布式任务", $tags="scheduler")
}

' ==== 数据层 ====
System_Boundary(data_layer, "数据层") {
 ContainerDb(structured_db, "结构化存储", "DuckDB", "关系型数据", $tags="core_db")
    ContainerDb(seaweedfs, "对象存储", "SeaweedFS", "非关系型数据", $tags="storage")
    Container(etl_engine, "ETL引擎", "Playwright+Selenium", "多源数据实时采集\n1. 智能反爬\n2. 数据清洗\n3. 数据载入", $tags="etl")

}

' ==== 外部系统 ====
System_Ext(plugins, "插件市场", "Coze API", $tags="ext")
System_Ext(data_sources, "数据源", "多渠道输入\n1. 网站\n2. 微信公众号\n3. 校园集市\n4. 小红书\n5. ...", $tags="ext")

' ==== 数据流关系 ====

' 用户流
Rel(user, msg_broker, "请求服务/提交贡献", "微信/网站/飞书UI")
Rel(msg_broker, ai_agent, "调用服务", "CozeAPI")
Rel(msg_broker, user, "提供服务/发放token", "微信/网站/飞书UI")
Rel(ai_agent, plugins, "调用插件", "CozeAPI")
Rel(ai_agent, knowledge_db, "RAG（检索增强生成）", "CozeAPI")

' 志愿者流
Rel(volunteer, msg_broker, "人工审核", "微信/网站/飞书UI")
Rel(volunteer, knowledge_db, "评估校准/贡献入库", "admin")

' 数据ETL流
Rel(data_sources, etl_engine, "数据采集", "HTTPS/API")
Rel(etl_engine, structured_db, "清洗/载入数据", "Python API")
Rel(etl_engine, seaweedfs, "清洗/载入数据", "Python API")
Rel(structured_db, msg_broker, "元数据推送", "AMQP")
Rel(seaweedfs, msg_broker, "元数据推送", "AMQP")
Rel(msg_broker, knowledge_db, "筛选入库", "gRPC")
Rel(ai_agent, msg_broker, "AI审核", "CozeAPI")

' 系统管理流
Rel(apisix, msg_broker, "流量路由", "HTTPS")
Rel(celery, etl_engine, "任务调度", "Redis Protocol")
Rel(celery, msg_broker, "任务调度", "Redis Protocol")
Rel(otel, apisix, "监控采集", "OTLP")

' ==== 样式定义 ====
AddElementTag("core_db", $fontColor="#BF360C", $borderColor="#D84315", $bgColor="#FFCCBC")
AddElementTag("etl", $fontColor="#1B5E20", $borderColor="#43A047", $bgColor="#C8E6C9")
AddElementTag("mq", $fontColor="#004D40", $borderColor="#00796B", $bgColor="#B2DFDB")
AddElementTag("ai", $fontColor="#311B92", $borderColor="#673AB7", $bgColor="#D1C4E9")

note right of msg_broker
<color:#00796B>**消息处理流程**

1. 接收用户贡献

2. 质量评估过滤

3. 触发知识库更新

4. Token发放

end note

note left of knowledge_db
<color:#D84315>**版本策略**

1. 时间窗口快照

2. 增量更新索引

3. 志愿者人工回滚

end note

' ==== 技术栈说明模块 ====
left to right direction
package "通信协议" <<Rectangle>> {
  [RPC] as rpc #LightBlue
  [gRPC] as grpc #LightGreen
  [AMQP] as amqp #LightPink
}

package "应用场景" <<Rectangle>> {
  [服务间通信] as service_com
  [消息队列] as mq
  [跨语言调用] as cross_lang
}

rpc -[hidden]-> grpc
grpc -[hidden]-> amqp
service_com -[hidden]-> mq
mq -[hidden]-> cross_lang

rpc --> service_com : "远程过程调用基础模式"
grpc --> cross_lang : "Google开发的\n现代RPC框架"
amqp --> mq : "高级消息队列协议"

note top of rpc
<color:#1E88E5>RPC（Remote Procedure Call）
基础通信范式，允许像调用本地方法一样
调用远程服务，不限定具体协议
end note

note top of grpc
<color:#43A047>gRPC特性：

- 基于HTTP/2

- 使用Protocol Buffers

- 支持双向流

- 微服务场景性能提升40%+
end note

note top of amqp
<color:#D81B60>AMQP（Advanced Message Queuing Protocol）
企业级消息标准：

- 持久化

- 事务支持

- 发布/订阅模式

- 南开架构中用于Token发放等异步场景
end note
@enduml

```text

## 📅 演进路线

| 阶段            | 关键里程碑                          | 技术栈与架构决策                     | 交付产物                          |
|-----------------|-----------------------------------|--------------------------------------|----------------------------------|
| **MVP启动期**  
(0-3月) | ✅ 核心服务上线  
▪ 微信公众号智能问答MVP  
▪ 动态爬虫框架1.0  
▪ 重点平台数据接入（官网/公众号）  
▪ 知识库基础检索功能 | 🛠 FastAPI（API网关）  
🤖 Coze（智能Agent）  
🕷 Playwright（自动化爬虫） | 📦 容器化核心服务  
📚 部署指南+运维手册  
🔍 知识库检索API文档 |
| **生态构建期**  
(4-6月) | 🚀 核心系统扩展  
▪ 全平台爬虫覆盖  
▪ 数据质量看板1.0  
▪ 用户贡献系统原型  
▪ 反爬策略增强 | 🕸 Scrapy（分布式爬虫）  
📊 Prometheus+Granfana（监控）  
🔐 JWT+RBAC（权限控制） | 🧩 可插拔爬虫框架  
📈 质量评估系统  
🪙 Token激励原型系统 |
| **体系升级期**  
(7-9月) | 🌟 系统架构演进  
▪ 微服务化改造  
▪ 分布式积分系统  
▪ 全链路监控体系  
▪ 多模态知识引擎 | ☁ Spring Cloud Alibaba（微服务）  
📦 ELK（日志分析）  
🧠 Milvus（向量检索） | 🔄 积分系统微服务集群  
👁️ 系统健康看板  
🎨 多模态处理SDK |

**小团队演进策略**：

1. 🎯 功能优先级：采用「剃刀原则」聚焦核心场景，首期仅保留问答/检索/基础爬虫功能

2. 🧪 验证驱动：Token机制先实现简单积分发放，二期再引入兑换/消费闭环

3. 📶 渐进接入：平台接入按「官网→公众号→校园集市→社交平台」顺序分阶段实施

4. 🚧 架构演进：从单体→模块化→微服务渐进式改造，避免早期过度设计

## 💻 技术实现

### 项目结构树

```plaintext
nkuwiki/
├── core/               # 核心
│   ├── agent/         # Agent核心模块
│   │   ├── coze/          # Coze平台集成
│   │   │   ├── coze_agent.py     # Agent实现
│   │   │   ├── coze_integration.py # API集成
│   │   │   └── coze_session.py   # 会话管理
│   │   ├── agent.py          # Agent抽象基类
│   │   ├── session_manager.py # 全局会话管理
│   │   └── agent_factory.py  # Agent工厂
│   ├── bridge/          # 连接agent和服务的桥梁
│   │   ├── bridge.py  # 桥梁
│   │   │   ├── context.py # 上下文
│   │   │   ├── reply.py # 回复
│   │   │   └── ...
│   ├── auth/          # 认证服务
│   │   ├── duckdb_operator.py  # DuckDB操作
│   │   └── redis_manager.py    # Redis连接管理
│   └── utils/         # 公共工具库
│       ├── common/        # 通用工具
│       │   ├── expired_dict.py  # 带过期字典
│       │   ├── string_utils.py   # 字符串处理
│       │   ├── const.py         # 常量定义
│       │   └── dequeue.py       # 双端队列实现
│       ├── plugins/       # 插件系统
│       │   ├── plugin_manager.py # 插件管理器
│       │   └── ...
│       ├── translate/     # 翻译工具
│       │   ├── factory.py # 翻译工厂
│       │   └── ...
│       ├── voice/         # 语音工具
│       │   ├── factory.py # 语音工厂
│       │   └── ...
│       └── anti_crawler/  # 反爬工具
│           ├── factory.py # 反爬工厂
│           └── ...
├── etl/               # 数据采集处理管道
│   ├── crawler/       # 爬虫管理
│   │   ├── base_crawler.py  # 爬虫基类
│   │   ├── wechat.py        # 微信公众号爬虫
│   │   └── init_script.js   # 反检测脚本
│   └── pipeline/      # 数据处理管道
│       ├── data_export.py   # 数据导出
│       └── merge_json.py    # 数据合并
├── services/
│   ├── terminal/      # 终端服务
│   ├── website/       # 网站服务
│   ├── wechatmp/      # 微信公众号服务
│   │   ├── wechatmp_channel.py  # 主通道逻辑
│   │   ├── passive_reply.py    # 被动回复处理
│   │   ├── active_reply.py     # 主动回复处理
│   │   └── common.py          # 公共方法
│   ├── chat_channel.py     # 通用聊天通道
│   ├── chat_message.py     # 聊天消息处理
│   └── channel_factory.py   # 通道管理
└── infra/
    ├── deploy/        # 部署配置
    │   └── scripts/    # 部署脚本
    │       ├── start.sh     # 启动脚本
    │       ├── shutdown.sh # 关闭脚本
    │       └── restart.sh  # 重启脚本
    ├── app.py           # 主程序
    └── monitoring/    # 监控体系
        ├── loki/      # 日志管理
        └── pyroscope/ # 持续性能分析
├── config.py  # 全局配置管理

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

```text

### 技术选型表

| 模块 | 子模块 | 技术栈 | 版本 | 选型依据 |
| --- | --- | --- | --- | --- |
| **爬虫引擎** | 混合采集架构 | Playwright + Selenium | 1.42.0 / 4.18.0 | 双引擎覆盖现代SPA与传统网页场景，Playwright处理复杂DOM性能提升40% |
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

#### 爬虫架构实现方案

```plantuml
@startuml
package "采集策略路由" #LightBlue {
    component "动态检测" as dynamic_detection
    component "反爬分析" as anti_spider
}

package "采集引擎" #LightGreen {
    component "Playwright" as playwright <<集群>>
    component "Mitmproxy" as mitmproxy
}

component "Browserless" as browserless

dynamic_detection --> playwright : "现代Web应用"
dynamic_detection --> mitmproxy : "公众号流量捕获"

playwright --> browserless : "浏览器实例池"
@enduml

```text

方案说明

1. playwright 处理现代Web应用（B站/小红书）

2. mitmproxy 捕获公众号流量

3. browserless 实现IP轮换和浏览器指纹混淆

#### 知识库入库流程

```plantuml
@startuml
!include https://raw.githubusercontent.com/plantuml-stdlib/C4-PlantUML/master/C4_Container.puml

' ==== 知识库入库流程标题 ====
skinparam titleFontSize 18
title 知识库入库流程\n<size:16>数据质量保障体系</size>

skinparam defaultFontName "Microsoft YaHei"
skinparam defaultFontSize 14
skinparam linetype ortho
left to right direction

title 知识库入库流程

' ==== 系统组件 ====
Container(etl, "ETL引擎", "Playwright+Selenium", "多源数据采集")
Container(msg_broker, "消息中枢", "RabbitMQ", "任务分发")
Container(quality_check, "质量评估", "Pandera", "数据校验")
ContainerDb(knowledge_db, "知识库", "FAISS", "向量化存储")
Container(volunteer_ui, "志愿者界面", "Web Admin", "人工审核")

' ==== 数据流 ====
Rel(etl, msg_broker, "原始数据推送", "AMQP")
Rel(msg_broker, quality_check, "待处理数据", "AMQP")
Rel(quality_check, knowledge_db, "合格数据入库", "gRPC")
Rel(quality_check, volunteer_ui, "待审核数据", "HTTP")
Rel(volunteer_ui, knowledge_db, "人工校准数据", "Admin API")

note right of quality_check
<color:#00796B>**质量评估标准**

1. 信息完整性

2. 时效性验证

3. 来源可信度

4. 重复性检测

end note

note bottom of knowledge_db
<color:#D84315>**版本控制策略**

1. 每日增量更新

2. 每周全量快照

3. 志愿者可回滚任意版本

end note
@enduml

```text

#### 用户贡献管道

```plantuml
@startuml
!include https://raw.githubusercontent.com/plantuml-stdlib/C4-PlantUML/master/C4_Container.puml

skinparam defaultFontName "Microsoft YaHei"
skinparam defaultFontSize 14
skinparam wrapWidth 200
skinparam nodeFontSize 12
skinparam linetype ortho
left to right direction
' ==== 系统边界定义 ====
System_Boundary(user_layer, "用户端")  {
    Person(user, "用户", "提交学习资料", $sprite="person2", $tags="user")
    Container(wechat_mini, "微信小程序", "微信生态接入", $tags="client")
    Container(web_upload, "Web上传", "网页端服务", $tags="client")
}

System_Boundary(access_layer, "接入层") {
    Container(msg_queue, "消息队列", "RabbitMQ", "异步任务处理", $tags="mq")
    Container(auth_service, "鉴权服务", "JWT", "身份验证与授权", $tags="auth")
    Container(preprocessor, "预处理器", "Python", "数据标准化", $tags="processor")
}

System_Boundary(process_layer, "处理层") {
    ContainerDb(duckdb, "DuckDB", "结构化元数据", "嵌入式OLAP数据库", $tags="core_db")
    Container(format_conv, "格式转换", "Pandoc", "统一Markdown格式", $tags="processor")
    Container(quality_check, "质量检测", "Pandera", "数据质量校验", $tags="quality")
}

' ==== 样式定义 ====
AddElementTag("user_layer", $fontColor="#1E88E5", $borderColor="#64B5F6", $bgColor="#BBDEFB")
AddElementTag("access_layer", $fontColor="#43A047", $borderColor="#66BB6A", $bgColor="#C8E6C9")
AddElementTag("process_layer", $fontColor="#FB8C00", $borderColor="#FFA726", $bgColor="#FFE0B2")
AddElementTag("core_db", $fontColor="#BF360C", $borderColor="#D84315", $bgColor="#FFCCBC")

' ==== 数据流关系 ====
Rel(user, wechat_mini, "提交资料", "微信API")
Rel(wechat_mini, auth_service, "身份认证", "JWT")
Rel(auth_service, msg_queue, "投递任务", "AMQP")
Rel(msg_queue, preprocessor, "消费任务", "AMQP")
Rel(preprocessor, format_conv, "标准化处理", "HTTP")
Rel(format_conv, quality_check, "格式校验", "HTTP")
Rel(quality_check, duckdb, "存储元数据", "DuckDB API")
Rel(quality_check, seaweedfs, "存储文件", "SeaweedFS API")

note right of msg_queue
<color="#00796B>**消息处理规范**

1. 消息持久化

2. 自动重试机制

3. 优先级队列

end note

note left of duckdb
<color="#D84315>**元数据规范**

1. 文件哈希值

2. 贡献者信息

3. 时间戳

end note
@enduml

```text

#### agent交互

```plantuml
@startuml
!include https://raw.githubusercontent.com/plantuml-stdlib/C4-PlantUML/master/C4_Component.puml

' ==== Agent交互标题 ====
skinparam titleFontSize 18
title 智能Agent交互架构\n<size:16>多模态协同工作流</size>

skinparam defaultFontName "Microsoft YaHei"
skinparam defaultFontSize 14

title 智能Agent交互架构

Component(ai_agent, "智能Agent", "Coze", "多模态处理核心")
ComponentDb(knowledge_base, "知识库", "FAISS")
Component(plugin_mgr, "插件管理器", "Python")
Component(user_interface, "用户界面", "多平台终端")

' ==== 数据流 ====
Rel(user_interface, ai_agent, "用户请求", "HTTP/WebSocket")
Rel(ai_agent, knowledge_base, "RAG检索", "gRPC")
Rel(ai_agent, plugin_mgr, "插件调用", "Coze API")
Rel(plugin_mgr, user_interface, "插件响应", "HTTP")
Rel(ai_agent, user_interface, "生成响应", "SSE")

note right of ai_agent
<color:#673AB7>**处理流程**

1. 解析用户意图

2. RAG增强检索

3. 多模态处理

4. 插件协同工作

end note

note left of plugin_mgr
<color:#43A047>**插件类型**

- 搜索引擎

- 创意生图

- 数据分析

- 校历查询
end note
@enduml

```text

#### web服务

```plantuml
@startuml
!include https://raw.githubusercontent.com/plantuml-stdlib/C4-PlantUML/master/C4_Container.puml

' ==== Web服务标题 ====
skinparam titleFontSize 18
title Web服务架构\n<size:16>高可用分布式系统</size>

skinparam defaultFontName "Microsoft YaHei"
skinparam defaultFontSize 14
skinparam linetype ortho

title Web服务架构

Container(api_gateway, "API网关", "APISIX", "流量控制")
Container(web_service, "Web服务", "FastAPI", "业务逻辑")
Container(task_worker, "Celery Worker", "分布式任务")
ContainerDb(redis, "Redis", "任务队列")

' ==== 数据流 ====
Rel_U(api_gateway, web_service, "路由请求", "HTTP/2")
Rel(web_service, task_worker, "异步任务", "Redis")
Rel(task_worker, redis, "任务状态存储", "Redis协议")
Rel(web_service, redis, "会话缓存", "RESP")

note right of api_gateway
<color:#1E88E5>**网关功能**

1. 限流熔断

2. JWT验证

3. 请求路由

end note

note left of task_worker
<color:#D81B60>**任务类型**

- 文件处理

- 数据清洗

- 通知发送

- 定时任务
end note
@enduml

```text

### 部署规范

Docker Compose配置

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

```text

部署说明：

1. 使用`env_file`管理敏感配置（需创建.env文件）

2. 健康检查机制保障服务启动顺序

3. 独立存储卷实现数据持久化

4. OpenTelemetry Collector实现统一监控

## 📚 文档维护

| 版本 | 日期       | 修改人   | 变更描述               |
|------|------------|----------|-----------------------|
| 1.0  | 2025-02-03 | aokimi   | 初稿       |
| 1.1  | 2025-02-05 | aokimi   | 爬虫架构全面转向Playwright|

