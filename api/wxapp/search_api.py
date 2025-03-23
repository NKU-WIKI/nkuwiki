from fastapi import APIRouter, Query, HTTPException, Body, Path, Depends
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
import logging
import json
from datetime import datetime

from core.utils.auth import TokenManager
from etl.retrieval.retrievers import QdrantRetriever, BM25Retriever, HybridRetriever
from llama_index.core import QueryBundle
from llama_index.core.schema import NodeWithScore

# 导入全局路由器
from api import wxapp_router as router
from api.common import get_api_logger, handle_api_errors, create_standard_response
from etl.load.py_mysql import (
    insert_record, update_record, delete_record, 
    query_records, count_records, get_record_by_id,
    execute_raw_query
)
from api.wxapp.common_utils import format_datetime, prepare_db_data, process_json_fields

# 设置日志记录器
logger = logging.getLogger(__name__)

# 定义一个简单的结果模型
class RetrievalResult:
    def __init__(self, results, total, query):
        self.results = results
        self.total = total
        self.query = query

# 定义一个搜索结果项目
class SearchResultItem:
    def __init__(self, id, title, content, score, source, url=None, metadata=None):
        self.id = id
        self.title = title
        self.content = content
        self.score = score
        self.source = source
        self.url = url
        self.metadata = metadata

# 获取检索器的函数
def get_retriever():
    # 这里简单返回一个模拟的检索器
    # 实际应用中，应该根据配置创建真实的检索器实例
    logger.warning("使用模拟检索器 - 实际项目中请实现真实检索功能")
    
    class MockRetriever:
        def search(self, query, limit=10, offset=0, filters=None):
            # 模拟搜索结果
            results = [
                SearchResultItem(
                    id=f"result-{i}",
                    title=f"搜索结果 {i} 标题",
                    content=f"这是关于 '{query}' 的搜索结果 {i} 的内容",
                    score=0.9 - (i * 0.1),
                    source="模拟数据",
                    metadata={"type": "mock"}
                )
                for i in range(limit)
            ]
            return RetrievalResult(results=results, total=100, query=query)
    
    return MockRetriever()

# 请求模型
class SearchQuery(BaseModel):
    query: str = Field(..., description="搜索查询词")
    limit: int = Field(10, description="返回结果数量限制")
    offset: int = Field(0, description="起始偏移量")
    filters: Optional[Dict[str, Any]] = Field(None, description="过滤条件")

# 返回模型
class SearchResult(BaseModel):
    id: str
    title: str
    content: str
    score: float
    source: str
    url: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class SearchResponse(BaseModel):
    results: List[SearchResult]
    total: int
    query: str

# 文件索引请求模型
class DocumentIndexRequest(BaseModel):
    file_id: str = Field(..., description="微信云存储的文件ID")
    file_name: str = Field(..., description="文件名称")
    openid: str = Field(..., description="用户openid")
    custom_metadata: Optional[Dict[str, Any]] = Field(None, description="自定义元数据")

# 文件索引响应模型
class DocumentIndexResponse(BaseModel):
    success: bool
    message: str
    document_id: Optional[str] = None
    suggested_keywords: Optional[List[str]] = None

# 帖子搜索请求模型
class SearchPostRequest(BaseModel):
    """帖子搜索请求"""
    keyword: Optional[str] = Field(None, description="关键词，搜索标题和内容")
    title: Optional[str] = Field(None, description="标题关键词")
    content: Optional[str] = Field(None, description="内容关键词")
    openid: Optional[str] = Field(None, description="按发帖用户openid筛选")
    nick_name: Optional[str] = Field(None, description="按用户昵称筛选")
    tags: Optional[List[str]] = Field(None, description="按标签筛选，支持多个标签")
    category_id: Optional[int] = Field(None, description="按分类ID筛选")
    start_time: Optional[str] = Field(None, description="开始时间，格式：YYYY-MM-DD HH:MM:SS")
    end_time: Optional[str] = Field(None, description="结束时间，格式：YYYY-MM-DD HH:MM:SS")
    status: Optional[int] = Field(1, description="帖子状态: 1-正常, 0-禁用")
    include_deleted: Optional[bool] = Field(False, description="是否包含已删除的帖子")
    sort_by: Optional[str] = Field("update_time DESC", description="排序方式，支持create_time/update_time/like_count/comment_count ASC/DESC")
    page: int = Field(1, description="页码", ge=1)
    page_size: int = Field(20, description="每页记录数", ge=1, le=100)

