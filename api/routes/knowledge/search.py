"""
知识库搜索API接口
提供混合搜索、高级搜索、历史记录等功能
"""
import asyncio
import hashlib
import json
import re
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

import jieba.analyse
from elasticsearch import AsyncElasticsearch
from fastapi import Query, APIRouter, Body, HTTPException, Depends
from pydantic import BaseModel, Field

from api.common.dependencies import get_current_active_user, get_current_active_user_optional
from api.models.common import Response, Request, PaginationInfo
from api.routes.wxapp._utils import batch_enrich_posts_with_user_info
from config import Config
from core.bridge.reply import Reply, ReplyType
from core.utils.logger import register_logger
from etl import ES_INDEX_NAME
from etl.rag.pipeline import RagPipeline
from etl.rag.strategies import RetrievalStrategy, RerankStrategy
from etl.utils.const import official_author as OFFICIAL_AUTHORS_WHITELIST
from etl.load import db_core
from etl.load.db_pool_manager import get_db_connection
from api.common.vector import get_retriever
from pathlib import Path

# 模块初始化
router = APIRouter()
logger = register_logger('api.routes.knowledge.search')

TABLE_MAPPING = {
    # 微信小程序平台
    "wxapp": {
        "name": "小程序",
        "post": {
            "content_field": "content",
            "title_field": "title",
            "author_field": "nickname",
            "status_field": "status",
            "deleted_field": "is_deleted",
            "time_field": "update_time"  # wxapp平台使用update_time
        },
        "comment": {
            "content_field": "content",
            "title_field": "content",
            "author_field": "nickname",
            "status_field": "status",
            "deleted_field": "is_deleted",
            "time_field": "update_time"  # wxapp平台使用update_time
        }
    },
    # 微信公众号平台
    "wechat": {
        "name": "微信公众号",
        "content_field": "content",
        "title_field": "title",
        "author_field": "author",
        "time_field": "publish_time"  # wechat平台使用publish_time
    },
    # 网站平台
    "website": {
        "name": "南开网站",
        "content_field": "content",
        "title_field": "title",
        "author_field": "author",
        "time_field": "publish_time"  # website平台使用publish_time
    },
    # 校园集市平台
    "market": {
        "name": "校园集市",
        "content_field": "content",
        "title_field": "title",
        "author_field": "author",
        "status_field": "status",
        "time_field": "publish_time"  # market平台使用publish_time
    }
}

def calculate_relevance(query: str, title: str, content: str, author: str = "", time_value: str = None) -> float:
    """计算文本相关度
    
    Args:
        query: 搜索关键词
        title: 标题
        content: 内容
        author: 作者
        time_value: 时间值
        
    Returns:
        float: 相关度分数，范围0-1
    """
    # 将查询词拆分为关键词列表
    keywords = re.findall(r'\w+', query.lower())
    if not keywords:
        return 0.0
        
    # 计算标题相关度
    title_score = 0.0
    title_lower = title.lower()
    for keyword in keywords:
        if keyword in title_lower:
            # 标题中的关键词权重更高
            title_score += 2.0
            
    # 计算作者相关度
    author_score = 0.0
    if author:
        author_lower = author.lower()
        for keyword in keywords:
            if keyword in author_lower:
                # 作者相关度与标题相当的权重
                author_score += 2.0
            
    # 计算内容相关度
    content_score = 0.0
    content_lower = content.lower()
    for keyword in keywords:
        # 内容中的关键词权重较低
        content_score += content_lower.count(keyword) * 0.1
        
    # 计算总相关度
    total_score = title_score + author_score + content_score
    
    # 时间相关度调整
    time_factor = 1.0
    if time_value:
        try:
            # 将字符串时间转换为datetime对象
            if isinstance(time_value, str):
                if 'T' in time_value:
                    time_datetime = datetime.fromisoformat(time_value)
                else:
                    time_datetime = datetime.strptime(time_value, "%Y-%m-%d %H:%M:%S")
            else:
                time_datetime = time_value
                
            # 计算时间差（天数）
            days_diff = (datetime.now() - time_datetime).days
            
            # 根据时间差计算时间因子，越新的内容加权越高
            # 一个月内的内容获得最高加权
            if days_diff <= 30:
                time_factor = 1.2
            # 三个月内的内容获得中等加权
            elif days_diff <= 90:
                time_factor = 1.1
            # 六个月内的内容获得轻微加权
            elif days_diff <= 180:
                time_factor = 1.05
            # 超过六个月的内容不加权
        except Exception as e:
            logger.debug(f"计算时间因子失败: {str(e)}")
    
    # 应用时间因子
    total_score *= time_factor
    
    # 归一化到0-1范围
    # 考虑标题、作者和内容的最大可能分数
    max_score = len(keywords) * 4.0 + len(keywords) * 0.1 * 10  # 标题和作者各2.0权重，假设内容中每个关键词最多出现10次
    if max_score == 0:
        return 0.0
        
    return min(total_score / max_score, 1.0)

