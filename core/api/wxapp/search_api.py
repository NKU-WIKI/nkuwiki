from fastapi import APIRouter, Query, HTTPException, Body, Path, Depends
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
import logging

from core.auth.jwt_handler import validate_token
from etl.retrieval.retrievers import get_retriever, RetrievalResult

# 创建路由器
router = APIRouter()

# 设置日志记录器
logger = logging.getLogger(__name__)

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
    user_id: str = Field(..., description="用户ID")
    custom_metadata: Optional[Dict[str, Any]] = Field(None, description="自定义元数据")

# 文件索引响应模型
class DocumentIndexResponse(BaseModel):
    success: bool
    message: str
    document_id: Optional[str] = None
    suggested_keywords: Optional[List[str]] = None

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
async def index_document(request: DocumentIndexRequest, token: str = Depends(validate_token)):
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
            user_id=request.user_id,
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