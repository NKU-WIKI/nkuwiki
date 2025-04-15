"""
微信小程序互动动作API接口
包括点赞、收藏、关注等功能
"""
from fastapi import APIRouter, Query
from api.models.common import Response, Request, validate_params, PaginationInfo
from etl.load.db_core import (
    async_query_records, async_get_by_id, async_insert, async_update, async_count_records, 
    execute_query, async_execute_custom_query
)
import time
import json
import logging
import traceback
import os

# 配置日志
logger = logging.getLogger("wxapp.action")
logger.setLevel(logging.DEBUG)  # 设置为DEBUG级别以捕获所有日志

# 添加控制台处理器
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# 初始化路由器
router = APIRouter()

@router.post("/comment")
async def create_comment(request: Request):
    """创建新评论"""
    # 修改logger输出级别确保所有消息都会打印
    logger.setLevel(logging.DEBUG)
    for handler in logger.handlers:
        handler.setLevel(logging.DEBUG)
        
    try:
        print("开始创建评论...")
        req_data = await request.json()
        required_params = ["post_id", "content", "openid"]
        error_response = validate_params(req_data, required_params)
        if(error_response):
            return error_response

        openid = req_data.get("openid")
        post_id = req_data.get("post_id")
        content = req_data.get("content")
        parent_id = req_data.get("parent_id")
        image = req_data.get("image", [])
        
        print(f"参数校验通过: openid={openid}, post_id={post_id}, content={content}")

        post = await async_get_by_id(
            table_name="wxapp_post",
            record_id=post_id
        )
        if not post:
            print(f"帖子不存在: post_id={post_id}")
            return Response.not_found(resource="帖子")
            
        print(f"找到帖子: post_id={post_id}")

        if parent_id:
            parent_comment = await async_get_by_id(
                table_name="wxapp_comment",
                record_id=parent_id
            )
            if not parent_comment:
                print(f"父评论不存在: parent_id={parent_id}")
                return Response.not_found(resource="回复的评论")
                
            print(f"找到父评论: parent_id={parent_id}")
            
            # 更新父评论的回复计数
            try:
                await async_update(
                    table_name="wxapp_comment",
                    record_id=parent_id,
                    data={"reply_count": parent_comment.get("reply_count", 0) + 1}
                )
                print(f"更新父评论回复计数: parent_id={parent_id}, reply_count={parent_comment.get('reply_count', 0) + 1}")
            except Exception as e:
                print(f"更新父评论回复计数失败: {str(e)}")

        user = await async_query_records(
            table_name="wxapp_user",
            conditions={"openid": openid},
            limit=1
        )
        if not user or not user.get('data'):
            print(f"用户不存在: openid={openid}")
            return Response.not_found(resource="用户")
            
        print(f"找到用户: openid={openid}")

        comment_data = {
            "post_id": post_id,
            "openid": openid,
            "content": content,
            "parent_id": parent_id,
            "image": image,
            "like_count": 0,
            "status": 1
        }
        
        print(f"评论数据准备完成: {comment_data}")

        try:
            comment_id = await async_insert(
                table_name="wxapp_comment",
                data=comment_data
            )
            print(f"评论插入结果: comment_id={comment_id}")
            
            if comment_id <= 0:
                print(f"评论插入失败: comment_id={comment_id}")
                return Response.db_error(details={"message": f"未能成功插入评论，返回ID: {comment_id}"})
        except Exception as e:
            print(f"评论插入异常: {str(e)}")
            return Response.db_error(details={"message": f"评论创建失败: {str(e)}"})


        comment = await async_get_by_id(
            table_name="wxapp_comment",
            record_id=comment_id
        )
        try:
            await async_update(
                table_name="wxapp_post",
                record_id=post_id,
                data={"comment_count": post.get("comment_count", 0) + 1}
            )
        except Exception as e:
            return Response.db_error(details={"message": f"帖子评论数更新失败: {str(e)}"})

        if parent_id:
            try:
                parent_comment = await async_get_by_id(
                    table_name="wxapp_comment",
                    record_id=parent_id
                )
                logger.debug(f"获取父评论: parent_id={parent_id}, 结果={parent_comment}")
                
                if parent_comment and parent_comment["openid"] != openid:
                    # 对评论的回复应该每次都产生通知
                    logger.debug(f"创建评论回复通知前检查: post={post}, comment_id={comment_id}, parent_openid={parent_comment['openid']}")
                    
                    # 输出到终端方便调试
                    print(f"创建评论回复通知: post_id={post_id}, comment_id={comment_id}, parent_id={parent_id}")
                    print(f"creator_openid={openid}, parent_openid={parent_comment['openid']}")
                    
                    # 获取发送者的头像
                    sender_info_sql = "SELECT nickname, avatar FROM wxapp_user WHERE openid = %s LIMIT 1"
                    sender_info = await async_execute_custom_query(sender_info_sql, [openid])
                    sender_avatar = sender_info[0].get("avatar", "") if sender_info else ""
                    sender_nickname = sender_info[0].get("nickname", "") if sender_info else ""
                    
                    # 使用直接执行SQL的方式插入通知
                    notification_sql = """
                    INSERT INTO wxapp_notification (
                        openid, title, content, type, is_read, sender, target_id, 
                        target_type, status, create_time, update_time
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                    """
                    notification_params = [
                        parent_comment["openid"],
                        "收到新回复",
                        f"用户回复了你的评论",
                        "comment",
                        0,
                        json.dumps({"openid": openid, "avatar": sender_avatar, "nickname": sender_nickname}),  # 将sender作为JSON对象存储，添加avatar
                        int(comment_id),
                        "comment",
                        1
                    ]
                    logger.debug(f"SQL: {notification_sql}")
                    logger.debug(f"参数: {notification_params}")
                    
                    # 执行数据库查询前输出终端信息
                    print(f"执行SQL: {notification_sql}")
                    print(f"参数: {notification_params}")
                    
                    try:
                        # 使用execute_query直接执行SQL
                        notification_id = execute_query(
                            notification_sql, 
                            notification_params, 
                            fetch=False
                        )
                        logger.debug(f"评论回复通知创建结果: notification_id={notification_id}")
                        print(f"评论回复通知创建结果: notification_id={notification_id}")
                        
                        # 验证通知是否实际创建
                        check_sql = "SELECT * FROM wxapp_notification WHERE target_id = %s AND type = 'comment' ORDER BY id DESC LIMIT 1"
                        check_result = execute_query(check_sql, [int(comment_id)])
                        logger.debug(f"检查通知创建结果: {check_result}")
                        print(f"检查通知创建结果: {check_result}")
                        
                        if not notification_id:
                            logger.error(f"评论回复通知创建失败，返回结果: {notification_id}")
                    except Exception as ne:
                        logger.exception(f"创建评论回复通知异常: {str(ne)}")
                        logger.error(traceback.format_exc())
                        print(f"创建评论回复通知异常: {str(ne)}")
            except Exception as pe:
                logger.exception(f"获取父评论异常: {str(pe)}")
                logger.error(traceback.format_exc())
                print(f"获取父评论异常: {str(pe)}")
        elif post["openid"] != openid:
            try:
                # 对帖子的评论应该每次都产生通知
                logger.debug(f"创建帖子评论通知前检查: post={post}, comment_id={comment_id}")
                
                # 输出到终端方便调试
                print(f"创建帖子评论通知: post_id={post_id}, comment_id={comment_id}")
                print(f"creator_openid={openid}, post_owner_openid={post['openid']}")
                print(f"条件判断: post['openid']({post['openid']}) != openid({openid}) = {post['openid'] != openid}")
                
                # 获取发送者的头像
                sender_info_sql = "SELECT nickname, avatar FROM wxapp_user WHERE openid = %s LIMIT 1"
                sender_info = await async_execute_custom_query(sender_info_sql, [openid])
                sender_avatar = sender_info[0].get("avatar", "") if sender_info else ""
                sender_nickname = sender_info[0].get("nickname", "") if sender_info else ""
                
                # 使用async_execute_custom_query直接执行SQL
                notification_sql = """
                INSERT INTO wxapp_notification (
                    openid, title, content, type, is_read, sender, target_id, 
                    target_type, status, create_time, update_time
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                """
                safe_title = post.get('title', '无标题')
                notification_params = [
                    post["openid"],
                    "收到新评论",
                    f"用户评论了你的帖子「{safe_title}」",
                    "comment",
                    0,
                    json.dumps({"openid": openid, "avatar": sender_avatar, "nickname": sender_nickname}),  # 将sender作为JSON对象存储
                    int(comment_id),
                    "comment",
                    1
                ]
                
                print(f"执行SQL: {notification_sql}")
                print(f"参数: {notification_params}")
                
                try:
                    # 使用异步方式执行SQL
                    notification_id = await async_execute_custom_query(
                        notification_sql, 
                        notification_params, 
                        fetch=False
                    )
                    print(f"帖子评论通知创建结果: notification_id={notification_id}")
                    
                    # 验证通知是否实际创建
                    check_sql = "SELECT * FROM wxapp_notification WHERE target_id = %s AND type = 'comment' ORDER BY id DESC LIMIT 1"
                    check_result = await async_execute_custom_query(check_sql, [int(comment_id)])
                    print(f"检查通知创建结果: {check_result}")
                    
                    if not check_result:
                        print("警告: 无法找到刚刚创建的通知记录，尝试直接使用mysql命令插入")
                        # 备用方案: 使用mysql命令直接插入
                        safe_title_escape = safe_title.replace("'", "\\'").replace('"', '\\"')
                        # 获取用户头像和昵称用于备用方案
                        sender_avatar = sender_info[0].get("avatar", "").replace("'", "\\'").replace('"', '\\"') if sender_info else ""
                        sender_nickname = sender_info[0].get("nickname", "").replace("'", "\\'").replace('"', '\\"') if sender_info else ""
                        sender_json = json.dumps({"openid": openid, "avatar": sender_avatar, "nickname": sender_nickname}).replace("'", "\\'")
                        os_command = f"""
                        mysql -u root -p"root" -e "INSERT INTO nkuwiki.wxapp_notification (openid, title, content, type, is_read, sender, target_id, target_type, status, create_time, update_time) VALUES ('{post['openid']}', '收到新评论', '用户评论了你的帖子「{safe_title_escape}」', 'comment', 0, '{sender_json}', {int(comment_id)}, 'comment', 1, NOW(), NOW());"
                        """
                        print(f"执行备用命令: {os_command}")
                        os.system(os_command)
                    
                except Exception as ne:
                    print(f"创建帖子评论通知异常: {str(ne)}")
                    print(traceback.format_exc())
                
            except Exception as pe:
                print(f"处理帖子评论通知异常: {str(pe)}")
                print(traceback.format_exc())

        return Response.success(data=comment)

    except Exception as e:
        return Response.error(details={"message": f"创建评论失败: {str(e)}"})


