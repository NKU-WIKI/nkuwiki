"""应用主入口模块，负责服务启动、配置加载和插件管理"""

import sys
import threading
import uvicorn
import uuid
import time
import argparse
import atexit
import warnings
from pathlib import Path
from contextvars import ContextVar
from contextlib import asynccontextmanager
from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.gzip import GZipMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.responses import JSONResponse

from api import router
from api.models.common import Response, Request
from core.utils.logger import register_logger
from config import Config

# 过滤pydub的ffmpeg警告
warnings.filterwarnings("ignore", message="Couldn't find ffmpeg or avconv", category=RuntimeWarning)

# =============================================================================
# 初始化配置和日志
# =============================================================================

# 创建配置对象
config = Config()
# 初始化日志系统
logger = register_logger("app")
# 创建应用上下文
request_id_var = ContextVar("request_id", default="")


# =============================================================================
# 应用生命周期管理
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动前执行
    logger.debug("应用正在启动...")
    # 预热资源
    logger.debug("正在预热应用资源...")
    try:
        # 可以在这里预加载模型、建立连接池等
        pass
    except Exception as e:
        logger.error(f"资源预热失败: {str(e)}")
    
    logger.debug("应用启动完成，准备接收请求")
    yield
    # 关闭时执行
    logger.debug("应用正在关闭...")
    # 清理资源
    try:
        cleanup_resources()
    except Exception as e:
        logger.error(f"资源清理失败: {str(e)}")
    
    logger.debug("应用已安全关闭")

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
        sys.stdout.flush()
        sys.stderr.flush()
    except Exception as e:
        print(f"关闭日志处理器失败: {str(e)}")
    
    logger.info("资源清理完成")

# =============================================================================
# 创建FastAPI应用
# =============================================================================

DEBUG = False
# 创建FastAPI应用
app = FastAPI(
    title="NKUWiki API",
    version=config.get("version", "1.0.0"),
    debug=DEBUG,
    openapi_url="/api/openapi.json" if DEBUG else None,  # 仅在调试模式开启OpenAPI
    docs_url="/api/docs" if DEBUG else None,             # 仅在调试模式开启Swagger
    redoc_url="/api/redoc" if DEBUG else None,           # 仅在调试模式开启ReDoc
    default_response_class=Response  
)

# 添加API路由器，所有路由统一添加/api前缀
api_router = APIRouter(prefix="/api")

# =============================================================================
# 中间件配置
# =============================================================================

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.get("cors.allow_origins", ["*"]),  # 允许的源列表
    allow_credentials=config.get("cors.allow_credentials", True),  # 允许携带凭证
    allow_methods=config.get("cors.allow_methods", ["*"]),  # 允许的HTTP方法
    allow_headers=config.get("cors.allow_headers", ["*"]),  # 允许的HTTP头
)

# 添加GZip压缩中间件
app.add_middleware(
    GZipMiddleware,
    minimum_size=1024  # 最小压缩大小（字节）
)

# 请求日志中间件
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """记录所有HTTP请求的中间件"""
    # 生成请求ID
    request_id = str(uuid.uuid4())[:8]  # 只使用UUID的前8位，更简洁
    request.state.request_id = request_id
    
    # 获取请求信息
    client_host = request.client.host if request.client else "unknown"
    start_time = time.time()
    
    # 检查是否需要记录此请求
    # 不记录静态资源、健康检查和其他不重要的请求
    path = request.url.path
    skip_logging = (
        path.startswith("/static/") or
        path.startswith("/assets/") or
        path.startswith("/img/") or
        path == "/api/health" or
        path.startswith("/favicon") or
        "__pycache__" in path
    )
    
    # 是否为API请求
    is_api_request = path.startswith("/api/") and not path == "/api/health"
    
    # 记录查询参数
    query_params = str(request.query_params) if request.query_params else ""
    
    if not skip_logging:
        if is_api_request:
            # 使用api_logger记录API请求
            from api import api_logger
            log_msg = f"API请求: {request.method} {path}"
            if query_params:
                log_msg += f" 参数: {query_params}"
            log_msg += f" [{request_id}] 来自 {client_host}"
            api_logger.info(log_msg)
            
            # 记录请求体内容 (仅POST/PUT请求)
            if request.method in ["POST", "PUT"] and "application/json" in request.headers.get("content-type", ""):
                try:
                    # 保存当前请求体位置
                    body_position = await request.body()
                    # 重置请求体位置，以便后续处理仍然可以读取
                    await request.body()
                    
                    if len(body_position) > 0:
                        # 只记录前500个字符，防止超长日志
                        body_str = body_position.decode('utf-8')
                        if len(body_str) > 500:
                            body_str = body_str[:500] + "... [截断]"
                        api_logger.debug(f"请求体: [{request_id}] {body_str}")
                except Exception as e:
                    api_logger.warning(f"无法记录请求体: [{request_id}] {str(e)}")
        else:
            # 使用普通logger记录其他请求
            logger.info(f"Request: {request.method} {path} [{request_id}]")
    
    try:
        # 调用下一个中间件或路由处理函数
        response = await call_next(request)
        
        # 计算处理时间
        process_time = (time.time() - start_time) * 1000
        
        # 记录请求结束 - 记录所有API请求和耗时信息
        if not skip_logging:
            if is_api_request:
                from api import api_logger
                status_code = response.status_code
                status_emoji = "✅" if 200 <= status_code < 300 else "❌"
                api_logger.info(
                    f"API响应: {request.method} {path} "
                    f"[{request_id}] {status_emoji} {status_code} 耗时: {process_time:.1f}ms"
                )
            else:
                logger.info(
                    f"Response: {request.method} {path} "
                    f"[{request_id}] {response.status_code} {process_time:.1f}ms"
                )
        
        # 添加处理时间到响应头
        response.headers["X-Process-Time"] = f"{process_time:.2f}ms"
        response.headers["X-Request-ID"] = request_id
        
        return response
    except Exception as e:
        # 计算处理时间
        process_time = (time.time() - start_time) * 1000
        
        # 记录请求异常 - 异常总是要记录
        if is_api_request:
            from api import api_logger
            api_logger.error(
                f"API错误: {request.method} {path} "
                f"[{request_id}] {str(e)} {process_time:.0f}ms"
            )
        else:
            logger.error(
                f"Error: {request.method} {path} "
                f"[{request_id}] {str(e)} {process_time:.0f}ms"
            )
        # 重新抛出异常，让全局异常处理器处理
        raise

