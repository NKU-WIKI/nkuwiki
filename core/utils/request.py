"""
请求处理工具模块
提供客户端IP获取、请求信息记录等基础功能
"""
from typing import Any, Dict, Optional
from fastapi import Request

def get_client_ip(request: Request) -> str:
    """
    获取客户端真实IP地址，考虑各种代理情况
    
    Args:
        request: FastAPI请求对象
        
    Returns:
        str: 客户端IP地址
    """
    # 尝试从X-Forwarded-For获取，这通常是反向代理添加的
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # X-Forwarded-For格式可能是: client, proxy1, proxy2, ...
        # 第一个通常是真实客户端IP
        client_ip = forwarded_for.split(",")[0].strip()
        return client_ip
    
    # 尝试从X-Real-IP获取，这是Nginx常设的头
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    # 回退到直接连接的客户端地址
    return request.client.host if request.client else "unknown"

def extract_request_info(request: Request) -> Dict[str, Any]:
    """
    提取请求的基本信息
    
    Args:
        request: FastAPI请求对象
        
    Returns:
        Dict: 包含请求基本信息的字典
    """
    # 获取请求路径和方法
    path = request.url.path
    method = request.method
    
    # 获取客户端IP
    client_ip = get_client_ip(request)
    
    # 获取查询参数
    query_params = dict(request.query_params)
    
    # 提取关键headers
    headers = {
        "user-agent": request.headers.get("user-agent", ""),
        "referer": request.headers.get("referer", ""),
        "accept-language": request.headers.get("accept-language", "")
    }
    
    return {
        "path": path,
        "method": method,
        "client_ip": client_ip,
        "query_params": query_params,
        "headers": headers
    } 