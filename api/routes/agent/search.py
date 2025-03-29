"""
智能体搜索API
提供知识库搜索功能
"""
from typing import List, Dict, Any, Optional
from fastapi import Depends, HTTPException, Query
from loguru import logger
import asyncio
from datetime import datetime
import re

from api import agent_router
from api.common import get_api_logger_dep, handle_api_errors
from api.models.search import AgentSearchRequest, AgentAdvancedSearchRequest
from api.models.agent.rag import KnowledgeSearchResponse
from etl.load.db_core import query_records, count_records
from core.utils.logger import register_logger

# 注册专用日志
search_logger = register_logger("agent_search")

# 定义可搜索的表和它们的配置
SEARCHABLE_TABLES = {
    "wxapp_posts": {
        "title_field": "title",
        "content_field": "content",
        "author_field": "nick_name",
        "time_field": "create_time",
        "name": "文章",
        "summary": "小程序文章内容"
    },
    "website_nku": {
        "title_field": "title",
        "content_field": "content",
        "author_field": "author",
        "time_field": "publish_time",
        "name": "网站",
        "summary": "南开大学网站内容"
    },
    "wechat_nku": {
        "title_field": "title",
        "content_field": "content",
        "author_field": "author",
        "time_field": "publish_time",
        "name": "公众号",
        "summary": "南开大学公众号内容"
    },
    "market_nku": {
        "title_field": "title",
        "content_field": "content",
        "author_field": "author",
        "time_field": "publish_time",
        "name": "集市",
        "summary": "南开大学校园集市内容"
    }
}

def calculate_relevance(item: Dict[str, Any], keyword: str, table_config: Dict[str, str]) -> float:
    """计算内容相关度，优化匹配算法"""
    score = 0.0
    max_score = 1.0
    
    # 获取标题和内容
    title = str(item.get(table_config["title_field"], ""))
    content = str(item.get(table_config["content_field"], ""))
    
    # 拆分关键词进行更灵活的匹配
    keywords = keyword.lower().split()
    
    # 1. 标题完全匹配
    if title.lower() == keyword.lower():
        return max_score
        
    # 2. 标题包含完整关键词
    if keyword.lower() in title.lower():
        score += 0.8
    else:
        # 3. 标题包含部分关键词
        matched_keywords = [kw for kw in keywords if kw in title.lower()]
        if matched_keywords:
            title_score = len(matched_keywords) / len(keywords) * 0.7
            score += title_score
            
            # 计算标题中关键词的密度
            title_density = sum(title.lower().count(kw.lower()) for kw in matched_keywords) / len(title) if len(title) > 0 else 0
            score += title_density * 0.1
    
    # 4. 内容包含完整关键词
    if keyword.lower() in content.lower():
        # 计算关键词在内容中出现的频率
        count = content.lower().count(keyword.lower())
        # 根据出现频率增加得分
        content_score = min(0.5, count * 0.1)
        score += content_score
        
        # 计算关键词在内容前部分出现的加权得分
        first_pos = content.lower().find(keyword.lower())
        if first_pos != -1:
            # 如果关键词出现在内容的前10%部分，给予更高得分
            pos_score = max(0, (1 - (first_pos / min(len(content), 1000))) * 0.1)
            score += pos_score
    else:
        # 5. 内容包含部分关键词
        matched_keywords = [kw for kw in keywords if kw in content.lower()]
        if matched_keywords:
            content_score = len(matched_keywords) / len(keywords) * 0.4
            score += content_score
            
            # 计算匹配的关键词在文章中的平均位置
            positions = []
            for kw in matched_keywords:
                pos = content.lower().find(kw.lower())
                if pos != -1:
                    positions.append(pos)
            
            if positions:
                avg_pos = sum(positions) / len(positions)
                # 位置越靠前，得分越高
                pos_score = max(0, (1 - (avg_pos / min(len(content), 2000))) * 0.1)
                score += pos_score
    
    # 考虑文档内容长度因素，中等长度的文档可能更有价值
    content_len = len(content)
    if 500 <= content_len <= 10000:
        score += 0.05
    
    # 确保分数不超过1.0
    return min(score, max_score)

