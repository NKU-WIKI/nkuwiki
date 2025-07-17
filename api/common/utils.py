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
from fastapi import APIRouter, Request, Depends, HTTPException

# 本地导入
from api.models.common import StatusCode, Response


# 请求ID上下文变量
request_id_var: ContextVar[str] = ContextVar('request_id', default='')

# API异常类
class APIError(HTTPException):
    """API异常，可指定状态码和详细信息"""
    def __init__(self, status_code: int = StatusCode.BAD_REQUEST, detail: str = None, headers: Dict[str, str] = None):
        super().__init__(status_code=status_code, detail=detail, headers=headers)

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
            # 确保返回的是字符串而不是模型对象
            if isinstance(formatted_chunk, str):
                yield f"data: {json.dumps({'content': formatted_chunk})}\n\n"
            else:
                yield f"data: {json.dumps({'content': str(formatted_chunk)})}\n\n"
    except Exception as e:
        logger.error(f"Stream response error: {str(e)}")
        yield f"data: {json.dumps({'error': str(e)})}\n\n"