@router.post("/search", response_model=SearchResponse)
async def search(query: SearchQuery):
    """
    执行搜索查询，返回最相关的结果
    """
    try:
        logger.debug(f"接收到搜索请求: {query.query}")
        
        # 获取检索器实例
        retriever = get_retriever()
        
        # 执行查询
        results = retriever.search(
            query=query.query,
            limit=query.limit,
            offset=query.offset,
            filters=query.filters
        )
        
        # 转换结果格式
        search_results = []
        for result in results.results:
            search_results.append(
                SearchResult(
                    id=result.id,
                    title=result.title,
                    content=result.content,
                    score=result.score,
                    source=result.source,
                    url=result.url,
                    metadata=result.metadata
                )
            )
        
        return SearchResponse(
            results=search_results,
            total=results.total,
            query=query.query
        )
        
    except Exception as e:
        logger.error(f"搜索过程中出错: {str(e)}")
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")

@router.post("/index-document", response_model=DocumentIndexResponse)
async def index_document(request: DocumentIndexRequest, token: Dict[str, Any] = Depends(TokenManager().get_current_user)):
    """
    为微信云存储中的文件建立索引，支持多种文档格式
    
    此API接收微信云存储的fileID，从中检索文件内容，然后建立检索索引
    支持的文件格式: PDF, DOCX, TXT, MARKDOWN 等
    """
    try:
        from etl.pipeline import index_cloud_document
        
        logger.debug(f"接收到文档索引请求: {request.file_name} (ID: {request.file_id})")
        
        # 调用索引管道处理云存储文档
        result = index_cloud_document(
            cloud_file_id=request.file_id,
            file_name=request.file_name,
            user_id=request.openid,
            metadata=request.custom_metadata or {}
        )
        
        if not result.get("success"):
            return DocumentIndexResponse(
                success=False,
                message=result.get("message", "文档索引失败"),
                document_id=None
            )
        
        # 生成建议的搜索关键词
        suggested_keywords = result.get("keywords", [])
        
        return DocumentIndexResponse(
            success=True,
            message="文档索引成功",
            document_id=result.get("document_id"),
            suggested_keywords=suggested_keywords
        )
        
    except Exception as e:
        logger.error(f"索引文档过程中出错: {str(e)}")
        return DocumentIndexResponse(
            success=False,
            message=f"文档索引失败: {str(e)}",
            document_id=None
        ) 

