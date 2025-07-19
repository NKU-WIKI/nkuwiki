"""
违禁词管理API
"""
from fastapi import APIRouter, Depends, Body
from typing import List, Dict, Any

from api.models.common import Response, validate_params
from etl.load import db_core
from core.utils.logger import register_logger
from api.common.dependencies import get_current_admin_user

router = APIRouter()
logger = register_logger('api.routes.wxapp.banwords')

# --- 公开接口 (Public Endpoints) ---

@router.get("/library", summary="获取违禁词库")
async def get_banwords_library():
    """获取所有违禁词分类及其下的词汇。这是一个公开接口。"""
    try:
        query = """
            SELECT
                c.id as category_id,
                c.name as category_name,
                c.default_risk,
                w.word
            FROM
                wxapp_banword_categories c
            LEFT JOIN
                wxapp_banwords w ON c.id = w.category_id
            ORDER BY
                c.name, w.word;
        """
        results = await db_core.execute_custom_query(query)
        
        library = {}
        if results:
            for row in results:
                cat_name = row['category_name']
                if cat_name not in library:
                    library[cat_name] = {
                        'id': row['category_id'],
                        'default_risk': row['default_risk'],
                        'words': []
                    }
                if row['word']:
                    library[cat_name]['words'].append(row['word'])
        
        return Response.success(data={"library": library})
        
    except Exception as e:
        logger.error(f"获取违禁词库失败: {e}")
        return Response.error(details="服务器内部错误")

@router.get("/categories", summary="获取违禁词分类")
async def get_banword_categories():
    """获取所有违禁词的分类列表。这是一个公开接口。"""
    try:
        result = await db_core.query_records("wxapp_banword_categories", fields=["id", "name"], order_by={"name": "ASC"})
        return Response.success(data=result.get('data', []))
    except Exception as e:
        logger.error(f"获取违fen禁词分类失败: {e}")
        return Response.error(details="服务器内部错误")

# --- 管理员接口 (Admin Endpoints) ---

@router.post("/category", summary="创建新分类 (管理员)")
async def create_category(
    payload: Dict[str, Any] = Body(...),
    admin: Dict[str, Any] = Depends(get_current_admin_user)
):
    """创建一个新的违禁词分类。"""
    # 参数验证
    required_params = ['name']
    if error_msg := validate_params(payload, required_params):
        return error_msg

    category_data = {
        "name": payload.get("name"),
        "default_risk": payload.get("default_risk", 3)
    }

    try:
        category_id = await db_core.insert_record("wxapp_banword_categories", category_data)
        if not category_id:
            return Response.db_error(details="创建分类失败")
        return Response.success(data={"id": category_id}, message="分类创建成功")
    except Exception as e:
        # 处理唯一键冲突
        if "Duplicate entry" in str(e):
            return Response.bad_request(details=f"分类 '{payload.get('name')}' 已存在")
        logger.error(f"创建分类时出错: {e}")
        return Response.error(details="服务器内部错误")


@router.post("/words", summary="向分类中批量添加违禁词 (管理员)")
async def add_words_to_category(
    payload: Dict[str, Any] = Body(...),
    admin: Dict[str, Any] = Depends(get_current_admin_user)
):
    """向一个分类中批量添加多个违禁词。"""
    required_params = ['category_id', 'words']
    if error_msg := validate_params(payload, required_params):
        return error_msg
    
    category_id = payload.get("category_id")
    words_to_add = payload.get("words", [])

    if not isinstance(words_to_add, list):
        return Response.bad_request(details="参数 'words' 必须是一个列表")

    records = [{"category_id": category_id, "word": word} for word in words_to_add]
    
    try:
        # 使用批量插入，并忽略重复项
        inserted_count = await db_core.batch_insert("wxapp_banwords", records, ignore_duplicates=True)
        return Response.success(data={"added_count": inserted_count}, message="批量添加完成")
    except Exception as e:
        logger.error(f"批量添加违禁词时出错: {e}")
        return Response.error(details="服务器内部错误")

@router.delete("/word", summary="从分类中删除违禁词 (管理员)")
async def delete_word_from_category(
    payload: Dict[str, Any] = Body(...),
    admin: Dict[str, Any] = Depends(get_current_admin_user)
):
    """从一个分类中删除一个指定的违禁词。"""
    required_params = ['category_id', 'word']
    if error_msg := validate_params(payload, required_params):
        return error_msg

    conditions = {
        "category_id": payload.get("category_id"),
        "word": payload.get("word")
    }

    try:
        # 直接使用db_core中的删除功能
        deleted_count = await db_core.delete_records("wxapp_banwords", conditions)
        if deleted_count > 0:
            return Response.success(message="删除成功")
        else:
            return Response.not_found(details="指定的词在分类中不存在")
    except Exception as e:
        logger.error(f"删除违禁词时出错: {e}")
        return Response.error(details="服务器内部错误") 