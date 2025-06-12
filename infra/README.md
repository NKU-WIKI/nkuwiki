# Infra 模块

## 模块概述

Infra模块是nkuwiki平台的基础设施模块，负责提供部署、监控和性能评测等基础功能。该模块为整个项目提供了底层支持服务。

## 子模块

### 1. deploy - 部署工具

提供项目部署相关的脚本和配置。

- **docker/** - Docker容器化部署配置
- **kubernetes/** - Kubernetes部署配置
- **scripts/** - 部署脚本

### 2. monitoring - 监控工具

提供系统监控和日志收集功能。

- **prometheus/** - Prometheus监控配置
- **grafana/** - Grafana仪表盘配置
- **alert/** - 告警配置

### 3. benchmark - 性能评测

提供系统性能评测工具。

- **stress_test.py** - 压力测试工具
- **latency_test.py** - 延迟测试工具
- **throughput_test.py** - 吞吐量测试工具

## 使用方法

### Docker部署

```bash
cd infra/deploy/docker
docker-compose up -d
```

### Kubernetes部署

```bash
cd infra/deploy/kubernetes
kubectl apply -f nkuwiki-deployment.yaml
```

### 运行性能测试

```bash
cd infra/benchmark
python stress_test.py --target http://localhost:8000 --users 100 --duration 60
```

## 监控系统

监控系统基于Prometheus和Grafana构建：

1. Prometheus负责收集和存储指标数据
2. Grafana负责可视化展示指标数据

可通过以下地址访问：

- Prometheus: `http://localhost:9090`
- Grafana: `http://localhost:3000`

## 日志系统

日志收集使用loguru库，并集成到ELK日志系统：

1. Elasticsearch存储日志数据
2. Logstash处理日志
3. Kibana展示和分析日志

可通过以下地址访问：

- Kibana: `http://localhost:5601`

## 基础设施

详细的基础设施部署文档。
