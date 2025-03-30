# """
# 智能体搜索API
# 提供知识库搜索功能
# """
# from typing import List, Dict, Any, Optional
from fastapi import Query, APIRouter
# import asyncio
# from datetime import datetime
# import time

# from api.models.common import Response, Request
# from api.models.search import (
#     SearchType,
#     SortOrder,
# )
# from api.database.search_dao import unified_search, query_records, search_by_post_request

router = APIRouter()

# @router.get("/search")
# async def search_knowledge(
#     request: Request,
#     keyword: str = Query(..., description="搜索关键词"),
#     limit: int = Query(10, description="返回结果数量")
# ):
#     """搜索知识库"""
#     try:
#         loop = asyncio.get_event_loop()
#         results = await loop.run_in_executor(None, lambda: query_records(query=keyword, limit=limit))
#         return Response.success(data={"results": results, "keyword": keyword, "total": len(results)})
#     except Exception as e:
#         return Response.error(message=f"搜索失败: {str(e)}")

# def _convert_search_results(result: Dict[str, Any]) -> Dict[str, Any]:
#     """转换搜索结果为响应对象"""
#     return {
#         "posts": [PostSearchItem(**post) for post in result["posts"]],
#         "comments": [CommentSearchItem(**comment) for comment in result["comments"]],
#         "websites": [WebsiteSearchItem(**website) for website in result["websites"]],
#         "wechats": [WechatSearchItem(**wechat) for wechat in result["wechats"]],
#         "markets": [MarketSearchItem(**market) for market in result["markets"]]
#     }

# def _create_search_response(result: Dict[str, Any], request_obj, items_dict: Dict[str, List]) -> Dict[str, Any]:
#     """创建统一的搜索响应数据"""
#     filters_applied = []
#     if hasattr(request_obj, 'advanced_filters'):
#         for filter_item in request_obj.advanced_filters:
#             filters_applied.append({
#                 "type": filter_item.filter_type.value,
#                 "values": filter_item.values
#             })

#     return {
#         "total": result["total"],
#         "page": result["page"],
#         "page_size": result["page_size"],
#         "total_pages": result["total_pages"],
#         "keyword": result["keyword"],
#         "search_type": getattr(request_obj, 'search_type', SearchType.ALL).value,
#         **items_dict,
#         "filters_applied": filters_applied,
#         "suggested_keywords": generate_suggested_keywords(result["keyword"])
#     }

# @router.get("/search/unified")
# async def agent_unified_search(
#     request: Request,
#     keyword: str = Query(..., description="搜索关键词"),
#     search_type: SearchType = Query(SearchType.ALL, description="搜索类型"),
#     page: int = Query(1, description="页码"),
#     page_size: int = Query(10, description="每页数量"),
#     start_time: Optional[datetime] = Query(None, description="开始时间"),
#     end_time: Optional[datetime] = Query(None, description="结束时间"),
#     sort_by: SortOrder = Query(SortOrder.RELEVANCE, description="排序方式"),
#     advanced_filters: Optional[List[AdvancedSearchFilter]] = Query(None, description="高级过滤条件")
# ):
#     """智能体统一搜索接口，支持多种内容类型的搜索"""
#     try:
#         unified_search_request = UnifiedSearchRequest(
#             keyword=keyword,
#             search_type=search_type,
#             page=page,
#             page_size=page_size,
#             start_time=start_time,
#             end_time=end_time,
#             sort_by=sort_by,
#             advanced_filters=advanced_filters
#         )
#         loop = asyncio.get_event_loop()
#         result = await loop.run_in_executor(None, lambda: unified_search(unified_search_request))
#         items_dict = _convert_search_results(result)
#         response_data = _create_search_response(result, unified_search_request, items_dict)
#         return Response.success(data=response_data)
#     except Exception as e:
#         return Response.error(message=f"统一搜索失败: {str(e)}")

# @router.get("/search/type")
# async def agent_search_by_type(
#     request: Request,
#     keyword: str = Query(..., description="搜索关键词"),
#     search_type: SearchType = Query(..., description="搜索类型")
# ):
#     """智能体按类型搜索接口，支持通过URL路径指定搜索类型"""
#     try:
#         unified_search_request = UnifiedSearchRequest(keyword=keyword, search_type=search_type)
#         loop = asyncio.get_event_loop()
#         result = await loop.run_in_executor(None, lambda: unified_search(unified_search_request))
#         items_dict = _convert_search_results(result)
#         response_data = _create_search_response(result, unified_search_request, items_dict)
#         return Response.success(data=response_data)
#     except Exception as e:
#         return Response.error(message=f"按类型搜索失败: {str(e)}")

# @router.get("/search/post")
# async def search_posts(
#     request: Request,
#     keywords: Optional[str] = Query(None, description="关键词"),
#     category_ids: Optional[List[int]] = Query(None, description="分类ID列表"),
#     tags: Optional[List[str]] = Query(None, description="标签列表"),
#     min_likes: Optional[int] = Query(None, description="最小点赞数"),
#     max_likes: Optional[int] = Query(None, description="最大点赞数"),
#     start_time: Optional[datetime] = Query(None, description="开始时间"),
#     end_time: Optional[datetime] = Query(None, description="结束时间"),
#     sort_order: SortOrder = Query(SortOrder.TIME_DESC, description="排序方式"),
#     page: int = Query(1, description="页码"),
#     page_size: int = Query(10, description="每页数量")
# ):
#     """帖子搜索接口，支持多种条件组合搜索"""
#     try:
#         post_search_request = PostSearchRequest(
#             keywords=keywords,
#             category_ids=category_ids,
#             tags=tags,
#             min_likes=min_likes,
#             max_likes=max_likes,
#             start_time=start_time,
#             end_time=end_time,
#             sort_order=sort_order,
#             page=page,
#             page_size=page_size
#         )
#         loop = asyncio.get_event_loop()
#         result = await loop.run_in_executor(None, lambda: search_by_post_request(post_search_request))
#         return Response.success(data={
#             "total": result["total"],
#             "page": result["page"],
#             "page_size": result["page_size"],
#             "total_pages": result["total_pages"],
#             "posts": [PostSearchItem(**post) for post in result["posts"]]
#         })
#     except Exception as e:
#         return Response.error(message=f"帖子搜索失败: {str(e)}")

# def generate_suggested_keywords(keyword: str) -> List[str]:
#     """根据关键词生成推荐关键词"""
#     if not keyword:
#         return []

#     keyword_map = {
#         "南开": ["南开大学", "南开精神", "南开校园"],
#         "课程": ["选课", "课表", "教材", "考试"],
#         "考试": ["期末考试", "考试安排", "复习资料"],
#         "活动": ["社团活动", "校园活动", "文艺演出"],
#         "食堂": ["餐厅", "美食", "饭卡"]
#     }

#     for key, values in keyword_map.items():
#         if key in keyword:
#             return values[:5]

#     return []

# @router.get("/related-search")
# async def related_search_endpoint(
#     request: Request,
#     keyword: str = Query(..., description="关键词")
# ):
#     """相关搜索接口"""
#     try:
#         api_logger = request.state.api_logger
#         if not keyword:
#             return Response.bad_request(details={"message": "缺少 keyword 参数"})

#         api_logger.debug(f"Search suggest request, keyword: {keyword}")
#     except Exception as e:
#         return Response.error(message=f"搜索建议失败: {str(e)}")

# @router.get("")
# async def search_endpoint(request: Request, search_type: str = Body(...)):
#     """通用搜索接口"""