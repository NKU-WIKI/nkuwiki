import time
import json
from typing import Dict, Any, Optional, List
import asyncio
from datetime import datetime
import re
import hashlib
from pathlib import Path

from elasticsearch import AsyncElasticsearch
from fastapi import Query, APIRouter, Body, HTTPException
from pydantic import BaseModel, Field
import jieba.analyse

from api.models.common import Response, Request, validate_params, PaginationInfo
from config import Config
from core.utils.logger import register_logger
from etl.load import (
    query_records, 
    insert_record, 
    update_record, 
    execute_custom_query, 
    count_records,
    get_by_id
)
from etl import ES_INDEX_NAME
from etl.rag.pipeline import RagPipeline
from etl.rag.strategies import RetrievalStrategy, RerankStrategy
from api.routes.wxapp._utils import batch_enrich_posts_with_user_info
from etl.utils.const import official_author as OFFICIAL_AUTHORS_WHITELIST

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
    openid: str,
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
        
        search_task = query_records(
            table_name=table,
            conditions={"where_condition": where_condition, "params": sql_params},
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
        # 使用通用函数批量补充用户信息，并传入openid
        enriched_posts = await batch_enrich_posts_with_user_info(wxapp_post_items, openid)
        
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
    asyncio.create_task(_record_search_history(query, openid))
    
    return {
        "data": sources,
        "pagination": pagination
    }

@router.get("/search")
async def search_endpoint(
    query: str = Query(..., description="搜索关键词"),
    openid: str = Query(..., description="用户openid"),
    platform: Optional[str] = Query("wechat,website,market,wxapp", description="平台标识(wechat,website,market,wxapp)，多个用逗号分隔"),
    tag: Optional[str] = Query(None, description="标签，多个用逗号分隔"),
    max_results: int = Query(10, description="单表最大结果数"),
    page: int = Query(1, description="分页页码"),
    page_size: int = Query(10, description="每页结果数"),
    sort_by: str = Query("relevance", description="排序方式：relevance-相关度，time-时间"),
    max_content_length: int = Query(500, description="单条内容最大长度，超过将被截断")
):
    """多表综合检索接口
    
    参数说明：
    - query: 搜索关键词，必填
    - openid: 用户openid，必填
    - platform: 平台标识，可选值：wechat/website/market/wxapp，多个用逗号分隔
    - tag: 标签，多个用逗号分隔
    - max_results: 单表最大结果数，默认10
    - page: 分页页码，默认1
    - page_size: 每页结果数，默认10
    - sort_by: 排序方式，可选值：relevance(相关度)/time(时间)，默认relevance
    - max_content_length: 单条内容最大长度，默认500，超过将被截断
    
    返回格式：
    {
        "code": 200,
        "message": "success",
        "data": [
            {
                "create_time": "2025-04-07T16:13:49",
                "update_time": "2025-04-07T16:13:49",
                "author": "作者",
                "platform": "平台标识",
                "original_url": "原文链接",
                "tag": "标签",
                "title": "标题",
                "content": "内容",
                "relevance": 0.85
            }
        ],
        "pagination": {
            "total": 100,
            "page": 1,
            "page_size": 10,
            "total_pages": 10
        }
    }
    """
    try:
        start_time = time.time()

        if not query:
            return Response.bad_request(details={"message": "查询关键词不能为空"})
        
        # 调用内部搜索方法
        search_result = await search_knowledge(
            query=query,
            openid=openid,
            platform=platform,
            tag=tag,
            max_results=max_results,
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            max_content_length=max_content_length
        )
        
        total_time = time.time() - start_time
        logger.debug(f"综合检索完成: query={query}, 耗时={total_time:.2f}秒, 结果数={len(search_result['data'])}")
        
        return Response.paged(
            data=search_result["data"],
            pagination=search_result["pagination"],
            details={"message": "搜索成功", "query": query, "response_time": total_time}
        )
        
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        logger.error(f"综合检索失败: {str(e)}\n{error_detail}")
        return Response.error(message=f"搜索失败: {str(e)}")

@router.get("/advanced-search")
async def advanced_search_endpoint(
    query: str = Query(..., description="搜索关键词"),
    openid: str = Query(..., description="用户openid，用于个性化推荐"),
    top_k_retrieve: int = Query(20, description="召回文档数量，建议值[10, 50]"),
    top_k_rerank: int = Query(10, description="重排文档数量，建议值[5, 20]"),
    retrieval_strategy: RetrievalStrategy = Query(
        default=RetrievalStrategy.AUTO, 
        description="检索策略：auto-自动, hybrid-混合, vector_only-仅向量, bm25_only-仅BM25, es_only-仅ES"
    ),
    rerank_strategy: RerankStrategy = Query(
        default=RerankStrategy.BGE_RERANKER,
        description="重排策略：no_rerank-不重排, bge_reranker-BGE模型, st_reranker-SentenceTransformer, personalized-个性化"
    )
):
    """
    高级混合检索接口，调用RAG管道执行检索和重排序，不生成回答。
    
    返回经过重排序的文档列表，包含详细的元数据和相关度分数。
    """
    try:
        start_time = time.time()
        
        if not query:
            return Response.bad_request(details={"message": "查询关键词不能为空"})
        
        logger.debug(
            f"高级检索开始: query='{query}', openid='{openid}', "
            f"retrieval_strategy='{retrieval_strategy.value}', rerank_strategy='{rerank_strategy.value}'"
        )
        
        # 1. 初始化 RAG 管道
        rag_pipeline = RagPipeline()
        
        # 2. 执行仅检索和重排序
        # retrieve_only 内部会调用 run(..., skip_generation=True)
        results = rag_pipeline.retrieve_only(
            query=query,
            top_k_retrieve=top_k_retrieve,
            top_k_rerank=top_k_rerank,
            user_id=openid,
            retrieval_strategy=retrieval_strategy,
            rerank_strategy=rerank_strategy
        )
        
        # 3. 格式化返回结果
        reranked_nodes = results.get("reranked_nodes", [])
        contexts = []
        for node_with_score in reranked_nodes:
            node = node_with_score.node
            metadata = node.metadata or {}
            
            # 截断内容
            content = node.get_content()
            is_truncated = False
            max_content_length=500
            if len(content) > max_content_length:
                content = content[:max_content_length] + "..."
                is_truncated = True

            publish_time = metadata.get('publish_time', '')
            context = {
                "title": metadata.get('title', '无标题'),
                "content": content,
                "original_url": metadata.get('original_url', ''),
                "author": metadata.get('author', ''),
                "platform": metadata.get('platform', ''),
                "tag": metadata.get('tag', '') or "",
                "relevance": node_with_score.score,
                "create_time": str(publish_time) if publish_time else "",
                "update_time": str(publish_time) if publish_time else "",
                "is_truncated": is_truncated,
                "is_official": metadata.get('is_official', False),
                "view_count": metadata.get('view_count', 0),
                "like_count": metadata.get('like_count', 0),
                "comment_count": metadata.get('comment_count', 0),
                "pagerank_score": metadata.get('pagerank_score', 0.0)
            }
            contexts.append(context)
            
        total_time = time.time() - start_time
        logger.debug(f"高级检索完成: query='{query}', 耗时={total_time:.2f}秒, 返回结果数={len(contexts)}")
        
        # 4. 记录搜索历史
        asyncio.create_task(_record_search_history(query, openid))

        return Response.success(
            data=contexts,
            details={
                "message": "高级检索成功",
                "query": query,
                "retrieval_strategy": results.get("retrieval_strategy"),
                "rerank_strategy": results.get("rerank_strategy"),
                "documents_retrieved": len(results.get("retrieved_nodes", [])),
                "documents_reranked": len(contexts),
                "response_time": total_time
            }
        )

    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        logger.error(f"高级检索失败: {str(e)}\n{error_detail}")
        return Response.error(message=f"高级检索失败: {str(e)}", code=500)

async def _elasticsearch_search_internal(
    query: str,
    enhanced_query: str = None,
    platform: Optional[str] = None,
    size: int = 10,
    offset: int = 0,
    max_content_length: int = 300,
    openid: Optional[str] = None
) -> Dict[str, Any]:
    """使用Elasticsearch进行内部复合查询"""
    
    es_client = AsyncElasticsearch(
        [f"http://{Config().get('etl.data.elasticsearch.host')}:{Config().get('etl.data.elasticsearch.port')}"]
    )

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
        
        return response
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
    openid: str = Query(..., description="用户openid"),
    platform: Optional[str] = Query(None, description="平台筛选，多个用逗号分隔"),
    page: int = Query(1, description="分页页码"),
    page_size: int = Query(10, description="每页结果数"),
    max_content_length: int = Query(300, description="内容最大长度")
):
    """
    使用Elasticsearch进行检索，支持通配符和数据源筛选。
    """
    try:
        start_time = time.time()
        
        offset = (page - 1) * page_size
        response = await _elasticsearch_search_internal(
            query=query,
            platform=platform,
            size=page_size,
            offset=offset,
            max_content_length=max_content_length,
            openid=openid
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
        
        if openid:
            asyncio.create_task(_record_search_history(query, openid))
        
        return Response.paged(
            data=processed_results,
            pagination=pagination
        )

    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        logger.error(f"ES检索失败: {str(e)}\n{error_detail}")
        return Response.error(message=f"ES检索失败: {str(e)}", code=500)

async def _record_search_history(query: str, openid: str):
    """记录搜索历史"""
    try:
        # 检查是否已存在相同的搜索历史
        history_query = "SELECT id FROM wxapp_search_history WHERE query = %s AND openid = %s"
        existing_history = await execute_custom_query(history_query, [query, openid], fetch='one')

        if existing_history:
            # 更新时间戳
            update_query = "UPDATE wxapp_search_history SET search_time = CURRENT_TIMESTAMP WHERE id = %s"
            await execute_custom_query(update_query, [existing_history['id']], fetch=False)
        else:
            # 插入新记录
            insert_query = "INSERT INTO wxapp_search_history (query, openid) VALUES (%s, %s)"
            await execute_custom_query(insert_query, [query, openid], fetch=False)
            
    except Exception as e:
        logger.error(f"记录搜索历史失败: {str(e)}")

@router.get("/suggestion")
async def get_search_suggest(
    query: str = Query(..., description="搜索关键词"),
    openid: str = Query(..., description="用户openid"),
    page_size: int = Query(5, description="返回结果数量")
):
    """搜索建议"""
    try:
        logger.debug(f"获取搜索建议: query={query}")
        if not query.strip():
            return Response.success(data=[])
            
        # 从 search_history 表中获取搜索建议
        suggest_query = """
            SELECT query, COUNT(*) as count 
            FROM wxapp_search_history 
            WHERE query LIKE %s AND openid = %s
            GROUP BY query 
            ORDER BY count DESC 
            LIMIT %s
        """
        
        like_query = f"%{query}%"
        results = await execute_custom_query(suggest_query, [like_query, openid, page_size], fetch='all')
        
        # 提取建议词
        suggestions = [row['query'] for row in results]
        
        # 异步记录搜索历史
        if openid:
            asyncio.create_task(_record_search_history(query, openid))
            
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
                ("post", execute_custom_query(
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
                ("post", execute_custom_query(
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
                ("user", execute_custom_query(
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
                ("user", execute_custom_query(
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
                await batch_enrich_posts_with_user_info(post_results)
                
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

@router.get("/history")
async def get_search_history(
    openid: str = Query(..., description="用户OpenID"),
    page_size: int = Query(10, description="返回结果数量")
):
    """获取用户搜索历史"""
    try:
        # 确保调用异步函数时使用了await
        history_data = await query_records(
            "wxapp_search_history",
            conditions={"openid": openid},
            order_by={"search_time": "DESC"},
            limit=page_size
        )
        # 直接返回从数据库获取的数据
        return Response.success(data=history_data["data"])
    except Exception as e:
        logger.error(f"获取搜索历史失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取搜索历史失败: {str(e)}")

@router.post("/history/clear")
async def clear_search_history(request: Request):
    """清空用户搜索历史"""
    try:
        data = await request.json()
        openid = data.get("openid")
        
        if not openid:
            return Response.bad_request(details={"message": "缺少openid"})
            
        sql = "DELETE FROM wxapp_search_history WHERE openid = %s"
        await execute_custom_query(sql, (openid,), fetch=None) # 确保异步调用
        
        return Response.success(details={"message": "清空搜索历史成功"})
        
    except Exception as e:
        logger.error(f"清空搜索历史失败: {e}")
        return Response.error(details={"message": str(e)})

@router.get("/hot")
async def get_hot_searches(
    page_size: int = Query(10, description="返回结果数量")
):
    """获取热门搜索词条"""
    try:
        hot_sql = """
        SELECT query, COUNT(*) as search_count
        FROM wxapp_search_history
        GROUP BY query
        ORDER BY search_count DESC
        LIMIT %s
        """
        # 确保异步调用
        hot_searches = await execute_custom_query(hot_sql, [page_size], fetch='all')
        return Response.success(data=hot_searches or [])
    except Exception as e:
        logger.error(f"获取热门搜索失败: {e}")
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