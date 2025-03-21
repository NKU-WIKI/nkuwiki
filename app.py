"""应用主入口模块，负责服务启动、配置加载和插件管理"""

import sys
import threading
from pathlib import Path
from loguru import logger
from contextvars import ContextVar
from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn
from config import Config
from etl.api.mysql_api import mysql_router
from core.api.agent_api import agent_router
from core.utils.common.singleton import singleton
from fastapi.responses import RedirectResponse

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
app.mount("/static", StaticFiles(directory="static"), name="static_files")

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

# 根路由重定向
# 不需要重定向了，下面的app.mount('/')定义了静态网页地址
# @app.get("/")
# async def redirect_to_web():
#     return RedirectResponse(url="/nkuwiki_web")

# 网站路由
website_dir = config.get("services.website.directory", str(Path("services/website").absolute()))
app.mount("/", StaticFiles(directory=website_dir, html=True), name="website")

# 额外的静态文件挂载点
app.mount("/img", StaticFiles(directory=str(Path(website_dir) / "img")), name="img_files")
app.mount("/assets", StaticFiles(directory=str(Path(website_dir) / "assets")), name="asset_files")

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
def run_api_service():
    """启动API服务，同时支持HTTP和HTTPS双模式"""
    # 设置信号处理
    setup_signal_handlers()
    
    host = "0.0.0.0"  # 固定监听所有网络接口
    
    # 获取SSL证书配置
    ssl_key_path = config.get("services.website.ssl_key_path", None)
    ssl_cert_path = config.get("services.website.ssl_cert_path", None)
    
    # 检查SSL证书配置
    has_ssl = ssl_key_path and ssl_cert_path and Path(ssl_key_path).exists() and Path(ssl_cert_path).exists()
    
    # 增加调试信息
    if has_ssl:
        logger.debug(f"SSL证书路径: 私钥={ssl_key_path}, 证书={ssl_cert_path}")
        logger.debug(f"证书文件存在: 私钥={Path(ssl_key_path).exists()}, 证书={Path(ssl_cert_path).exists()}")
    else:
        logger.warning("SSL证书配置不完整或文件不存在，将尝试使用HTTP模式启动")
    
    # 端口配置
    http_port = config.get("services.website.http_port", 80)
    https_port = config.get("services.website.https_port", 443)  # 回归使用标准HTTPS端口
    
    # 确定生产/调试模式
    debug_mode = config.get("services.website.debug_mode", False)
    if debug_mode:
        # 调试模式 - 使用调试端口
        debug_port = config.get("services.website.debug_port", 8443)
        logger.info(f"检测到调试模式，使用调试端口: {debug_port}")
        https_port = debug_port
    else:
        # 生产模式 - 使用标准端口
        logger.info(f"以生产模式启动，使用标准端口: {https_port}")
    
    # 检查是否使用Cloudflare
    use_cloudflare = config.get("services.website.use_cloudflare", True)
    if use_cloudflare:
        logger.info("检测到Cloudflare模式，优化配置用于Cloudflare反向代理")
    
    # 检查端口是否被占用
    def is_port_in_use(port):
        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            result = s.connect_ex((host, port)) == 0
            logger.debug(f"端口 {port} 占用状态: {'已占用' if result else '未占用'}")
            return result
    
    # 计算worker数量
    def calculate_workers(manual_workers=None):
        """计算合适的worker数量，考虑CPU核心数和手动指定数量"""
        import os, multiprocessing
        
        # 如果手动指定了worker数量，优先使用
        if manual_workers is not None and manual_workers > 0:
            logger.info(f"使用手动指定的worker数量: {manual_workers}")
            return manual_workers
            
        # 否则基于CPU核心数计算
        try:
            cpu_count = multiprocessing.cpu_count()
            # 使用 (2 * CPU核心数 + 1) 的通用公式，但最大限制为8
            recommended = min(2 * cpu_count + 1, 8)
            logger.info(f"基于CPU核心数({cpu_count})计算的推荐worker数量: {recommended}")
            return recommended
        except:
            # 如果无法获取CPU核心数，使用安全默认值
            logger.warning("无法确定CPU核心数，使用默认worker数量: 4")
            return 4
    
    # 获取worker数量设置
    worker_arg = config.get("services.website.worker_count", None)
    
    # 尝试启动服务
    try:
        # 导入uvicorn
        import uvicorn
        
        # 确定最优启动方案 - 通过配置和环境决定
        use_http = False  # 默认不使用HTTP
        use_https = has_ssl  # 有SSL证书才启用HTTPS
        worker_count = calculate_workers(worker_arg)  # 根据CPU和配置计算worker
        
        # Cloudflare优先使用HTTP (灵活模式)
        if use_cloudflare:
            use_http = True
            logger.info("Cloudflare灵活模式: 使用HTTP连接提供服务")
            
            # 检查HTTP端口是否可用
            if is_port_in_use(http_port):
                logger.error(f"HTTP端口 {http_port} 已被占用，无法启动HTTP服务")
                use_http = False
        
        # 检查是否为特权端口（需要root权限）
        def is_privileged_port(port):
            return port < 1024
            
        # 准备启动参数
        common_params = {
            "reload": False,
            "workers": worker_count,
            "log_level": "debug" if debug_mode else "info",
            "limit_concurrency": 2000,  # 增加并发限制
            "timeout_keep_alive": 75,  # 增加保活时间
            "backlog": 4096,  # 增加队列长度
            "proxy_headers": True,
            "forwarded_allow_ips": "*"
        }
        
        # 为特权端口提供警告
        if (use_http and is_privileged_port(http_port)) or (use_https and is_privileged_port(https_port)):
            logger.warning(f"使用特权端口 (HTTP:{http_port} 或 HTTPS:{https_port})，如果不是root用户可能无法绑定")
            logger.warning("请确保应用有足够权限，或考虑使用 setcap 设置权限: sudo setcap 'cap_net_bind_service=+ep' /usr/bin/python3")
            
        # 确定使用哪种协议启动
        if use_http:
            logger.info(f"以HTTP模式启动 ({host}:{http_port})，worker数量: {worker_count}")
            uvicorn.run(
                "app:app", 
                host=host, 
                port=http_port,
                **common_params
            )
        elif use_https:
            logger.info(f"以HTTPS模式启动 ({host}:{https_port})，worker数量: {worker_count}")
            uvicorn.run(
                "app:app", 
                host=host, 
                port=https_port,
                ssl_keyfile=ssl_key_path,
                ssl_certfile=ssl_cert_path,
                **common_params
            )
        else:
            logger.error("无法启动服务：既没有可用的HTTP端口，也没有配置SSL证书")
    except Exception as e:
        logger.error(f"服务启动失败: {str(e)}", exc_info=True)
    finally:
        # 清理资源
        cleanup_resources()

