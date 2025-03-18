# nkuwiki 项目文档

此目录包含nkuwiki项目的详细文档。

## 文档索引

### 快速入门

- [安装指南](./installation_guide.md) - 环境准备、项目安装和依赖管理
- [配置指南](./configuration_guide.md) - 详细配置说明和通道配置
- [部署指南](./deployment_guide.md) - 部署MySQL和Qdrant服务，项目运行方法

### 服务文档

- [应用入口](./application_entry.md) - app.py应用入口文件详解
- [服务架构](./service_architecture.md) - 系统架构和主要组件说明
- [API服务使用指南](./api_usage_guide.md) - API服务的使用方法
- [问答服务使用指南](./qa_service_guide.md) - 问答服务的配置和使用方法

### 开发文档

- [日志指南](./logging_guide.md) - 日志配置和使用方法

### API文档

- [MySQL API](../etl/api/mysql_api.md) - MySQL数据库访问接口
- [Agent API](../core/api/agent_api.md) - 智能体交互接口
- [HiAgent API](./api/HiagentAPI.md) - HiAgent API文档
- [Coze API](./api/cozeAPI.md) - Coze API文档

### 资源

- [技术报告](./assets/技术报告.pdf) - 项目技术报告

## 项目架构图

请参考[服务架构](./service_architecture.md)文档了解nkuwiki项目的架构设计。

## 启动服务

nkuwiki提供两种服务模式：

1. **API服务**: `python app.py --api`
2. **问答服务**: `python app.py --qa`

可同时启动两种服务：`python app.py --api --qa`

详细参数和使用方法见[应用入口](./application_entry.md)文档。
