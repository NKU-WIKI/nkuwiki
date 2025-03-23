"""应用主入口模块，负责服务启动、配置加载和插件管理"""

import sys
import threading
import uvicorn
from pathlib import Path
from contextvars import ContextVar
from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from config import Config
from api import register_routers
from api.common import create_standard_response
from api.common.monitor import setup_api_monitor
from singleton_decorator import singleton
from core.utils.logger import register_logger, logger
from api.common.middleware import NotFoundMiddleware, APILoggingMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from starlette.exceptions import HTTPException as StarletteHTTPException
import atexit
import warnings
from fastapi.middleware.gzip import GZipMiddleware

# 过滤pydub的ffmpeg警告
warnings.filterwarnings("ignore", message="Couldn't find ffmpeg or avconv", category=RuntimeWarning)

# 创建配置对象
config = Config()

# 初始化日志系统
logger = register_logger("nkuwiki")
logger.info("日志系统初始化完成")

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

# 应用启动和关闭事件
@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动前执行
    logger.info("应用正在启动...")
    
    # 预热资源
    logger.info("正在预热应用资源...")
    try:
        # 可以在这里预加载模型、建立连接池等
        pass
    except Exception as e:
        logger.error(f"资源预热失败: {str(e)}")
        
    logger.info("应用启动完成，准备接收请求")
    yield
    # 关闭时执行
    logger.info("应用正在关闭...")
    
    # 清理资源
    try:
        cleanup_resources()
    except Exception as e:
        logger.error(f"资源清理失败: {str(e)}")
    
    logger.info("应用已安全关闭")