async def search_knowledge(
    query: str, 
    current_user: Optional[Dict[str, Any]], # 使用current_user代替openid
    platform: Optional[str] = None,
    tag: Optional[str] = None,
    max_results: int = 30,  # 显著增加默认单表查询结果数量
    page: int = 1,
    page_size: int = 10,
    sort_by: str = "relevance",
    max_content_length: int = 500
) -> Dict[str, Any]:
    """知识库搜索核心逻辑，供内部调用
    
    Args:
        query: 搜索关键词
        openid: 用户openid
        platform: 平台标识，可选值：wechat/website/market/wxapp，多个用逗号分隔
        tag: 标签，多个用逗号分隔
        max_results: 单表最大结果数，默认30
        page: 分页页码，默认1
        page_size: 每页结果数，默认10
        sort_by: 排序方式，可选值：relevance(相关度)/time(时间)，默认relevance
        max_content_length: 单条内容最大长度，默认500，超过将被截断
        
    Returns:
        Dict: 搜索结果，包含分页信息和数据列表
        {
            "data": [...], // 字典对象列表
            "pagination": {...} // 分页信息
        }
    """
    
    if not query:
        return {"data": [], "pagination": {"total": 0, "page": page, "page_size": page_size, "total_pages": 0}}
    
    # 处理平台标识参数，支持多平台
    table_list = []
    if platform:
        # 分割平台字符串
        platform_list = [p.strip() for p in platform.split(',') if p.strip()]
        
        for p in platform_list:
            if p == "wxapp":
                table_list.append("wxapp_post")
            elif p in ["wechat", "website", "market"]:
                table_list.append(f"{p}_nku")
            else:
                logger.warning(f"平台 {p} 不存在或不支持搜索")
                continue
    else:
        # 不指定平台时，搜索所有表
        table_list = ["wechat_nku", "website_nku", "market_nku", "wxapp_post"]
    
    # 处理标签参数，为不同平台提供默认标签
    tag_list = []
    if tag:
        tag_list = tag.split(",")
    else:
        # 不指定tag时，根据平台添加默认标签
        if len(table_list) == 1:
            if table_list[0] == "wxapp_post":
                tag_list = ["post"]
            elif table_list[0] in ["wechat_nku", "website_nku", "market_nku"]:
                tag_list = ["nku"]
    
    logger.debug(f"知识库搜索: query={query}, platform={platform}, tag={tag_list}, tables={table_list}, max_content_length={max_content_length}")
    
    # 验证表名是否合法
    valid_tables = []
    for table in table_list:
        platform_name = table.split("_")[0]
        if platform_name in TABLE_MAPPING:
            valid_tables.append(table)
        else:
            logger.warning(f"平台 {platform_name} 不存在或不支持搜索")
            
    if not valid_tables:
        return {"data": [], "pagination": {"total": 0, "page": page, "page_size": page_size, "total_pages": 0}}
            
    offset = (page - 1) * page_size
    
    # 搜索所有指定表
    all_results = []
    search_tasks = []
    
    # 构建并发搜索任务
    for table in valid_tables:
        # 从表名中提取平台和标签
        platform_name, *rest = table.split("_")
        tag_name = rest[0] if rest else ""
        platform_info = TABLE_MAPPING.get(platform_name)

        if not platform_info:
            logger.warning(f"平台 {platform_name} 在 TABLE_MAPPING 中没有定义，跳过")
            continue
        
        # 如果是wxapp平台，需要根据tag获取对应的表结构
        if platform_name == "wxapp":
            if not tag_name or tag_name not in platform_info:
                logger.warning(f"wxapp平台缺少有效标签，跳过表 {table}")
                continue
            table_info = platform_info[tag_name]
        else:
            table_info = platform_info
            
        content_field = table_info["content_field"]
        title_field = table_info["title_field"]
        
        # 分词处理查询字符串
        keywords = [k.strip() for k in query.split() if k.strip()]
        if not keywords:
            keywords = [query]  # 如果分词后为空，使用原始查询
            
        logger.debug(f"分词结果: {keywords}")
        
        # 构建WHERE条件部分
        where_parts = []
        sql_params = []
        
        # 获取作者字段
        author_field = table_info.get("author_field", "author")
        
        # 为每个关键词构建LIKE条件
        for keyword in keywords:
            # 标题中包含关键词
            where_parts.append(f"{title_field} LIKE %s")
            sql_params.append(f"%{keyword}%")
            
            # 内容中包含关键词
            where_parts.append(f"{content_field} LIKE %s")
            sql_params.append(f"%{keyword}%")
            
            # 作者中包含关键词
            where_parts.append(f"{author_field} LIKE %s")
            sql_params.append(f"%{keyword}%")
        
        # 使用OR连接所有条件
        where_condition = "(" + " OR ".join(where_parts) + ")"
        
        # 如果表有状态字段，只搜索正常状态的记录
        if "status_field" in table_info:
            where_condition += f" AND {table_info['status_field']} = 1"
            
        # 如果表有删除字段，只搜索未删除的记录
        if "deleted_field" in table_info:
            where_condition += f" AND {table_info['deleted_field']} = 0"
        
        # 从表中获取时间字段
        time_field = table_info.get("time_field", "publish_time")
        
        logger.debug(f"搜索SQL条件: {where_condition}, 参数: {sql_params}")
        
        # 更新排序方式，使用各表配置的时间字段进行降序排序
        order_by_dict = {time_field: "DESC", "id": "DESC"}
        
        search_task = db_core.query_records(
            table_name=table,
            conditions={
                "where_condition": where_condition,
                "params": sql_params
            },
            order_by=order_by_dict,
            limit=max_results
        )
        search_tasks.append((table, search_task))
        
    # 并发执行所有搜索任务
    search_results = await asyncio.gather(*[task for _, task in search_tasks])
    
    # 处理搜索结果
    total_count = 0
    for i, (table, _) in enumerate(search_tasks):
        table_results = search_results[i]
        platform_name = table.split("_")[0]
        platform_info = TABLE_MAPPING[platform_name]
        
        for item in table_results["data"]:
            # 计算相关度
            # 从表中获取作者字段名
            author_field = platform_info.get("author_field", "author")
            if platform_name == "wxapp":
                table_info = platform_info[table.split("_")[1]]
                author_field = table_info.get("author_field", "nickname")
                time_field = table_info.get("time_field", "update_time")
            else:
                time_field = platform_info.get("time_field", "publish_time")
                
            # 获取作者值和时间值
            author = item.get(author_field, "")
            time_value = item.get(time_field)
            
            relevance = calculate_relevance(
                query, 
                item.get("title", ""), 
                item.get("content", ""),
                author,
                time_value
            )
            item["relevance"] = relevance
            
            # 为每个结果添加表和来源信息
            item["_table"] = table
            item["_type"] = platform_info["name"]
            
            # 截断过长内容
            if "content" in item and item["content"] and len(item["content"]) > max_content_length:
                item["content"] = item["content"][:max_content_length] + "..."
                item["_content_truncated"] = True
                
            all_results.append(item)
            total_count += 1
            
    # 根据排序方式排序
    if sort_by == "relevance":
        all_results.sort(key=lambda x: x.get("relevance", 0), reverse=True)
    else:  # time
        # 按每个表配置的时间字段排序
        all_results.sort(key=lambda x: 
            # 获取对应表的时间字段
            x.get(
                TABLE_MAPPING.get(
                    x.get("_table", "").split("_")[0], 
                    {}
                ).get("time_field", "publish_time"), 
                # 如果没有配置或找不到值，使用create_time
                x.get("create_time", "1970-01-01")
            ), 
            reverse=True
        )
    
    # 分页
    paged_results = all_results[offset:offset+page_size] if all_results else []
    
    # 转换为字典格式
    sources = []
    
    # 收集所有来自wxapp_post的项目，用于批量查询用户信息
    wxapp_post_items = [item for item in paged_results if item.get("_table") == "wxapp_post"]
    other_items = [item for item in paged_results if item.get("_table") != "wxapp_post"]

    # 优先处理其他平台的item
    for item in other_items:
        source = item.copy()
        platform_name = source.get("_table", "").split("_")[0]
        
        # 确保有is_truncated字段
        source["is_truncated"] = item.get("_content_truncated", False)
        
        # 添加平台信息
        source["platform"] = platform_name
        
        # 对于非wxapp平台，需要进行额外字段处理
        if platform_name in TABLE_MAPPING and platform_name != "wxapp":
            platform_info = TABLE_MAPPING[platform_name]
            
            # 获取作者字段名和值
            author_field = platform_info.get("author_field", "author")
            author = item.get(author_field, "") or "未知作者"
            
            # 获取标题和内容的字段名和值
            title_field = platform_info.get("title_field", "title")
            content_field = platform_info.get("content_field", "content")
            title = item.get(title_field, "") or "无标题"
            content = item.get(content_field, "") or ""
            
            # 获取其他值
            original_url = item.get("original_url", "")
            
            # 处理标签，如果存在
            tag_val = ""
            if "tag" in item and item["tag"]:
                try:
                    if isinstance(item["tag"], str):
                        tag_val = json.loads(item["tag"])
                    else:
                        tag_val = item["tag"]
                except:
                    tag_val = ""
                    
            # 处理时间字段
            publish_time = item.get("publish_time")
            create_time = publish_time
            update_time = publish_time
            
            # 添加或覆盖处理后的字段，符合API文档规范
            source.update({
                "author": author,
                "title": title,
                "content": content,
                "original_url": original_url,
                "tag": tag_val,
                "create_time": str(create_time) if create_time else "",
                "update_time": str(update_time) if update_time else "",
                "is_official": item.get("is_official", False)
            })

        if "_table" in source: del source["_table"]
        if "_type" in source: del source["_type"]
        if "_content_truncated" in source: del source["_content_truncated"]
        
        sources.append(source)
    
    # 如果有wxapp_post的帖子，批量查询用户信息并格式化字段
    if wxapp_post_items:
        # 使用通用函数批量补充用户信息，并传入user_id
        enriched_posts = await batch_enrich_posts_with_user_info(wxapp_post_items, current_user['id'] if current_user else None)
        
        for post in enriched_posts:
            # 格式化字段以符合API文档规范
            user_info = post.get("user_info", {})
            post.update({
                "author": user_info.get("nickname", ""),
                "avatar": user_info.get("avatar", ""),
                "title": post.get("title", ""),
                "content": post.get("content", ""),
                "original_url": f"wxapp://post/{post.get('id', '')}",
                "tag": post.get("tag", "") if post.get("tag") else "",
                "create_time": str(post.get("create_time", "")),
                "update_time": str(post.get("update_time", "")),
                "platform": "wxapp",
            })
            # 清理临时或内部字段
            if "_table" in post: del post["_table"]
            if "_type" in post: del post["_type"]
            if "_content_truncated" in post: del post["_content_truncated"]
            if "user_info" in post: del post["user_info"]
            sources.append(post)

    # 由于处理顺序打乱了原有的排序，需要根据sort_by重新排序
    if sort_by == "relevance":
        sources.sort(key=lambda x: x.get("relevance", 0), reverse=True)
    else:  # time
        def get_sort_time(item):
            platform = item.get('platform')
            if platform == 'wxapp':
                return item.get('update_time', '1970-01-01T00:00:00')
            else:
                return item.get('create_time', '1970-01-01T00:00:00')
        sources.sort(key=get_sort_time, reverse=True)

    # 创建分页信息
    pagination = {
        "total": total_count,
        "page": page,
        "page_size": page_size,
        "total_pages": (total_count + page_size - 1) // page_size if page_size > 0 else 1
    }
    
    # 记录搜索历史
    if current_user:
        asyncio.create_task(_record_search_history(query, current_user['id']))
    
    return {
        "data": sources,
        "pagination": pagination
    }

@router.get("/search", summary="混合搜索")
async def search_endpoint(
    query: str = Query(..., description="搜索关键词"),
    platform: Optional[str] = Query("wechat,website,market,wxapp", description="平台标识(wechat,website,market,wxapp)，多个用逗号分隔"),
    tag: Optional[str] = Query(None, description="标签，多个用逗号分隔"),
    max_results: int = Query(10, description="单表最大结果数"),
    page: int = Query(1, description="分页页码"),
    page_size: int = Query(10, description="每页结果数"),
    sort_by: str = Query("relevance", description="排序方式：relevance-相关度，time-时间"),
    max_content_length: int = Query(500, description="单条内容最大长度，超过将被截断"),
    current_user: Optional[Dict[str, Any]] = Depends(get_current_active_user_optional) # 依赖注入
):
    """
    提供跨平台、多来源的综合信息搜索功能。
    
    - **核心功能**: 根据关键词在 `website`, `wechat`, `market`, `wxapp` 等多个平台中进行搜索。
    - **排序**: 支持按 `relevance` (相关度) 或 `time` (发布时间) 排序。
    - **认证**: 可选。提供有效的JWT Token时，会记录用户搜索历史并启用个性化功能。
    """
    try:
        # 调用核心搜索逻辑
        search_result = await search_knowledge(
            query=query,
            current_user=current_user,
            platform=platform,
            tag=tag,
            max_results=max_results,
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            max_content_length=max_content_length
        )
        
        # 记录搜索历史（如果用户已登录）
        if current_user and query:
            try:
                await _record_search_history(query, current_user['id'])
            except Exception as e:
                logger.error(f"记录用户 {current_user['id']} 的搜索历史失败: {e}", exc_info=True)

        pagination_info = PaginationInfo(
            total=search_result["pagination"]["total"],
            page=page,
            page_size=page_size
        )

        return Response.paged(
            data=search_result["data"],
            pagination=pagination_info
        )

    except Exception as e:
        logger.error(f"[/knowledge/search] 搜索失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"服务器内部错误: {str(e)}"
        )


