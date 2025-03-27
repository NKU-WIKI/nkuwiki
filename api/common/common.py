"""
API通用模块
提供API相关的通用功能，包括响应格式、装饰器、中间件等
"""
# 标准库导入
import re
import json
from contextvars import ContextVar
from typing import Any, Callable, Optional, Dict, List, Union
from datetime import datetime

# 第三方库导入
from fastapi import APIRouter, Request, Depends

# 本地导入
from core.utils.logger import register_logger

# 初始化API通用日志记录器
logger = register_logger("api")
api_logger = logger  # 添加变量供其他模块导入

# 请求ID上下文变量
request_id_var: ContextVar[str] = ContextVar('request_id', default='')

# API错误基类
class APIError(Exception):
    """API错误基类"""
    def __init__(self, message: str, code: int = 500, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(message)

# 格式化工具
def format_response_content(content: Any) -> Any:
    """格式化响应内容，处理特殊类型"""
    if isinstance(content, (dict, list)):
        return process_json_fields(content)
    elif isinstance(content, datetime):
        return content.isoformat()
    return content

def process_json_fields(data: Union[Dict, List]) -> Union[Dict, List]:
    """处理JSON字段，格式化特殊类型"""
    if isinstance(data, dict):
        return {k: process_json_fields(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [process_json_fields(item) for item in data]
    elif isinstance(data, datetime):
        return data.isoformat()
    return data

# API请求处理中间件
async def api_request_handler(request: Request):
    """API请求处理中间件，设置请求ID等通用处理"""
    # 获取或生成请求ID
    request_id = request.headers.get("X-Request-ID", f"req-{id(request)}")
    # 设置上下文变量
    request_id_var.set(request_id)
    return request_id

def get_schema_api_router(**kwargs):
    """获取增强的API路由器（支持标准响应格式）"""
    router = APIRouter(**kwargs)
    # 添加路由级别的中间件或依赖
    router.dependencies.append(Depends(api_request_handler))
    return router 

# 格式化函数
def format_response_content(content, format_type):
    """格式化响应内容"""
    if format_type == "markdown":
        # 已经是Markdown格式，不需要特殊处理
        return content
    elif format_type == "text":
        # 移除Markdown标记
        text = content
        # 移除标题标记
        text = re.sub(r'#+\s+', '', text)
        # 移除粗体和斜体
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
        text = re.sub(r'\*(.*?)\*', r'\1', text)
        # 移除链接，保留文本
        text = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', text)
        # 移除代码块
        text = re.sub(r'```.*?\n(.*?)```', r'\1', text, flags=re.DOTALL)
        # 移除行内代码
        text = re.sub(r'`(.*?)`', r'\1', text)
        return text
    elif format_type == "html":
        # 将Markdown转换为HTML（简化转换）
        html = content
        # 标题转换
        html = re.sub(r'### (.*?)(\n|$)', r'<h3>\1</h3>\2', html)
        html = re.sub(r'## (.*?)(\n|$)', r'<h2>\1</h2>\2', html)
        html = re.sub(r'# (.*?)(\n|$)', r'<h1>\1</h1>\2', html)
        # 粗体和斜体
        html = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', html)
        html = re.sub(r'\*(.*?)\*', r'<em>\1</em>', html)
        # 链接
        html = re.sub(r'\[(.*?)\]\((.*?)\)', r'<a href="\2">\1</a>', html)
        # 代码块
        html = re.sub(r'```(.*?)\n(.*?)```', r'<pre><code>\2</code></pre>', html, flags=re.DOTALL)
        # 行内代码
        html = re.sub(r'`(.*?)`', r'<code>\1</code>', html)
        # 段落
        html = re.sub(r'([^\n])\n([^\n])', r'\1<br>\2', html)
        return html
    
    return content

async def stream_response(generator, format_type="markdown"):
    """生成流式响应"""
    try:
        for chunk in generator:
            # 格式化每个块
            formatted_chunk = format_response_content(chunk, format_type)
            # 确保返回的是字符串而不是 JSONResponse 对象
            if isinstance(formatted_chunk, str):
                yield f"data: {json.dumps({'content': formatted_chunk})}\n\n"
            else:
                yield f"data: {json.dumps({'content': str(formatted_chunk)})}\n\n"
    except Exception as e:
        logger.error(f"Stream response error: {str(e)}")
        yield f"data: {json.dumps({'error': str(e)})}\n\n"