# nkuwiki API使用指南

## 简介

nkuwiki API服务是南开百科知识平台的后端服务接口，提供知识检索、智能问答等功能。本指南介绍如何使用这些API。

## API服务基本信息

- **API基础URL**: `http://服务器IP:8000`
- **API版本**: 1.0.0
- **描述**: 南开百科知识平台API服务

## 启动API服务

API服务可通过以下命令启动：

```bash
python app.py --api --host 0.0.0.0 --port 8000
```

参数说明：

- `--api`: 启动API服务
- `--host`: 指定服务主机地址，默认为0.0.0.0
- `--port`: 指定服务端口，默认为8000

## 可用API端点

### 1. 根路径

- **URL**: `/`
- **方法**: GET
- **描述**: 返回API服务基本信息
- **响应示例**:

```json
{
    "name": "nkuwiki API",
    "version": "1.0.0",
    "description": "南开百科知识平台API服务",
    "status": "running"
}
```

### 2. 健康检查

- **URL**: `/health`
- **方法**: GET
- **描述**: 检查API服务运行状态
- **响应示例**:

```json
{
    "status": "ok",
    "timestamp": "2023-01-01T12:00:00.000000",
    "database": "connected"
}
```

### 3. MySQL API

访问MySQL数据库的相关API，详见[MySQL API文档](../etl/api/mysql_api.md)。

### 4. Agent API

访问智能体功能的相关API，详见[Agent API文档](../core/api/agent_api.md)。

## 跨域资源共享(CORS)

API服务配置了CORS中间件，允许来自所有源的请求访问API。在生产环境中，建议限制允许访问的源。

## 错误处理

API返回标准HTTP状态码：

- 200: 请求成功
- 400: 请求参数有误
- 401: 未授权
- 403: 禁止访问
- 404: 资源不存在
- 500: 服务器内部错误

错误响应将包含错误描述信息。

## 日志与监控

API服务使用loguru进行日志记录，日志文件位于`logs/app.log`，每天轮换一次，保留7天的日志记录。

## 问题排查

如遇到API服务问题，请：

1. 检查健康检查端点返回状态
2. 查看日志文件获取详细错误信息
3. 确认数据库连接状态

## 注意事项

1. 所有查询接口均会进行SQL注入防护
2. 自定义查询仅支持SELECT操作，不支持数据修改操作
3. 默认查询结果限制为100条记录，可通过limit参数调整