@router.post("/comment/like")
async def like_comment(request: Request):
    """点赞/取消点赞评论"""
    try:
        req_data = await request.json()
        required_params = ["comment_id", "openid"]
        error_response = validate_params(req_data, required_params)
        if(error_response):
            return error_response

        openid = req_data.get("openid")
        comment_id = req_data.get("comment_id")

        comment = await async_get_by_id(
            table_name="wxapp_comment",
            record_id=comment_id
        )
        if not comment:
            return Response.not_found(resource="评论")

        # 查询是否已点赞
        like_record = await async_query_records(
            table_name="wxapp_action",
            conditions={
                "openid": openid,
                "action_type": "like",
                "target_id": comment_id,
                "target_type": "comment"
            },
            limit=1
        )

        already_liked = like_record and len(like_record.get('data', [])) > 0

        if already_liked:
            # 取消点赞
            try:
                execute_query(
                    "DELETE FROM wxapp_action WHERE openid = %s AND action_type = %s AND target_id = %s AND target_type = %s",
                    [openid, "like", comment_id, "comment"]
                )
            except Exception as e:
                return Response.db_error(details={"message": f"取消点赞失败: {str(e)}"})
            
            new_like_count = max(0, comment.get("like_count", 0) - 1)
            await async_update(
                table_name="wxapp_comment",
                record_id=comment_id,
                data={"like_count": new_like_count}
            )

            return Response.success(data={
                "success": True,
                "status": "unliked",
                "like_count": new_like_count,
                "is_liked": False
            }, details={"message": "取消点赞成功"})
        else:
            # 创建点赞
            try:
                like_id = await async_insert(
                    table_name="wxapp_action",
                    data={
                        "openid": openid,
                        "action_type": "like",
                        "target_id": comment_id,
                        "target_type": "comment"
                    }
                )
            except Exception as e:
                return Response.db_error(details={"message": f"点赞操作失败: {str(e)}"})

            new_like_count = comment.get("like_count", 0) + 1
            await async_update(
                table_name="wxapp_comment",
                record_id=comment_id,
                data={"like_count": new_like_count}
            )

            if openid != comment["openid"]:
                # 先检查是否已存在此类通知
                check_notification_sql = """
                SELECT id FROM wxapp_notification 
                WHERE openid = %s AND type = 'like' AND target_id = %s AND target_type = 'comment'
                AND sender LIKE %s
                LIMIT 1
                """
                existing_notification = await async_execute_custom_query(
                    check_notification_sql, 
                    [comment["openid"], comment_id, f'%{openid}%']
                )
                
                # 只有在不存在通知时才创建
                if not existing_notification:
                    # 获取发送者的头像和昵称
                    sender_info_sql = "SELECT nickname, avatar FROM wxapp_user WHERE openid = %s LIMIT 1"
                    sender_info = await async_execute_custom_query(sender_info_sql, [openid])
                    sender_avatar = sender_info[0].get("avatar", "") if sender_info else ""
                    sender_nickname = sender_info[0].get("nickname", "") if sender_info else ""
                    
                    notification_data = {
                        "openid": comment["openid"],
                        "title": "收到点赞",
                        "content": "有用户点赞了你的评论",
                        "type": "like",
                        "is_read": False,
                        "sender": json.dumps({"openid": openid, "avatar": sender_avatar, "nickname": sender_nickname}),  # 将sender作为JSON对象存储
                        "target_id": comment_id,
                        "target_type": "comment",
                        "status": 1
                    }

                    await async_insert(
                        table_name="wxapp_notification",
                        data=notification_data
                    )

            return Response.success(data={
                "success": True,
                "status": "liked",
                "like_count": new_like_count,
                "is_liked": True
            }, details={"message": "点赞成功"})

    except Exception as e:
        return Response.error(details={"message": f"操作失败: {str(e)}"})