@agent_router.post("/search", response_model=KnowledgeSearchResponse)
@handle_api_errors("知识搜索")
async def search_knowledge(
    request: AgentSearchRequest,
    api_logger=Depends(get_api_logger_dep)
):
    """
    搜索知识库，支持多表搜索
    
    提供基于关键词的跨表内容搜索，支持相关度排序和内容摘要生成
    """
    search_logger.debug(f"处理搜索请求：keyword={request.keyword}, limit={request.limit}, tables={request.tables}")
    
    try:
        all_results = []
        tables_to_search = request.tables if request.tables else ["wxapp_posts"]
        
        # 验证表名
        for table in tables_to_search:
            if table not in SEARCHABLE_TABLES:
                raise HTTPException(status_code=400, detail=f"不支持搜索的表: {table}")
        
        # 并行搜索多个表
        search_tasks = []
        loop = asyncio.get_event_loop()
        
        for table in tables_to_search:
            table_config = SEARCHABLE_TABLES[table]
            title_field = table_config["title_field"]
            content_field = table_config["content_field"]
            
            # 拆分关键词用于更灵活的搜索
            keywords = request.keyword.split()
            conditions = []
            params = []
            
            # 构建更灵活的搜索条件
            if len(keywords) == 1:
                # 单个关键词，使用LIKE
                condition = f"({title_field} LIKE %s OR {content_field} LIKE %s)"
                params.extend([f"%{request.keyword}%", f"%{request.keyword}%"])
                conditions.append(condition)
            else:
                # 多个关键词，增加更灵活的匹配方式
                for kw in keywords:
                    if len(kw) >= 2:  # 只搜索长度>=2的关键词
                        condition = f"({title_field} LIKE %s OR {content_field} LIKE %s)"
                        params.extend([f"%{kw}%", f"%{kw}%"])
                        conditions.append(condition)
                
                # 添加精确短语匹配，提高优先级
                condition = f"({title_field} LIKE %s OR {content_field} LIKE %s)"
                params.extend([f"%{request.keyword}%", f"%{request.keyword}%"])
                conditions.append(condition)
            
            # 如果没有有效的搜索条件，添加原始关键词
            if not conditions:
                condition = f"({title_field} LIKE %s OR {content_field} LIKE %s)"
                params.extend([f"%{request.keyword}%", f"%{request.keyword}%"])
                conditions.append(condition)
            
            where_condition = " OR ".join(conditions)
            
            # 增加排除已删除记录的条件
            if "is_deleted" in await get_table_columns(table):
                where_condition = f"({where_condition}) AND (is_deleted = 0 OR is_deleted IS NULL)"
            
            search_logger.debug(f"搜索表{table}，条件: {where_condition}，参数: {params}")
            
            # 创建异步搜索任务
            task = loop.run_in_executor(
                None,
                lambda t=table, wc=where_condition, p=params: query_records(
                    table_name=t,
                    conditions={"where_condition": wc, "params": p},
                    limit=request.limit * 3,  # 增加初始结果数以便后续筛选
                    order_by="id DESC"  # 默认按ID倒序
                )
            )
            search_tasks.append((table, task))
        
        # 收集所有表的搜索结果
        for table, task in search_tasks:
            table_config = SEARCHABLE_TABLES[table]
            results = await task
            search_logger.debug(f"表 {table} 返回 {len(results)} 条结果")
            
            # 格式化搜索结果
            for item in results:
                # 截取内容摘要
                content_field = table_config["content_field"]
                content = str(item.get(content_field, ""))
                content_preview = ""
                
                if content:
                    # 尝试找出关键词在内容中的位置
                    match = re.search(request.keyword, content, re.IGNORECASE)
                    
                    # 如果没找到完整关键词，尝试匹配拆分后的关键词
                    if not match and len(request.keyword.split()) > 1:
                        for kw in request.keyword.split():
                            if len(kw) >= 2:  # 只匹配长度>=2的关键词
                                match = re.search(kw, content, re.IGNORECASE)
                                if match:
                                    break
                    
                    if match:
                        # 截取关键词周围的文本
                        start = max(0, match.start() - 50)
                        end = min(len(content), match.end() + 150)
                        content_preview = content[start:end]
                        if start > 0:
                            content_preview = "..." + content_preview
                        if end < len(content):
                            content_preview = content_preview + "..."
                    else:
                        # 没有找到关键词，截取开头
                        content_preview = content[:200] + "..." if len(content) > 200 else content
                
                # 处理日期字段
                time_field = table_config["time_field"]
                create_time = item.get(time_field)
                if isinstance(create_time, datetime):
                    create_time = create_time.strftime("%Y-%m-%d %H:%M:%S")
                
                # 计算相关度
                relevance = calculate_relevance(item, request.keyword, table_config)
                
                # 只添加相关度大于0的结果
                if relevance > 0:
                    result_item = {
                        "id": item.get("id"),
                        "title": item.get(table_config["title_field"], ""),
                        "content_preview": content_preview,
                        "author": item.get(table_config["author_field"], ""),
                        "create_time": create_time,
                        "type": table_config["name"],
                        "view_count": item.get("view_count", 0),
                        "like_count": item.get("like_count", 0),
                        "comment_count": item.get("comment_count", 0),
                        "relevance": relevance,
                        "source": table
                    }
                    
                    # 根据 include_content 参数决定是否包含完整内容
                    if request.include_content:
                        result_item["content"] = content
                        
                    all_results.append(result_item)
        
        # 按相关度排序
        all_results.sort(key=lambda x: x["relevance"], reverse=True)
        search_logger.debug(f"排序后共有 {len(all_results)} 条相关结果")
        
        # 如果有结果限制，只返回最相关的结果
        if len(all_results) > request.limit:
            all_results = all_results[:request.limit]
        
        return {
            "results": all_results,
            "keyword": request.keyword,
            "total": len(all_results)
        }
    
    except Exception as e:
        search_logger.error(f"搜索知识库出错: {str(e)}")
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")

