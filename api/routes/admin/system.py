from typing import Dict, Any
from fastapi import Query, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from fastapi import Depends
import time

from etl.load.db_pool_manager import (
    get_pool_stats,
    get_active_instances,
    get_max_mysql_connections,
    get_mysql_current_connections,
    resize_pool_if_needed,
    CONNECTION_POOL
)
from api.routes.admin import admin_router
from api.common import get_api_logger_dep, handle_api_errors

@admin_router.get("/system/db-pool", response_model=Dict[str, Any])
@handle_api_errors("获取数据库连接池状态")
async def get_db_pool_status(api_logger=Depends(get_api_logger_dep)):
    """获取数据库连接池状态信息"""
    try:
        # 获取本实例连接池统计信息
        stats = get_pool_stats()
        
        # 获取所有活跃实例
        active_instances = get_active_instances()
        
        # 获取MySQL连接信息
        max_connections = get_max_mysql_connections()
        current_connections = get_mysql_current_connections()
        
        # 计算使用率
        usage_ratio = current_connections / max_connections if max_connections > 0 else 0
        
        return {
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
        }
    except Exception as e:
        api_logger.error(f"获取数据库连接池状态失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取数据库连接池状态失败: {str(e)}")
        
@admin_router.post("/system/db-pool/resize", response_model=Dict[str, Any])
@handle_api_errors("调整数据库连接池大小")
async def resize_db_pool(
    size: int = Query(..., description="新的连接池大小", ge=4, le=64),
    api_logger=Depends(get_api_logger_dep)
):
    """手动调整数据库连接池大小"""
    try:
        # 获取当前连接池大小
        current_size = getattr(CONNECTION_POOL, 'pool_size', 0)
        api_logger.info(f"手动调整连接池大小: {current_size} -> {size}")
        
        # 修改后的函数需要实现
        result = resize_pool_if_needed(force_size=size)
        
        return {
            "status": "success" if result else "error",
            "message": f"连接池大小已调整为 {size}" if result else "连接池大小调整失败",
            "previous_size": current_size,
            "new_size": size if result else current_size,
            "timestamp": time.time()
        }
    except Exception as e:
        api_logger.error(f"调整数据库连接池大小失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"调整连接池大小失败: {str(e)}") 