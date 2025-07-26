"""
微信小程序互动动作API接口
包括点赞、收藏、关注等功能
"""
import asyncio
from typing import Dict, Any

import aiomysql
from fastapi import APIRouter, Body, Depends

from api.common.dependencies import get_current_active_user
from api.models.common import Response
from ._utils import _update_count, create_notification
from core.utils.logger import register_logger
from etl.load import execute_custom_query, insert_record
from etl.load.db_pool_manager import get_db_connection as _get_db_connection

# 模块初始化
logger = register_logger('api.routes.wxapp.action')
router = APIRouter()

# --- 配置常量 ---

# 定义动作到表和计数器字段的映射
ACTION_CONFIG = {
    "post": {
        "table": "wxapp_post",
        "id_column": "id",
        "fields": {"like": "like_count", "favorite": "favorite_count"}
    },
    "comment": {
        "table": "wxapp_comment",
        "id_column": "id",
        "fields": {"like": "like_count"}
    },
    "user": {
        "table": "wxapp_user",
        "id_column": "id",
        "fields": {"follow": "follower_count"}
    }
}


async def _handle_notification(
    current_user: Dict[str, Any],
    resource: Dict[str, Any],
    target_id: str,
    target_type: str,
    action_type: str,
    is_active: bool
):
    """处理发送通知的逻辑"""
    # 只有在点赞/关注等激活操作时才发送通知
    if not is_active:
        return

    sender_openid = current_user['openid']
    recipient_openid = resource.get('openid') if target_type != 'user' else target_id

    # 自己给自己操作，或没有接收者，则不发通知
    if not recipient_openid or recipient_openid == sender_openid:
        return

    try:
        sender_payload = {
            "openid": sender_openid,
            "avatar": current_user.get("avatar", ""),
            "nickname": current_user.get("nickname", "一位热心用户")
        }
        
        action_text_map = {"like": "赞了", "favorite": "收藏了", "follow": "关注了"}
        resource_name_map = {"post": "帖子", "comment": "评论", "user": "你"}

        action_text = action_text_map.get(action_type, "操作了")
        resource_name = resource_name_map.get(target_type, "内容")

        content_preview = ""
        if target_type in ["post", "comment"]:
            text = resource.get('content') if target_type == 'comment' else resource.get('title', '无标题')
            content_preview = f"「{text[:20]}...」" if len(text) > 20 else f"「{text}」"
        
        title = f"你收到了一个新{action_text[:-1]}"
        content = f"{sender_payload['nickname']} {action_text}你的{resource_name}{content_preview}。"

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


@router.post("/toggle", summary="通用点赞/收藏/关注操作")
async def toggle_action(
    action_data: Dict[str, Any] = Body(...),
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    通用切换操作：点赞/取消点赞、收藏/取消收藏、关注/取消关注。
    """
    try:
        # 1. 参数校验和配置获取
        target_id = action_data.get("target_id")
        target_type = action_data.get("target_type")
        action_type = action_data.get("action_type")

        if not all([target_id, target_type, action_type]):
            return Response.bad_request(details={"message": "缺少必要参数: target_id, target_type, 或 action_type"})

        config = ACTION_CONFIG.get(target_type)
        if not config or action_type not in config["fields"]:
            return Response.bad_request(details={"message": f"不支持的操作: {target_type} {action_type}"})

        # 2. 检查目标资源是否存在
        resource_result = await execute_custom_query(
            f"SELECT * FROM {config['table']} WHERE {config['id_column']} = %s", (target_id,)
        )
        if not resource_result:
            return Response.not_found(resource=f"目标资源 {target_type} (id: {target_id})")
        resource = resource_result[0]

        # 3. 核心数据库操作
        user_id = current_user['id']
        
        # 检查当前状态
        existing_action = await execute_custom_query(
            "SELECT id FROM wxapp_action WHERE user_id = %s AND action_type = %s AND target_id = %s AND target_type = %s",
            (user_id, action_type, target_id, target_type),
            fetch='one'
        )

        is_active = False
        latest_count = resource.get(config["fields"][action_type], 0)

        async with _get_db_connection() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await conn.begin()
                try:
                    count_field = config["fields"][action_type]

                    if existing_action:
                        # 如果记录存在，则删除
                        await cursor.execute(
                            "DELETE FROM wxapp_action WHERE id = %s",
                            (existing_action['id'],)
                        )
                        await cursor.execute(
                            f"UPDATE {config['table']} SET {count_field} = GREATEST(0, {count_field} - 1) WHERE id = %s",
                            (target_id,)
                        )
                        is_active = False
                    else:
                        # 创建新操作
                        await cursor.execute(
                            "INSERT INTO wxapp_action (user_id, action_type, target_id, target_type) VALUES (%s, %s, %s, %s)",
                            (user_id, action_type, target_id, target_type)
                        )
                        await cursor.execute(
                            f"UPDATE {config['table']} SET {count_field} = {count_field} + 1 WHERE id = %s",
                            (target_id,)
                        )
                        is_active = True

                    # 重新查询最新的计数值
                    await cursor.execute(f"SELECT {count_field} FROM {config['table']} WHERE id = %s", (target_id,))
                    result = await cursor.fetchone()
                    latest_count = result[count_field]

                    await conn.commit()

                except Exception as e:
                    await conn.rollback()
                    raise e

        # 更新相关用户的总计数
        amount = 1 if is_active else -1
        if target_type in ["post", "comment"]:
            author_id = resource.get("user_id")
            if author_id:
                author_count_field = action_type + "_count"
                await _update_count("wxapp_user", author_id, author_count_field, amount)

        if action_type == "follow":
            # 更新被关注者的粉丝数
            await _update_count("wxapp_user", target_id, "follower_count", amount)
            # 更新操作发起者的关注数
            await _update_count("wxapp_user", user_id, "following_count", amount)

        # 5. 异步发送通知
        asyncio.create_task(
            _handle_notification(current_user, resource, target_id, target_type, action_type, is_active)
        )

        return Response.success(data={"is_active": is_active, "count": latest_count if latest_count is not None else 0})

    except Exception as e:
        error_message = f"切换操作失败: {str(e) if str(e) != '0' else '未知错误'}"
        logger.error(f"Toggle action failed: {error_message}", exc_info=True)
        return Response.error(details={"message": error_message})