@router.get("/advanced-search", summary="高级RAG搜索")
async def advanced_search_endpoint(
    query: str = Query(..., description="搜索关键词"),
    top_k_retrieve: int = Query(20, description="召回文档数量，建议值[10, 50]"),
    top_k_rerank: int = Query(10, description="重排文档数量，建议值[5, 20]"),
    retrieval_strategy: RetrievalStrategy = Query(
        default=RetrievalStrategy.AUTO, 
        description="检索策略：auto-自动, hybrid-混合, vector_only-仅向量, bm25_only-仅BM25, es_only-仅ES"
    ),
    rerank_strategy: RerankStrategy = Query(
        default=RerankStrategy.BGE_RERANKER,
        description="重排策略：no_rerank-不重排, bge_reranker-BGE模型, st_reranker-SentenceTransformer, personalized-个性化"
    ),
    current_user: Dict[str, Any] = Depends(get_current_active_user) # 严格依赖
):
    """
    高级RAG搜索，使用可配置的检索和重排策略，提供更精准的结果。
    此接口必须登录后才能使用。
    """
    user_id = current_user['id']
    start_time = time.time()
    logger.info(f"高级搜索开始: query='{query}', user='{user_id}', retrieval='{retrieval_strategy}', rerank='{rerank_strategy}'")

    # 异步记录搜索历史
    asyncio.create_task(_record_search_history(query, user_id))

    try:
        pipeline = RagPipeline()
        rag_result = await pipeline.run(
            query=query,
            retrieval_strategy=retrieval_strategy,
            rerank_strategy=rerank_strategy,
            top_k_retrieve=top_k_retrieve,
            top_k_rerank=top_k_rerank,
            user_id=user_id
        )

        end_time = time.time()
        logger.info(f"高级搜索完成: query='{query}', retrieved={len(rag_result.retrieved_nodes)}, reranked={len(rag_result.reranked_nodes)}, duration={end_time - start_time:.2f}s")

        return Response.success(data=rag_result.to_dict())
    except Exception as e:
        logger.exception(f"高级搜索失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def _elasticsearch_search_internal(
    query: str,
    current_user: Optional[Dict[str, Any]], # 使用current_user
    enhanced_query: str = None,
    platform: Optional[str] = None,
    size: int = 10,
    offset: int = 0,
    max_content_length: int = 300
) -> Dict[str, Any]:
    """使用Elasticsearch进行内部复合查询"""
    
    es_client = AsyncElasticsearch(
        [f"http://{Config().get('etl.data.elasticsearch.host')}:{Config().get('etl.data.elasticsearch.port')}"])

    try:
        search_query = {
            "query": {
                "multi_match": {
                    "query": query,
                    "fields": ["title^2", "content"],
                    "type": "best_fields"
                }
            },
            "size": size,
            "from": offset,
            "highlight": {
                "pre_tags": ["<mark>"],
                "post_tags": ["</mark>"],
                "fields": {
                    "content": {
                        "fragment_size": 150,
                        "number_of_fragments": 3
                    }
                }
            }
        }

        # 如果提供了 enhanced_query，也将其加入查询以提高召回率
        if enhanced_query and enhanced_query != query:
            # 使用 bool 查询来合并原始查询和增强查询
            search_query["query"] = {
                "bool": {
                    "should": [
                        {"multi_match": search_query["query"]["multi_match"]},
                        {
                            "multi_match": {
                                "query": enhanced_query,
                                "fields": ["title^2", "content"],
                                "type": "best_fields"
                            }
                        }
                    ],
                    "minimum_should_match": 1
                }
            }
        
        # 添加平台筛选
        if platform:
            platform_list = [p.strip() for p in platform.split(',') if p.strip()]
            if platform_list:
                # 确保 bool 查询存在
                if "bool" not in search_query["query"]:
                    # 如果之前没有 bool 查询，需要将 multi_match 包装进去
                    original_query = search_query["query"]
                    search_query["query"] = {"bool": {"must": [original_query]}}

                search_query["query"]["bool"]["filter"] = [
                    {"terms": {"platform.keyword": platform_list}}
                ]

        logger.debug(f"Executing ES query: {json.dumps(search_query, indent=2, ensure_ascii=False)}")
        response = await es_client.search(index=ES_INDEX_NAME, body=search_query)
        
        # 将 Elasticsearch 响应对象转换为可序列化的 Python 字典
        # 解决 ObjectApiResponse 不可 JSON 序列化的问题
        if hasattr(response, 'body'):
            # 对于 Elasticsearch 9.x 版本，响应是 ObjectApiResponse 对象
            response_dict = response.body
            if isinstance(response_dict, dict):
                return response_dict
            else:
                # 如果 body 不是字典，尝试转换为字典
                return json.loads(json.dumps(response_dict))
        elif hasattr(response, 'to_dict'):
            # 对于某些版本的 Elasticsearch 客户端，可能有 to_dict 方法
            return response.to_dict()
        else:
            # 尝试直接转换为字典
            try:
                return dict(response)
            except (TypeError, ValueError):
                # 如果无法直接转换，尝试通过 JSON 序列化再反序列化
                return json.loads(json.dumps(response, default=lambda o: str(o)))
    except Exception as e:
        logger.exception(f"Elasticsearch 内部查询失败: {e}")
        # 返回一个空的、符合ES格式的响应
        return {
            "hits": {
                "total": {"value": 0, "relation": "eq"},
                "max_score": None,
                "hits": []
            }
        }
    finally:
        await es_client.close()

@router.get("/es-search", summary="Elasticsearch 复合查询接口") 
async def elasticsearch_search_endpoint( 
    query: str = Query(..., description="搜索关键词"), 
    platform: Optional[str] = Query(None, description="平台筛选，多个用逗号分隔"), 
    page: int = Query(1, description="分页页码"), 
    page_size: int = Query(10, description="每页结果数"), 
    max_content_length: int = Query(300, description="内容最大长度"),
    current_user: Optional[Dict[str, Any]] = Depends(get_current_active_user_optional)
): 
    """ 
    使用Elasticsearch进行检索，支持通配符和数据源筛选。 
    """ 
    try: 
        start_time = time.time() 
        
        offset = (page - 1) * page_size 
        response = await _elasticsearch_search_internal( 
            query=query, 
            current_user=current_user,  # 使用JWT中的用户信息
            platform=platform, 
            size=page_size, 
            offset=offset, 
            max_content_length=max_content_length 
        ) 
 
        if 'error' in response: 
            logger.error(f"ES内部检索失败: {response['error']}") 
            return Response.error(message=response['error'], code=500) 
        
        results = response['hits']['hits'] 
        total_hits = response['hits']['total']['value'] 
        
        processed_results = [] 
        for hit in results: 
            source = hit['_source'] 
            score = hit['_score'] 
            
            title = source.get('title', '无标题') 
            platform = source.get('platform', '') 
            author = source.get('author', '') 
            original_url = source.get('original_url', '') 
            original_content_length = len(source.get('content', '')) 
            
            logger.debug(f"  文档 ID={hit['_id']}, 分数={score:.4f}, 平台={platform}") 
            logger.debug(f"    标题: {title[:50]}{'...' if len(title) > 50 else ''}") 
            logger.debug(f"    作者: {author}, 内容长度: {original_content_length}字符") 
            
            content = source.get('content', '') 
            is_truncated = False 
            if content and len(content) > max_content_length: 
                content = content[:max_content_length] + "..." 
                is_truncated = True 
                logger.debug(f"    内容已截断: {original_content_length} -> {max_content_length}字符") 
            
            # 动态判断是否为官方来源 
            is_official = source.get('is_official', False) 
            if platform == 'website' or author in OFFICIAL_AUTHORS_WHITELIST: 
                is_official = True 
            
            result_item = { 
                "title": title, 
                "content": content, 
                "original_url": original_url, 
                "author": author, 
                "platform": platform, 
                "tag": source.get('tag', '') if source.get('tag') else "", 
                "create_time": str(source.get('publish_time', '')) if source.get('publish_time') else "", 
                "update_time": str(source.get('publish_time', '')) if source.get('publish_time') else "", 
                "relevance": score, 
                "is_truncated": is_truncated, 
                "is_official": is_official 
            } 
            processed_results.append(result_item) 
        
        pagination = PaginationInfo( 
            total=total_hits, 
            page=page, 
            page_size=page_size, 
            total_pages=(total_hits + page_size - 1) // page_size if page_size > 0 else 1 
        ) 
        
        platform_stats = {p: 0 for p in set(r['platform'] for r in processed_results)} 
        for result in processed_results: 
            platform_stats[result.get('platform', 'unknown')] += 1 
        
        logger.debug(f"ES检索完成汇总:") 
        logger.debug(f"  查询: '{query}', 平台过滤: {platform}") 
        logger.debug(f"  检索耗时: {time.time() - start_time:.2f}秒") 
        logger.debug(f"  命中总数: {total_hits}, 返回数量: {len(processed_results)}") 
        logger.debug(f"  平台分布: {platform_stats}") 
        if processed_results: 
            scores = [r['relevance'] for r in processed_results] 
            logger.debug(f"  分数范围: {min(scores):.4f} ~ {max(scores):.4f}") 
        
        # 如果用户已登录，记录搜索历史
        if current_user:
            asyncio.create_task(_record_search_history(query, current_user['id']))
        
        return Response.paged( 
            data=processed_results, 
            pagination=pagination 
        ) 
 
    except Exception as e: 
        import traceback 
        error_detail = traceback.format_exc() 
        logger.error(f"ES检索失败: {str(e)}\n{error_detail}") 
        return Response.error(message=f"ES检索失败: {str(e)}", code=500)

