#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
洞察相关的API
"""
import datetime
import json
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List, Dict, Any

from api.models.common import ApiResponse, Pagination
from api.models.knowledge import Insight
from etl.load import db_core
from core.utils.logger import register_logger

# 遵循规范，创建模块专用的日志记录器
logger = register_logger('api.routes.knowledge.insights')

router = APIRouter(prefix="/knowledge", tags=["Knowledge"])

@router.get("/insights", response_model=ApiResponse[List[Insight]], summary="获取结构化洞察列表")
async def get_insights(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    category: Optional[str] = Query(None, description="按分类筛选，例如：官方, 社区, 集市"),
    date: Optional[str] = Query(None, description="按日期筛选，格式 YYYY-MM-DD"),
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
        
        if date:
            try:
                # 仅验证格式，不转换
                datetime.datetime.strptime(date, "%Y-%m-%d")
                conditions['insight_date'] = date
            except ValueError:
                raise HTTPException(status_code=400, detail="日期格式无效，请使用 YYYY-MM-DD 格式。")

        # 使用db_core中的函数式查询接口，更安全简洁
        result = await db_core.query_records(
            table_name="insights",
            conditions=conditions,
            order_by={"insight_date": "DESC", "id": "DESC"},
            limit=page_size,
            offset=(page - 1) * page_size
        )
        
        # db_core.query_records 返回包含 'data' 和 'total' 的字典
        insights_data = result.get('data', [])
        total = result.get('total', 0)

        # 虽然Pydantic用于文档，但手动处理以确保datetime等类型正确序列化
        processed_results = []
        if insights_data:
            for row in insights_data:
                # 直接将row（已经是dict）传递，Pydantic模型在文档层生效
                processed_results.append(row)

        pagination = Pagination(total=total, page=page, page_size=page_size)
        
        return ApiResponse(
            code=200, 
            message="成功", 
            data=processed_results, 
            pagination=pagination
        )

    except Exception as e:
        logger.error(f"获取洞察列表时发生错误: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="获取洞察列表时发生服务器错误") 