# =============================================================================
# 异常处理
# =============================================================================

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局通用异常处理器，确保所有异常都返回标准格式"""
    logger.error(f"未捕获的异常: {str(exc)}", exc_info=True)
    
    return Response.internal_error(
        details={"message": f"服务器内部错误: {str(exc)}"}
    )

# =============================================================================
# 路由注册
# =============================================================================

# 添加健康检查端点
@api_router.get("/health")
async def health_check():
    """健康检查端点，返回服务状态"""
    return Response.success(
        data={
            "status": "ok",
            "server_time": time.time(),
            "version": config.get("version", "1.0.0")
        }
    )

# 注册所有API路由
logger.debug("开始注册API路由...")
api_router.include_router(router)
app.include_router(api_router) 
logger.debug("API路由注册完成")

# 挂载静态文件目录，用于微信校验文件等
app.mount("/static", StaticFiles(directory="static"), name="static_files")

# 挂载Mihomo控制面板静态文件
app.mount("/mihomo", StaticFiles(directory="/var/www/html/mihomo", html=True), name="mihomo_dashboard")

# 网站路由 - 确保具体路径挂载在根路径之前
website_dir = config.get("services.website.directory", str(Path("services/website").absolute()))
app.mount("/img", StaticFiles(directory=str(Path(website_dir) / "img")), name="img_files")
app.mount("/assets", StaticFiles(directory=str(Path(website_dir) / "assets")), name="asset_files")

# 挂载网站根目录 - 放在最后
app.mount("/", StaticFiles(directory=website_dir, html=True), name="website")

# =============================================================================
# 服务启动相关函数
# =============================================================================

def run_qa_service():
    """启动问答服务"""
    channel_type = config.get("services.channel_type", "terminal")
    logger.debug(f"Starting QA service with channel type: {channel_type}")
    
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

def run_api_service(port, workers=1):
    """启动API服务，通过Nginx反向代理实现HTTP/HTTPS访问"""
    host = "127.0.0.1"  # 只监听本地接口，由Nginx转发请求
    
    try:
        # 配置日志
        log_level = "info"  # 设置为info级别确保请求被记录
        
        # 设置环境变量，启用uvicorn的访问日志
        import os
        os.environ["UVICORN_ACCESS_LOG"] = "1"
        os.environ["UVICORN_LOG_LEVEL"] = "info"
        
        # 将workers转为整数确保类型一致
        if isinstance(workers, str):
            workers = int(workers)

        # 确保port是整数类型
        if isinstance(port, str):
            port = int(port)
        
        common_params = {
            "reload": False,
            "workers": workers,           
            "log_level": log_level,
            "access_log": True,  # 启用访问日志
            "limit_concurrency": 500, 
            "timeout_keep_alive": 30, 
            "backlog": 1024,        
            "proxy_headers": True,
            "forwarded_allow_ips": "*",
            "log_config": None  # 让uvicorn使用默认配置，不覆盖
        }
        
        # 添加详细日志
        logger.debug(f"启动参数 - host: {host}({type(host).__name__}), port: {port}({type(port).__name__}), workers: {workers}({type(workers).__name__})")
        
        # 启动HTTP服务
        logger.debug(f"以多进程模式启动 ({host}:{port})，worker数量: {workers}")
        uvicorn.run(
            "app:app", 
            host=host, 
            port=port,
            **common_params
        )
    except Exception as e:
        import traceback
        logger.error(f"服务启动失败: {str(e)}")
        logger.error(f"错误详情: {traceback.format_exc()}")
    finally:
        # 清理资源
        cleanup_resources()

# =============================================================================
# 主函数
# =============================================================================

if __name__ == "__main__":
    # 注册退出时的清理函数
    atexit.register(cleanup_resources)
    
    # 创建命令行参数解析器
    parser = argparse.ArgumentParser(description="nkuwiki服务启动工具")
    parser.add_argument("--qa", action="store_true", help="启动问答服务")
    parser.add_argument("--api", action="store_true", help="启动API服务")
    parser.add_argument("--port", type=int, default=8000, help="API服务监听端口")
    parser.add_argument("--workers", type=int, default=1, help="API服务worker进程数量，默认为1")
    
    args = parser.parse_args()
    
    # 修改默认行为：如果没有指定任何服务，默认启动API服务
    if not (args.qa or args.api):
        args.api = True
        logger.warning("未指定服务类型，默认启动API服务。请明确使用--api或--qa参数。")
    
    # 启动指定的服务
    if args.qa:
        # 在单独线程中启动问答服务
        qa_thread = threading.Thread(target=run_qa_service)
        qa_thread.daemon = True
        qa_thread.start()
        logger.info("问答服务已在后台启动")
    
    if args.api:
        # 启动API服务
        run_api_service(args.port, args.workers)
    elif args.qa:
        # 如果只启动了问答服务，则等待问答服务线程结束
        qa_thread.join()