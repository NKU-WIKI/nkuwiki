"""应用主入口模块，负责服务启动、配置加载和插件管理"""

import sys
import time
import threading
from pathlib import Path
from loguru import logger
from contextvars import ContextVar
from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from config import Config
from etl.api.mysql_api import mysql_router

# 创建配置对象
config = Config()
config.load_config()

# 创建日志目录
log_dir = Path('./infra/deploy/log')
log_dir.mkdir(exist_ok=True, parents=True)

# 配置日志
log_day_str = '{time:%Y-%m-%d}'
logger.configure(
    handlers=[
        {"sink": sys.stdout, "format": "{time:YYYY-MM-DD HH:mm:ss} | {level} | {module} | {message}"},
        {"sink": f"{log_dir}/app_{log_day_str}.log", "rotation": "1 day", "retention": "3 months", "level": "INFO"},
    ]
)

# 创建应用上下文
request_id_var: ContextVar[str] = ContextVar("request_id", default="")

# 创建FastAPI应用
app = FastAPI(
    title="NKUWIKI API",
    description="南开百科知识平台API服务",
    version="1.0.0",
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源的请求，生产环境应限制
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有HTTP方法
    allow_headers=["*"],  # 允许所有HTTP头
)

# 请求日志中间件
@app.middleware("http")
async def log_requests(request: Request, call_next):
    import uuid
    import time
    
    # 生成请求ID并存储在上下文变量中
    request_id = str(uuid.uuid4())
    request_id_var.set(request_id)
    
    # 记录请求开始
    start_time = time.time()
    method = request.method
    url = request.url.path
    
    logger.info(f"Request started: {method} {url} [ID: {request_id}]")
    
    # 处理请求
    response = await call_next(request)
    
    # 计算处理时间并记录
    process_time = time.time() - start_time
    logger.info(f"Request completed: {method} {url} [ID: {request_id}] - Status: {response.status_code} - Time: {process_time:.3f}s")
    
    return response

# 依赖注入函数
def get_logger():
    """提供日志记录器的依赖注入"""
    return logger.bind(request_id=request_id_var.get())

def get_config():
    """提供配置对象的依赖注入"""
    return config

# 根路由
@app.get("/")
async def root():
    """API根路径，返回API服务基本信息"""
    return {
        "name": "NKUWIKI API",
        "version": "1.0.0",
        "description": "南开百科知识平台API服务",
        "status": "running"
    }

# 健康检查端点
@app.get("/health")
async def health_check(logger=Depends(get_logger)):
    """健康检查"""
    from datetime import datetime
    from etl.load import get_conn
    
    # 检查数据库连接
    try:
        with get_conn() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1")
                db_status = "connected"
    except Exception as e:
        logger.error(f"数据库连接失败: {str(e)}")
        db_status = f"error: {str(e)}"
    
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "database": db_status
    }

# 集成MySQL路由
app.include_router(mysql_router)

# 信号处理函数
def setup_signal_handlers():
    """设置信号处理函数，用于优雅退出"""
    # 确保只在主线程注册信号处理器
    if threading.current_thread() is threading.main_thread():
        import signal
        signal.signal(signal.SIGINT, handle_signal)
        signal.signal(signal.SIGTERM, handle_signal)
        if hasattr(signal, 'SIGUSR1'):
            signal.signal(signal.SIGUSR1, handle_signal)

def handle_signal(signum, frame):
    """信号处理回调函数"""
    logger.info(f"Signal {signum} received, exiting...")
    sys.exit(0)

# 启动应用
def run_app():
    """启动API服务"""
    # 设置信号处理
    setup_signal_handlers()
    
    # 配置API网关
    api_host = config.get("api.host", "0.0.0.0")
    api_port = config.get("api.port", 80)
    
    # 输出启动信息
    logger.info(f"正在启动API服务，地址: http://{api_host}:{api_port}")
    
    # 启动服务
    uvicorn.run(
        app,
        host=api_host,
        port=api_port,
        log_level="info"
    )

# 单独运行FastAPI服务
if __name__ == "__main__":
    run_app()
