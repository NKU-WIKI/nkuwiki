"""
智能体搜索API
提供知识库搜索功能
"""
from typing import List, Dict, Any
from fastapi import Depends, HTTPException
from loguru import logger
import asyncio
from datetime import datetime

from api import agent_router
from api.common import get_api_logger_dep, handle_api_errors
from api.models.search import AgentSearchRequest
from api.models.agent.rag import KnowledgeSearchResponse
from etl.load.py_mysql import query_records

@agent_router.post("/search", response_model=KnowledgeSearchResponse)
@handle_api_errors("知识搜索")
async def search_knowledge(
    request: AgentSearchRequest,
    api_logger=Depends(get_api_logger_dep)
):
    """搜索知识库"""
    try:
        api_logger.debug(f"处理搜索请求：keyword={request.keyword}, limit={request.limit}")
        
        # 使用同步方式查询，将其放入线程池中执行
        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(
            None, 
            lambda: query_records(
                table_name="wxapp_posts",
                conditions={
                    "where_condition": "title LIKE %s OR content LIKE %s", 
                    "params": [f"%{request.keyword}%", f"%{request.keyword}%"]
                },
                limit=request.limit,
                order_by="update_time DESC"
            )
        )
        
        # 格式化搜索结果
        formatted_results = []
        for item in results:
            # 截取内容摘要
            content = item.get("content", "")
            if content and len(content) > 200:
                content = content[:200] + "..."
                
            # 处理日期字段
            create_time = item.get("create_time")
            if isinstance(create_time, datetime):
                create_time = create_time.strftime("%Y-%m-%d %H:%M:%S")
                
            formatted_results.append({
                "id": item.get("id"),
                "title": item.get("title", ""),
                "content_preview": content,
                "author": item.get("author", ""),
                "create_time": create_time,
                "type": item.get("type", "文章"),
                "view_count": item.get("view_count", 0),
                "like_count": item.get("like_count", 0),
                "comment_count": item.get("comment_count", 0),
                "relevance": 0  # 简单搜索不计算相关度
            })
        
        return {
            "results": formatted_results,
            "keyword": request.keyword,
            "total": len(formatted_results)
        }
    
    except Exception as e:
        logger.error(f"搜索知识库出错: {str(e)}")
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}") 