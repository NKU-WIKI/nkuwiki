import re
import time
import asyncio
from datetime import datetime
from fastapi import Query, APIRouter, Body
from typing import Optional, List, Dict, Any
from api.models.knowledge import Source

from api.models.common import Response, Request, validate_params
from etl.load.db_core import (
    async_query_records,async_execute_custom_query
)
from core.utils.logger import register_logger

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
            "data": [...], // Source对象列表
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
        platform_name, tag_name = table.split("_")
        platform_info = TABLE_MAPPING[platform_name]
        
        # 如果是wxapp平台，需要根据tag获取对应的表结构
        if platform_name == "wxapp":
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
        search_task = async_query_records(
            table_name=table,
            conditions={"where_condition": where_condition, "params": sql_params},
            order_by=f"{time_field} DESC, id DESC",  # 按表配置的时间字段降序排序
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
    
    # 转换为Source模型格式
    sources = []
    for item in paged_results:
        table_name = item.get("_table", "")
        platform_name = table_name.split("_")[0]
        if platform_name in TABLE_MAPPING:
            platform_info = TABLE_MAPPING[platform_name]
            
            # 获取各字段值，不存在则使用空字符串
            # 修复wxapp平台的作者字段获取方式
            author_field = ""
            if platform_name == "wxapp":
                if "post" in table_name:
                    author_field = platform_info["post"]["author_field"]
                elif "comment" in table_name:
                    author_field = platform_info["comment"]["author_field"]
                else:
                    author_field = "nickname"  # 默认作者字段
            else:
                author_field = platform_info["author_field"]
            
            author = item.get(author_field, "") or "未知作者"
            
            # 获取标题和内容的字段名称
            if platform_name == "wxapp":
                if "post" in table_name:
                    title_field = platform_info["post"]["title_field"]
                    content_field = platform_info["post"]["content_field"]
                elif "comment" in table_name:
                    title_field = platform_info["comment"]["title_field"]
                    content_field = platform_info["comment"]["content_field"]
                else:
                    title_field = "title"  # 默认标题字段
                    content_field = "content"  # 默认内容字段
            else:
                title_field = platform_info["title_field"]
                content_field = platform_info["content_field"]
            
            title = item.get(title_field, "") or "无标题"
            content = item.get(content_field, "") or ""
            
            # 转换平台标识为简短形式
            platform_value = platform_name
            
            original_url = item.get("original_url", "")
            
            # 提取标签，如果存在
            tag = None
            if "tag" in item and item["tag"]:
                try:
                    if isinstance(item["tag"], str):
                        import json
                        tag = json.loads(item["tag"])
                    else:
                        tag = item["tag"]
                except:
                    tag = None
            
            # 提取图片，如果存在
            image = None
            if "image" in item and item["image"]:
                try:
                    if isinstance(item["image"], str):
                        import json
                        image = json.loads(item["image"])
                    else:
                        image = item["image"]
                except:
                    image = None
            
            # 处理时间字段
            if platform_name == "wxapp":
                # wxapp表使用原始的update_time和create_time
                create_time = item.get("create_time")
                update_time = item.get("update_time")
                publish_time = None
                scrape_time = None
            else:
                # 非wxapp表使用publish_time作为create_time和update_time
                publish_time = item.get("publish_time")
                scrape_time = item.get("scrape_time")
                create_time = publish_time 
                update_time = publish_time 

            # 标记内容是否被截断
            is_truncated = item.get("_content_truncated", False)
            is_official = item.get("is_official", False)
            # 创建Source实例
            source = Source(
                author=author,
                platform=platform_value,
                original_url=original_url,
                tag=tag,
                title=title,
                content=content,
                image=image,
                publish_time=publish_time,
                scrape_time=scrape_time,
                create_time=create_time,
                update_time=update_time,
                relevance=item.get("relevance", 0),
                is_official=is_official,
                is_truncated=is_truncated
            )
            
            sources.append(source)
    
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
    platform: Optional[str] = Query(None, description="平台标识(wechat,website,market,wxapp)，多个用逗号分隔"),
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
                "is_official": "是否为官方信息",
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

async def _record_search_history(query: str, openid: str):
    """记录搜索历史"""
    try:
        # 检查是否存在相同的搜索记录
        sql = """
            SELECT id FROM search_history 
            WHERE query = %s AND openid = %s 
            ORDER BY create_time DESC 
            LIMIT 1
        """
        result = execute_query(sql, [query, openid])
        
        if result:
            # 更新现有记录的时间
            sql = "UPDATE search_history SET update_time = %s WHERE id = %s"
            execute_query(sql, [datetime.now(), result[0]["id"]])
        else:
            # 插入新记录
            sql = """
                INSERT INTO search_history (query, openid, create_time, update_time)
                VALUES (%s, %s, %s, %s)
            """
            execute_query(sql, [query, openid, datetime.now(), datetime.now()])
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
            
        suggestions = await async_execute_custom_query(
            """
            SELECT keyword 
            FROM wxapp_search_history 
            WHERE keyword LIKE %s 
            GROUP BY keyword 
            ORDER BY COUNT(*) DESC, MAX(search_time) DESC
            LIMIT %s
            """,
            [f"%{query}%", page_size]
        )
        
        # 异步记录搜索历史
        if openid:
            asyncio.create_task(_record_search_history(query, openid))
            
        return Response.success(data=[s["keyword"] for s in suggestions])
    except Exception as e:
        logger.error(f"获取搜索建议失败: {str(e)}")
        return Response.error(details={"message": f"获取搜索建议失败: {str(e)}"})

@router.get("/search-wxapp")
async def search(
    query: str = Query(..., description="搜索关键词"),
    search_type: str = Query("all", description="搜索类型: all, post, user"),
    page: int = Query(1, description="页码"),
    page_size: int = Query(10, description="每页记录数量")
):
    """综合搜索"""
    try:
        if not query.strip():
            return Response.bad_request(details={"message": "搜索关键词不能为空"})
            
        logger.debug(f"执行搜索: query={query}, search_type={search_type}, page={page}, page_size={page_size}")
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
            ORDER BY update_time DESC
            LIMIT %s OFFSET %s
            """
            search_tasks.append(
                ("post", async_execute_custom_query(
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
                ("post", async_execute_custom_query(
                    post_count_sql,
                    [f"%{query}%", f"%{query}%"]
                ))
            )
        
        if search_type == "all" or search_type == "user":
            # 搜索用户任务
            user_sql = """
            SELECT id, openid, nickname, avatar, bio
            FROM wxapp_user
            WHERE status = 1 AND (nickname LIKE %s OR bio LIKE %s)
            ORDER BY update_time DESC
            LIMIT %s OFFSET %s
            """
            search_tasks.append(
                ("user", async_execute_custom_query(
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
                ("user", async_execute_custom_query(
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
            for post in search_results_map["post"]:
                search_results.append({
                    "id": post["id"],
                    "title": post["title"],
                    "content": post["content"],
                    "type": "post",
                    "like_count": post["like_count"],
                    "comment_count": post["comment_count"],
                    "view_count": post["view_count"],
                    "update_time": post["update_time"]
                })
            
            post_total = count_results_map["post"][0]['total'] if count_results_map["post"] else 0
            total += post_total
        
        if "user" in search_results_map:
            for user in search_results_map["user"]:
                search_results.append({
                    "id": user["id"],
                    "openid": user["openid"],
                    "nickname": user["nickname"],
                    "avatar": user["avatar"],
                    "bio": user["bio"],
                    "type": "user"
                })
            
            user_total = count_results_map["user"][0]['total'] if count_results_map["user"] else 0
            total += user_total
        
        # 异步记录搜索历史
        asyncio.create_task(_record_search_history(query))
        
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
            details={"query": query, "search_type": search_type}
        )
    except Exception as e:
        logger.error(f"搜索失败: {str(e)}")
        return Response.error(details={"message": f"搜索失败: {str(e)}"})

async def _record_search_history(keyword, openid=None):
    """记录搜索历史"""
    try:
        # 简化版本，只记录关键词
        if not keyword or not keyword.strip():
            return
            
        await async_execute_custom_query(
            "INSERT INTO wxapp_search_history (keyword, search_time, openid) VALUES (%s, NOW(), %s)",
            [keyword, openid or "anonymous"],
            fetch=False
        )
    except Exception as e:
        # 记录搜索历史失败不影响主流程
        logger.debug(f"记录搜索历史失败: {e}")
        pass

@router.get("/history")
async def get_search_history(
    openid: str = Query(..., description="用户OpenID"),
    page_size: int = Query(10, description="返回结果数量")
):
    """获取搜索历史"""
    try:
        logger.debug(f"获取搜索历史: openid={openid}, page_size={page_size}")
        if not openid:
            return Response.bad_request(details={"message": "缺少openid参数"})

        # 直接使用SQL查询搜索历史并去重
        history_sql = """
        SELECT DISTINCT keyword, MAX(search_time) as search_time
        FROM wxapp_search_history
        WHERE openid = %s
        GROUP BY keyword
        ORDER BY MAX(search_time) DESC
        LIMIT %s
        """
        
        history = await async_execute_custom_query(history_sql, [openid, page_size])
        
        return Response.success(data=history or [])
    except Exception as e:
        logger.error(f"获取搜索历史失败: {str(e)}")
        return Response.error(details={"message": f"获取搜索历史失败: {str(e)}"})

@router.post("/history/clear")
async def clear_search_history(request: Request):
    """清空搜索历史"""
    try:
        # 参数验证
        req_data = await request.json()
        required_params = ["openid"]
        error_response = validate_params(req_data, required_params)
        if error_response:
            return error_response
            
        openid = req_data.get("openid")
        logger.debug(f"清空搜索历史: openid={openid}")
        
        # 删除历史记录
        await async_execute_custom_query(
            "DELETE FROM wxapp_search_history WHERE openid = %s",
            [openid],
            fetch=False
        )
        
        return Response.success(details={"message": "清空搜索历史成功"})
    except Exception as e:
        logger.error(f"清空搜索历史失败: {str(e)}")
        return Response.error(details={"message": f"清空搜索历史失败: {str(e)}"})

@router.get("/hot")
async def get_hot_searches(
    page_size: int = Query(10, description="返回结果数量")
):
    """获取热门搜索"""
    try:
        logger.debug(f"获取热门搜索: page_size={page_size}")
        hot_searches = await async_execute_custom_query(
            """
            SELECT keyword, COUNT(*) as count 
            FROM wxapp_search_history 
            WHERE search_time > DATE_SUB(NOW(), INTERVAL 7 DAY)
            GROUP BY keyword 
            ORDER BY count DESC 
            LIMIT %s
            """,
            [page_size]
        )
        
        return Response.success(data=hot_searches or [])
    except Exception as e:
        logger.error(f"获取热门搜索失败: {str(e)}")
        return Response.error(details={"message": f"获取热门搜索失败: {str(e)}"}) 