@agent_router.post("/search/advanced", response_model=KnowledgeSearchResponse)
@handle_api_errors("高级知识搜索")
async def advanced_search_knowledge(
    request: AgentAdvancedSearchRequest,
    api_logger=Depends(get_api_logger_dep)
):
    """
    高级知识库搜索，支持更多搜索条件和排序方式
    
    提供基于多条件的跨表内容搜索，支持时间范围、作者筛选、多种排序方式
    """
    search_logger.debug(f"处理高级搜索请求：keyword={request.keyword}, limit={request.limit}, tables={request.tables}")
    
    try:
        all_results = []
        tables_to_search = request.tables if request.tables else ["wxapp_posts"]
        
        # 验证表名
        for table in tables_to_search:
            if table not in SEARCHABLE_TABLES:
                raise HTTPException(status_code=400, detail=f"不支持搜索的表: {table}")
        
        # 并行搜索多个表
        search_tasks = []
        loop = asyncio.get_event_loop()
        
        for table in tables_to_search:
            table_config = SEARCHABLE_TABLES[table]
            title_field = table_config["title_field"]
            content_field = table_config["content_field"]
            author_field = table_config["author_field"]
            time_field = table_config["time_field"]
            
            # 构建搜索条件
            conditions = []
            params = []
            
            # 关键词搜索条件
            if request.keyword:
                keywords = request.keyword.split()
                
                # 构建更灵活的关键词搜索条件
                keyword_conditions = []
                for kw in keywords:
                    if len(kw) >= 2:  # 只搜索长度>=2的关键词
                        keyword_condition = f"({title_field} LIKE %s OR {content_field} LIKE %s)"
                        params.extend([f"%{kw}%", f"%{kw}%"])
                        keyword_conditions.append(keyword_condition)
                
                # 添加精确短语匹配
                if request.keyword:
                    keyword_condition = f"({title_field} LIKE %s OR {content_field} LIKE %s)"
                    params.extend([f"%{request.keyword}%", f"%{request.keyword}%"])
                    keyword_conditions.append(keyword_condition)
                
                if keyword_conditions:
                    conditions.append(f"({' OR '.join(keyword_conditions)})")
            
            # 标题搜索条件
            if request.title:
                conditions.append(f"{title_field} LIKE %s")
                params.append(f"%{request.title}%")
            
            # 内容搜索条件
            if request.content:
                conditions.append(f"{content_field} LIKE %s")
                params.append(f"%{request.content}%")
            
            # 作者搜索条件
            if request.author:
                conditions.append(f"{author_field} LIKE %s")
                params.append(f"%{request.author}%")
            
            # 时间范围条件
            if request.start_time:
                conditions.append(f"{time_field} >= %s")
                params.append(request.start_time.strftime("%Y-%m-%d %H:%M:%S"))
            
            if request.end_time:
                conditions.append(f"{time_field} <= %s")
                params.append(request.end_time.strftime("%Y-%m-%d %H:%M:%S"))
            
            # 拼接所有条件
            where_condition = " AND ".join(conditions) if conditions else "1=1"
            
            # 增加排除已删除记录的条件
            if "is_deleted" in await get_table_columns(table):
                where_condition = f"({where_condition}) AND (is_deleted = 0 OR is_deleted IS NULL)"
            
            search_logger.debug(f"高级搜索表{table}，条件: {where_condition}，参数: {params}")
            
            # 确定排序方式
            order_by = request.sort_by if request.sort_by else "id DESC"
            
            # 创建异步搜索任务
            task = loop.run_in_executor(
                None,
                lambda t=table, wc=where_condition, p=params, ob=order_by: query_records(
                    table_name=t,
                    conditions={"where_condition": wc, "params": p},
                    limit=request.limit * 3,  # 增加初始结果数以便后续筛选
                    order_by=ob
                )
            )
            search_tasks.append((table, task))
        
        # 收集所有表的搜索结果
        for table, task in search_tasks:
            table_config = SEARCHABLE_TABLES[table]
            results = await task
            search_logger.debug(f"表 {table} 返回 {len(results)} 条结果")
            
            # 格式化搜索结果
            for item in results:
                # 截取内容摘要
                content_field = table_config["content_field"]
                content = str(item.get(content_field, ""))
                content_preview = ""
                
                if content:
                    # 尝试找出关键词在内容中的位置
                    match = None
                    if request.keyword:
                        match = re.search(request.keyword, content, re.IGNORECASE)
                        
                        # 如果没找到完整关键词，尝试匹配拆分后的关键词
                        if not match and len(request.keyword.split()) > 1:
                            for kw in request.keyword.split():
                                if len(kw) >= 2:  # 只匹配长度>=2的关键词
                                    match = re.search(kw, content, re.IGNORECASE)
                                    if match:
                                        break
                    
                    if match:
                        # 截取关键词周围的文本
                        start = max(0, match.start() - 50)
                        end = min(len(content), match.end() + 150)
                        content_preview = content[start:end]
                        if start > 0:
                            content_preview = "..." + content_preview
                        if end < len(content):
                            content_preview = content_preview + "..."
                    else:
                        # 没有找到关键词，截取开头
                        content_preview = content[:200] + "..." if len(content) > 200 else content
                
                # 处理日期字段
                time_field = table_config["time_field"]
                create_time = item.get(time_field)
                if isinstance(create_time, datetime):
                    create_time = create_time.strftime("%Y-%m-%d %H:%M:%S")
                
                # 计算相关度（仅当有关键词时）
                relevance = 0.0
                if request.keyword:
                    relevance = calculate_relevance(item, request.keyword, table_config)
                else:
                    # 如果没有关键词，按时间新旧或者默认顺序来设置一个基础相关度
                    # 保证结果有序但不影响后续排序
                    relevance = 0.5
                
                # 构建结果项
                result_item = {
                    "id": item.get("id"),
                    "title": item.get(table_config["title_field"], ""),
                    "content_preview": content_preview,
                    "author": item.get(table_config["author_field"], ""),
                    "create_time": create_time,
                    "type": table_config["name"],
                    "view_count": item.get("view_count", 0),
                    "like_count": item.get("like_count", 0),
                    "comment_count": item.get("comment_count", 0),
                    "relevance": relevance,
                    "source": table
                }
                
                # 根据 include_content 参数决定是否包含完整内容
                if request.include_content:
                    result_item["content"] = content
                    
                all_results.append(result_item)
        
        # 根据排序方式处理结果
        if request.sort_by == "relevance":
            # 按相关度排序
            all_results.sort(key=lambda x: x["relevance"], reverse=True)
        elif request.sort_by == "time_desc":
            # 按时间倒序（最新的在前）
            all_results.sort(key=lambda x: x["create_time"], reverse=True)
        elif request.sort_by == "time_asc":
            # 按时间正序（最早的在前）
            all_results.sort(key=lambda x: x["create_time"])
        elif request.sort_by == "likes":
            # 按点赞数排序
            all_results.sort(key=lambda x: x["like_count"], reverse=True)
        elif request.sort_by == "views":
            # 按浏览量排序
            all_results.sort(key=lambda x: x["view_count"], reverse=True)
        else:
            # 默认按相关度排序
            all_results.sort(key=lambda x: x["relevance"], reverse=True)
        
        search_logger.debug(f"排序后共有 {len(all_results)} 条相关结果")
        
        # 如果有结果限制，只返回最相关的结果
        if len(all_results) > request.limit:
            all_results = all_results[:request.limit]
        
        return {
            "results": all_results,
            "keyword": request.keyword or "",
            "total": len(all_results)
        }
    
    except Exception as e:
        search_logger.error(f"高级搜索知识库出错: {str(e)}")
        raise HTTPException(status_code=500, detail=f"高级搜索失败: {str(e)}")

async def get_table_columns(table_name: str) -> List[str]:
    """获取表的所有列名"""
    try:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: query_records(
                table_name="information_schema.columns",
                conditions={
                    "where_condition": "table_schema = %s AND table_name = %s",
                    "params": [SEARCHABLE_TABLES.get("wxapp_posts", {}).get("database", "nkuwiki"), table_name]
                }
            )
        )
        return [col["COLUMN_NAME"] for col in result]
    except Exception as e:
        search_logger.error(f"获取表结构失败: {str(e)}")
        return [] 