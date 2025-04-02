"""
微信小程序互动动作API接口
包括点赞、收藏、关注等功能
"""
from fastapi import APIRouter, Request, Query
from api.models.common import Response, Request, validate_params, PaginationInfo
from etl.load.db_core import (
    query_records, get_record_by_id, insert_record, update_record, count_records, delete_record,
    async_query_records, async_get_by_id, async_insert, async_update, async_count_records, execute_custom_query,
    async_query, execute_query
)
from datetime import datetime
import time

# 初始化路由器
router = APIRouter()

@router.post("/comment")
async def create_comment(request: Request):
    """创建新评论"""
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
            "root_id": req_data.get("root_id", parent_id),
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
                return Response.db_error(message="评论创建失败", error_detail=f"未能成功插入评论，返回ID: {comment_id}")
        except Exception as e:
            print(f"评论插入异常: {str(e)}")
            return Response.db_error(message="评论创建失败", error_detail=str(e))


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
            return Response.db_error(message="帖子评论数更新失败", error_detail=str(e))

        if parent_id:
            parent_comment = await async_get_by_id(
                table_name="wxapp_comment",
                record_id=parent_id
            )
            if parent_comment and parent_comment["openid"] != openid:
                notification_data = {
                    "openid": parent_comment["openid"],
                    "title": "收到新回复",
                    "content": f"用户回复了你的评论",
                    "type": "comment",
                    "is_read": False,
                    "sender": {"openid": openid},
                    "target_id": comment_id,
                    "target_type": "comment",
                    "status": 1
                }
                await async_insert(
                    table_name="wxapp_notification",
                    data=notification_data
                )
        elif post["openid"] != openid:
            notification_data = {
                "openid": post["openid"],
                "title": "收到新评论",
                "content": f"用户评论了你的帖子「{post.get('title', '无标题')}」",
                "type": "comment",
                "is_read": False,
                "sender": {"openid": openid},
                "target_id": comment_id,
                "target_type": "comment",
                "status": 1
            }
            await async_insert(
                table_name="wxapp_notification",
                data=notification_data
            )

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
                notification_data = {
                    "openid": comment["openid"],
                    "title": "收到点赞",
                    "content": "有用户点赞了你的评论",
                    "type": "like",
                    "is_read": False,
                    "sender": {"openid": openid},
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
        if(error_response):
            return error_response

        openid = req_data.get("openid")
        post_id = req_data.get("post_id")

        post = await async_get_by_id(
            table_name="wxapp_post",
            record_id=post_id
        )
        if not post:
            return Response.not_found(resource="帖子")

        # 查询是否已点赞
        like_record = await async_query_records(
            table_name="wxapp_action",
            conditions={
                "openid": openid,
                "action_type": "like",
                "target_id": post_id,
                "target_type": "post"
            },
            limit=1
        )

        already_liked = like_record and len(like_record.get('data', [])) > 0

        if already_liked:
            # 取消点赞
            try:
                execute_query(
                    "DELETE FROM wxapp_action WHERE openid = %s AND action_type = %s AND target_id = %s AND target_type = %s",
                    [openid, "like", post_id, "post"]
                )
            except Exception as e:
                return Response.db_error(details={"message": f"取消点赞失败: {str(e)}"})
            
            new_like_count = max(0, post.get("like_count", 0) - 1)
            await async_update(
                table_name="wxapp_post",
                record_id=post_id,
                data={"like_count": new_like_count}
            )

            # 更新用户点赞数
            user = await async_query_records(
                table_name="wxapp_user",
                conditions={"openid": openid},
                limit=1
            )
            if user and user.get('data'):
                user_data = user['data'][0]
                await async_update(
                    table_name="wxapp_user",
                    record_id=user_data["id"],
                    data={"like_count": max(0, user_data.get("like_count", 0) - 1)}
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
                        "target_id": post_id,
                        "target_type": "post"
                    }
                )
            except Exception as e:
                return Response.db_error(details={"message": f"点赞操作失败: {str(e)}"})

            new_like_count = post.get("like_count", 0) + 1
            await async_update(
                table_name="wxapp_post",
                record_id=post_id,
                data={"like_count": new_like_count}
            )

            # 更新用户点赞数
            user = await async_query_records(
                table_name="wxapp_user",
                conditions={"openid": openid},
                limit=1
            )
            if user and user.get('data'):
                user_data = user['data'][0]
                await async_update(
                    table_name="wxapp_user",
                    record_id=user_data["id"],
                    data={"like_count": user_data.get("like_count", 0) + 1}
                )

            if openid != post["openid"]:
                notification_data = {
                    "openid": post["openid"],
                    "title": "收到点赞",
                    "content": f"有用户点赞了你的帖子「{post.get('title', '无标题')}」",
                    "type": "like",
                    "is_read": False,
                    "sender": {"openid": openid},
                    "target_id": post_id,
                    "target_type": "post",
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
        post = await async_get_by_id("wxapp_post", post_id)
        if not post:
            return Response.not_found(resource="帖子")

        exists = await async_query_records(
            "wxapp_action",
            {"openid": openid, "action_type": "favorite", "target_id": post_id, "target_type": "post"},
            limit=1
        )
        
        has_favorited = exists and exists.get('data') and len(exists.get('data')) > 0
        if has_favorited:
            # 取消收藏
            execute_custom_query(
                "DELETE FROM wxapp_action WHERE openid = %s AND action_type = 'favorite' AND target_id = %s AND target_type = %s",
                [openid, post_id, "post"],
                fetch=False
            )
            
            new_count = max(0, post["favorite_count"] - 1)
            await async_update("wxapp_post", post_id, {"favorite_count": new_count})
            
            # 更新被收藏用户的收藏数
            await async_update(
                "wxapp_user",
                {"openid": post["openid"]},
                {"favorite_count": execute_custom_query(
                    "SELECT favorite_count FROM wxapp_user WHERE openid = %s",
                    [post["openid"]], fetch=True)[0]["favorite_count"] - 1}
            )

            return Response.success(data={
                "success": True,
                "status": "unfavorited",
                "favorite_count": new_count,
                "is_favorited": False
            }, details={"message": "取消收藏成功"})
        else:
            # 创建收藏
            await async_insert("wxapp_action", {
                "openid": openid,
                "action_type": "favorite",
                "target_id": post_id,
                "target_type": "post"
            })

            new_count = post["favorite_count"] + 1
            await async_update("wxapp_post", post_id, {"favorite_count": new_count})

            # 更新被收藏用户的获赞数
            await async_update(
                "wxapp_user",
                {"openid": post["openid"]},
                {"favorite_count": execute_custom_query(
                    "SELECT favorite_count FROM wxapp_user WHERE openid = %s",
                    [post["openid"]], fetch=True)[0]["favorite_count"] + 1}
            )

            if post["openid"] != openid:
                notification_data = {
                    "openid": post["openid"],
                    "title": "帖子被收藏",
                    "content": f"您的帖子「{post.get('title', '无标题')}」被用户收藏了",
                    "type": "favorite",
                    "is_read": False,
                    "sender": {"openid": openid},
                    "target_id": post_id,
                    "target_type": "post",
                    "status": 1
                }
                await async_insert(
                    table_name="wxapp_notification",
                    data=notification_data
                )

            return Response.success(data={
                "success": True,
                "status": "favorited",
                "favorite_count": new_count,
                "is_favorited": True
            }, details={"message": "收藏成功"})

    except Exception as e:
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

        # 检查被关注用户是否存在
        followed_user = await async_query_records(
            table_name="wxapp_user",
            conditions={"openid": followed_id},
            limit=1
        )
        
        if not followed_user or not followed_user.get('data'):
            return Response.not_found(resource="被关注用户")

        existing_follow = await async_query_records(
            table_name="wxapp_action",
            conditions={
                "openid": openid,
                "action_type": "follow",
                "target_type": "user",
                "target_id": followed_id
            },
            limit=1
        )
        has_followed = existing_follow and existing_follow.get('data')

        if has_followed:
            # 取消关注
            execute_custom_query(
                "DELETE FROM wxapp_action WHERE openid = %s AND action_type = 'follow' AND target_type = 'user' AND target_id = %s",
                [openid, followed_id],
                fetch=False
            )

            # 更新关注者和被关注者的计数
            await async_update(
                "wxapp_user",
                {"openid": openid},
                {"following_count": execute_custom_query(
                    "SELECT following_count FROM wxapp_user WHERE openid = %s",
                    [openid], fetch=True)[0]["following_count"] - 1}
            )
            await async_update(
                "wxapp_user",
                {"openid": followed_id},
                {"follower_count": execute_custom_query(
                    "SELECT follower_count FROM wxapp_user WHERE openid = %s",
                    [followed_id], fetch=True)[0]["follower_count"] - 1}
            )

            return Response.success(data={
                "success": True,
                "status": "unfollowed",
                "is_following": False
            }, details={"message": "取消关注成功"})
        else:
            # 创建关注
            action_data = {
                "openid": openid,
                "action_type": "follow",
                "target_type": "user",
                "target_id": followed_id
            }
            await async_insert("wxapp_action", action_data)

            # 更新关注者和被关注者的计数
            await async_update(
                "wxapp_user",
                {"openid": openid},
                {"following_count": execute_custom_query(
                    "SELECT following_count FROM wxapp_user WHERE openid = %s",
                    [openid], fetch=True)[0]["following_count"] + 1}
            )
            await async_update(
                "wxapp_user",
                {"openid": followed_id},
                {"follower_count": execute_custom_query(
                    "SELECT follower_count FROM wxapp_user WHERE openid = %s",
                    [followed_id], fetch=True)[0]["follower_count"] + 1}
            )

            if followed_id != openid:
                notification_data = {
                    "openid": followed_id,
                    "title": "收到新关注",
                    "content": "有用户关注了你",
                    "type": "follow",
                    "is_read": False,
                    "sender": {"openid": openid},
                    "target_id": openid,
                    "target_type": "user",
                    "status": 1
                }
                await async_insert("wxapp_notification", notification_data)

            return Response.success(data={
                "success": True,
                "status": "followed",
                "is_following": True
            }, details={"message": "关注成功"})

    except Exception as e:
        return Response.error(details={"message": f"操作失败: {str(e)}"})

