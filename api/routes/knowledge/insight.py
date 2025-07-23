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

        # 如果 date_str 不是 'all', 则需要先确定要查询的具体日期
        if not date_str or date_str.lower() != 'all':
            # 查找目标日期：
            # 1. 如果提供了 date_str, 则查找 <= date_str 的最新日期
            # 2. 如果未提供 date_str, 则查找最新的日期
            date_find_conditions: Dict[str, Any] = {}
            where_parts = []
            params_list = []

            if category:
                date_find_conditions['category'] = category
            
            if date_str:
                try:
                    datetime.strptime(date_str, "%Y-%m-%d")
                    where_parts.append("DATE(insight_date) <= %s")
                    params_list.append(date_str)
                except ValueError:
                    raise HTTPException(status_code=400, detail="日期格式无效，请使用 YYYY-MM-DD 格式，或传入 'all'。")

            if where_parts:
                date_find_conditions['where_condition'] = " AND ".join(where_parts)
                date_find_conditions['params'] = params_list

            # 查询满足条件的最大日期
            date_result = await db_core.query_records(
                table_name="insights",
                fields=["MAX(DATE(insight_date)) as max_date"],
                conditions=date_find_conditions,
                limit=1
            )
            
            target_date = None
            if date_result.get('data') and date_result['data'][0].get('max_date'):
                target_date = date_result['data'][0]['max_date']

            # 如果没有找到任何符合条件的日期，直接返回空结果
            if not target_date:
                pagination = PaginationInfo(total=0, page=page, page_size=page_size)
                return Response.paged(data=[], pagination=pagination, message="成功")

            # 使用找到的日期作为最终查询条件
            conditions['where_condition'] = "DATE(insight_date) = %s"
            conditions['params'] = [target_date]
        # 如果 date_str 是 'all', 则不添加任何日期条件，查询所有记录

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