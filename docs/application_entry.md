# nkuwiki 应用入口

## 概述

`app.py` 是nkuwiki平台的主入口文件，负责服务启动、配置加载和插件管理。它提供了两种服务模式：

1. **API服务模式** - 提供HTTP API接口供外部系统访问
2. **问答服务模式** - 通过多种渠道提供智能问答功能

## 文件结构

`app.py` 文件包含以下主要部分：

1. 导入和配置初始化
2. App单例类定义
3. FastAPI应用创建与配置
4. 请求日志中间件
5. 依赖注入函数
6. API路由定义
7. 服务启动函数
8. 信号处理函数
9. 命令行参数解析与服务启动

## 关键组件

### App单例类

```python
@singleton
class App:
    """应用程序单例，提供全局访问点"""
    def __init__(self):
        self.config = config
        self.logger = logger
        
    def get_config(self):
        """获取配置对象"""
        return self.config
        
    def get_logger(self):
        """获取日志对象"""
        return self.logger
```

App单例类提供了全局配置和日志的统一访问点。

### 依赖注入函数

```python
def get_logger():
    """提供日志记录器的依赖注入"""
    return logger.bind(request_id=request_id_var.get())

def get_config():
    """提供配置对象的依赖注入"""
    return config
```

依赖注入函数用于在FastAPI路由处理器中获取配置和日志对象。

### 服务启动函数

```python
def run_api_service(host="0.0.0.0", port=8000):
    """启动API服务"""
    setup_signal_handlers()
    logger.info(f"Starting API service on {host}:{port}")
    uvicorn.run(app, host=host, port=port)

def run_qa_service():
    """启动问答服务"""
    setup_signal_handlers()
    channel_type = config.get("services.channel_type", "terminal")
    from services.channel_factory import create_channel
    channel = create_channel(channel_type)
    if channel:
        channel.startup()
```

这两个函数分别用于启动API服务和问答服务。

## 命令行参数

应用支持以下命令行参数：

```bash
python app.py [--qa] [--api] [--host HOST] [--port PORT]
```

- `--qa`: 启动问答服务
- `--api`: 启动API服务
- `--host`: API服务主机地址（默认：0.0.0.0）
- `--port`: API服务端口（默认：8000）

如果不指定任何参数，默认只启动问答服务。

### 启动API服务

```bash
python app.py --api --host 0.0.0.0 --port 8000
```

### 启动问答服务

```bash
python app.py --qa
```

### 同时启动两种服务

```bash
python app.py --qa --api
```

## 日志配置

日志配置使用loguru库，日志文件位于 `logs/app.log`，每天轮换一次，保留7天的日志历史。

```python
logger.add("logs/app.log", 
    rotation="1 day",  # 每天轮换一次日志文件
    retention="7 days",  # 保留7天的日志
    level="DEBUG",
    encoding="utf-8"
)
```

## 信号处理

应用实现了信号处理机制，可以优雅地响应中断信号：

```python
def setup_signal_handlers():
    """设置信号处理函数，用于优雅退出"""
    if threading.current_thread() is threading.main_thread():
        import signal
        signal.signal(signal.SIGINT, handle_signal)
        signal.signal(signal.SIGTERM, handle_signal)
        if hasattr(signal, 'SIGUSR1'):
            signal.signal(signal.SIGUSR1, handle_signal)
```

## 关键文件依赖

- `config.py`: 配置管理
- `etl/api/mysql_api.py`: MySQL API路由
- `core/api/agent_api.py`: Agent API路由
- `services/channel_factory.py`: 服务渠道工厂

## 扩展与维护

如需扩展应用功能，可以考虑：

1. 在 `app.py` 中添加新的API路由
2. 在 `services/channel_factory.py` 中添加新的服务渠道
3. 修改配置文件与依赖注入系统

维护应用时，请确保：

1. 保持单例模式的正确使用
2. 正确处理进程信号
3. 维护良好的日志记录

## 应用入口

详细的应用入口说明文档。
