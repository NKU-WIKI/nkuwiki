#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
搜索DAO层
提供各种搜索相关的数据库交互方法
"""

import time
import json
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime
from loguru import logger

from etl.load.db_core import execute_query, insert_record, update_record
from api.models.search import (
    SearchType, SortOrder, UnifiedSearchRequest, PostSearchRequest,
    PostSearchItem, CommentSearchItem, WebsiteSearchItem, 
    WechatSearchItem, MarketSearchItem
)
from core.utils.logger import register_logger

# 注册日志
log = register_logger("search_dao")

def search_posts(keyword: str, 
                 start_time: Optional[datetime] = None,
                 end_time: Optional[datetime] = None,
                 sort_by: str = "time_desc",
                 page: int = 1, 
                 page_size: int = 20,
                 tags: List[str] = None,
                 category_id: Optional[int] = None,
                 openid: Optional[str] = None) -> Tuple[List[Dict[str, Any]], int]:
    """
    搜索帖子
    
    Args:
        keyword: 搜索关键词
        start_time: 开始时间
        end_time: 结束时间
        sort_by: 排序方式
        page: 页码
        page_size: 每页记录数
        tags: 标签列表
        category_id: 分类ID
        openid: 用户openid
        
    Returns:
        帖子列表和总数
    """
    try:
        # 构建WHERE条件
        where_clause = "WHERE (title LIKE %s OR content LIKE %s) AND status = 1 AND is_deleted = 0"
        params = [f"%{keyword}%", f"%{keyword}%"]
        
        # 添加时间范围筛选
        if start_time:
            where_clause += " AND create_time >= %s"
            params.append(start_time)
        if end_time:
            where_clause += " AND create_time <= %s"
            params.append(end_time)
        
        # 添加标签筛选
        if tags and len(tags) > 0:
            tag_conditions = []
            for tag in tags:
                tag_conditions.append("tags LIKE %s")
                params.append(f"%{tag}%")
            where_clause += f" AND ({' OR '.join(tag_conditions)})"
        
        # 添加分类筛选
        if category_id is not None:
            where_clause += " AND category_id = %s"
            params.append(category_id)
        
        # 添加用户筛选
        if openid:
            where_clause += " AND openid = %s"
            params.append(openid)
            
        # 构建排序条件
        order_clause = ""
        if sort_by == SortOrder.TIME_DESC:
            order_clause = "ORDER BY create_time DESC"
        elif sort_by == SortOrder.TIME_ASC:
            order_clause = "ORDER BY create_time ASC"
        elif sort_by == SortOrder.RELEVANCE:
            # 相关度排序，使用MySQL的全文搜索功能
            order_clause = "ORDER BY MATCH(title, content) AGAINST(%s IN BOOLEAN MODE) DESC"
            params.append(keyword)
            
        # 计算总数
        count_sql = f"SELECT COUNT(*) as total FROM wxapp_posts {where_clause}"
        count_result = execute_query(count_sql, params)
        total = count_result[0]['total'] if count_result else 0
        
        # 分页查询
        offset = (page - 1) * page_size
        sql = f"""
        SELECT id, openid, nick_name, avatar, content, title, 
               images, tags, category_id, location, view_count, 
               like_count, comment_count, favorite_count, 
               create_time, update_time
        FROM wxapp_posts
        {where_clause}
        {order_clause}
        LIMIT %s OFFSET %s
        """
        params.extend([page_size, offset])
        
        # 执行查询
        posts = execute_query(sql, params)
        
        # 处理结果中的特殊字段
        for post in posts:
            # 处理JSON字段
            if isinstance(post.get('images'), str) and post['images']:
                try:
                    post['images'] = json.loads(post['images'])
                except:
                    post['images'] = []
            else:
                post['images'] = []
                
            if isinstance(post.get('tags'), str) and post['tags']:
                try:
                    post['tags'] = json.loads(post['tags'])
                except:
                    post['tags'] = []
            else:
                post['tags'] = []
        
        return posts, total
        
    except Exception as e:
        log.error(f"搜索帖子出错: {str(e)}")
        return [], 0
        
def search_comments(keyword: str, 
                    start_time: Optional[datetime] = None,
                    end_time: Optional[datetime] = None,
                    sort_by: str = "time_desc",
                    page: int = 1, 
                    page_size: int = 20,
                    openid: Optional[str] = None) -> Tuple[List[Dict[str, Any]], int]:
    """
    搜索评论
    
    Args:
        keyword: 搜索关键词
        start_time: 开始时间
        end_time: 结束时间
        sort_by: 排序方式
        page: 页码
        page_size: 每页记录数
        openid: 用户openid
        
    Returns:
        评论列表和总数
    """
    try:
        # 构建WHERE条件
        where_clause = "WHERE content LIKE %s AND status = 1 AND is_deleted = 0"
        params = [f"%{keyword}%"]
        
        # 添加时间范围筛选
        if start_time:
            where_clause += " AND create_time >= %s"
            params.append(start_time)
        if end_time:
            where_clause += " AND create_time <= %s"
            params.append(end_time)
        
        # 添加用户筛选
        if openid:
            where_clause += " AND openid = %s"
            params.append(openid)
            
        # 构建排序条件
        order_clause = ""
        if sort_by == SortOrder.TIME_DESC:
            order_clause = "ORDER BY create_time DESC"
        elif sort_by == SortOrder.TIME_ASC:
            order_clause = "ORDER BY create_time ASC"
        elif sort_by == SortOrder.RELEVANCE:
            # 相关度排序
            order_clause = "ORDER BY create_time DESC"  
            
        # 计算总数
        count_sql = f"SELECT COUNT(*) as total FROM wxapp_comments {where_clause}"
        count_result = execute_query(count_sql, params)
        total = count_result[0]['total'] if count_result else 0
        
        # 分页查询
        offset = (page - 1) * page_size
        sql = f"""
        SELECT id, post_id, openid, nick_name, avatar, content, 
               parent_id, images, like_count, create_time, update_time
        FROM wxapp_comments
        {where_clause}
        {order_clause}
        LIMIT %s OFFSET %s
        """
        params.extend([page_size, offset])
        
        # 执行查询
        comments = execute_query(sql, params)
        
        # 处理结果中的特殊字段
        for comment in comments:
            # 处理JSON字段
            if isinstance(comment.get('images'), str) and comment['images']:
                try:
                    comment['images'] = json.loads(comment['images'])
                except:
                    comment['images'] = []
            else:
                comment['images'] = []
        
        return comments, total
        
    except Exception as e:
        log.error(f"搜索评论出错: {str(e)}")
        return [], 0

def search_websites(keyword: str, 
                   start_time: Optional[datetime] = None,
                   end_time: Optional[datetime] = None,
                   sort_by: str = "time_desc",
                   page: int = 1, 
                   page_size: int = 20) -> Tuple[List[Dict[str, Any]], int]:
    """
    搜索网站文章
    
    Args:
        keyword: 搜索关键词
        start_time: 开始时间
        end_time: 结束时间
        sort_by: 排序方式
        page: 页码
        page_size: 每页记录数
        
    Returns:
        网站文章列表和总数
    """
    try:
        # 构建WHERE条件
        where_clause = "WHERE (title LIKE %s OR content LIKE %s)"
        params = [f"%{keyword}%", f"%{keyword}%"]
        
        # 添加时间范围筛选
        if start_time:
            where_clause += " AND publish_time >= %s"
            params.append(start_time)
        if end_time:
            where_clause += " AND publish_time <= %s"
            params.append(end_time)
            
        # 构建排序条件
        order_clause = ""
        if sort_by == SortOrder.TIME_DESC:
            order_clause = "ORDER BY publish_time DESC"
        elif sort_by == SortOrder.TIME_ASC:
            order_clause = "ORDER BY publish_time ASC"
        elif sort_by == SortOrder.RELEVANCE:
            # 简单相关度排序
            order_clause = "ORDER BY (CASE WHEN title LIKE %s THEN 3 ELSE 0 END) + " \
                          "(CASE WHEN content LIKE %s THEN 1 ELSE 0 END) DESC, publish_time DESC"
            params.extend([f"%{keyword}%", f"%{keyword}%"])
            
        # 计算总数
        count_sql = f"SELECT COUNT(*) as total FROM website_nku {where_clause}"
        count_result = execute_query(count_sql, params)
        total = count_result[0]['total'] if count_result else 0
        
        # 分页查询
        offset = (page - 1) * page_size
        sql = f"""
        SELECT id, platform, original_url, title, author, 
               publish_time, scrape_time, content_type, content
        FROM website_nku
        {where_clause}
        {order_clause}
        LIMIT %s OFFSET %s
        """
        params.extend([page_size, offset])
        
        # 执行查询
        websites = execute_query(sql, params)
        
        return websites, total
        
    except Exception as e:
        log.error(f"搜索网站文章出错: {str(e)}")
        return [], 0

def search_wechats(keyword: str, 
                  start_time: Optional[datetime] = None,
                  end_time: Optional[datetime] = None,
                  sort_by: str = "time_desc",
                  page: int = 1, 
                  page_size: int = 20) -> Tuple[List[Dict[str, Any]], int]:
    """
    搜索公众号文章
    
    Args:
        keyword: 搜索关键词
        start_time: 开始时间
        end_time: 结束时间
        sort_by: 排序方式
        page: 页码
        page_size: 每页记录数
        
    Returns:
        公众号文章列表和总数
    """
    try:
        # 构建WHERE条件
        where_clause = "WHERE (title LIKE %s OR content LIKE %s)"
        params = [f"%{keyword}%", f"%{keyword}%"]
        
        # 添加时间范围筛选
        if start_time:
            where_clause += " AND publish_time >= %s"
            params.append(start_time)
        if end_time:
            where_clause += " AND publish_time <= %s"
            params.append(end_time)
            
        # 构建排序条件
        order_clause = ""
        if sort_by == SortOrder.TIME_DESC:
            order_clause = "ORDER BY publish_time DESC"
        elif sort_by == SortOrder.TIME_ASC:
            order_clause = "ORDER BY publish_time ASC"
        elif sort_by == SortOrder.RELEVANCE:
            # 简单相关度排序
            order_clause = "ORDER BY (CASE WHEN title LIKE %s THEN 3 ELSE 0 END) + " \
                          "(CASE WHEN content LIKE %s THEN 1 ELSE 0 END) DESC, publish_time DESC"
            params.extend([f"%{keyword}%", f"%{keyword}%"])
            
        # 计算总数
        count_sql = f"SELECT COUNT(*) as total FROM wechat_nku {where_clause}"
        count_result = execute_query(count_sql, params)
        total = count_result[0]['total'] if count_result else 0
        
        # 分页查询
        offset = (page - 1) * page_size
        sql = f"""
        SELECT id, platform, original_url, title, author, 
               publish_time, scrape_time, content_type, content
        FROM wechat_nku
        {where_clause}
        {order_clause}
        LIMIT %s OFFSET %s
        """
        params.extend([page_size, offset])
        
        # 执行查询
        wechats = execute_query(sql, params)
        
        return wechats, total
        
    except Exception as e:
        log.error(f"搜索公众号文章出错: {str(e)}")
        return [], 0

def search_markets(keyword: str, 
                  start_time: Optional[datetime] = None,
                  end_time: Optional[datetime] = None,
                  sort_by: str = "time_desc",
                  page: int = 1, 
                  page_size: int = 20) -> Tuple[List[Dict[str, Any]], int]:
    """
    搜索市场信息
    
    Args:
        keyword: 搜索关键词
        start_time: 开始时间
        end_time: 结束时间
        sort_by: 排序方式
        page: 页码
        page_size: 每页记录数
        
    Returns:
        市场信息列表和总数
    """
    try:
        # 构建WHERE条件
        where_clause = "WHERE (title LIKE %s OR content LIKE %s)"
        params = [f"%{keyword}%", f"%{keyword}%"]
        
        # 添加时间范围筛选
        if start_time:
            where_clause += " AND publish_time >= %s"
            params.append(start_time)
        if end_time:
            where_clause += " AND publish_time <= %s"
            params.append(end_time)
            
        # 构建排序条件
        order_clause = ""
        if sort_by == SortOrder.TIME_DESC:
            order_clause = "ORDER BY publish_time DESC"
        elif sort_by == SortOrder.TIME_ASC:
            order_clause = "ORDER BY publish_time ASC"
        elif sort_by == SortOrder.RELEVANCE:
            # 简单相关度排序
            order_clause = "ORDER BY (CASE WHEN title LIKE %s THEN 3 ELSE 0 END) + " \
                          "(CASE WHEN content LIKE %s THEN 1 ELSE 0 END) DESC, publish_time DESC"
            params.extend([f"%{keyword}%", f"%{keyword}%"])
            
        # 计算总数
        count_sql = f"SELECT COUNT(*) as total FROM market_nku {where_clause}"
        count_result = execute_query(count_sql, params)
        total = count_result[0]['total'] if count_result else 0
        
        # 分页查询
        offset = (page - 1) * page_size
        sql = f"""
        SELECT id, publish_time, title, content, 
               author, original_url, platform, 
               content_type, scrape_time
        FROM market_nku
        {where_clause}
        {order_clause}
        LIMIT %s OFFSET %s
        """
        params.extend([page_size, offset])
        
        # 执行查询
        markets = execute_query(sql, params)
        
        return markets, total
        
    except Exception as e:
        log.error(f"搜索市场信息出错: {str(e)}")
        return [], 0

def unified_search(request: UnifiedSearchRequest) -> Dict[str, Any]:
    """
    统一搜索接口，根据搜索类型搜索不同的内容
    
    Args:
        request: 统一搜索请求对象
        
    Returns:
        Dict: 包含不同类型的搜索结果
    """
    result = {
        "total": 0,
        "page": request.page,
        "page_size": request.page_size,
        "total_pages": 0,
        "keyword": request.keyword,
        "posts": [],
        "comments": [],
        "websites": [],
        "wechats": [],
        "markets": []
    }
    
    sort_by_value = request.sort_by.value if isinstance(request.sort_by, SortOrder) else request.sort_by
    
    # 根据搜索类型执行不同的搜索
    if request.search_type == SearchType.ALL or request.search_type == SearchType.POST:
        posts, post_total = search_posts(
            keyword=request.keyword,
            start_time=request.start_time,
            end_time=request.end_time,
            sort_by=sort_by_value,
            page=request.page,
            page_size=request.page_size
        )
        result["posts"] = posts
        result["total"] += post_total
    
    if request.search_type == SearchType.ALL or request.search_type == SearchType.COMMENT:
        comments, comment_total = search_comments(
            keyword=request.keyword,
            start_time=request.start_time,
            end_time=request.end_time,
            sort_by=sort_by_value,
            page=request.page,
            page_size=request.page_size
        )
        result["comments"] = comments
        result["total"] += comment_total
    
    if request.search_type == SearchType.ALL or request.search_type == SearchType.WEBSITE:
        websites, website_total = search_websites(
            keyword=request.keyword,
            start_time=request.start_time,
            end_time=request.end_time,
            sort_by=sort_by_value,
            page=request.page,
            page_size=request.page_size
        )
        result["websites"] = websites
        result["total"] += website_total
    
    if request.search_type == SearchType.ALL or request.search_type == SearchType.WECHAT:
        wechats, wechat_total = search_wechats(
            keyword=request.keyword,
            start_time=request.start_time,
            end_time=request.end_time,
            sort_by=sort_by_value,
            page=request.page,
            page_size=request.page_size
        )
        result["wechats"] = wechats
        result["total"] += wechat_total
    
    if request.search_type == SearchType.ALL or request.search_type == SearchType.MARKET:
        markets, market_total = search_markets(
            keyword=request.keyword,
            start_time=request.start_time,
            end_time=request.end_time,
            sort_by=sort_by_value,
            page=request.page,
            page_size=request.page_size
        )
        result["markets"] = markets
        result["total"] += market_total
    
    # 计算总页数
    result["total_pages"] = (result["total"] + request.page_size - 1) // request.page_size
    
    return result

def query_records(query: str, limit: int = 10, include_content: bool = False) -> List[Dict[str, Any]]:
    """
    综合查询记录，从多个表中搜索数据并返回统一格式的结果
    
    Args:
        query: 搜索关键词
        limit: 返回结果数量限制
        include_content: 是否包含完整内容
        
    Returns:
        List: 搜索结果列表
    """
    results = []
    try:
        # 从各个表中查询数据
        posts, _ = search_posts(keyword=query, page=1, page_size=limit//3)
        websites, _ = search_websites(keyword=query, page=1, page_size=limit//3)
        wechats, _ = search_wechats(keyword=query, page=1, page_size=limit//3)
        
        # 转换帖子结果
        for post in posts:
            content_preview = post["content"]
            if not include_content and len(content_preview) > 100:
                content_preview = content_preview[:100] + "..."
                
            results.append({
                "id": post["id"],
                "title": post.get("title", "无标题"),
                "content_preview": content_preview,
                "author": post.get("nick_name", "匿名用户"),
                "create_time": post["create_time"].strftime("%Y-%m-%d %H:%M:%S") if isinstance(post["create_time"], datetime) else post["create_time"],
                "type": "帖子",
                "view_count": post.get("view_count", 0),
                "like_count": post.get("like_count", 0),
                "comment_count": post.get("comment_count", 0),
                "relevance": 0.9  # 模拟相关度得分
            })
        
        # 转换网站结果
        for website in websites:
            content_preview = website.get("content", "")
            if not include_content and content_preview and len(content_preview) > 100:
                content_preview = content_preview[:100] + "..."
                
            results.append({
                "id": website["id"],
                "title": website["title"],
                "content_preview": content_preview,
                "author": website.get("author", "未知"),
                "create_time": website["publish_time"].strftime("%Y-%m-%d %H:%M:%S") if isinstance(website["publish_time"], datetime) else website["publish_time"],
                "type": "网站文章",
                "view_count": 0,
                "like_count": 0,
                "comment_count": 0,
                "relevance": 0.8  # 模拟相关度得分
            })
        
        # 转换公众号结果
        for wechat in wechats:
            content_preview = wechat.get("content", "")
            if not include_content and content_preview and len(content_preview) > 100:
                content_preview = content_preview[:100] + "..."
                
            results.append({
                "id": wechat["id"],
                "title": wechat["title"],
                "content_preview": content_preview,
                "author": wechat.get("author", "未知"),
                "create_time": wechat["publish_time"].strftime("%Y-%m-%d %H:%M:%S") if isinstance(wechat["publish_time"], datetime) else wechat["publish_time"],
                "type": "公众号文章",
                "view_count": 0,
                "like_count": 0,
                "comment_count": 0,
                "relevance": 0.7  # 模拟相关度得分
            })
        
        # 按相关度排序
        results.sort(key=lambda x: x["relevance"], reverse=True)
        
        # 限制返回数量
        return results[:limit]
        
    except Exception as e:
        log.error(f"综合查询记录出错: {str(e)}")
        return []

def search_by_post_request(request: PostSearchRequest) -> Dict[str, Any]:
    """
    按帖子搜索请求查询帖子
    
    Args:
        request: 帖子搜索请求
        
    Returns:
        Dict: 包含帖子列表和分页信息
    """
    try:
        # 构建WHERE条件
        where_parts = []
        params = []
        
        # 构建关键词搜索条件
        if request.keyword:
            where_parts.append("(title LIKE %s OR content LIKE %s)")
            params.extend([f"%{request.keyword}%", f"%{request.keyword}%"])
        else:
            if request.title:
                where_parts.append("title LIKE %s")
                params.append(f"%{request.title}%")
            if request.content:
                where_parts.append("content LIKE %s")
                params.append(f"%{request.content}%")
        
        # 添加用户过滤条件
        if request.openid:
            where_parts.append("openid = %s")
            params.append(request.openid)
        if request.nick_name:
            where_parts.append("nick_name LIKE %s")
            params.append(f"%{request.nick_name}%")
        
        # 添加标签过滤条件
        if request.tags and len(request.tags) > 0:
            tag_conditions = []
            for tag in request.tags:
                tag_conditions.append("tags LIKE %s")
                params.append(f"%{tag}%")
            where_parts.append(f"({' OR '.join(tag_conditions)})")
        
        # 添加分类过滤条件
        if request.category_id is not None:
            where_parts.append("category_id = %s")
            params.append(request.category_id)
        
        # 添加时间范围过滤条件
        if request.start_time:
            where_parts.append("create_time >= %s")
            params.append(request.start_time)
        if request.end_time:
            where_parts.append("create_time <= %s")
            params.append(request.end_time)
        
        # 添加状态条件
        where_parts.append("status = %s")
        params.append(request.status)
        
        # 处理是否包含已删除的帖子
        if not request.include_deleted:
            where_parts.append("is_deleted = 0")
        
        # 构建完整的WHERE子句
        where_clause = "WHERE " + " AND ".join(where_parts) if where_parts else ""
        
        # 计算总数
        count_sql = f"SELECT COUNT(*) as total FROM wxapp_posts {where_clause}"
        count_result = execute_query(count_sql, params)
        total = count_result[0]['total'] if count_result else 0
        
        # 分页查询
        offset = (request.page - 1) * request.page_size
        sql = f"""
        SELECT id, openid, nick_name, avatar, content, title, 
               images, tags, category_id, location, view_count, 
               like_count, comment_count, favorite_count, 
               create_time, update_time
        FROM wxapp_posts
        {where_clause}
        ORDER BY {request.sort_by}
        LIMIT %s OFFSET %s
        """
        params.extend([request.page_size, offset])
        
        # 执行查询
        posts = execute_query(sql, params)
        
        # 处理结果中的特殊字段
        for post in posts:
            # 处理JSON字段
            if isinstance(post.get('images'), str) and post['images']:
                try:
                    post['images'] = json.loads(post['images'])
                except:
                    post['images'] = []
            else:
                post['images'] = []
                
            if isinstance(post.get('tags'), str) and post['tags']:
                try:
                    post['tags'] = json.loads(post['tags'])
                except:
                    post['tags'] = []
            else:
                post['tags'] = []
        
        # 构建结果
        result = {
            "posts": posts,
            "total": total,
            "page": request.page,
            "page_size": request.page_size,
            "total_pages": (total + request.page_size - 1) // request.page_size
        }
        
        return result
        
    except Exception as e:
        log.error(f"按帖子搜索请求查询帖子出错: {str(e)}")
        return {"posts": [], "total": 0, "page": request.page, "page_size": request.page_size, "total_pages": 0} 