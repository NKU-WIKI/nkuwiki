"""
微信小程序互动动作API接口
包括点赞、收藏、关注等功能
"""
from fastapi import APIRouter, Query, Body, Depends
from api.models.common import Response, validate_params
from etl.load import (
    get_by_id
)
from etl.load.db_pool_manager import get_db_connection as _get_db_connection
from typing import Dict, Any
import aiomysql
from core.utils.logger import register_logger
from ._utils import _update_count, create_notification

# 配置日志
logger = register_logger('api.routes.wxapp.action')
# 初始化路由器
router = APIRouter()

@router.post("/toggle", summary="通用点赞/收藏/关注操作")
async def toggle_action(
    action_data: Dict[str, Any] = Body(...)
):
    """
    通用切换操作：点赞/取消点赞、收藏/取消收藏、关注/取消关注。
    """
    try:
        # 参数验证
        required_params = ["target_id", "target_type", "action_type", "openid"]
        error_response = validate_params(action_data, required_params)
        if error_response:
            return error_response

        target_id = action_data["target_id"]
        target_type = action_data["target_type"]
        action_type = action_data["action_type"]
        openid = action_data["openid"]

        # 检查目标资源是否存在
        table_name_map = {
            "post": "wxapp_post",
            "comment": "wxapp_comment",
            "user": "wxapp_user"
        }
        table_name = table_name_map.get(target_type)
        if not table_name:
            return Response.bad_request(details={"message": f"不支持的目标类型: {target_type}"})

        id_column = 'openid' if target_type == 'user' else 'id'
        resource = await get_by_id(table_name, target_id, id_column=id_column)
        if not resource:
            return Response.not_found(resource=f"目标资源 {target_type}")

        async with _get_db_connection() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                # 尝试直接删除动作，根据影响的行数判断是取消还是执行
                delete_query = "DELETE FROM wxapp_action WHERE openid = %s AND action_type = %s AND target_id = %s AND target_type = %s"
                affected_rows = await cursor.execute(delete_query, (openid, action_type, target_id, target_type))

                if affected_rows > 0:
                    # 删除了记录，说明是取消操作
                    is_active = False
                    amount = -1
                else:
                    # 未删除任何记录，说明是新增操作
                    insert_query = "INSERT INTO wxapp_action (openid, action_type, target_id, target_type) VALUES (%s, %s, %s, %s)"
                    await cursor.execute(insert_query, (openid, action_type, target_id, target_type))
                    is_active = True
                    amount = 1

                # 使用新的通用函数更新计数
                count_field_map = {
                    "post": {"like": "like_count", "favorite": "favorite_count"},
                    "comment": {"like": "like_count", "favorite": "favorite_count"},
                    "user": {"follow": "follower_count"}
                }
                
                count_field = count_field_map.get(target_type, {}).get(action_type)
                
                if count_field and table_name:
                    await _update_count(cursor, table_name, count_field, target_id, amount, id_column=id_column)
                
                # 单独处理操作发起者的计数
                if target_type == "user" and action_type == "follow":
                    # 更新被关注者的粉丝数在上面已处理，这里更新关注者自己的关注数
                    await _update_count(cursor, "wxapp_user", "following_count", openid, amount, id_column='openid')
                elif action_type == "favorite":
                    # 更新收藏者自己的总收藏数
                    await _update_count(cursor, "wxapp_user", "favorite_count", openid, amount, id_column='openid')

                await conn.commit()

        # 在事务之外发送通知
        if is_active:
            try:
                sender_info = await get_by_id("wxapp_user", openid, id_column='openid', fields=['nickname', 'avatar'])
                sender_payload = {"openid": openid, "avatar": sender_info.get("avatar", ""), "nickname": sender_info.get("nickname", "")}
                
                recipient_openid = None
                if target_type == "user":
                    recipient_openid = target_id
                elif resource.get("openid"):
                    recipient_openid = resource.get("openid")

                # 如果有接收者且不是给自己操作，则发送通知
                if recipient_openid and recipient_openid != openid:
                    action_text = {"like": "赞了", "favorite": "收藏了", "follow": "关注了"}.get(action_type, "操作了")
                    resource_name = {"post": "帖子", "comment": "评论", "user": "你"}.get(target_type, "内容")
                    
                    content_preview = ""
                    if target_type in ["post", "comment"]:
                        text = resource.get('content') if target_type == 'comment' else resource.get('title', '无标题')
                        content_preview = f"「{text[:20]}...」" if len(text) > 20 else f"「{text}」"
                    
                    title = f"你收到了一个新{action_text[:-1]}"
                    content = f"用户 {sender_payload['nickname']} {action_text}你的{resource_name}{content_preview}。"

                    await create_notification(
                        openid=recipient_openid,
                        title=title,
                        content=content,
                        target_id=target_id,
                        target_type=target_type,
                        sender_payload=sender_payload,
                        notification_type=action_type
                    )
            except Exception as notify_exc:
                logger.error(f"发送通知失败: {notify_exc}", exc_info=True)

        return Response.success(data={"is_active": is_active})

    except Exception as e:
        logger.error(f"Toggle action failed: {e}", exc_info=True)
        return Response.error(details={"message": str(e)})



