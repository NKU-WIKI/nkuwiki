# nkuwiki 开源·共治·普惠的南开百科

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)[![Version](https://img.shields.io/badge/version-0.3.0-blue.svg)](https://github.com/your-org/nkuwiki/releases)

## 🚀 立即体验

- 🔗 [Coze](https://www.coze.cn/store/agent/7473464038963036186?bot_id=true&bid=6ffcvvj3k6g0j)
- 🔗 [Hiagent](https://coze.nankai.edu.cn/product/llm/chat/cuh2gospkp8br093l2eg)
- 🤖 企微机器人参考[三步将nkuwiki bot添加到你的群](https://nankai.feishu.cn/wiki/UT4EwiPxmisBdOk3d1ycnGR2nve?from=from_copylink)
- 🔎 微信服务号：nkuwiki知识社区（无限制，用户体验更好）
- 🗝️ 微信订阅号 nkuwiki（有消极回复限制）

## 📇 目录

- [nkuwiki 开源·共治·普惠的南开百科](#nkuwiki-开源共治普惠的南开百科)
  - [🚀 立即体验](#-立即体验)
  - [📇 目录](#-目录)
  - [⚡ 快速开始](#-快速开始)
    - [环境准备](#环境准备)
    - [获取代码](#获取代码)
    - [安装依赖](#安装依赖)
      - [方式一：使用 venv 创建虚拟环境](#方式一使用-venv-创建虚拟环境)
      - [方式二：使用 conda 创建虚拟环境](#方式二使用-conda-创建虚拟环境)
      - [安装项目依赖](#安装项目依赖)
    - [配置项目](#配置项目)
    - [运行项目](#运行项目)
      - [部署mysql和qdrant服务（可跳过）](#部署mysql和qdrant服务可跳过)
        - [docker部署](#docker部署)
        - [源代码部署](#源代码部署)
      - [运行](#运行)
    - [开发指南](#开发指南)
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

## ⚡ 快速开始

### 环境准备

- python 3.10.12
- python3-venv(linux可能需要单独安装，windows/macos一般内置) or miniconda3
- git
- docker or docker-desktop (windows)(可选，用于容器化部署)
- mysql latest (可选，用于rag)
- qdrant latest (可选，用于rag)

### 获取代码

```bash
# 克隆仓库
git clone https://github.com/aokimi0/nkuwiki.git
cd nkuwiki
```

### 安装依赖

#### 方式一：使用 venv 创建虚拟环境

step1 安装python3-venv（windows/macos用户可跳过）

```bash
# linux系统（ubuntu/debian）可能需要单独安装venv
sudo apt update
sudo apt install python3-venv

# centos/rhel系统
sudo yum install python3-devel

# windows/macos系统通常已包含venv模块，无需额外安装
```

step2 创建虚拟环境

```bash
# 创建虚拟环境（默认在当前目录）
python3 -m venv nkuwiki --python=3.10.12

# 或者指定安装路径
# python3 -m venv path/to/yourvenv --python=3.10.12
# 例如 python3 -m venv /opt/venvs/nkuwiki --python=3.10.12 (linux)
# python3 -m venv d:\venvs\nkuwiki --python=3.10.12 (windows)
```

step3 激活虚拟环境

```bash
# 当前目录环境激活
# linux/macos
source nkuwiki/bin/activate
# windows
nkuwiki\scripts\activate

# 指定路径环境激活
# linux/macos
# source path/to/yourvenv/bin/activate
# 例如 source /opt/venvs/nkuwiki/bin/activate
# windows
# path\to\yourvenv\scripts\activate
# 例如 d:\venvs\nkuwiki\scripts\activate
```

#### 方式二：使用 conda 创建虚拟环境

step1 安装miniconda3

```bash
# 下载miniconda安装程序
# windows: https://repo.anaconda.com/miniconda/Miniconda3-latest-Windows-x86_64.exe
# linux: https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
# macos: https://repo.anaconda.com/miniconda/Miniconda3-latest-MacOSX-x86_64.sh

# linux/macos安装
# bash miniconda3-latest-linux-x86_64.sh
# 按照提示完成安装并初始化
# conda init

# windows安装
# 运行下载的exe文件，按照提示完成安装
```

step2 创建虚拟环境

```bash
# 创建名为nkuwiki的环境，指定python版本为3.10.12
conda create -n nkuwiki python=3.10.12

# 或者指定安装路径
# conda create -p path/to/conda/envs/nkuwiki python=3.10.12
# 例如 conda create -p /opt/conda/envs/nkuwiki python=3.10.12 (linux/macos)
# conda create -p d:\conda\envs\nkuwiki python=3.10.12 (windows)
```

step3 激活虚拟环境

```bash
# 使用环境名激活
conda init
conda activate nkuwiki

# 或者使用路径激活
# conda activate path/to/conda/envs/nkuwiki
# 例如 conda activate /opt/conda/envs/nkuwiki (linux/macos)
# conda activate d:\conda\envs\nkuwiki (windows)
```

#### 安装项目依赖

```bash
pip install -r requirements.txt
playwright install chromium # 使用playwright内置浏览器
```

### 配置项目

step1 创建配置文件：

```bash
# 复制配置模板
cp config-template.json config.json
```

step2 编辑`config.json`文件，填入必要的配置信息。以下是一个简单的示例，完整的可用配置和注释参见[config.py](./config.py)的`available_setting`。

```json
{
  "core": {
    "agent": {
      "coze": {
        "bot_id": "your_bot_id",
        "api_key": "your_api_key"
      }
    }
  },
  "services": {
    "channel_type": "terminal",
    "agent_type": "coze",
  },
  "etl": {
    "crawler": {
      "accounts": {
        "unofficial_accounts": "这是一个公众号",
        "university_official_accounts": "XX大学",
        "school_official_accounts": "XX学院",
        "club_official_accounts": "XX社团"
      },
      "market_token": "your_market_token"
    }，
    "retrieval": {
      "re_only": true,
    },
    "embedding": {
      "name": "BAAI/bge-large-zh-v1.5"
      "vector_size": 1024,
    },
    "reranker": {
      "name": "BAAI/bge-reranker-base"
    },
    "chunking": {
      "split_type": 0,
      "chunk_size": 512,
      "chunk_overlap": 200
    },
    "data": {
      "base_path": "./etl/data",
      "cache": {
        "path": "/cache"
      },
      "raw": {
        "path": "/raw"
      },
      "index": {
        "path": "/index"
      },
      "qdrant": {
        "path": "/qdrant",
        "url": "http://localhost:6333",
        "collection": "main_index",
        "vector_size": 1024
      },
      "mysql": {
        "path": "/mysql",
        "host": "127.0.0.1",
        "port": 3306,
        "user": "your_db_user",
        "password": "your_db_password",
        "name": "mysql"
      },
      "nltk": {
        "path": "/nltk"
      },
      "models": {
        "path": "/models",
        "hf_endpoint": "https://hf-api.gitee.com",
        "hf_home": "/models",
        "sentence_transformers_home": "/models"
      }
    }
  }
}

```

### 运行项目

#### 部署mysql和qdrant服务（可跳过）

如果需要使用`etl`模块中的**数据导出和rag检索**需要部署mysql和qdrant服务。在资源充沛的环境（本地）推荐使用docker容器部署，在资源受限的环境（服务器）推荐源代码部署。

##### docker部署

step1 安装docker/docker-desktop

```bash
# linux系统（ubuntu/debian）
sudo apt update
sudo apt install docker.io docker-compose
sudo systemctl enable docker
sudo systemctl start docker
# 添加当前用户到docker组（免sudo运行docker）
sudo usermod -aG docker $USER
# 重新登录以使权限生效

# centos/rhel系统
sudo yum install -y yum-utils
sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
sudo yum install docker-ce docker-ce-cli containerd.io docker-compose-plugin
sudo systemctl enable docker
sudo systemctl start docker
# 添加当前用户到docker组（免sudo运行docker）
sudo usermod -aG docker $USER
# 重新登录以使权限生效

# windows系统
# 下载Docker Desktop安装程序：https://www.docker.com/products/docker-desktop/
# 运行安装程序，按照提示完成安装
# 安装完成后启动Docker Desktop

# macos系统
# 下载Docker Desktop安装程序：https://www.docker.com/products/docker-desktop/
# 将下载的.dmg文件拖到Applications文件夹
# 启动Docker Desktop
```

step2 docker部署示例

```bash
# mysql
docker run -d --name mysql -p 3306:3306 -e MYSQL_ROOT_PASSWORD=your_password -v path\to\your\data\mysql:/var/lib/mysql mysql:latest # (windows需安装docker-desktop)
# 示例
# docker run -d --name mysql -p 3306:3306 -e MYSQL_ROOT_PASSWORD=123456 -v d:\code\nkuwiki\etl\data\mysql:/var/lib/mysql mysql:latest
# qdrant
docker run -d --name qdrant -p 6333:6333 -p 6334:6334 \
    -v path\to\your\data\qdrant:/qdrant/storage \
    qdrant/qdrant:latest 
# 示例
# docker run -d --name qdrant -p 6333:6333 -p 6334:6334 -v d:\code\nkuwiki\etl\data\qdrant:/qdrant/storage qdrant/qdrant:latest 
```

##### 源代码部署

step1 安装mysql

```bash
# linux系统（ubuntu/debian）
sudo apt update
sudo apt install mysql-server
sudo systemctl enable mysql
sudo systemctl start mysql
# 设置root密码
sudo mysql_secure_installation

# centos/rhel系统
sudo yum install mysql-server
sudo systemctl enable mysqld
sudo systemctl start mysqld
# 获取临时root密码
sudo grep 'temporary password' /var/log/mysqld.log
# 设置新密码
mysql -uroot -p
ALTER USER 'root'@'localhost' IDENTIFIED BY 'your_new_password';

# windows系统
# 下载mysql安装程序：https://dev.mysql.com/downloads/installer/
# 运行安装程序，按照提示完成安装
# 安装过程中会提示设置root密码

# macos系统
brew install mysql
brew services start mysql
# 设置root密码
mysql_secure_installation
```

step2 安装qdrant

```bash
# linux系统（ubuntu/debian/centos/rhel）
curl -L https://github.com/qdrant/qdrant/releases/latest/download/qdrant-x86_64-unknown-linux-gnu.tar.gz -o qdrant.tar.gz
tar -xvf qdrant.tar.gz
cd qdrant
# 启动qdrant服务
./qdrant

# windows系统
# 下载qdrant：https://github.com/qdrant/qdrant/releases
# 解压下载的文件
# 运行qdrant.exe

# macos系统
curl -L https://github.com/qdrant/qdrant/releases/latest/download/qdrant-x86_64-apple-darwin.tar.gz -o qdrant.tar.gz
tar -xvf qdrant.tar.gz
cd qdrant
# 启动qdrant服务
./qdrant
```

step3 配置服务

```bash
# mysql配置（根据需要修改）
# linux/macos
sudo mysql
CREATE USER 'your_user'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON *.* TO 'your_user'@'localhost';
FLUSH PRIVILEGES;

# qdrant配置（可选，默认配置通常足够）
# 配置文件位置：
# linux: /etc/qdrant/config.yaml
# windows: C:\Program Files\Qdrant\config.yaml
# macos: /usr/local/etc/qdrant/config.yaml
```

#### 运行

运行前确保激活虚拟环境和安装了依赖。

```bash
# 启动智能问答服务
cd nkuwiki & python3 app.py

# 启动爬虫任务 (示例)
# 确保已安装 playwright install chromium
cd nkuwiki & python3 ./etl/crawler/wechat.py
```

### 开发指南

1. **添加新爬虫**：
   - 在`etl/crawler`目录创建新的爬虫类，继承`BaseCrawler`
   - 添加`self.platform`,`self.base_url`，`self.content_type`等配置。
   - 实现`login_for_cookies`方法（如果需要登录）,`scrape`和`download`方法。

2. **添加新服务通道**：
   - 在`services`目录创建新的通道类
   - 在`services/channel_factory.py`中注册新通道

3. **调试**：
   - 建议使用`services/terminal`模块进行命令行调试，配置`channel_type = terminal`
   - 查看`logs/`目录下的日志文件排查问题

更详细的开发文档请参考[docs](./docs)目录。

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
- [@Frederick2313072](https://github.com/Frederick2313072)
- [@Because66666](https://github.com/Because66666)

现任志愿者团队

- [@aokimi0](https://github.com/aokimi0)
- [@hht421](https://github.com/hht421)
- [@hengdaoye50](https://github.com/hengdaoye50)
- [@Because66666](https://github.com/Because66666)

## 🏗 系统架构图

![系统架构图](./docs/assets/系统架构图.png)

## 📅 演进路线

| 阶段 | 关键里程碑 | 技术栈与架构决策 | 交付产物 |
| --- | --- | --- | --- |
| **MVP启动期** | ✅ 核心服务上线 | 🛠 FastAPI（API网关） | 📦 容器化核心服务 |
| (0-3月) | ▪ 微信公众号智能问答MVP | 🤖 Coze（智能Agent） | 📚 部署指南+运维手册 |
|  | ▪ 动态爬虫框架1.0 | 🕷 Playwright（自动化爬虫） | 🔍 知识库检索API文档 |
|  | ▪ 重点平台数据接入（官网/公众号） |  |  |
|  | ▪ 知识库基础检索功能 |  |  |
| **生态构建期** | 🚀 核心系统扩展 | 🕸 Scrapy（分布式爬虫） | 🧩 可插拔爬虫框架 |
| (4-6月) | ▪ 全平台爬虫覆盖 | 📊 Prometheus+Granfana（监控） | 📈 质量评估系统 |
|  | ▪ 数据质量看板1.0 | 🔐 JWT+RBAC（权限控制） | 🪙 Token激励原型系统 |
|  | ▪ 用户贡献系统原型 |  |  |
|  | ▪ 反爬策略增强 |  |  |
| **体系升级期** | 🌟 系统架构演进 | ☁ Spring Cloud Alibaba（微服务） | 🔄 积分系统微服务集群 |
| (7-9月) | ▪ 微服务化改造 | 📦 ELK（日志分析） | 👁️ 系统健康看板 |
|  | ▪ 分布式积分系统 | 🧠 Milvus（向量检索） | 🎨 多模态处理SDK |
|  | ▪ 全链路监控体系 |  |  |
|  | ▪ 多模态知识引擎 |  |  |

**小团队演进策略**：

1. 🎯 功能优先级：采用「剃刀原则」聚焦核心场景，首期仅保留问答/检索/基础爬虫功能
2. 🧪 验证驱动：Token机制先实现简单积分发放，二期再引入兑换/消费闭环
3. 📶 渐进接入：平台接入按「官网→公众号→校园集市→社交平台」顺序分阶段实施
4. 🚧 架构演进：从单体→模块化→微服务渐进式改造，避免早期过度设计

## 💻 技术实现

### 项目结构树

```plaintext
- core # core模块，负责智能体对话、贡献激励、平台治理等算法应用
  - agent  # 智能体应用
    - coze  # Coze平台对接
      - coze_agent.py
    （openai,chatgpt,hiagent、etc.）
    - session_manager.py  # 会话管理器
    - agent_factory.py  # 智能体工厂
  - auth  # 处理认证和授权
  - bridge  # 桥接服务与智能体
  - utils  # 通用工具函数和类
    - plugins  # 插件管理系统
      - plugin_manager.py  # 插件管理器
    - common  # 通用工具库
    - voice  # 语音处理
    - translate  # 翻译工具
- docs  # 项目文档
  - logging_guide.md  # 日志指南
  - assets  # 文档资源
    - 技术报告.pdf
  - HiagentAPI  # HiAgent API文档
    - HiagentAPI.md
- etl  # etl模块，负责数据抽取、转换和加载
  - __init__.py  # etl模块全局共享配置项、环境变量、路径和工具函数
  - api  # 检索和生成服务的api
  - crawler  # 爬虫模块，负责从各种数据源抓取数据
    - base_crawler.py  # 基础爬虫类
    (website,wechat, market, etc.)
    - __init__.py  # 爬虫模块专用配置项、环境变量、路径和工具函数
  - transform  # 转换模块，负责数据格式转换、处理和清洗
    - transformation.py  # 转换工具
  - load  # 加载模块，将原始数据导出到索引数据,关系数据库（mysql）和向量数据库（qdrant）
    - mysql_tables # mysql建表语句
    - json2mysql.py  # JSON数据导入MySQL
    - pipieline.py # 文档索引建立、嵌入、检索、重排全流程
  - embedding  # 嵌入处理模块
    - hierarchical.py # 文档处理成节点树，建立索引
    - ingestion.py  # 文档分块、嵌入
    - hf_embeddings.py # 嵌入模型
  - retrieval  # 检索模块
    - retrivers.py # 稀疏/稠密/混合检索器
    - rerankders.py # 重排器
  - utils  # 工具
  - data # 数据持久化存储目录，gitignore，一般放在项目代码外，仅本地测试时放在项目中，可在config.json中配置挂载路径
    - cache  # 缓存目录，存储临时处理的数据
    - index  # 索引目录，存储建立的搜索索引
    - models  # 模型目录，存储下载的机器学习模型
    - mysql  # MySQL数据库目录，存储关系型数据
    - qdrant  # Qdrant向量数据库目录，存储向量检索数据
    - nltk  # NLTK数据目录，存储自然语言处理工具包数据
    - raw  # 原始数据目录，存储爬取的原始数据
- infra  # 基础设施
  - __init__.py
- services  # services模块，提供多渠道服务
  - wechatmp  # 微信公众号服务
    - active_reply.py  # 主动回复
    - passive_reply.py  # 被动回复
    - wechatmp_channel.py  # 微信公众号渠道
  - terminal  # 终端服务，调试用
  - website  # 网站服务
  - channel_factory.py  # 渠道工厂
- requirements.txt  # 项目依赖文件
- app.py  # 应用程序入口
- config.py  # 全局配置管理类，包含所有可用配置项的注释和默认值
- config.json  # 配置文件，包含敏感信息，gitignore
- .cursors # cursor项目规则，推荐开发使用
```

### 技术选型表

| 模块 | 子模块 | 技术栈 | 版本 | 选型依据 |
| --- | --- | --- | --- | --- |
| **爬虫引擎** | 混合采集架构 | Playwright + Selenium | 1.42.0 / 4.18.0 | 双引擎覆盖现代SPA与传统网页场景，Playwright处理复杂DOM性能提升40% |
|  | 反爬解决方案 | Browserless + mitmproxy | 2.7.0 / 10.1.0 | 分布式浏览器指纹混淆 + 公众号API流量镜像捕获能力 |
| **数据清洗** | 数据清洗 | Pandera + DuckDB | 0.11.0 / 0.9.2 | 声明式数据验证框架 + 列式存储实时处理能力 |
| **消息队列** | 用户贡献处理 | RabbitMQ | 3.13.0 | 支持AMQP 1.0协议，消息持久化与死信队列保障数据完整性 |
| **存储层** | 对象存储 | SeaweedFS | 3.64 | 对象存储与文件系统统一接口，自动纠删码机制 |
|  | 元数据存储 | DuckDB | 0.9.2 | 支持Python原生OLAP查询，向量化执行引擎加速 |
| **任务调度** | 分布式任务 | Celery + Redis | 5.3.6 / 7.2.4 | 支持优先级队列与任务状态追踪，Redis Streams保障消息可靠性 |
| **监控体系** | 链路追踪 | OpenTelemetry | 1.24.0 | 统一观测数据标准，支持Metrics/Logs/Traces三支柱 |
| **核心组件** | API网关 | Apache APISIX | 3.8.0 | 动态插件架构支持JWT鉴权/限流/熔断等策略热更新 |
| **Agent模块** | API交互层 | FastAPI + HTTPX | 0.110.0 | 异步HTTP客户端支持SSE/WebSocket长连接 |
|  | 多模态处理 | Coze Multi-Modal API | 2024.2 | 支持文生图/图生文多模态联合推理 |
| **微信服务** | 消息路由 | FastAPI WebSocket | 0.110.0 | 支持万人级并发消息推送，消息压缩率60%+ |
|  | 任务调度 | Celery | 5.3.6 | 支持定时任务与工作流编排，任务失败自动重试 |
| **基础设施** | 容器编排 | Docker Compose | 2.24.5 | 支持服务依赖管理，开发-生产环境一致性保障 |
|  | 日志管理 | Loki + Promtail | 2.9.4 | 支持日志标签化索引，存储空间节省70% |

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