# 创建FastAPI应用
app = FastAPI(
    title="nkuwiki API",
    description="南开百科知识平台API服务",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",  # 自定义文档URL
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    default_response_class=JSONResponse,
    # 性能优化设置
    openapi_cache_max_age=3600,  # OpenAPI文档缓存1小时
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

# 添加GZip压缩中间件
app.add_middleware(GZipMiddleware, minimum_size=1000)  # 大于1KB的响应将被压缩

# 添加API日志中间件
app.add_middleware(APILoggingMiddleware)

# 添加404处理中间件（必须放在后面以先捕获404响应）
app.add_middleware(NotFoundMiddleware)

# 注册所有API路由
logger.info("开始注册API路由...")
register_routers(app)
logger.info("API路由注册完成")

# 注册API监控系统
setup_api_monitor(app)

# 挂载静态文件目录，用于微信校验文件等
app.mount("/static", StaticFiles(directory="static"), name="static_files")

# 添加全局异常处理器
@app.exception_handler(StarletteHTTPException)
async def global_http_exception_handler(request: Request, exc: StarletteHTTPException):
    """全局HTTP异常处理器，确保异常也返回标准格式"""
    # 特别处理404错误
    if exc.status_code == 404:
        logger.warning(
            f"404 未找到: {request.method} {request.url.path} | "
            f"客户端: {request.client.host if request.client else 'unknown'} | "
            f"UA: {request.headers.get('User-Agent', 'unknown')}"
        )
        
    return JSONResponse(
        status_code=exc.status_code,
        content=create_standard_response(
            data=None,
            code=exc.status_code,
            message=str(exc.detail)
        )
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局通用异常处理器，确保所有异常都返回标准格式"""
    logger.error(f"未捕获的异常: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content=create_standard_response(
            data=None,
            code=500,
            message=f"服务器内部错误: {str(exc)}"
        )
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

# 网站路由
website_dir = config.get("services.website.directory", str(Path("services/website").absolute()))
app.mount("/", StaticFiles(directory=website_dir, html=True), name="website")
app.mount("/img", StaticFiles(directory=str(Path(website_dir) / "img")), name="img_files")
app.mount("/assets", StaticFiles(directory=str(Path(website_dir) / "assets")), name="asset_files")

# 健康检查端点
@app.get("/health")
async def health_check(logger=Depends(get_logger)):
    """健康检查接口"""
    import datetime
    logger.debug("执行健康检查")
    
    health_info = {
        "status": "ok",
        "version": "1.0.0",
        "timestamp": datetime.datetime.now().isoformat(),
        "services": {}
    }
    
    # 检查数据库连接
    try:
        from etl.load import get_connection_stats
        db_stats = get_connection_stats()
        
        # 数据库状态判断
        pool_exists = db_stats["local"]["pool_exists"] if "local" in db_stats else False
        
        health_info["services"]["database"] = {
            "status": "ok" if pool_exists else "fail",
            "connection_pool": db_stats
        }
    except Exception as e:
        logger.error(f"数据库健康检查失败: {str(e)}")
        health_info["services"]["database"] = {
            "status": "fail",
            "error": str(e)
        }
    
    # 检查文件系统
    try:
        import os
        import shutil
        
        disk = shutil.disk_usage("/")
        health_info["services"]["disk"] = {
            "status": "ok",
            "total_gb": disk.total / (1024**3),
            "used_gb": disk.used / (1024**3),
            "free_gb": disk.free / (1024**3),
            "percent_used": disk.used / disk.total * 100
        }
    except Exception as e:
        logger.error(f"磁盘健康检查失败: {str(e)}")
        health_info["services"]["disk"] = {
            "status": "fail",
            "error": str(e)
        }
    
    return create_standard_response(health_info)

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

def cleanup_resources():
    """清理系统资源，确保优雅退出"""
    logger.debug("开始清理资源...")
    
    # 清理数据库连接池
    try:
        from etl.load import close_conn_pool
        close_conn_pool()
        logger.debug("数据库连接池已关闭")
    except Exception as e:
        logger.error(f"关闭数据库连接池失败: {str(e)}")
    
    # 清理临时文件
    try:
        import tempfile
        import shutil
        temp_dir = Path(tempfile.gettempdir()) / "nkuwiki"
        if temp_dir.exists():
            shutil.rmtree(temp_dir, ignore_errors=True)
            logger.debug(f"临时目录已清理: {temp_dir}")
    except Exception as e:
        logger.error(f"清理临时文件失败: {str(e)}")
    
    # 关闭日志处理器
    try:
        logger.debug("正在关闭日志处理器...")
        # 确保日志完全写入
        import sys
        sys.stdout.flush()
        sys.stderr.flush()
    except Exception as e:
        print(f"关闭日志处理器失败: {str(e)}")
    
    logger.info("资源清理完成")

def handle_signal(signum, frame):
    """信号处理回调函数"""
    logger.info(f"收到信号 {signum}，准备退出...")
    cleanup_resources()
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
def run_api_service(port):
    """启动API服务，通过Nginx反向代理实现HTTP/HTTPS访问"""
    # 设置信号处理
    setup_signal_handlers()
    
    # 固定参数配置
    host = "127.0.0.1"  # 只监听本地接口，由Nginx转发请求
    
    # 尝试启动服务
    try:
        # 导入uvicorn
        import uvicorn
        
        # 准备启动参数 - 单进程稳定模式
        common_params = {
            "reload": False,
            "workers": 1,            # 只使用1个worker
            "log_level": "info",
            "limit_concurrency": 500, # 降低并发限制
            "timeout_keep_alive": 30, # 降低保活时间
            "backlog": 1024,         # 降低队列长度
            "proxy_headers": True,
            "forwarded_allow_ips": "*"
        }
        
        # 启动HTTP服务
        logger.info(f"以单进程稳定模式启动 ({host}:{port})，worker数量: 1")
        uvicorn.run(
            "app:app", 
            host=host, 
            port=port,
            **common_params
        )
    except Exception as e:
        logger.error(f"服务启动失败: {str(e)}", exc_info=True)
    finally:
        # 清理资源
        cleanup_resources()

# 主函数
if __name__ == "__main__":
    import argparse
    import atexit
    import datetime
    
    # 注册退出时的清理函数
    atexit.register(cleanup_resources)
    
    # 创建命令行参数解析器
    parser = argparse.ArgumentParser(description="nkuwiki服务启动工具")
    parser.add_argument("--qa", action="store_true", help="启动问答服务")
    parser.add_argument("--api", action="store_true", help="启动API服务")
    parser.add_argument("--port", type=int, default=8000, help="API服务监听端口")
    
    args = parser.parse_args()
    
    # 修改默认行为：如果没有指定任何服务，默认启动API服务
    if not (args.qa or args.api):
        args.api = True
        # 记录日志，提醒用户未指定服务类型，默认启动API服务
        logger.warning("未指定服务类型，默认启动API服务。请明确使用--api或--qa参数。")
    
    # 启动指定的服务
    if args.qa:
        # 在单独线程中启动问答服务
        qa_thread = threading.Thread(target=run_qa_service)
        qa_thread.daemon = True
        qa_thread.start()
        logger.info("问答服务已在后台启动")
    
    if args.api:
        # 修改run_api_service函数参数，传入端口
        run_api_service(args.port)
    elif args.qa:
        # 如果只启动了问答服务，则等待问答服务线程结束
        qa_thread.join()