@router.post("/post/like")
async def like_post(request: Request):
    """点赞/取消点赞帖子"""
    try:
        req_data = await request.json()
        required_params = ["post_id", "openid"]
        error_response = validate_params(req_data, required_params)
        if error_response:
            return error_response

        openid = req_data.get("openid")
        post_id = req_data.get("post_id")

        # 使用单一查询获取帖子信息
        post_query = """
        SELECT * FROM wxapp_post 
        WHERE id = %s
        """
        post_result = await async_execute_custom_query(post_query, [post_id])
        
        if not post_result:
            return Response.not_found(resource="帖子")
            
        post = post_result[0]

        # 使用直接SQL查询检查是否已点赞
        like_query = """
        SELECT id FROM wxapp_action 
        WHERE openid = %s AND action_type = 'like' AND target_id = %s AND target_type = 'post' 
        LIMIT 1
        """
        like_record = await async_execute_custom_query(like_query, [openid, post_id])
        
        already_liked = bool(like_record)

        if already_liked:
            # 取消点赞
            try:
                # 使用单一查询删除点赞记录
                delete_sql = """
                DELETE FROM wxapp_action 
                WHERE openid = %s AND action_type = 'like' AND target_id = %s AND target_type = 'post'
                """
                await async_execute_custom_query(delete_sql, [openid, post_id], fetch=False)
            except Exception as e:
                return Response.db_error(details={"message": f"取消点赞失败: {str(e)}"})
            
            new_like_count = max(0, post.get("like_count", 0) - 1)
            
            # 使用单一查询更新帖子点赞数
            update_post_sql = """
            UPDATE wxapp_post 
            SET like_count = %s 
            WHERE id = %s
            """
            await async_execute_custom_query(update_post_sql, [new_like_count, post_id], fetch=False)

            # 使用单一查询更新用户点赞数
            update_user_sql = """
            UPDATE wxapp_user 
            SET like_count = GREATEST(0, like_count - 1) 
            WHERE openid = %s
            """
            await async_execute_custom_query(update_user_sql, [openid], fetch=False)

            return Response.success(data={
                "success": True,
                "status": "unliked",
                "like_count": new_like_count,
                "is_liked": False
            }, details={"message": "取消点赞成功"})
        else:
            # 创建点赞
            try:
                # 使用单一查询插入点赞记录
                insert_sql = """
                INSERT INTO wxapp_action (openid, action_type, target_id, target_type, create_time, update_time)
                VALUES (%s, %s, %s, %s, NOW(), NOW())
                """
                await async_execute_custom_query(
                    insert_sql, 
                    [openid, "like", post_id, "post"], 
                    fetch=False
                )
            except Exception as e:
                return Response.db_error(details={"message": f"点赞操作失败: {str(e)}"})

            new_like_count = post.get("like_count", 0) + 1
            
            # 使用单一查询更新帖子点赞数
            update_post_sql = """
            UPDATE wxapp_post 
            SET like_count = %s 
            WHERE id = %s
            """
            await async_execute_custom_query(update_post_sql, [new_like_count, post_id], fetch=False)

            # 使用单一查询更新用户点赞数
            update_user_sql = """
            UPDATE wxapp_user 
            SET like_count = like_count + 1 
            WHERE openid = %s
            """
            await async_execute_custom_query(update_user_sql, [openid], fetch=False)

            # 创建通知
            if openid != post["openid"]:
                # 先检查是否已存在此类通知
                check_notification_sql = """
                SELECT id FROM wxapp_notification 
                WHERE openid = %s AND type = 'like' AND target_id = %s AND target_type = 'post'
                AND sender LIKE %s
                LIMIT 1
                """
                existing_notification = await async_execute_custom_query(
                    check_notification_sql, 
                    [post["openid"], post_id, f'%{openid}%']
                )
                
                # 只有在不存在通知时才创建
                if not existing_notification:
                    # 获取发送者的头像和昵称
                    sender_info_sql = "SELECT nickname, avatar FROM wxapp_user WHERE openid = %s LIMIT 1"
                    sender_info = await async_execute_custom_query(sender_info_sql, [openid])
                    sender_avatar = sender_info[0].get("avatar", "") if sender_info else ""
                    sender_nickname = sender_info[0].get("nickname", "") if sender_info else ""
                    
                    notification_sql = """
                    INSERT INTO wxapp_notification (
                        openid, title, content, type, is_read, sender, target_id, 
                        target_type, status, create_time, update_time
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                    """
                    notification_params = [
                        post["openid"],
                        "收到点赞",
                        f"有用户点赞了你的帖子「{post.get('title', '无标题')}」",
                        "like",
                        False,
                        json.dumps({"openid": openid, "avatar": sender_avatar, "nickname": sender_nickname}),  # 将sender作为JSON对象存储
                        post_id,
                        "post",
                        1
                    ]
                    await async_execute_custom_query(notification_sql, notification_params, fetch=False)

            return Response.success(data={
                "success": True,
                "status": "liked",
                "like_count": new_like_count,
                "is_liked": True
            }, details={"message": "点赞成功"})

    except Exception as e:
        logger.error(f"点赞操作失败: {e}")
        return Response.error(details={"message": f"操作失败: {str(e)}"})

