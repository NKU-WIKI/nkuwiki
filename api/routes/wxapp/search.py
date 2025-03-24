"""
微信小程序搜索API
提供小程序搜索功能
"""
from typing import List, Dict, Any, Optional
from fastapi import Depends, Query
from loguru import logger

from api import wxapp_router
from api.common import handle_api_errors, get_api_logger_dep
from api.database.vector import retrieve_hybrid
from api.models.wxapp.search import WxappSearchResponse

@wxapp_router.get("/search", response_model=WxappSearchResponse)
@handle_api_errors("小程序搜索")
async def wxapp_search(
    keyword: str = Query(..., description="搜索关键词"),
    limit: int = Query(10, description="返回结果数量"),
    api_logger=Depends(get_api_logger_dep)
):
    """小程序搜索功能，用于搜索帖子、评论等内容"""
    api_logger.debug(f"处理小程序搜索请求: keyword={keyword}, limit={limit}")
    
    try:
        # 使用混合检索
        results = await retrieve_hybrid(
            query=keyword,
            limit=limit
        )
        
        # 格式化结果
        search_results = []
        for item in results:
            search_results.append({
                "id": item.get("id", ""),
                "title": item.get("title", "未知标题"),
                "content": item.get("content", ""),
                "score": item.get("score", 0.0),
                "source": item.get("source", "未知来源"),
                "metadata": item.get("metadata", {})
            })
        
        return WxappSearchResponse(
            results=search_results,
            total=len(search_results),
            keyword=keyword
        )
    
    except Exception as e:
        api_logger.error(f"搜索失败: {str(e)}")
        raise 