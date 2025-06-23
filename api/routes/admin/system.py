from fastapi import APIRouter
import time
from etl.load.db_pool_manager import db_pool
from api.models.common import Response

router = APIRouter()

@router.get("/dbpool/status", summary="获取数据库连接池状态")
async def get_db_pool_status():
    """获取 aiomysql 数据库连接池的状态信息。"""
    try:
        if not db_pool:
            return Response.error(message="连接池未初始化")

        return Response.success(data={
            "status": "ok",
            "provider": "aiomysql",
            "minsize": db_pool.minsize,
            "maxsize": db_pool.maxsize,
            "current_size": db_pool.size,
            "free_size": db_pool.freesize,
            "timestamp": time.time()
        })
    except Exception as e:
        return Response.error(message=f"获取数据库连接池状态失败: {str(e)}")