@router.post("/post/favorite")
async def favorite_post(request: Request):
    """收藏/取消收藏帖子"""
    try:
        req_data = await request.json()
        required_params = ["post_id", "openid"]
        error_response = validate_params(req_data, required_params)
        if (error_response):
            return error_response

        openid = req_data.get("openid")
        post_id = req_data.get("post_id")
        
        # 获取帖子信息
        post_sql = "SELECT * FROM wxapp_post WHERE id = %s"
        post_result = await async_execute_custom_query(post_sql, [post_id])
        
        if not post_result:
            return Response.not_found(resource="帖子")
            
        post = post_result[0]

        # 检查是否已收藏
        favorite_sql = """
        SELECT * FROM wxapp_action 
        WHERE openid = %s AND action_type = 'favorite' AND target_id = %s AND target_type = 'post'
        LIMIT 1
        """
        favorite_result = await async_execute_custom_query(favorite_sql, [openid, post_id])
        
        has_favorited = bool(favorite_result)
        
        if has_favorited:
            # 取消收藏
            delete_sql = """
            DELETE FROM wxapp_action 
            WHERE openid = %s AND action_type = 'favorite' AND target_id = %s AND target_type = 'post'
            """
            await async_execute_custom_query(delete_sql, [openid, post_id], fetch=False)
            
            # 更新帖子收藏数
            new_count = max(0, post["favorite_count"] - 1)
            update_post_sql = "UPDATE wxapp_post SET favorite_count = %s WHERE id = %s"
            await async_execute_custom_query(update_post_sql, [new_count, post_id], fetch=False)
            
            # 更新被收藏用户的收藏数
            update_user_sql = """
            UPDATE wxapp_user 
            SET favorite_count = GREATEST(0, favorite_count - 1) 
            WHERE openid = %s
            """
            await async_execute_custom_query(update_user_sql, [post["openid"]], fetch=False)

            return Response.success(data={
                "success": True,
                "status": "unfavorited",
                "favorite_count": new_count,
                "is_favorited": False
            }, details={"message": "取消收藏成功"})
        else:
            # 创建收藏
            insert_sql = """
            INSERT INTO wxapp_action (openid, action_type, target_id, target_type, create_time, update_time)
            VALUES (%s, %s, %s, %s, NOW(), NOW())
            """
            await async_execute_custom_query(insert_sql, [openid, "favorite", post_id, "post"], fetch=False)

            # 更新帖子收藏数
            new_count = post["favorite_count"] + 1
            update_post_sql = "UPDATE wxapp_post SET favorite_count = %s WHERE id = %s"
            await async_execute_custom_query(update_post_sql, [new_count, post_id], fetch=False)

            # 更新被收藏用户的收藏数
            update_user_sql = "UPDATE wxapp_user SET favorite_count = favorite_count + 1 WHERE openid = %s"
            await async_execute_custom_query(update_user_sql, [post["openid"]], fetch=False)

            # 创建通知
            if post["openid"] != openid:
                # 先检查是否已存在此类通知
                check_notification_sql = """
                SELECT id FROM wxapp_notification 
                WHERE openid = %s AND type = 'favorite' AND target_id = %s AND target_type = 'post'
                AND sender LIKE %s
                LIMIT 1
                """
                existing_notification = await async_execute_custom_query(
                    check_notification_sql, 
                    [post["openid"], post_id, f'%{openid}%']
                )
                
                # 只有在不存在通知时才创建
                if not existing_notification:
                    # 获取发送者的头像和昵称
                    sender_info_sql = "SELECT nickname, avatar FROM wxapp_user WHERE openid = %s LIMIT 1"
                    sender_info = await async_execute_custom_query(sender_info_sql, [openid])
                    sender_avatar = sender_info[0].get("avatar", "") if sender_info else ""
                    sender_nickname = sender_info[0].get("nickname", "") if sender_info else ""
                    
                    notification_sql = """
                    INSERT INTO wxapp_notification (
                        openid, title, content, type, is_read, sender, target_id, 
                        target_type, status, create_time, update_time
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                    """
                    notification_params = [
                        post["openid"],
                        "帖子被收藏",
                        f"您的帖子「{post.get('title', '无标题')}」被用户收藏了",
                        "favorite",
                        False,
                        json.dumps({"openid": openid, "avatar": sender_avatar, "nickname": sender_nickname}),  # 将sender作为JSON对象存储
                        post_id,
                        "post",
                        1
                    ]
                    await async_execute_custom_query(notification_sql, notification_params, fetch=False)

            return Response.success(data={
                "success": True,
                "status": "favorited",
                "favorite_count": new_count,
                "is_favorited": True
            }, details={"message": "收藏成功"})

    except Exception as e:
        logger.error(f"收藏操作失败: {e}")
        return Response.error(details={"message": f"操作失败: {str(e)}"})