async def _record_search_history(query: str, user_id: int):
    """记录用户搜索历史到数据库
    
    Args:
        query: 搜索关键词
        user_id: 用户ID
    """
    if not user_id:
        logger.warning("无法记录搜索历史，因为user_id为空")
        return
        
    try:
        # 使用 user_id 记录搜索历史
        history_data = {
            "user_id": user_id,
            "query": query,
            "search_time": time.strftime('%Y-%m-%d %H:%M:%S')
        }
        await db_core.insert_record("wxapp_search_history", history_data)
        logger.debug(f"用户 {user_id} 的搜索历史 '{query}' 已记录")
    except Exception as e:
        logger.error(f"记录用户 {user_id} 的搜索历史失败: {str(e)}")

@router.get("/suggestion", summary="获取搜索建议")
async def get_search_suggest(
    query: str = Query(..., description="搜索关键词"),
    page_size: int = Query(5, description="返回结果数量"),
    current_user: Optional[Dict[str, Any]] = Depends(get_current_active_user_optional)
):
    """搜索建议"""
    try:
        logger.debug(f"获取搜索建议: query={query}")
        if not query.strip():
            return Response.success(data=[])
        
        # 如果用户未登录，返回空结果
        if not current_user:
            return Response.success(data=[])
            
        # 从 search_history 表中获取搜索建议
        suggest_query = """
            SELECT query, COUNT(*) as count 
            FROM wxapp_search_history 
            WHERE query LIKE %s AND user_id = %s
            GROUP BY query 
            ORDER BY count DESC 
            LIMIT %s
        """
        
        like_query = f"%{query}%"
        results = await db_core.execute_custom_query(suggest_query, [like_query, current_user['id'], page_size], fetch='all')
        
        # 提取建议词
        suggestions = [row['query'] for row in results]
        
        # 异步记录搜索历史
        asyncio.create_task(_record_search_history(query, current_user['id']))
            
        return Response.success(data=suggestions)
    except Exception as e:
        logger.error(f"获取搜索建议失败: {str(e)}")
        return Response.error(details={"message": f"获取搜索建议失败: {str(e)}"})

@router.get("/search-wxapp")
async def search(
    query: str = Query(..., description="搜索关键词"),
    search_type: str = Query("all", description="搜索类型: all, post, user"),
    page: int = Query(1, description="页码"),
    page_size: int = Query(10, description="每页记录数量"),
    sort_by: str = Query("time", description="排序方式: time(时间), relevance(相关度)")
):
    """综合搜索"""
    try:
        if not query.strip():
            return Response.bad_request(details={"message": "搜索关键词不能为空"})
            
        logger.debug(f"执行搜索: query={query}, search_type={search_type}, page={page}, page_size={page_size}, sort_by={sort_by}")
        offset = (page - 1) * page_size
        search_results = []
        total = 0
        
        # 准备异步查询任务
        search_tasks = []
        count_tasks = []
        
        if search_type == "all" or search_type == "post":
            # 搜索帖子任务
            post_sql = """
            SELECT id, openid, title, content, category_id, view_count, like_count, 
                   comment_count, favorite_count, create_time, update_time
            FROM wxapp_post
            WHERE status = 1 AND (title LIKE %s OR content LIKE %s)
            """
            
            # 默认按时间排序
            if sort_by == "time":
                post_sql += " ORDER BY update_time DESC"
            # 如果不是时间排序，暂不排序，后面会根据相关度计算排序
            
            post_sql += " LIMIT %s OFFSET %s"
            
            search_tasks.append(
                ("post", db_core.execute_custom_query(
                    post_sql, 
                    [f"%{query}%", f"%{query}%", page_size, offset]
                ))
            )
            
            # 获取帖子总数任务
            post_count_sql = """
            SELECT COUNT(*) as total FROM wxapp_post
            WHERE status = 1 AND (title LIKE %s OR content LIKE %s)
            """
            count_tasks.append(
                ("post", db_core.execute_custom_query(
                    post_count_sql,
                    [f"%{query}%", f"%{query}%"]
                ))
            )
        
        if search_type == "all" or search_type == "user":
            # 搜索用户任务 - 增加更多用户字段
            user_sql = """
            SELECT id, openid, nickname, avatar, bio, gender, province, city, 
                   post_count, follower_count, following_count, like_count, favorite_count, 
                   status, create_time, update_time
            FROM wxapp_user
            WHERE status = 1 AND (nickname LIKE %s OR bio LIKE %s)
            """
            
            # 默认按时间排序
            if sort_by == "time":
                user_sql += " ORDER BY update_time DESC"
            # 如果不是时间排序，暂不排序，后面会根据相关度计算排序
            
            user_sql += " LIMIT %s OFFSET %s"
            
            search_tasks.append(
                ("user", db_core.execute_custom_query(
                    user_sql,
                    [f"%{query}%", f"%{query}%", page_size, offset]
                ))
            )
            
            # 获取用户总数任务
            user_count_sql = """
            SELECT COUNT(*) as total FROM wxapp_user
            WHERE status = 1 AND (nickname LIKE %s OR bio LIKE %s)
            """
            count_tasks.append(
                ("user", db_core.execute_custom_query(
                    user_count_sql,
                    [f"%{query}%", f"%{query}%"]
                ))
            )
        
        # 并行执行所有查询任务
        all_tasks = [task for _, task in search_tasks] + [task for _, task in count_tasks]
        all_results = await asyncio.gather(*all_tasks)
        
        # 处理结果
        search_results_map = {}
        count_results_map = {}
        
        for i, (result_type, _) in enumerate(search_tasks):
            search_results_map[result_type] = all_results[i]
            
        for i, (result_type, _) in enumerate(count_tasks):
            count_results_map[result_type] = all_results[i + len(search_tasks)]
        
        # 构建搜索结果
        if "post" in search_results_map:
            post_results = []
            for post in search_results_map["post"]:
                # 如果是按相关度排序，计算相关度分数
                if sort_by == "relevance":
                    relevance = calculate_relevance(
                        query,
                        post.get("title", ""),
                        post.get("content", ""),
                        "",  # 不考虑作者
                        post.get("update_time")
                    )
                    post["relevance"] = relevance
                
                post_results.append({
                    "id": post["id"],
                    "title": post["title"],
                    "content": post["content"],
                    "type": "post",
                    "like_count": post["like_count"],
                    "comment_count": post["comment_count"],
                    "view_count": post["view_count"],
                    "update_time": post["update_time"],
                    "create_time": post.get("create_time"),
                    "openid": post.get("openid", ""),  # 确保有openid字段
                    "relevance": post.get("relevance", 0) if sort_by == "relevance" else 0
                })
            
            # 如果是按相关度排序，对结果进行排序
            if sort_by == "relevance":
                post_results.sort(key=lambda x: x.get("relevance", 0), reverse=True)
            
            # 补充用户信息
            if post_results:
                await batch_enrich_posts_with_user_info(post_results, None)

            search_results.extend(post_results)
            post_total = count_results_map["post"][0]['total'] if count_results_map["post"] else 0
            total += post_total
        
        if "user" in search_results_map:
            user_results = []
            for user in search_results_map["user"]:
                # 如果是按相关度排序，计算相关度分数
                if sort_by == "relevance":
                    relevance = calculate_relevance(
                        query,
                        user.get("nickname", ""),
                        user.get("bio", ""),
                        "",  # 不考虑作者
                        None  # 不考虑时间
                    )
                    user["relevance"] = relevance
                
                # 增强用户数据，返回更多字段
                user_result = {
                    "id": user["id"],
                    "openid": user["openid"],
                    "nickname": user["nickname"],
                    "avatar": user["avatar"],
                    "bio": user["bio"],
                    "type": "user",
                    "relevance": user.get("relevance", 0) if sort_by == "relevance" else 0,
                    # 添加更多字段
                    "gender": user.get("gender", 0),
                    "province": user.get("province", ""),
                    "city": user.get("city", ""),
                    "post_count": user.get("post_count", 0),
                    "follower_count": user.get("follower_count", 0),
                    "following_count": user.get("following_count", 0),
                    "like_count": user.get("like_count", 0),
                    "favorite_count": user.get("favorite_count", 0),
                    "create_time": user.get("create_time"),
                    "update_time": user.get("update_time"),
                    "status": user.get("status", 1)
                }
                user_results.append(user_result)
            
            # 如果是按相关度排序，对结果进行排序
            if sort_by == "relevance":
                user_results.sort(key=lambda x: x.get("relevance", 0), reverse=True)
            
            search_results.extend(user_results)
            user_total = count_results_map["user"][0]['total'] if count_results_map["user"] else 0
            total += user_total
        
        # 如果是按相关度排序，需要对所有结果再次排序
        if sort_by == "relevance" and len(search_results) > 0:
            search_results.sort(key=lambda x: x.get("relevance", 0), reverse=True)
            # 页面分割
            start_idx = (page - 1) * page_size
            end_idx = min(start_idx + page_size, len(search_results))
            search_results = search_results[start_idx:end_idx]
        
        # 异步记录搜索历史
        # 暂时不记录搜索历史，因为没有传入openid参数
        # asyncio.create_task(_record_search_history(query, openid))
        
        # 计算分页
        pagination = {
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size if page_size > 0 else 1
        }
        
        return Response.paged(
            data=search_results,
            pagination=pagination,
            details={"query": query, "search_type": search_type, "sort_by": sort_by}
        )
    except Exception as e:
        logger.error(f"搜索失败: {str(e)}")
        return Response.error(details={"message": f"搜索失败: {str(e)}"})

