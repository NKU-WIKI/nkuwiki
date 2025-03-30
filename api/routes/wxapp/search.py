"""
微信小程序搜索API
提供小程序搜索功能
"""
from fastapi import Query, APIRouter, Body
from api.models.common import Response, Request, validate_params

from etl.load.db_core import (
    async_query_records, async_execute_custom_query
)
from core.utils.logger import register_logger

router = APIRouter()
logger = register_logger('api.routes.wxapp.search')

@router.get("/suggestion")
async def get_search_suggest(
    keyword: str = Query(..., description="搜索关键词")
):
    """搜索建议"""
    try:
        logger.debug(f"获取搜索建议: keyword={keyword}")
        suggestions = await async_execute_custom_query(
            "SELECT keyword FROM wxapp_search_history WHERE keyword LIKE %s GROUP BY keyword ORDER BY COUNT(*) DESC LIMIT 5",
            [f"%{keyword}%"]
        )
        return Response.success(data=[s["keyword"] for s in suggestions])
    except Exception as e:
        logger.error(f"获取搜索建议失败: {str(e)}")
        return Response.error(details={"message": f"获取搜索建议失败: {str(e)}"})

@router.get("/search")
async def search(
    keyword: str = Query(..., description="搜索关键词"),
    search_type: str = Query("all", description="搜索类型: all, post, user"),
    page: int = Query(1, description="页码"),
    limit: int = Query(10, description="返回结果数量")
):
    """综合搜索"""
    try:
        logger.debug(f"执行搜索: keyword={keyword}, search_type={search_type}, page={page}, limit={limit}")
        offset = (page - 1) * limit
        search_results = []
        total = 0
        
        if search_type == "all" or search_type == "post":
            # 搜索帖子
            post_sql = """
            SELECT id, openid, title, content, category_id, view_count, like_count, 
                   comment_count, favorite_count, create_time, update_time
            FROM wxapp_post
            WHERE status = 1 AND (title LIKE %s OR content LIKE %s)
            ORDER BY update_time DESC
            LIMIT %s OFFSET %s
            """
            posts = await async_execute_custom_query(
                post_sql, 
                [f"%{keyword}%", f"%{keyword}%", limit, offset]
            )
            
            # 获取帖子总数
            post_count_sql = """
            SELECT COUNT(*) as total FROM wxapp_post
            WHERE status = 1 AND (title LIKE %s OR content LIKE %s)
            """
            post_count = await async_execute_custom_query(
                post_count_sql,
                [f"%{keyword}%", f"%{keyword}%"]
            )
            post_total = post_count[0]['total'] if post_count else 0
            total += post_total
            
            # 添加帖子结果
            for post in posts:
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
        
        if search_type == "all" or search_type == "user":
            # 搜索用户
            user_sql = """
            SELECT id, openid, nickname, avatar, bio
            FROM wxapp_user
            WHERE status = 1 AND (nickname LIKE %s OR bio LIKE %s)
            ORDER BY update_time DESC
            LIMIT %s OFFSET %s
            """
            users = await async_execute_custom_query(
                user_sql,
                [f"%{keyword}%", f"%{keyword}%", limit, offset]
            )
            
            # 获取用户总数
            user_count_sql = """
            SELECT COUNT(*) as total FROM wxapp_user
            WHERE status = 1 AND (nickname LIKE %s OR bio LIKE %s)
            """
            user_count = await async_execute_custom_query(
                user_count_sql,
                [f"%{keyword}%", f"%{keyword}%"]
            )
            user_total = user_count[0]['total'] if user_count else 0
            total += user_total
            
            # 添加用户结果
            for user in users:
                search_results.append({
                    "id": user["id"],
                    "openid": user["openid"],
                    "nickname": user["nickname"],
                    "avatar": user["avatar"],
                    "bio": user["bio"],
                    "type": "user"
                })
        
        # 记录搜索历史
        await _record_search_history(keyword)
        
        # 计算分页
        pagination = {
            "total": total,
            "page": page,
            "page_size": limit,
            "total_pages": (total + limit - 1) // limit if limit > 0 else 1
        }
        
        response_data = {
            "results": search_results,
            "total": total,
            "keyword": keyword,
            "search_type": search_type
        }
        
        return Response.paged(
            data=response_data["results"],
            pagination=pagination,
            details={"keyword": keyword, "search_type": search_type}
        )
    except Exception as e:
        logger.error(f"搜索失败: {str(e)}")
        return Response.error(details={"message": f"搜索失败: {str(e)}"})

async def _record_search_history(keyword, openid=None):
    """记录搜索历史"""
    try:
        # 简化版本，只记录关键词
        if not keyword:
            return
            
        await async_execute_custom_query(
            "INSERT INTO wxapp_search_history (keyword, search_time, openid) VALUES (%s, NOW(), %s)",
            [keyword, openid or "anonymous"]
        )
    except Exception:
        # 记录搜索历史失败不影响主流程
        pass

@router.get("/history")
async def get_search_history(
    openid: str = Query(..., description="用户OpenID"),
    limit: int = Query(10, description="返回结果数量")
):
    """获取搜索历史"""
    try:
        logger.debug(f"获取搜索历史: openid={openid}, limit={limit}")
        if not openid:
            return Response.bad_request(details={"message": "缺少openid参数"})

        history = await async_query_records(
            table_name="wxapp_search_history",
            conditions={"openid": openid},
            order_by="search_time DESC",
            limit=limit
        )
        
        # 去重
        unique_keywords = []
        seen = set()
        if history and 'data' in history:
            for item in history['data']:
                if item['keyword'] not in seen:
                    seen.add(item['keyword'])
                    unique_keywords.append(item)
        
        return Response.success(data=unique_keywords)
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
            [openid]
        )
        
        return Response.success(details={"message": "清空搜索历史成功"})
    except Exception as e:
        logger.error(f"清空搜索历史失败: {str(e)}")
        return Response.error(details={"message": f"清空搜索历史失败: {str(e)}"})

@router.get("/hot")
async def get_hot_searches(
    limit: int = Query(10, description="返回结果数量")
):
    """获取热门搜索"""
    try:
        logger.debug(f"获取热门搜索: limit={limit}")
        hot_searches = await async_execute_custom_query(
            """
            SELECT keyword, COUNT(*) as count 
            FROM wxapp_search_history 
            WHERE search_time > DATE_SUB(NOW(), INTERVAL 7 DAY)
            GROUP BY keyword 
            ORDER BY count DESC 
            LIMIT %s
            """,
            [limit]
        )
        
        return Response.success(data=hot_searches)
    except Exception as e:
        logger.error(f"获取热门搜索失败: {str(e)}")
        return Response.error(details={"message": f"获取热门搜索失败: {str(e)}"}) 