@router.post("/search_post", response_model=Dict[str, Any], summary="高级搜索帖子")
@handle_api_errors("搜索帖子")
async def search_post(
    search: SearchPostRequest,
    api_logger=Depends(get_api_logger)
):
    """
    高级搜索帖子功能，支持多条件灵活搜索，包括关键词、标题、内容、发帖人等
    """
    api_logger.debug(f"搜索帖子请求: {search.dict()}")
    
    # 计算分页参数
    offset = (search.page - 1) * search.page_size
    limit = search.page_size
    
    # 构建基础查询条件
    conditions = {}
    where_clauses = []
    params = []
    
    # 处理关键词搜索（标题和内容）
    if search.keyword:
        where_clauses.append("(title LIKE %s OR content LIKE %s)")
        keyword_param = f"%{search.keyword}%"
        params.extend([keyword_param, keyword_param])
    
    # 处理标题搜索
    if search.title:
        where_clauses.append("title LIKE %s")
        params.append(f"%{search.title}%")
    
    # 处理内容搜索
    if search.content:
        where_clauses.append("content LIKE %s")
        params.append(f"%{search.content}%")
    
    # 处理用户搜索
    if search.openid:
        where_clauses.append("openid = %s")
        params.append(search.openid)
    
    # 处理昵称搜索
    if search.nick_name:
        where_clauses.append("nick_name LIKE %s")
        params.append(f"%{search.nick_name}%")
    
    # 处理标签搜索
    if search.tags and len(search.tags) > 0:
        tags_conditions = []
        for tag in search.tags:
            tags_conditions.append("JSON_CONTAINS(tags, %s)")
            params.append(json.dumps(tag))
        where_clauses.append(f"({' OR '.join(tags_conditions)})")
    
    # 处理分类搜索
    if search.category_id:
        where_clauses.append("category_id = %s")
        params.append(search.category_id)
    
    # 处理时间范围
    if search.start_time:
        where_clauses.append("create_time >= %s")
        params.append(search.start_time)
    
    if search.end_time:
        where_clauses.append("create_time <= %s")
        params.append(search.end_time)
    
    # 处理状态
    if search.status is not None:
        where_clauses.append("status = %s")
        params.append(search.status)
    
    # 默认不包含已删除帖子
    if not search.include_deleted:
        where_clauses.append("is_deleted = 0")
    
    # 构建完整的WHERE子句
    where_clause = " AND ".join(where_clauses) if where_clauses else "1=1"
    
    # 处理排序
    sort_options = ["create_time", "update_time", "like_count", "comment_count", "view_count"]
    sort_by = search.sort_by
    if sort_by:
        # 简单验证排序参数格式
        sort_parts = sort_by.split()
        if len(sort_parts) >= 1 and sort_parts[0].lower() not in [opt.lower() for opt in sort_options]:
            sort_by = "update_time DESC"  # 默认排序
    else:
        sort_by = "update_time DESC"  # 默认排序
    
    # 构建并执行查询
    count_query = f"SELECT COUNT(*) as total FROM wxapp_posts WHERE {where_clause}"
    total_count_result = execute_raw_query(count_query, params)
    total_count = total_count_result[0]['total'] if total_count_result else 0
    
    # 查询数据
    data_query = f"""
        SELECT * 
        FROM wxapp_posts 
        WHERE {where_clause} 
        ORDER BY {sort_by} 
        LIMIT {limit} OFFSET {offset}
    """
    
    posts = execute_raw_query(data_query, params)
    
    # 处理查询结果
    json_fields = ["images", "tags", "liked_users", "favorite_users", "extra"]
    datetime_fields = ["create_time", "update_time"]
    
    for post in posts:
        # 处理JSON字段
        for field in json_fields:
            if field in post and post[field]:
                try:
                    post[field] = json.loads(post[field])
                except (json.JSONDecodeError, TypeError):
                    # 如果解析失败，设置为空列表或字典
                    post[field] = [] if field in ["images", "tags", "liked_users", "favorite_users"] else {}
            else:
                # 设置默认值
                post[field] = [] if field in ["images", "tags", "liked_users", "favorite_users"] else {}
        
        # 格式化时间字段
        for field in datetime_fields:
            if field in post and post[field]:
                post[field] = format_datetime(post[field])
    
    # 构建分页信息
    total_pages = (total_count + limit - 1) // limit if total_count > 0 else 0
    pagination = {
        "total": total_count,
        "page": search.page,
        "page_size": search.page_size,
        "total_pages": total_pages,
        "has_next": search.page < total_pages,
        "has_prev": search.page > 1
    }
    
    return create_standard_response({
        "posts": posts,
        "pagination": pagination,
        "search_info": {
            "keyword": search.keyword,
            "filters": {k: v for k, v in search.dict().items() if v is not None and k not in ["page", "page_size", "sort_by"]}
        }
    }) 