@router.get("/history", summary="获取当前用户搜索历史")
async def get_search_history(
    page_size: int = Query(10, description="返回结果数量"),
    current_user: Dict[str, Any] = Depends(get_current_active_user) # 严格依赖
):
    user_id = current_user.get("id")
    if not user_id:
        return Response.error(message="无法获取用户信息")
    
    # 基于user_id查询
    sql = "SELECT query FROM wxapp_search_history WHERE user_id = %s ORDER BY search_time DESC LIMIT %s"
    results = await db_core.execute_custom_query(sql, [user_id, page_size])
    
    # 提取查询字符串列表
    history_list = [row['query'] for row in results] if results else []
    return Response.success(data=history_list)

@router.post("/history/clear", summary="清空当前用户搜索历史")
async def clear_search_history(
    current_user: Dict[str, Any] = Depends(get_current_active_user) # 严格依赖
):
    user_id = current_user.get("id")
    if not user_id:
        return Response.error(message="无法获取用户信息")
        
    # 基于user_id删除
    sql = "DELETE FROM wxapp_search_history WHERE user_id = %s"
    await db_core.execute_custom_query(sql, [user_id], fetch='none')

    return Response.success(message="搜索历史已清空")

@router.get("/hot", summary="获取热门搜索")
async def get_hot_searches(
    page_size: int = Query(10, description="返回结果数量"),
    days: int = Query(7, description="查询最近N天的数据")
):
    """获取热门搜索词条（公开接口）"""
    try:
        # noinspection SqlNoDataSourceInspection
        hot_sql = """
        SELECT query as search_query, COUNT(*) as search_count
        FROM wxapp_search_history
        WHERE search_time >= CURDATE() - INTERVAL %s DAY
        GROUP BY query
        ORDER BY search_count DESC
        LIMIT %s
        """
        # 确保异步调用
        hot_searches = await db_core.execute_custom_query(hot_sql, [days, page_size], fetch='all')
        return Response.success(data=hot_searches or [])
    except Exception as e:
        logger.error(f"获取热门搜索失败: {e}")
        return Response.error(message="获取热门搜索失败")
        return Response.error(details={"message": f"获取热门搜索失败: {str(e)}"})

@router.get("/snapshot")
async def get_snapshot(url: str = Query(..., description="要获取快照的原始URL")):
    """
    获取指定URL的网页快照
    """
    try:
        # 计算URL的MD5哈希
        url_hash = hashlib.md5(url.encode()).hexdigest()
        
        # 构建快照文件路径
        snapshots_dir = Path(Config().get('etl.data.storage.base_path', '/data') + '/raw/website/snapshots')
        snapshot_path = snapshots_dir / f"{url_hash}.html"
        
        if snapshot_path.exists():
            # 读取并返回快照内容
            content = snapshot_path.read_text(encoding='utf-8')
            return Response.success(data={"url": url, "content": content})
        else:
            return Response.error(message="未能找到对应URL的网页快照", code=404)
            
    except Exception as e:
        logger.error(f"获取快照失败: {str(e)}")
        return Response.error(message="服务器内部错误，无法获取快照", code=500)

@router.get("/recommend", summary="获取热门和最新帖子")
async def recommend_endpoint(
    limit: int = Query(20, description="每类帖子的数量限制"),
    hot_weight: float = Query(0.7, description="热度权重"),
    new_weight: float = Query(0.3, description="新度权重"),
    enable_ai_recommendation: bool = Query(True, description="是否启用AI智能推荐"),
    user_id: str = Query(None, description="用户ID，用于个性化AI推荐"),
    days: int = Query(7, description="查询最近N天的数据")
):
    """
    获取热门和最新帖子

    从多个平台（wxapp_post, wechat_nku, website_nku, market_nku）获取：
    - 最热帖子：基于点赞、评论、收藏、浏览量计算热度分数
    - 最新帖子：最近7天内发布的帖子
    - 综合推荐：结合热度和时间的综合推荐
    - AI智能推荐：基于用户行为和内容分析的个性化推荐
    """
    try:
        result = await get_recommend_data(limit, hot_weight, new_weight, enable_ai_recommendation, user_id, days)
        return Response.success(data=result)
    except Exception as e:
        logger.error(f"获取热门和最新帖子失败: {str(e)}", exc_info=True)
        return Response.error(message="获取热门和最新帖子失败", code=500)


