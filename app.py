"""应用主入口模块，负责服务启动、配置加载和插件管理"""

import sys
import threading
import uvicorn
import uuid
import time
import argparse
import atexit
import warnings
import os
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
from api.common.logging_middleware import SearchLoggingMiddleware
from api.models.common import Response, Request
from core.utils.logger import register_logger, logger
from config import Config
from etl.load.db_pool_manager import init_db_pool, close_db_pool

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
    logger.debug("应用启动中...")
    
    # 初始化数据库连接池
    await init_db_pool()
    
    yield
    
    # 应用关闭时执行清理
    logger.debug("应用关闭中，开始清理资源...")
    
    try:
        from etl.load import close_db_pool
        await close_db_pool()
        logger.debug("数据库连接池已关闭")
    except Exception as e:
        logger.error(f"关闭数据库连接池失败: {str(e)}")
    
    logger.debug("应用已安全关闭")

# =============================================================================
# 创建FastAPI应用
# =============================================================================

DEBUG = False
# 创建FastAPI应用
print("正在创建FastAPI应用...")
app = FastAPI(
    title="NKU-Wiki API", description="南开大学知识维基项目", version=config.get("version", "1.0.0"),
    debug=DEBUG,
    openapi_url="/api/openapi.json" if DEBUG else None,  # 仅在调试模式开启OpenAPI
    docs_url="/api/docs" if DEBUG else None,             # 仅在调试模式开启Swagger
    redoc_url="/api/redoc" if DEBUG else None,           # 仅在调试模式开启ReDoc
    default_response_class=Response,
    lifespan=lifespan  # 注册生命周期事件
)
print("✅ FastAPI应用创建成功")

# 添加API路由器
app.include_router(router)

# 挂载静态文件目录，用于访问上传的图片
# 从配置中读取上传目录路径
upload_dir = config.get("etl.data.uploads.path", "/app/data/uploads")
app.mount("/static", StaticFiles(directory=upload_dir), name="static")


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

# 添加搜索历史记录中间件
app.add_middleware(SearchLoggingMiddleware)

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
@app.get("/health")
async def health_check():
    """健康检查端点，返回服务状态"""
    return Response.success(
        data={
            "status": "ok",
            "server_time": time.time(),
            "version": config.get("version", "1.0.0")
        }
    )

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
    """启动API服务"""
    logger.info("准备启动 NKUWiki API 服务...")
    
    # 打印服务访问地址
    protocol = "https" if config.get('server.https', False) else "http"
    host = "127.0.0.1"
    
    logger.info(f"服务将运行在: {protocol}://{host}:{port}")
    if DEBUG:
        logger.info(f"Swagger UI: {protocol}://{host}:{port}/api/docs")
        logger.info(f"ReDoc: {protocol}://{host}:{port}/api/redoc")
    
    # 检测是否在Docker容器中运行（通过检查是否存在.dockerenv文件）
    is_docker = Path("/.dockerenv").exists()
    if is_docker:
        logger.info("检测到Docker环境，禁用自动重载功能")
        
    # 启动Uvicorn服务器
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=port,
        workers=workers,
        log_level="info",
        reload=not is_docker  # 在Docker环境中禁用reload
    )

# =============================================================================
# 主函数
# =============================================================================

if __name__ == "__main__":
    """主函数入口，根据命令行参数启动不同服务"""
    parser = argparse.ArgumentParser(description="NKUWiki应用启动器")
    parser.add_argument("--api", action="store_true", help="启动FastAPI Web服务")
    parser.add_argument("--qa", action="store_true", help="启动终端问答服务")
    parser.add_argument("--port", type=int, default=8000, help="API服务端口号")
    parser.add_argument("--workers", type=int, default=1, help="API服务工作进程数")
    args = parser.parse_args()

    try:
        if args.api:
            # 调用封装好的服务启动函数
            run_api_service(port=args.port, workers=args.workers)
        elif args.qa:
            # 在一个独立的线程中运行问答服务，避免阻塞主线程
            qa_thread = threading.Thread(target=run_qa_service, daemon=True)
            qa_thread.start()
            # 保持主线程运行以接收信号
            while qa_thread.is_alive():
                time.sleep(1)
        else:
            # 默认启动问答服务
            logger.info("未指定服务类型，默认启动终端问答服务...")
            run_qa_service()
            
    except KeyboardInterrupt:
        logger.info("收到退出信号，正在关闭服务...")
    except Exception as e:
        logger.error(f"应用启动失败: {str(e)}", exc_info=True)
    finally:
        logger.info("服务已停止")