from typing import Dict, Any
from fastapi import Query, Depends, APIRouter
from fastapi.security import OAuth2PasswordRequestForm
import time
from etl.load.db_pool_manager import (
    get_pool_stats,
    get_active_instances,
    get_max_mysql_connections,
    get_mysql_current_connections,
    resize_pool_if_needed,
    CONNECTION_POOL
)
from api.models.common import Response, Request, validate_params

router = APIRouter()

@router.get("/dbpool/status")
async def get_db_pool_status(request: Request):
    """获取数据库连接池状态信息"""
    try:
        stats = get_pool_stats()

        active_instances = get_active_instances()

        max_connections = get_max_mysql_connections()
        current_connections = get_mysql_current_connections()

        usage_ratio = current_connections / max_connections if max_connections > 0 else 0

        return Response.success(data={
            "status": "ok",
            "instance": stats,
            "active_instances": len(active_instances),
            "instances_detail": active_instances,
            "mysql_connections": {
                "max": max_connections,
                "current": current_connections,
                "usage_ratio": usage_ratio
            },
            "timestamp": time.time()
        },details={"message":"获取数据库连接池状态成功"})
    except Exception as e:
        return Response.error(details={"message": f"获取数据库连接池状态失败: {str(e)}"}) 

@router.post("/dbpool/resize")
async def resize_db_pool(request: Request):
    """动态调整数据库连接池大小"""
    try:
        req_data = await request.json()
        required_params = ["size"]
        error_response = validate_params(req_data, required_params)
        if(error_response):
            return error_response

        size = req_data.get("size")
        if not isinstance(size, int) or size <= 0:
            return Response.bad_request(details={"message": "size 必须是正整数"})

        config.set("database.pool_size", size)
        db_pool.resize(size) # type: ignore
        return Response.success(details={"message": f"数据库连接池大小已调整为: {size}"})
    except Exception as e:
        return Response.error(details={"message": f"调整数据库连接池大小失败: {str(e)}"})