# 主函数
if __name__ == "__main__":
    import argparse
    import atexit
    
    # 注册退出时的清理函数
    atexit.register(cleanup_resources)
    
    # 创建命令行参数解析器
    parser = argparse.ArgumentParser(description="nkuwiki服务启动工具")
    parser.add_argument("--qa", action="store_true", help="启动问答服务")
    parser.add_argument("--api", action="store_true", help="启动API服务")
    parser.add_argument("--http-only", action="store_true", help="仅启动HTTP服务，适用于Cloudflare灵活模式")
    parser.add_argument("--worker", type=int, help="指定worker数量，不指定则根据CPU核心数自动计算")
    
    args = parser.parse_args()
    
    # 把worker数量参数传入配置
    if args.worker is not None:
        config.set("services.website.worker_count", args.worker)
        logger.info(f"从命令行指定worker数量: {args.worker}")
    
    # 如果指定了HTTP-only模式
    if args.http_only:
        logger.info("使用HTTP-only模式启动，适用于Cloudflare灵活模式")
        try:
            # 检查端口
            http_port = config.get("services.website.http_port", 80)
            host = "0.0.0.0"
            
            # 计算worker数量
            import os, multiprocessing
            worker_arg = config.get("services.website.worker_count", None)
            
            if worker_arg is not None:
                worker_count = worker_arg
            else:
                try:
                    cpu_count = multiprocessing.cpu_count()
                    worker_count = min(2 * cpu_count + 1, 8)  # 使用标准公式，但最大限制为8
                except:
                    worker_count = 4  # 默认安全值
            
            logger.info(f"使用 {worker_count} 个worker启动HTTP服务")
            
            # 检查是否为特权端口
            if http_port < 1024:
                logger.warning(f"使用特权端口 {http_port}，如果不是root用户可能无法绑定")
                logger.warning("请确保应用有足够权限，或考虑使用 setcap 设置权限: sudo setcap 'cap_net_bind_service=+ep' /usr/bin/python3")
            
            import uvicorn
            uvicorn.run(
                "app:app", 
                host=host, 
                port=http_port,
                reload=False,
                workers=worker_count,
                log_level="info",
                limit_concurrency=2000,
                timeout_keep_alive=75,  # 增加保活时间
                backlog=4096,  # 增加队列长度
                proxy_headers=True,
                forwarded_allow_ips="*"
            )
            sys.exit(0)
        except Exception as e:
            logger.error(f"HTTP-only模式启动失败: {str(e)}", exc_info=True)
            sys.exit(1)
    
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
        # 主线程启动API服务
        run_api_service()
    elif args.qa:
        # 如果只启动了问答服务，则等待问答服务线程结束
        qa_thread.join()
