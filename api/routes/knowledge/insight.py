#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
洞察相关的API
"""
from datetime import date, datetime
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, Dict, Any

from api.models.common import Response, PaginationInfo
from etl.load import db_core
from core.utils.logger import register_logger

# 遵循规范，创建模块专用的日志记录器
logger = register_logger('api.insight')

router = APIRouter(tags=["Knowledge"])

@router.get("/insight", summary="获取结构化洞察列表")
async def get_insight(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    category: Optional[str] = Query(None, description="按分类筛选，例如：官方, 社区, 集市"),
    date_str: Optional[str] = Query(None, alias="date", description="按日期筛选 (格式 YYYY-MM-DD)。不提供则默认为今天。若需获取所有日期的洞察，请传入 'all'。"),
):
    """
    分页获取结构化的洞察信息。
    - 支持按 **分类** 和 **日期** 进行筛选。
    - 返回结果按日期倒序排列。
    """
    try:
        conditions: Dict[str, Any] = {}
        if category:
            conditions['category'] = category

        target_date = date_str
        if target_date is None:
            target_date = date.today().isoformat()

        if target_date.lower() != 'all':
            try:
                datetime.strptime(target_date, "%Y-%m-%d")
                # 使用 DATE() 函数进行比较，忽略时间部分
                conditions['where_condition'] = "DATE(insight_date) = %s"
                conditions['params'] = [target_date]
            except ValueError:
                raise HTTPException(status_code=400, detail="日期格式无效，请使用 YYYY-MM-DD 格式，或传入 'all'。")

        logger.debug(f"查询洞察的条件: {conditions}")

        # 使用db_core中的函数式查询接口，更安全简洁
        result = await db_core.query_records(
            table_name="insights",
            conditions=conditions,
            order_by={"insight_date": "DESC", "id": "DESC"},
            limit=page_size,
            offset=(page - 1) * page_size
        )
        
        logger.debug(f"数据库查询结果: {result}")

        insights_data = result.get('data', [])
        total = result.get('total', 0)

        pagination = PaginationInfo(
            total=total, 
            page=page, 
            page_size=page_size
        )
        
        return Response.paged(
            data=insights_data, 
            pagination=pagination,
            message="成功"
        )

    except Exception as e:
        logger.error(f"获取洞察列表时发生错误: {e}", exc_info=True)
        return Response.error(details={"message": "获取洞察列表时发生内部错误"})