@router.post("/user/follow")
async def follow_user(request: Request):
    """关注/取消关注用户"""
    try:
        req_data = await request.json()
        required_params = ["followed_id", "openid"]
        error_response = validate_params(req_data, required_params)
        if (error_response):
            return error_response

        openid = req_data.get("openid")
        followed_id = req_data.get("followed_id")

        if openid == followed_id:
            return Response.bad_request(details={"message": "不能关注自己"})

        # 检查被关注用户是否存在，并获取其用户ID
        followed_sql = "SELECT id, openid FROM wxapp_user WHERE openid = %s LIMIT 1"
        followed_user = await async_execute_custom_query(followed_sql, [followed_id])
        
        if not followed_user:
            return Response.not_found(resource="被关注用户")
            
        # 获取用户数字ID
        user_id = followed_user[0]["id"]
        
        # 也获取当前用户的ID
        current_user_sql = "SELECT id FROM wxapp_user WHERE openid = %s LIMIT 1"
        current_user = await async_execute_custom_query(current_user_sql, [openid])
        
        if not current_user:
            return Response.not_found(resource="当前用户")
            
        current_user_id = current_user[0]["id"]

        # 查询是否已关注 - 使用数字ID
        follow_sql = """
        SELECT * FROM wxapp_action 
        WHERE openid = %s AND action_type = 'follow' AND target_type = 'user' AND target_id = %s
        LIMIT 1
        """
        existing_follow = await async_execute_custom_query(follow_sql, [openid, user_id])
        
        has_followed = bool(existing_follow)

        if has_followed:
            # 取消关注 - 使用数字ID
            delete_sql = """
            DELETE FROM wxapp_action 
            WHERE openid = %s AND action_type = 'follow' AND target_type = 'user' AND target_id = %s
            """
            await async_execute_custom_query(delete_sql, [openid, user_id], fetch=False)

            # 更新关注者的关注数
            update_following_sql = """
            UPDATE wxapp_user 
            SET following_count = GREATEST(0, following_count - 1) 
            WHERE openid = %s
            """
            await async_execute_custom_query(update_following_sql, [openid], fetch=False)
            
            # 更新被关注者的粉丝数
            update_follower_sql = """
            UPDATE wxapp_user 
            SET follower_count = GREATEST(0, follower_count - 1) 
            WHERE openid = %s
            """
            await async_execute_custom_query(update_follower_sql, [followed_id], fetch=False)

            return Response.success(data={
                "success": True,
                "status": "unfollowed",
                "is_following": False
            }, details={"message": "取消关注成功"})
        else:
            # 创建关注 - 使用数字ID
            insert_sql = """
            INSERT INTO wxapp_action (openid, action_type, target_type, target_id, create_time, update_time)
            VALUES (%s, %s, %s, %s, NOW(), NOW())
            """
            await async_execute_custom_query(insert_sql, [openid, "follow", "user", user_id], fetch=False)

            # 更新关注者的关注数
            update_following_sql = """
            UPDATE wxapp_user 
            SET following_count = following_count + 1 
            WHERE openid = %s
            """
            await async_execute_custom_query(update_following_sql, [openid], fetch=False)
            
            # 更新被关注者的粉丝数
            update_follower_sql = """
            UPDATE wxapp_user 
            SET follower_count = follower_count + 1 
            WHERE openid = %s
            """
            await async_execute_custom_query(update_follower_sql, [followed_id], fetch=False)

            # 创建通知 - 为通知保存openid
            if followed_id != openid:
                # 先检查是否已存在此类通知
                check_notification_sql = """
                SELECT id FROM wxapp_notification 
                WHERE openid = %s AND type = 'follow' AND target_type = 'user'
                AND sender LIKE %s
                LIMIT 1
                """
                existing_notification = await async_execute_custom_query(
                    check_notification_sql, 
                    [followed_id, f'%{openid}%']
                )
                
                # 只有在不存在通知时才创建
                if not existing_notification:
                    # 获取发送者的头像和昵称
                    sender_info_sql = "SELECT nickname, avatar FROM wxapp_user WHERE openid = %s LIMIT 1"
                    sender_info = await async_execute_custom_query(sender_info_sql, [openid])
                    sender_avatar = sender_info[0].get("avatar", "") if sender_info else ""
                    sender_nickname = sender_info[0].get("nickname", "") if sender_info else ""
                    
                    notification_sql = """
                    INSERT INTO wxapp_notification (
                        openid, title, content, type, is_read, sender, target_id, 
                        target_type, status, create_time, update_time
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                    """
                    notification_params = [
                        followed_id,
                        "收到新关注",
                        "有用户关注了你",
                        "follow",
                        False,
                        json.dumps({"openid": openid, "avatar": sender_avatar, "nickname": sender_nickname}),  # 将sender作为JSON对象存储
                        current_user_id, # 使用关注者的数字ID作为target_id
                        "user",
                        1
                    ]
                    await async_execute_custom_query(notification_sql, notification_params, fetch=False)

            return Response.success(data={
                "success": True,
                "status": "followed",
                "is_following": True
            }, details={"message": "关注成功"})

    except Exception as e:
        logger.error(f"关注操作失败: {e}")
        return Response.error(details={"message": f"操作失败: {str(e)}"})

