# nkuwiki 开源·共治·普惠的南开百科

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)[![Version](https://img.shields.io/badge/version-0.3.0-blue.svg)](https://github.com/your-org/nkuwiki/releases)

<img src="./docs/assets/wiki7.png" width="400" alt="nkuwiki logo" />

## 🚀 立即体验

- 🔗 [Coze](https://www.coze.cn/store/agent/7473464038963036186?bot_id=true&bid=6ffcvvj3k6g0j)
- 🔗 [Hiagent](https://coze.nankai.edu.cn/product/llm/chat/cuh2gospkp8br093l2eg)
- 🤖 企微机器人参考[三步将nkuwiki bot添加到你的群](https://nankai.feishu.cn/wiki/UT4EwiPxmisBdOk3d1ycnGR2nve?from=from_copylink)
- 🔎 微信服务号：nkuwiki知识社区（无限制，用户体验更好）
- 🗝️ 微信订阅号 nkuwiki（有消极回复限制）

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

## ⚡ 快速开始

1. **克隆项目**
```bash
git clone https://github.com/NKU-WIKI/nkuwiki.git
cd nkuwiki
```

2. **安装依赖**
```bash
pip install -r requirements.txt
```

3. **配置项目**
- 复制配置模板：`cp config-template/config-terminal.json config.json`
- 编辑 `config.json`，填入必要的配置项（API密钥等）

4. **启动服务**

以下为应用示例，更多功能详见[文档](./docs)

**终端问答模式（流式输出支持）**

```bash
python app.py
```

![终端模式效果](./docs/assets/terminal-qa.png)

**api模式**

```bash
python app.py --api --port 8000

# 检查服务状态
curl -X GET "http://localhost:8000/api/health"

# 一键部署服务集群（在linux服务器上）
nkuwiki_service_manager.sh deploy 8000 8 # 8000~8007端口8个实例，nginx负载均衡

```

## 🏗 系统架构

![系统架构图](./docs/assets/系统架构图.png)

项目采用模块化设计，主要包含以下模块：

- **core/**: 核心功能模块
  - agent/: 智能体对话实现
  - auth/: 认证授权
  - utils/: 通用工具

- **etl/**: 数据处理模块
  - crawler/: 数据采集
  - transform/: 数据转换
  - load/: 数据加载
  - embedding/: 向量化处理
  - retrieval/: 检索服务

- **api/**: API服务模块
  - models/: 数据模型
  - routers/: 路由处理
  - database/: 数据库操作

- **services/**: 多渠道服务
  - app/: 微信小程序
  - wechatmp/: 微信公众号
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

### 代码规范

- 代码风格遵循 PEP8
- 使用 black 进行代码格式化
- 遵循 vscode 的 markdownlint 规范

### 日志规范

- 默认使用 debug 级别
- 重要信息使用 info 级别
- 使用 `core/utils/logger.py` 中的 `register_logger` 注册日志

### 配置管理

- 配置项统一在 `config.py` 中定义
- 实际配置值在 `config.json` 中设置
- 支持嵌套配置引用

### 命名规范

- 默认小写
- 缩写用大写
- 类名首字母大写
- 驼峰命名用大写
- 下划线分割用小写

## 🤝 如何参与

⭐ **联系方式**：您可以直接添加微信 `ao_kimi` ，飞书联系 @廖望，或者联系开发团队与志愿者团队任意成员。

🌱 **使用即贡献，贡献即治理**：您可以通过使用我们的服务，联系我们反馈您的宝贵意见，向朋友安利我们的服务，上传您认为有价值的资料，在我们的项目提issue或PR，或者直接加入开发团队与志愿者团队等多种方式为社区发展作出贡献。我们欢迎任何形式，不计大小的贡献！

现任开发团队：
- [@aokimi0](https://github.com/aokimi0)
- [@LiaojunChen](https://github.com/LiaojunChen)
- [@hht421](https://github.com/hht421)
- [@Frederick2313072](https://github.com/Frederick2313072)
- [@Because66666](https://github.com/Because66666)

现任志愿者团队：
- [@aokimi0](https://github.com/aokimi0)
- [@hht421](https://github.com/hht421)
- [@hengdaoye50](https://github.com/hengdaoye50)
- [@Because66666](https://github.com/Because66666)

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 📞 联系我们

- 微信：ao_kimi
- 飞书：@廖望