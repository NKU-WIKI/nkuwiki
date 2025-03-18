# nkuwiki 服务架构

## 系统架构概述

nkuwiki平台采用模块化设计，主要包含两大服务：

1. **API服务**：基于FastAPI构建的HTTP API服务，提供数据访问和智能体交互功能
2. **问答服务**：基于多渠道设计的智能问答服务，支持终端、微信公众号等多种交互方式

## 主要组件

### 1. App单例类

nkuwiki使用单例模式管理全局应用实例，提供统一的配置和日志访问点：

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

### 2. FastAPI应用

API服务使用FastAPI框架构建，支持：

- 自动OpenAPI文档生成
- 依赖注入系统
- 中间件支持
- 路由整合

```python
app = FastAPI(
    title="nkuwiki API",
    description="南开百科知识平台API服务",
    version="1.0.0",
)
```

### 3. 日志系统

系统使用loguru库实现结构化日志记录：

- 按日轮转日志文件
- 保留7天日志历史
- 请求ID跟踪
- 上下文变量绑定

### 4. 依赖注入系统

通过FastAPI依赖注入机制提供：

- 日志注入：`get_logger()`
- 配置注入：`get_config()`

### 5. 路由集成

系统集成两个主要路由模块：

- MySQL API路由：`mysql_router`
- Agent API路由：`agent_router`

## 服务启动流程

### API服务启动

API服务通过`run_api_service`函数启动：

```python
def run_api_service(host="0.0.0.0", port=8000):
    """启动API服务"""
    # 设置信号处理
    setup_signal_handlers()
    
    logger.info(f"Starting API service on {host}:{port}")
    
    # 启动FastAPI服务
    uvicorn.run(app, host=host, port=port)
```

### 问答服务启动

问答服务通过`run_qa_service`函数启动：

```python
def run_qa_service():
    """启动问答服务"""
    # 设置信号处理
    setup_signal_handlers()
    
    # 获取渠道类型
    channel_type = config.get("services.channel_type", "terminal")
    
    # 使用渠道工厂创建渠道
    from services.channel_factory import create_channel
    channel = create_channel(channel_type)
    if channel:
        channel.startup()
```

### 命令行启动

通过命令行参数控制启动服务类型：

```bash
python app.py [--qa] [--api] [--host HOST] [--port PORT]
```

- `--qa`: 启动问答服务
- `--api`: 启动API服务
- `--host`: API服务主机地址（默认：0.0.0.0）
- `--port`: API服务端口（默认：8000）

如未指定任何服务，默认只启动问答服务。

## 安全与信号处理

系统实现信号处理器用于优雅退出：

```python
def setup_signal_handlers():
    """设置信号处理函数，用于优雅退出"""
    # 确保只在主线程注册信号处理器
    if threading.current_thread() is threading.main_thread():
        import signal
        signal.signal(signal.SIGINT, handle_signal)
        signal.signal(signal.SIGTERM, handle_signal)
        if hasattr(signal, 'SIGUSR1'):
            signal.signal(signal.SIGUSR1, handle_signal)
```

## 服务间通信

在同时启动问答服务和API服务时，使用线程实现并行运行：

```python
if args.qa:
    # 在单独线程中启动问答服务
    qa_thread = threading.Thread(target=run_qa_service)
    qa_thread.daemon = True
    qa_thread.start()
    
if args.api:
    # 主线程启动API服务
    run_api_service(host=args.host, port=args.port)
```

## 服务架构

详细的服务架构设计文档。
