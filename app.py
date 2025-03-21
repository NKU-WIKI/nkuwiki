"""应用主入口模块，负责服务启动、配置加载和插件管理"""

import sys
import time
import threading
from pathlib import Path
from loguru import logger
from contextvars import ContextVar
from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles  # 添加导入
import uvicorn

from config import Config
from etl.api.mysql_api import mysql_router
from core.api.agent_api import agent_router
from core.utils.common.singleton import singleton

# 创建配置对象
config = Config()

# 创建日志目录
log_dir = Path('./infra/deploy/log')
log_dir.mkdir(exist_ok=True, parents=True)

# 移除默认的控制台日志处理器
logger.remove()

# 添加文件日志处理器
logger.add("logs/app.log", 
    rotation="1 day",  # 每天轮换一次日志文件
    retention="7 days",  # 保留7天的日志
    level="DEBUG",
    encoding="utf-8"
)

# 定义全局App单例类
@singleton
class App:
    """
    应用程序单例，提供全局访问点
    """
    def __init__(self):
        self.config = config
        self.logger = logger
        
    def get_config(self):
        """获取配置对象"""
        return self.config
        
    def get_logger(self):
        """获取日志对象"""
        return self.logger

# 创建应用上下文
request_id_var: ContextVar[str] = ContextVar("request_id", default="")

# 创建FastAPI应用
app = FastAPI(
    title="nkuwiki API",
    description="南开百科知识平台API服务",
    version="1.0.0",
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源的请求，生产环境应限制
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],  # 明确指定允许的方法
    allow_headers=["*"],  # 允许所有HTTP头
    expose_headers=["*"]  # 暴露所有响应头
)

# 集成MySQL路由
app.include_router(mysql_router)
# 集成Agent路由
app.include_router(agent_router)

# 挂载静态文件目录，用于微信校验文件等
app.mount("/static", StaticFiles(directory="static"), name="static")

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
app.mount("/", StaticFiles(directory="/home/nkuwiki/nkuwiki-shell/nkuwiki/services/website", html=True), name="static")
# @app.get("/")
# async def root():
#     """API根路径，返回API服务基本信息"""
#     return {
#         "name": "nkuwiki API",
#         "version": "1.0.0",
#         "description": "南开百科知识平台API服务",
#         "status": "running"
#     }

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

# 启动问答服务
def run_qa_service():
    """启动问答服务"""
    # 设置信号处理
    setup_signal_handlers()
    
    # 获取渠道类型
    channel_type = config.get("services.channel_type", "terminal")
    logger.info(f"Starting QA service with channel type: {channel_type}")
    
    try:
        # 导入渠道工厂
        from services.channel_factory import create_channel
        
        # 使用渠道工厂创建渠道
        channel = create_channel(channel_type)
        if channel:
            channel.startup()
        else:
            logger.error(f"Failed to create channel: {channel_type}")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Error starting channel {channel_type}: {str(e)}")
        sys.exit(1)

# 启动API服务
def run_api_service(port=80):
    """启动API服务，同时支持HTTP和HTTPS"""
    # 设置信号处理
    setup_signal_handlers()
    
    host = "0.0.0.0"  # 固定监听所有网络接口
    
    # 获取SSL证书配置
    ssl_key_path = config.get("services.website.ssl_key_path", None)
    ssl_cert_path = config.get("services.website.ssl_cert_path", None)
    
    # 检查SSL证书配置
    has_ssl = ssl_key_path and ssl_cert_path and Path(ssl_key_path).exists() and Path(ssl_cert_path).exists()
    
    # 获取HTTP和HTTPS端口，默认HTTP为80，HTTPS为443
    if port is None:
        http_port = config.get("services.app.port", 80)
    else:
        http_port = port
    
    https_port = config.get("services.app.https_port", 443)
    
    logger.info(f"Starting API service on HTTP: {host}:{http_port}")
    
    # 启动HTTP服务
    http_thread = threading.Thread(
        target=lambda: uvicorn.run(app, host=host, port=http_port)
    )
    http_thread.daemon = True
    http_thread.start()
    
    # 如果有SSL证书配置，启动HTTPS服务
    if has_ssl:
        logger.info(f"Starting API service on HTTPS: {host}:{https_port}")
        # 使用SSL配置启动HTTPS服务
        uvicorn.run(
            app, 
            host=host, 
            port=https_port,
            ssl_keyfile=ssl_key_path,
            ssl_certfile=ssl_cert_path
        )
    else:
        logger.warning("未找到SSL证书配置，仅启动HTTP服务")
        # 等待HTTP线程结束（实际上不会结束，除非进程被终止）
        http_thread.join()

# 主函数
if __name__ == "__main__":
    import argparse
    
    # 创建命令行参数解析器
    parser = argparse.ArgumentParser(description="nkuwiki服务启动工具")
    parser.add_argument("--qa", action="store_true", help="启动问答服务")
    parser.add_argument("--api", action="store_true", help="启动API服务")
    parser.add_argument("--port", type=int, default=80, help="API服务端口")
    
    args = parser.parse_args()
    
    # 如果没有指定任何服务，默认只启动问答服务
    if not (args.qa or args.api):
        args.qa = True
    
    # 启动指定的服务
    if args.qa:
        # 在单独线程中启动问答服务
        qa_thread = threading.Thread(target=run_qa_service)
        qa_thread.daemon = True
        qa_thread.start()
        logger.info("问答服务已在后台启动")
    
    if args.api:
        # 主线程启动API服务（支持HTTP和HTTPS双模式）
        run_api_service(port=args.port)
    elif args.qa:
        # 如果只启动了问答服务，则等待问答服务线程结束
        qa_thread.join()
