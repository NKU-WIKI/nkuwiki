
from fastapi import APIRouter
from api.models.common import Request, Response, validate_params
from etl.load.db_core import (
    query_records, get_record_by_id, insert_record, update_record, count_records, delete_record,
    async_query_records, async_get_by_id, async_insert, async_update, async_count_records, execute_custom_query
)

router = APIRouter()

# 幂等操作用get请求，用查询参数，不用路径参数和请求体
# 非幂等操作用post请求，用请求体，不用查询参数
@router.get("/endpoint")
async def endpoint(request: Request): 
    try:
        # 参数验证
        required_params = ["openid", "param1", "param2"]
        error_response = await validate_params(request, required_params)
        if(error_response):
            return error_response
        # 业务逻辑... 使用etl.load.db_core 中的方法直接操作表
        # 失败
        if(f1):
            return Response.bad_request(details={"message": f"操作失败: {str(e)}"})
        if(f2):
            return Response.not_found(details={"message": "xxx不存在"})
        # ....
        # 成功
        return Response.success(details={"message": "xxx操作成功"})
    except Exception as e:
        return Response.error(details=f"未预料到的错误: {str(e)}")

