"""
微信小程序搜索API
提供小程序搜索功能
"""
from fastapi import Query, APIRouter, Body
from api.models.common import Response, Request, validate_params
import asyncio

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
        if not keyword.strip():
            return Response.success(data=[])
            
        suggestions = await async_execute_custom_query(
            """
            SELECT keyword 
            FROM wxapp_search_history 
            WHERE keyword LIKE %s 
            GROUP BY keyword 
            ORDER BY COUNT(*) DESC, MAX(search_time) DESC
            LIMIT 5
            """,
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
        if not keyword.strip():
            return Response.bad_request(details={"message": "搜索关键词不能为空"})
            
        logger.debug(f"执行搜索: keyword={keyword}, search_type={search_type}, page={page}, limit={limit}")
        offset = (page - 1) * limit
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
                    [f"%{keyword}%", f"%{keyword}%", limit, offset]
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
                    [f"%{keyword}%", f"%{keyword}%"]
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
                    [f"%{keyword}%", f"%{keyword}%", limit, offset]
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
                    [f"%{keyword}%", f"%{keyword}%"]
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
        asyncio.create_task(_record_search_history(keyword))
        
        # 计算分页
        pagination = {
            "total": total,
            "page": page,
            "page_size": limit,
            "total_pages": (total + limit - 1) // limit if limit > 0 else 1
        }
        
        return Response.paged(
            data=search_results,
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
    limit: int = Query(10, description="返回结果数量")
):
    """获取搜索历史"""
    try:
        logger.debug(f"获取搜索历史: openid={openid}, limit={limit}")
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
        
        history = await async_execute_custom_query(history_sql, [openid, limit])
        
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
        
        return Response.success(data=hot_searches or [])
    except Exception as e:
        logger.error(f"获取热门搜索失败: {str(e)}")
        return Response.error(details={"message": f"获取热门搜索失败: {str(e)}"}) 