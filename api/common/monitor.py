"""
API监控工具模块
提供API状态监控和健康检查功能
"""
import time
import datetime
import threading
import json
from typing import Dict, Any, Optional, List, Tuple
from collections import defaultdict
from fastapi import FastAPI, Request, Response, Depends
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import HTMLResponse
from loguru import logger

# 保存API状态信息
api_status = {
    "start_time": datetime.datetime.now().isoformat(),
    "total_requests": 0,
    "active_requests": 0,
    "endpoint_stats": defaultdict(lambda: {
        "count": 0,
        "errors": 0,
        "total_time": 0,
        "avg_time": 0,
        "min_time": float('inf'),
        "max_time": 0,
        "last_status": 200
    }),
    "status_counts": defaultdict(int),
    "recent_errors": []
}

# 状态锁，防止并发更新问题
status_lock = threading.Lock()

# 保留的最近错误数量
MAX_RECENT_ERRORS = 50

# 添加监控面板HTML模板
MONITOR_HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>nkuwiki API监控</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
            color: #333;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1, h2, h3 {
            color: #1a73e8;
        }
        h1 {
            margin-top: 0;
            padding-bottom: 10px;
            border-bottom: 1px solid #eee;
        }
        .card {
            background: white;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 20px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        .stats {
            display: flex;
            flex-wrap: wrap;
            gap: 20px;
            margin-bottom: 30px;
        }
        .stat-card {
            flex: 1;
            min-width: 200px;
            background: #f8f9fa;
            border-radius: 8px;
            padding: 15px;
            text-align: center;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        .stat-value {
            font-size: 32px;
            font-weight: bold;
            margin: 10px 0;
            color: #1a73e8;
        }
        .stat-label {
            font-size: 14px;
            color: #666;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
        }
        th, td {
            padding: 12px 15px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        th {
            background-color: #f8f9fa;
            font-weight: bold;
        }
        tr:hover {
            background-color: #f5f5f5;
        }
        .success { color: #28a745; }
        .warning { color: #ffc107; }
        .error { color: #dc3545; }
        .status-badge {
            padding: 5px 10px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: bold;
        }
        .status-200 {
            background-color: #d4edda;
            color: #155724;
        }
        .status-300 {
            background-color: #d1ecf1;
            color: #0c5460;
        }
        .status-400 {
            background-color: #fff3cd;
            color: #856404;
        }
        .status-500 {
            background-color: #f8d7da;
            color: #721c24;
        }
        .refresh-btn {
            background-color: #1a73e8;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
            margin-bottom: 20px;
        }
        .refresh-btn:hover {
            background-color: #0d62c9;
        }
        .reset-btn {
            background-color: #dc3545;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
            margin-left: 10px;
        }
        .reset-btn:hover {
            background-color: #c82333;
        }
        .time-info {
            font-size: 14px;
            color: #666;
            margin-bottom: 20px;
        }
        .error-list {
            max-height: 300px;
            overflow-y: auto;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>nkuwiki API监控面板</h1>
        
        <div class="buttons">
            <button class="refresh-btn" onclick="refreshData()">刷新数据</button>
            <button class="reset-btn" onclick="resetStats()">重置统计</button>
        </div>
        
        <div class="time-info">
            <p>服务启动时间: <span id="start-time">-</span></p>
            <p>运行时长: <span id="uptime">-</span></p>
            <p>最后更新: <span id="last-update">-</span></p>
        </div>
        
        <div class="stats">
            <div class="stat-card">
                <div class="stat-label">总请求数</div>
                <div class="stat-value" id="total-requests">-</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">当前活跃请求</div>
                <div class="stat-value" id="active-requests">-</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">成功请求 (2xx)</div>
                <div class="stat-value success" id="success-requests">-</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">错误请求 (4xx/5xx)</div>
                <div class="stat-value error" id="error-requests">-</div>
            </div>
        </div>
        
        <h2>端点统计</h2>
        <table id="endpoints-table">
            <thead>
                <tr>
                    <th>端点</th>
                    <th>调用次数</th>
                    <th>错误数</th>
                    <th>平均时间 (ms)</th>
                    <th>最大时间 (ms)</th>
                    <th>最小时间 (ms)</th>
                    <th>最后状态</th>
                </tr>
            </thead>
            <tbody id="endpoints-body">
                <tr>
                    <td colspan="7" style="text-align: center;">加载中...</td>
                </tr>
            </tbody>
        </table>
        
        <h2>最近错误</h2>
        <div class="error-list">
            <table id="errors-table">
                <thead>
                    <tr>
                        <th>时间</th>
                        <th>路径</th>
                        <th>方法</th>
                        <th>状态/错误</th>
                        <th>耗时 (ms)</th>
                    </tr>
                </thead>
                <tbody id="errors-body">
                    <tr>
                        <td colspan="5" style="text-align: center;">加载中...</td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>

    <script>
        // 格式化时间
        function formatDateTime(isoString) {
            const date = new Date(isoString);
            return date.toLocaleString();
        }
        
        // 格式化持续时间
        function formatUptime(seconds) {
            const days = Math.floor(seconds / 86400);
            const hours = Math.floor((seconds % 86400) / 3600);
            const minutes = Math.floor((seconds % 3600) / 60);
            const remainingSeconds = Math.floor(seconds % 60);
            
            let result = '';
            if (days > 0) result += `${days}天 `;
            if (hours > 0 || days > 0) result += `${hours}小时 `;
            if (minutes > 0 || hours > 0 || days > 0) result += `${minutes}分钟 `;
            result += `${remainingSeconds}秒`;
            
            return result;
        }
        
        // 加载数据
        async function loadData() {
            try {
                const response = await fetch('/api/stats');
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                const data = await response.json();
                
                // 更新基本信息
                document.getElementById('start-time').textContent = formatDateTime(data.start_time);
                document.getElementById('uptime').textContent = formatUptime(data.uptime_seconds);
                document.getElementById('last-update').textContent = new Date().toLocaleString();
                
                // 更新统计卡片
                document.getElementById('total-requests').textContent = data.total_requests;
                document.getElementById('active-requests').textContent = data.active_requests;
                
                // 计算成功和错误请求
                let successRequests = 0;
                let errorRequests = 0;
                
                for (const [status, count] of Object.entries(data.status_counts)) {
                    const statusCode = parseInt(status);
                    if (statusCode >= 200 && statusCode < 400) {
                        successRequests += count;
                    } else if (statusCode >= 400) {
                        errorRequests += count;
                    }
                }
                
                document.getElementById('success-requests').textContent = successRequests;
                document.getElementById('error-requests').textContent = errorRequests;
                
                // 更新端点表格
                const endpointsBody = document.getElementById('endpoints-body');
                endpointsBody.innerHTML = '';
                
                if (Object.keys(data.endpoint_stats).length === 0) {
                    const row = document.createElement('tr');
                    row.innerHTML = '<td colspan="7" style="text-align: center;">暂无数据</td>';
                    endpointsBody.appendChild(row);
                } else {
                    for (const [endpoint, stats] of Object.entries(data.endpoint_stats)) {
                        const row = document.createElement('tr');
                        const statusClass = `status-${Math.floor(stats.last_status / 100) * 100}`;
                        
                        row.innerHTML = `
                            <td>${endpoint}</td>
                            <td>${stats.count}</td>
                            <td>${stats.errors}</td>
                            <td>${(stats.avg_time * 1000).toFixed(2)}</td>
                            <td>${(stats.max_time * 1000).toFixed(2)}</td>
                            <td>${stats.min_time === Infinity ? '-' : (stats.min_time * 1000).toFixed(2)}</td>
                            <td><span class="status-badge ${statusClass}">${stats.last_status}</span></td>
                        `;
                        endpointsBody.appendChild(row);
                    }
                }
                
                // 更新错误表格
                const errorsBody = document.getElementById('errors-body');
                errorsBody.innerHTML = '';
                
                if (data.recent_errors.length === 0) {
                    const row = document.createElement('tr');
                    row.innerHTML = '<td colspan="5" style="text-align: center;">暂无错误</td>';
                    errorsBody.appendChild(row);
                } else {
                    for (const error of data.recent_errors) {
                        const row = document.createElement('tr');
                        const statusOrError = error.status || error.error;
                        const statusClass = error.status ? `status-${Math.floor(error.status / 100) * 100}` : 'error';
                        
                        row.innerHTML = `
                            <td>${formatDateTime(error.time)}</td>
                            <td>${error.path}</td>
                            <td>${error.method}</td>
                            <td><span class="status-badge ${statusClass}">${statusOrError}</span></td>
                            <td>${(error.duration * 1000).toFixed(2)}</td>
                        `;
                        errorsBody.appendChild(row);
                    }
                }
                
            } catch (error) {
                console.error('获取数据失败:', error);
                alert('获取监控数据失败，请检查控制台错误信息');
            }
        }
        
        // 刷新数据
        function refreshData() {
            loadData();
        }
        
        // 重置统计
        async function resetStats() {
            if (!confirm('确定要重置所有统计数据吗？')) {
                return;
            }
            
            try {
                const response = await fetch('/api/stats/reset', {
                    method: 'POST'
                });
                
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                
                alert('统计数据已重置');
                loadData();
            } catch (error) {
                console.error('重置数据失败:', error);
                alert('重置统计数据失败，请检查控制台错误信息');
            }
        }
        
        // 页面加载时获取数据
        document.addEventListener('DOMContentLoaded', loadData);
        
        // 每30秒自动刷新一次
        setInterval(loadData, 30000);
    </script>
</body>
</html>
"""

class APIMonitorMiddleware(BaseHTTPMiddleware):
    """API监控中间件，收集请求统计信息"""
    
    async def dispatch(self, request: Request, call_next):
        # 跳过静态文件和健康检查请求
        if request.url.path.startswith("/static") or request.url.path == "/health":
            return await call_next(request)
            
        # 记录请求开始时间
        start_time = time.time()
        
        # 获取路由标识
        path = request.url.path
        method = request.method
        route_id = f"{method} {path}"
        
        # 增加活跃请求计数
        with status_lock:
            api_status["total_requests"] += 1
            api_status["active_requests"] += 1
        
        # 处理请求
        try:
            response = await call_next(request)
            
            # 计算处理时间
            process_time = time.time() - start_time
            
            # 更新统计信息
            with status_lock:
                # 减少活跃请求计数
                api_status["active_requests"] -= 1
                
                # 更新状态码统计
                api_status["status_counts"][str(response.status_code)] += 1
                
                # 更新端点统计
                endpoint_stats = api_status["endpoint_stats"][route_id]
                endpoint_stats["count"] += 1
                endpoint_stats["total_time"] += process_time
                endpoint_stats["avg_time"] = endpoint_stats["total_time"] / endpoint_stats["count"]
                endpoint_stats["min_time"] = min(endpoint_stats["min_time"], process_time)
                endpoint_stats["max_time"] = max(endpoint_stats["max_time"], process_time)
                endpoint_stats["last_status"] = response.status_code
                
                # 记录错误
                if response.status_code >= 400:
                    endpoint_stats["errors"] += 1
                    # 添加到最近错误列表
                    if len(api_status["recent_errors"]) >= MAX_RECENT_ERRORS:
                        api_status["recent_errors"].pop(0)  # 移除最旧的错误
                    
                    error_info = {
                        "time": datetime.datetime.now().isoformat(),
                        "path": path,
                        "method": method,
                        "status": response.status_code,
                        "duration": process_time
                    }
                    api_status["recent_errors"].append(error_info)
            
            return response
        except Exception as e:
            # 处理异常
            process_time = time.time() - start_time
            
            with status_lock:
                # 减少活跃请求计数
                api_status["active_requests"] -= 1
                
                # 更新端点统计
                endpoint_stats = api_status["endpoint_stats"][route_id]
                endpoint_stats["count"] += 1
                endpoint_stats["errors"] += 1
                endpoint_stats["total_time"] += process_time
                
                # 记录错误
                if len(api_status["recent_errors"]) >= MAX_RECENT_ERRORS:
                    api_status["recent_errors"].pop(0)
                
                error_info = {
                    "time": datetime.datetime.now().isoformat(),
                    "path": path,
                    "method": method,
                    "error": str(e),
                    "duration": process_time
                }
                api_status["recent_errors"].append(error_info)
            
            # 记录错误日志
            logger.error(f"API错误: {method} {path} - {str(e)}")
            # 重新抛出异常以便其他错误处理器处理
            raise

def reset_stats():
    """重置API统计信息"""
    global api_status
    with status_lock:
        start_time = api_status["start_time"]
        api_status = {
            "start_time": start_time,
            "total_requests": 0,
            "active_requests": 0,
            "endpoint_stats": defaultdict(lambda: {
                "count": 0,
                "errors": 0,
                "total_time": 0,
                "avg_time": 0,
                "min_time": float('inf'),
                "max_time": 0,
                "last_status": 200
            }),
            "status_counts": defaultdict(int),
            "recent_errors": []
        }

def get_api_stats() -> Dict[str, Any]:
    """获取API统计信息的副本"""
    with status_lock:
        # 创建副本以避免并发修改问题
        stats_copy = {
            "start_time": api_status["start_time"],
            "total_requests": api_status["total_requests"],
            "active_requests": api_status["active_requests"],
            "endpoint_stats": {k: dict(v) for k, v in api_status["endpoint_stats"].items()},
            "status_counts": dict(api_status["status_counts"]),
            "recent_errors": list(api_status["recent_errors"]),
            "uptime_seconds": (datetime.datetime.now() - datetime.datetime.fromisoformat(api_status["start_time"])).total_seconds()
        }
    return stats_copy

def setup_api_monitor(app: FastAPI):
    """为FastAPI应用设置API监控"""
    # 添加中间件
    app.add_middleware(APIMonitorMiddleware)
    
    # 添加健康检查端点
    @app.get("/health", tags=["监控"])
    async def health_check():
        """API健康检查端点"""
        return {
            "status": "ok",
            "time": datetime.datetime.now().isoformat(),
            "api_version": getattr(app, "version", "1.0.0")
        }
    
    # 添加统计信息端点
    @app.get("/api/stats", tags=["监控"])
    async def get_stats():
        """获取API统计信息"""
        return get_api_stats()
    
    # 添加重置统计信息端点
    @app.post("/api/stats/reset", tags=["监控"])
    async def reset_api_stats():
        """重置API统计信息"""
        reset_stats()
        return {"status": "ok", "message": "统计信息已重置"}
    
    # 添加监控面板页面
    @app.get("/api/monitor", response_class=HTMLResponse, tags=["监控"])
    async def monitor_dashboard():
        """API监控面板"""
        return MONITOR_HTML_TEMPLATE
    
    # 使用带有默认request_id的logger
    logger.bind(request_id="system", module="monitor").info("API监控系统已启动") 