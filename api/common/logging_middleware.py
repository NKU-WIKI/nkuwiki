import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response
import urllib.parse

# 添加项目根目录以便导入
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from etl.load.db_core import async_execute_custom_query
from core.utils.logger import register_logger

logger = register_logger('api.middleware')

class SearchLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # 我们只关心知识库的搜索请求
        if request.method == "GET" and "/api/knowledge/search" in request.url.path:
            # 解析查询参数
            query_params = dict(request.query_params)
            user_id = query_params.get("openid")
            query_text = query_params.get("query")

            # 如果关键参数存在，则记录
            if user_id and query_text:
                try:
                    # 解码可能存在的URL编码字符
                    decoded_query_text = urllib.parse.unquote_plus(query_text)
                    
                    # 使用正确的表名和字段名
                    sql = "INSERT INTO wxapp_search_history (openid, keyword) VALUES (%s, %s)"
                    await async_execute_custom_query(sql, (user_id, decoded_query_text), fetch=False)
                    logger.debug(f"Logged search query for user {user_id} into wxapp_search_history: '{decoded_query_text}'")
                except Exception as e:
                    logger.error(f"Failed to log search history: {e}")

        response = await call_next(request)
        return response 