async def get_recommend_data(
    limit: int = 50,
    hot_weight: float = 0.7,
    new_weight: float = 0.3,
    enable_ai_recommendation: bool = True,
    user_id: str = None,
    days: int = 7
) -> Dict[str, Any]:
    """
    从数据库中获取最新和最热的帖子数据

    Args:
        limit: 返回结果数量限制，默认20
        hot_weight: 热度权重，默认0.7
        new_weight: 新度权重，默认0.3
        enable_ai_recommendation: 是否启用AI智能推荐，默认启用
        user_id: 用户ID，用于个性化AI推荐
        days: 查询最近N天的数据，默认7天

    Returns:
        包含热门和最新帖子的字典
    """
    try:
        async with get_db_connection() as connection:
            async with connection.cursor() as cursor:
                # 获取最近7天的时间
                seven_days_ago = datetime.now() - timedelta(days=days)

                # 1. 获取 wechat_nku 热门文章（基于点赞和浏览）
                wechat_hot_query = """
                SELECT 
                    id, title, content, author, original_url,
                    view_count, like_count, publish_time, update_time, 'wechat' as platform,
                    ((like_count * 5 + view_count * 1) / 6.0) as hot_score,
                    is_official
                FROM wechat_nku 
                ORDER BY hot_score DESC, publish_time DESC
                LIMIT %s
                """
                await cursor.execute(wechat_hot_query, (limit,))
                wechat_hot_data = await cursor.fetchall()

                # 2. 获取 wechat_nku 最新文章（最近7天内，仅按时间排序）
                wechat_new_query = """
                SELECT 
                    id, title, content, author, original_url,
                    view_count, publish_time, update_time, 'wechat' as platform,
                    0 as hot_score,
                    is_official
                FROM wechat_nku 
                WHERE publish_time >= %s
                ORDER BY publish_time DESC
                LIMIT %s
                """
                await cursor.execute(wechat_new_query, (seven_days_ago, limit))
                wechat_new_data = await cursor.fetchall()

                # 3. 获取 website_nku 热门内容（基于浏览量）
                website_hot_query = """
                SELECT 
                    id, title, content, author, original_url,
                    view_count, publish_time, update_time, 'website' as platform,
                    view_count as hot_score,
                    is_official
                FROM website_nku 
                ORDER BY hot_score DESC, publish_time DESC
                LIMIT %s
                """
                await cursor.execute(website_hot_query, (limit,))
                website_hot_data = await cursor.fetchall()

                # 4. 获取 website_nku 最新内容（仅按时间排序）
                website_new_query = """
                SELECT 
                    id, title, content, author, original_url,
                    view_count, publish_time, update_time, 'website' as platform,
                    0 as hot_score,
                    is_official
                FROM website_nku 
                WHERE publish_time >= %s
                ORDER BY publish_time DESC
                LIMIT %s
                """
                await cursor.execute(website_new_query, (seven_days_ago, limit))
                website_new_data = await cursor.fetchall()

                # 5. 获取 market_nku 热门内容（基于点赞、评论、浏览）
                market_hot_query = """
                SELECT 
                    id, title, content, author, original_url, category,
                    view_count, like_count, comment_count, publish_time, update_time, 'market' as platform,
                    ((like_count * 4 + comment_count * 3 + view_count * 1) / 8.0) as hot_score
                FROM market_nku 
                WHERE status = 1
                ORDER BY hot_score DESC, publish_time DESC
                LIMIT %s
                """
                await cursor.execute(market_hot_query, (limit,))
                market_hot_data = await cursor.fetchall()

                # 6. 获取 market_nku 最新内容（仅按时间排序）
                market_new_query = """
                SELECT 
                    id, title, content, author, original_url, category,
                    view_count, like_count, comment_count, publish_time, update_time, 'market' as platform,
                    0 as hot_score
                FROM market_nku 
                WHERE status = 1 AND publish_time >= %s
                ORDER BY publish_time DESC
                LIMIT %s
                """
                await cursor.execute(market_new_query, (seven_days_ago, limit))
                market_new_data = await cursor.fetchall()

                # 7. 获取 wxapp_post 热门帖子（基于综合热度分数）
                wxapp_hot_query = """
                SELECT 
                    id, title, content, user_id, nickname, avatar,
                    view_count, like_count, comment_count, favorite_count,
                    create_time, update_time, 'wxapp' as platform,
                    ((like_count * 4 + comment_count * 3 + favorite_count * 2 + view_count * 1) / 10.0) as hot_score
                FROM wxapp_post 
                WHERE status = 1 AND is_deleted = 0
                ORDER BY hot_score DESC, create_time DESC
                LIMIT %s
                """
                await cursor.execute(wxapp_hot_query, (limit,))
                wxapp_hot_data = await cursor.fetchall()

                # 8. 获取 wxapp_post 最新帖子（最近7天内，仅按时间排序）
                wxapp_new_query = """
                SELECT 
                    id, title, content, user_id, nickname, avatar,
                    view_count, like_count, comment_count, favorite_count,
                    create_time, update_time, 'wxapp' as platform,
                    0 as hot_score
                FROM wxapp_post 
                WHERE status = 1 AND is_deleted = 0 AND create_time >= %s
                ORDER BY create_time DESC
                LIMIT %s
                """
                await cursor.execute(wxapp_new_query, (seven_days_ago, limit))
                wxapp_new_data = await cursor.fetchall()

                # 处理查询结果
                def format_post_data(row, platform: str) -> Dict[str, Any]:
                    """格式化帖子数据"""
                    def safe_float(value, default=0.0):
                        """安全地转换为float，处理异常情况"""
                        try:
                            if value is None:
                                return default
                            return float(value)
                        except (ValueError, TypeError):
                            return default

                    if platform == "wechat":
                        # wechat字段: id, title, content, author, original_url, view_count, publish_time, update_time, platform, hot_score, is_official
                        return {
                            "id": row[0],
                            "title": row[1],
                            "content": row[2][:200] + "..." if len(row[2]) > 200 else row[2],
                            "author": row[3],
                            "platform": platform,
                            "view_count": row[5],
                            "like_count": row[6] if len(row) > 6 and platform != "wechat_new" else 0,  # 新文章查询中没有like_count
                            "create_time": str(row[6]) if row[6] else "",  # publish_time for wechat_new
                            "update_time": str(row[7]) if row[7] else "",
                            "hot_score": safe_float(row[9]),
                            "is_truncated": len(row[2]) > 200,
                            "original_url": row[4],
                            "is_official": bool(row[10])
                        }
                    elif platform == "website":
                        # website字段: id, title, content, author, original_url, view_count, publish_time, update_time, platform, hot_score, is_official
                        return {
                            "id": row[0],
                            "title": row[1],
                            "content": row[2][:200] + "..." if len(row[2]) > 200 else row[2],
                            "author": row[3],
                            "platform": platform,
                            "view_count": row[5],
                            "pagerank_score": 0.0,  # 新查询中没有pagerank_score
                            "create_time": str(row[6]) if row[6] else "",  # publish_time
                            "update_time": str(row[7]) if row[7] else "",
                            "hot_score": safe_float(row[9]),
                            "is_truncated": len(row[2]) > 200,
                            "original_url": row[4],
                            "is_official": bool(row[10])
                        }
                    elif platform == "market":
                        # market字段: id, title, content, author, original_url, category, view_count, like_count, comment_count, publish_time, update_time, platform, hot_score
                        return {
                            "id": row[0],
                            "title": row[1],
                            "content": row[2][:200] + "..." if len(row[2]) > 200 else row[2],
                            "author": row[3],
                            "platform": platform,
                            "category": row[5],
                            "view_count": row[6],
                            "like_count": row[7],
                            "comment_count": row[8],
                            "create_time": str(row[9]) if row[9] else "",  # publish_time
                            "update_time": str(row[10]) if row[10] else "",
                            "hot_score": safe_float(row[12]),
                            "is_truncated": len(row[2]) > 200,
                            "original_url": row[4]
                        }
                    elif platform == "wxapp":
                        # wxapp字段: id, title, content, user_id, nickname, avatar, view_count, like_count, comment_count, favorite_count, create_time, update_time, platform, hot_score
                        return {
                            "id": row[0],
                            "title": row[1],
                            "content": row[2][:200] + "..." if len(row[2]) > 200 else row[2],
                            "author": row[4] or "匿名用户",  # nickname
                            "avatar": row[5] or "",
                            "platform": platform,
                            "view_count": row[6],
                            "like_count": row[7],
                            "comment_count": row[8],
                            "favorite_count": row[9],
                            "create_time": str(row[10]) if row[10] else "",
                            "update_time": str(row[11]) if row[11] else "",
                            "hot_score": safe_float(row[13]),
                            "is_truncated": len(row[2]) > 200,
                            "original_url": f"wxapp://post/{row[0]}"
                        }

                # 整理热门内容
                hot_posts = []
                for platform, data in [
                    ("wechat", wechat_hot_data),
                    ("website", website_hot_data),
                    ("market", market_hot_data),
                    ("wxapp", wxapp_hot_data)
                ]:
                    for row in data:
                        hot_posts.append(format_post_data(row, platform))

                # 整理最新内容
                new_posts = []
                for platform, data in [
                    ("wechat", wechat_new_data),
                    ("website", website_new_data),
                    ("market", market_new_data),
                    ("wxapp", wxapp_new_data)
                ]:
                    for row in data:
                        new_posts.append(format_post_data(row, platform))

                # 按热度分数排序热门内容
                hot_posts.sort(key=lambda x: x.get("hot_score", 0), reverse=True)
                hot_posts = hot_posts[:limit]

                # 按时间排序最新内容
                new_posts.sort(key=lambda x: x.get("create_time", ""), reverse=True)
                new_posts = new_posts[:limit]

                # 生成综合推荐（结合热度和新度）
                all_posts = hot_posts + new_posts
                # 去重（基于ID和平台）
                seen = set()
                unique_posts = []
                for post in all_posts:
                    key = (post['id'], post['platform'])
                    if key not in seen:
                        seen.add(key)
                        unique_posts.append(post)

                # 计算综合分数
                for post in unique_posts:
                    hot_score = post.get("hot_score", 0)
                    create_time = post.get("create_time", "")
                    try:
                        if create_time:
                            post_time = datetime.fromisoformat(create_time.replace("T", " ").split(".")[0])
                            days_old = (datetime.now() - post_time).days
                            time_factor = 1.0 / (1.0 + days_old) * 100
                        else:
                            time_factor = 0
                    except:
                        time_factor = 0

                    post["combined_score"] = hot_score * hot_weight + time_factor * new_weight

                # 按综合分数排序
                recommended_posts = sorted(unique_posts, key=lambda x: x.get("combined_score", 0), reverse=True)[:limit]

                # AI智能推荐功能
                ai_recommended_posts = []
                if enable_ai_recommendation:
                    try:
                        ai_recommended_posts = await get_ai_recommended_posts(
                            hot_posts=hot_posts[:10],  # 传入前10个热门帖子作为候选
                            new_posts=new_posts[:10],  # 传入前10个最新帖子作为候选
                            user_id=user_id,
                            limit=min(limit, 10)  # AI推荐数量限制
                        )
                        logger.info(f"AI智能推荐成功获取{len(ai_recommended_posts)}条帖子")
                    except Exception as e:
                        logger.error(f"AI智能推荐失败: {str(e)}", exc_info=True)
                        # AI推荐失败时使用综合推荐作为备选
                        ai_recommended_posts = recommended_posts[:limit//2]

                logger.info(f"成功获取热门帖子{len(hot_posts)}条，最新帖子{len(new_posts)}条，推荐帖子{len(recommended_posts)}条，AI推荐{len(ai_recommended_posts)}条")

                return {
                    "hot_posts": hot_posts,
                    "new_posts": new_posts,
                    "recommended_posts": recommended_posts,
                    "ai_recommended_posts": ai_recommended_posts,
                    "total_count": {
                        "hot": len(hot_posts),
                        "new": len(new_posts),
                        "recommended": len(recommended_posts),
                        "ai_recommended": len(ai_recommended_posts)
                    },
                    "summary": {
                        "platforms": ["wechat", "website", "market", "wxapp"],
                        "hot_weight": hot_weight,
                        "new_weight": new_weight,
                        "limit_per_category": limit,
                        "ai_recommendation_enabled": enable_ai_recommendation,
                        "description": "包含微信公众号、南开网站、校园集市、小程序帖子数据，支持AI智能推荐"
                    }
                }

    except Exception as e:
        logger.error(f"获取热门和最新帖子失败: {str(e)}", exc_info=True)
        return {
            "hot_posts": [],
            "new_posts": [],
            "recommended_posts": [],
            "error": str(e),
            "total_count": {
                "hot": 0,
                "new": 0,
                "recommended": 0
            }
        }


async def get_ai_recommended_posts(
    hot_posts: List[Dict[str, Any]],
    new_posts: List[Dict[str, Any]],
    user_id: str = None,
    limit: int = 10
) -> List[Dict[str, Any]]:
    """
    使用AI智能体获取个性化推荐帖子

    Args:
        hot_posts: 热门帖子列表（作为参考）
        new_posts: 最新帖子列表（作为参考）
        user_id: 用户ID，用于个性化推荐
        limit: 返回结果数量限制

    Returns:
        AI推荐的帖子列表
    """
    try:
        # 导入agent
        from core.agent.coze.coze_agent import CozeAgent
        import json
        import time

        # 获取用户画像
        user_profile = await get_user_preference_profile(user_id) if user_id else {}

        # 使用AI决定候选帖子池的获取策略
        strategy_prompt = f"""
作为一个智能推荐系统，请为用户制定获取候选帖子池的策略。

用户信息：
- 用户ID: {user_id or "匿名用户"}
- 历史偏好: {user_profile.get('preferences', '暂无数据')}
- 活跃领域: {user_profile.get('active_areas', '通用')}
- 兴趣标签: {user_profile.get('interest_tags', [])}

当前可用数据源：
1. 热门帖子 (热度较高的内容)
2. 最新帖子 (时效性强的内容)
3. 微信公众号文章 (platform = 'wechat')
4. 南开网站内容 (platform = 'nku_website')
5. 校园集市帖子 (platform = 'market')
6. 小程序帖子 (platform = 'wxapp')

请返回一个获取候选帖子的策略，包含：
1. 主要数据源选择
2. 搜索关键词（基于用户偏好）
3. 筛选条件
4. 候选池大小建议

返回JSON格式：
{{
    "primary_sources": ["数据源1", "数据源2"],
    "search_keywords": ["关键词1", "关键词2"],
    "filter_conditions": {{
        "min_hot_score": 数值,
        "platforms": ["平台1", "平台2"],
        "categories": ["分类1", "分类2"]
    }},
    "candidate_pool_size": 数值,
    "reasoning": "策略说明"
}}
"""

        # 创建CozeAgent实例获取策略
        agent = CozeAgent('answerGenerate')
        from core.bridge.context import Context, ContextType

        strategy_context = Context()
        strategy_context.type = ContextType.TEXT
        strategy_context["session_id"] = f"strategy_{user_id or 'anonymous'}_{int(time.time())}"
        strategy_context["format"] = "text"

        logger.info("使用AI制定候选帖子池获取策略")
        strategy_response = agent.reply(strategy_prompt, strategy_context)

        # 解析AI策略
        strategy = None
        if strategy_response.type == ReplyType.TEXT and strategy_response.content:
            try:
                response_text = strategy_response.content.strip()
                json_start = response_text.find('{')
                json_end = response_text.rfind('}') + 1

                if json_start != -1 and json_end > json_start:
                    json_text = response_text[json_start:json_end]
                    strategy = json.loads(json_text)
                    logger.info(f"AI策略解析成功: {strategy.get('reasoning', '无说明')}")
            except json.JSONDecodeError as e:
                logger.warning(f"解析AI策略失败: {str(e)}")

        # 如果AI策略解析失败，使用默认策略
        if not strategy:
            strategy = {
                "primary_sources": ["hot", "new", "search"],
                "search_keywords": user_profile.get('interest_tags', [])[:3],
                "filter_conditions": {
                    "min_hot_score": 0.1,
                    "platforms": ["wechat", "nku_website", "wxapp"],
                    "categories": []
                },
                "candidate_pool_size": 50,
                "reasoning": "使用默认推荐策略"
            }

        # 根据AI策略获取候选帖子池
        candidate_posts = []

        logger.info(f"开始构建候选池 - 热门帖子: {len(hot_posts)}, 最新帖子: {len(new_posts)}")
        logger.info(f"AI策略数据源: {strategy.get('primary_sources', [])}")

        # 1. 从热门帖子中添加（不筛选）
        if "hot" in strategy.get("primary_sources", []):
            for post in hot_posts:
                candidate_posts.append(_format_candidate_post(post))
            logger.info(f"从热门帖子添加了 {len(hot_posts)} 个候选")

        # 2. 从最新帖子中添加（不筛选）
        if "new" in strategy.get("primary_sources", []):
            for post in new_posts:
                candidate_posts.append(_format_candidate_post(post))
            logger.info(f"从最新帖子添加了 {len(new_posts)} 个候选")

        # 3. 基于关键词搜索额外候选
        if "search" in strategy.get("primary_sources", []) and strategy.get("search_keywords"):
            search_candidates = await _search_posts_by_ai_strategy(
                keywords=strategy["search_keywords"],
                filter_conditions=strategy["filter_conditions"],
                limit=strategy.get("candidate_pool_size", 50) // 2
            )
            candidate_posts.extend(search_candidates)
            logger.info(f"通过关键词搜索添加了 {len(search_candidates)} 个候选")

        logger.info(f"候选池构建完成，总候选数: {len(candidate_posts)}")

        # 去重候选帖子
        seen_posts = set()
        unique_candidates = []
        for post in candidate_posts:
            key = (post["id"], post["platform"])
            if key not in seen_posts:
                seen_posts.add(key)
                unique_candidates.append(post)

        logger.info(f"去重后候选数: {len(unique_candidates)}")

        # 限制候选池大小
        max_candidates = strategy.get("candidate_pool_size", 50)  # 使用50作为默认值
        unique_candidates = unique_candidates[:max_candidates]

        # 如果候选池为空，尝试补救措施
        if not unique_candidates:
            logger.warning("AI策略未能获取到有效的候选帖子，尝试补救措施")
            
            # 补救措施1: 如果传入的帖子列表不为空，直接使用它们
            if hot_posts or new_posts:
                logger.info("使用传入的热门和最新帖子作为候选")
                fallback_candidates = []
                for post in (hot_posts + new_posts)[:max_candidates]:
                    fallback_candidates.append(_format_candidate_post(post))
                
                if fallback_candidates:
                    unique_candidates = fallback_candidates
                    logger.info(f"补救成功，获得 {len(unique_candidates)} 个候选帖子")
            
            # 如果仍然为空，返回降级推荐
            if not unique_candidates:
                logger.error("补救措施失败，使用降级推荐策略")
                return _fallback_recommendation(hot_posts + new_posts, limit, hot_posts, new_posts)

        # 如果候选池仍然为空，记录警告并返回空结果
        if not unique_candidates:
            logger.warning("候选池为空，无法提供推荐")
            return {
                "hot_posts": [],
                "new_posts": [],
                "recommended_posts": [],
                "ai_recommended_posts": [],
                "total_count": {
                    "hot": 0,
                    "new": 0,
                    "recommended": 0,
                    "ai_recommended": 0
                },
                "summary": {
                    "platforms": ["wechat", "website", "market", "wxapp"],
                    "hot_weight": hot_weight,
                    "new_weight": new_weight,
                    "limit_per_category": limit,
                    "ai_recommendation_enabled": enable_ai_recommendation,
                    "description": "包含微信公众号、南开网站、校园集市、小程序帖子数据，支持AI智能推荐"
                }
            }

        logger.info(f"候选池准备就绪，包含 {len(unique_candidates)} 个帖子")

        # 构建AI推荐请求的prompt
        recommendation_prompt = f"""
作为一个智能推荐系统，请基于以下信息为用户推荐最相关的帖子：

用户画像：
- 用户ID: {user_id or "匿名用户"}
- 历史偏好: {user_profile.get('preferences', '暂无数据')}
- 活跃领域: {user_profile.get('active_areas', '通用')}
- 兴趣标签: {user_profile.get('interest_tags', [])}

获取策略说明: {strategy.get('reasoning', '智能策略')}

候选帖子池（共{len(unique_candidates)}个）：
"""

        # 添加候选帖子信息
        for i, post in enumerate(unique_candidates[:20], 1):  # 最多显示前20个候选
            recommendation_prompt += f"""
{i}. 【{post['platform'].upper()}】{post['title']}
   作者: {post['author']} | 热度: {post['hot_score']:.1f}
   内容摘要: {post['content'][:50]}...
   分类: {post.get('category', '未分类')}
"""

        recommendation_prompt += f"""

请从以上候选帖子中选择最适合该用户的{min(limit, len(unique_candidates))}个帖子进行推荐。

要求：
1. 考虑用户的历史偏好和活跃领域
2. 结合获取策略的考量因素
3. 平衡热门度和内容质量
4. 优先推荐多样化的内容（不同平台、不同主题）
5. 返回格式为JSON数组，包含推荐帖子的编号和推荐理由
6. 必须给出推荐结果！！！

返回格式示例：
[
    {{"post_number": 1, "reason": "推荐理由"}},
    {{"post_number": 3, "reason": "推荐理由"}}
]
"""

        # 调用AI智能体进行推荐
        logger.info(f"调用AI智能体进行个性化推荐，候选帖子数：{len(unique_candidates)}")

        recommendation_context = Context()
        recommendation_context.type = ContextType.TEXT
        recommendation_context["session_id"] = f"recommendation_{user_id or 'anonymous'}_{int(time.time())}"
        recommendation_context["format"] = "text"

        ai_response = agent.reply(recommendation_prompt, recommendation_context)

        logger.info(ai_response)

        if ai_response.type != ReplyType.TEXT or not ai_response.content:
            logger.warning("AI智能体返回了无效的推荐结果")
            return _fallback_recommendation(unique_candidates, limit, hot_posts, new_posts)

        # 解析AI推荐结果
        recommended_posts = []
        try:
            # 尝试从AI回复中提取JSON
            response_text = ai_response.content.strip()

            # 查找JSON部分
            json_start = response_text.find('[')
            json_end = response_text.rfind(']') + 1

            if json_start != -1 and json_end > json_start:
                json_text = response_text[json_start:json_end]
                ai_recommendations = json.loads(json_text)

                for rec in ai_recommendations:
                    post_number = rec.get("post_number")
                    reason = rec.get("reason", "AI推荐")

                    if isinstance(post_number, int) and 1 <= post_number <= len(unique_candidates):
                        # 获取候选帖子数据
                        candidate_post = unique_candidates[post_number - 1]

                        # 从原始帖子列表中找到完整数据
                        full_post = None
                        for post in hot_posts + new_posts:
                            if (post.get("id") == candidate_post["id"] and
                                post.get("platform") == candidate_post["platform"]):
                                full_post = post.copy()
                                break

                        # 如果在原始列表中没找到，使用候选帖子数据
                        if not full_post:
                            full_post = candidate_post.copy()

                        full_post["ai_recommendation_reason"] = reason
                        full_post["ai_score"] = len(ai_recommendations) - len(recommended_posts)
                        full_post["ai_strategy"] = strategy.get('reasoning', '智能策略')
                        recommended_posts.append(full_post)

                        if len(recommended_posts) >= limit:
                            break

            else:
                logger.warning("AI回复中未找到有效的JSON格式推荐结果")
                return _fallback_recommendation(unique_candidates, limit, hot_posts, new_posts)

        except json.JSONDecodeError as e:
            logger.warning(f"解析AI推荐结果JSON失败: {str(e)}")
            return _fallback_recommendation(unique_candidates, limit, hot_posts, new_posts)

        logger.info(f"AI智能推荐成功解析{len(recommended_posts)}条推荐结果")
        return recommended_posts

    except Exception as e:
        logger.error(f"AI智能推荐失败: {str(e)}", exc_info=True)
        # 降级到基于规则的推荐
        return _fallback_recommendation(hot_posts + new_posts, limit, hot_posts, new_posts)

def _meets_filter_criteria(post: Dict[str, Any], filter_conditions: Dict[str, Any]) -> bool:
    """
    检查帖子是否满足筛选条件

    Args:
        post: 帖子数据
        filter_conditions: 筛选条件

    Returns:
        bool: 是否满足条件
    """
    try:
        # 检查最小热度分数
        min_hot_score = filter_conditions.get("min_hot_score", 0)
        if post.get("hot_score", 0) < min_hot_score:
            return False

        # 检查平台限制
        allowed_platforms = filter_conditions.get("platforms", [])
        if allowed_platforms and post.get("platform", "") not in allowed_platforms:
            return False

        # 检查分类限制
        allowed_categories = filter_conditions.get("categories", [])
        if allowed_categories and post.get("category", "") not in allowed_categories:
            return False

        return True
    except Exception as e:
        logger.warning(f"检查筛选条件失败: {str(e)}")
        return True  # 默认通过


def _format_candidate_post(post: Dict[str, Any]) -> Dict[str, Any]:
    """
    格式化候选帖子数据

    Args:
        post: 原始帖子数据

    Returns:
        格式化后的帖子数据
    """
    return {
        "id": post.get("id"),
        "title": post.get("title", ""),
        "content": post.get("content", "")[:300],  # 截断内容以节省token
        "platform": post.get("platform", ""),
        "author": post.get("author", ""),
        "hot_score": post.get("hot_score", 0),
        "category": post.get("category", ""),
        "create_time": post.get("create_time", ""),
        "update_time": post.get("update_time", "")
    }


async def _search_posts_by_ai_strategy(
    keywords: List[str],
    filter_conditions: Dict[str, Any],
    limit: int = 25
) -> List[Dict[str, Any]]:
    """
    根据AI策略中的关键词搜索帖子

    Args:
        keywords: 搜索关键词列表
        filter_conditions: 筛选条件
        limit: 返回结果数量限制

    Returns:
        搜索到的帖子列表
    """
    try:
        if not keywords:
            return []

        # 构建搜索查询
        search_query = " ".join(keywords[:3])  # 最多使用前3个关键词

        logger.info(f"基于AI策略搜索帖子: 关键词={search_query}, 限制={limit}")

        # 使用现有的搜索功能
        search_result = await search_knowledge(
            query=search_query,
            current_user=None,
            platform=",".join(filter_conditions.get("platforms", ["wechat", "website", "market", "wxapp"])),
            max_results=limit,
            page=1,
            page_size=limit,
            sort_by="relevance"
        )

        candidates = []
        for post in search_result.get("data", []):
            if _meets_filter_criteria(post, filter_conditions):
                candidates.append(_format_candidate_post(post))

        logger.info(f"AI策略搜索获得{len(candidates)}个候选帖子")
        return candidates

    except Exception as e:
        logger.error(f"基于AI策略搜索帖子失败: {str(e)}")
        return []


async def get_user_preference_profile(user_id: str) -> Dict[str, Any]:
    """
    获取用户偏好画像

    Args:
        user_id: 用户ID

    Returns:
        用户偏好数据
    """
    try:
        if not user_id:
            return {}

        # 查询用户最近的搜索历史
        search_history_sql = """
        SELECT query FROM wxapp_search_history 
        WHERE user_id = %s 
        ORDER BY search_time DESC 
        LIMIT 20
        """
        search_history = await db_core.execute_custom_query(search_history_sql, [user_id], fetch='all')

        # 查询用户最近的互动记录（点赞、收藏等）
        interaction_sql = """
        SELECT p.title, p.content, p.category_id 
        FROM wxapp_post p
        JOIN wxapp_like l ON p.id = l.post_id
        WHERE l.user_id = %s AND l.status = 1
        ORDER BY l.create_time DESC
        LIMIT 10
        """
        liked_posts = await db_core.execute_custom_query(interaction_sql, [user_id], fetch='all')

        # 提取兴趣标签
        interest_tags = []
        preferences = []

        # 从搜索历史中提取关键词
        for record in search_history:
            query = record.get('query', '')
            if query and len(query) > 1:
                # 简单的关键词提取
                words = jieba.analyse.extract_tags(query, topK=3)
                interest_tags.extend(words)
                preferences.append(query)

        # 从点赞帖子中提取标签
        for post in liked_posts:
            title = post.get('title', '')
            if title:
                words = jieba.analyse.extract_tags(title, topK=2)
                interest_tags.extend(words)

        # 去重并限制数量
        interest_tags = list(dict.fromkeys(interest_tags))[:10]
        preferences = list(dict.fromkeys(preferences))[:5]

        # 确定活跃领域
        active_areas = ["通用"]
        if any(tag in ["学习", "课程", "考试", "作业"] for tag in interest_tags):
            active_areas.append("学习")
        if any(tag in ["社团", "活动", "聚会"] for tag in interest_tags):
            active_areas.append("社交")
        if any(tag in ["二手", "商品", "买卖"] for tag in interest_tags):
            active_areas.append("交易")

        profile = {
            "preferences": preferences,
            "interest_tags": interest_tags,
            "active_areas": active_areas,
            "interaction_count": len(liked_posts),
            "search_activity": len(search_history)
        }

        logger.debug(f"用户{user_id}偏好画像: {profile}")
        return profile

    except Exception as e:
        logger.error(f"获取用户偏好画像失败: {str(e)}")
        return {}


def _fallback_recommendation(
    all_posts: List[Dict[str, Any]],
    limit: int,
    hot_posts: List[Dict[str, Any]],
    new_posts: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    降级推荐策略，当AI推荐失败时使用

    Args:
        all_posts: 所有候选帖子
        limit: 返回结果数量限制
        hot_posts: 热门帖子列表
        new_posts: 最新帖子列表

    Returns:
        推荐帖子列表
    """
    try:
        # 简单的基于规则的推荐：热门帖子 + 最新帖子的混合
        recommendations = []

        # 取一半热门帖子
        hot_count = min(limit // 2, len(hot_posts))
        recommendations.extend(hot_posts[:hot_count])

        # 取一半最新帖子
        new_count = min(limit - hot_count, len(new_posts))
        recommendations.extend(new_posts[:new_count])

        # 如果还不够，从剩余帖子中补充
        if len(recommendations) < limit:
            remaining = limit - len(recommendations)
            seen_ids = {(p.get('id'), p.get('platform')) for p in recommendations}

            for post in all_posts:
                if len(recommendations) >= limit:
                    break
                key = (post.get('id'), post.get('platform'))
                if key not in seen_ids:
                    recommendations.append(post)
                    seen_ids.add(key)

        # 为降级推荐添加标识
        for post in recommendations:
            post["ai_recommendation_reason"] = "基于热度和时间的规则推荐"
            post["ai_score"] = post.get("hot_score", 0)
            post["ai_strategy"] = "降级推荐策略"

        logger.info(f"使用降级推荐策略，返回{len(recommendations)}条推荐")
        return recommendations[:limit]

    except Exception as e:
        logger.error(f"降级推荐策略失败: {str(e)}")
        return []
