"""
微信小程序用户行为API，只保留产生通知的接口
"""
from fastapi import APIRouter, Request, Query
from api.models.common import Response, Request, validate_params, PaginationInfo
from etl.load.db_core import (
    query_records, get_record_by_id, insert_record, update_record, count_records, delete_record,
    async_query_records, async_get_by_id, async_insert, async_update, async_count_records, execute_custom_query,
    async_query, execute_query
)
from datetime import datetime

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
        images = req_data.get("images", [])
        
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
            "images": images,
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
    """点赞评论"""
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
            return Response.success(data={
                "success": True,
                "status": "already_liked",
                "message": "已经点赞",
                "like_count": comment.get("like_count", 0),
                "is_liked": True
            })

        # 创建点赞记录
        like_data = {
            "openid": openid,
            "action_type": "like",
            "target_id": comment_id,
            "target_type": "comment"
        }

        try:
            like_id = await async_insert(
                table_name="wxapp_action",
                data=like_data
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
            "message": "点赞成功",
            "like_count": new_like_count,
            "is_liked": True
        })
    except Exception as e:
        return Response.error(details={"message": f"点赞评论失败: {str(e)}"})

@router.post("/comment/unlike")
async def unlike_comment(request: Request):
    """取消点赞评论"""
    try:
        req_data = await request.json()
        required_params = ["comment_id", "openid"]
        error_response = validate_params(req_data, required_params)
        if(error_response):
            return error_response

        openid = req_data.get("openid")
        comment_id = req_data.get("comment_id")

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

        # 判断逻辑修改为与get_comment_status一致
        already_liked = bool(like_record)
        if not already_liked:
            return Response.bad_request(details={"message": "未点赞，无法取消点赞"})

        comment = await async_get_by_id(
            table_name="wxapp_comment",
            record_id=comment_id
        )
        if comment and comment.get("like_count", 0) > 0:
            new_like_count = comment["like_count"] - 1
        else:
            new_like_count = 0

        # 删除点赞记录
        try:
            execute_query(
                "DELETE FROM wxapp_action WHERE openid = %s AND action_type = %s AND target_id = %s AND target_type = %s",
                [openid, "like", comment_id, "comment"]
            )
        except Exception as e:
            return Response.db_error(details={"message": f"删除点赞记录失败: {str(e)}"})
        
        # 更新评论点赞数
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
    except Exception as e:
        return Response.error(details={"message": f"取消点赞评论失败: {str(e)}"})


@router.post("/post/like")
async def like_post(
    request: Request,
):
    """点赞帖子"""
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
            conditions={
                "openid": openid,
                "action_type": 'like',
                "target_id": post_id
            },
            limit=1,
        )
        if exists:
            return Response.bad_request(details={"message": "已经点赞，请勿重复点赞"})

        await async_insert(
            "wxapp_action",
            data={
                "openid": openid,
                "action_type": 'like',
                "target_id": post_id
            },
        )

        await async_update(
            "wxapp_post",
            post_id,
            {"like_count": post["like_count"] + 1},
        )

        if post["openid"] != openid:
            notification_data = {
                "openid": post["openid"],
                "title": "帖子被点赞",
                "content": f"您的帖子「{post.get('title', '无标题')}」被用户点赞了",
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

        return Response.success(details={"like_count": post["like_count"] + 1})
    except Exception as e:
        return Response.error(details={"message": f"点赞失败: {str(e)}"})


@router.post("/post/favorite")
async def favorite_post(
    request: Request,
):
    """收藏帖子"""
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
            {"openid": openid, "action_type": "favorite", "target_id": post_id},
            limit=1
        )

        if exists:
            return Response.success(details={"status": "already_favorited"})

        await async_insert("wxapp_action", {
            "openid": openid,
            "action_type": "favorite",
            "target_id": post_id,
            "target_type": "post"
        })

        post = await async_get_by_id("wxapp_post", post_id)
        new_count = post["favorite_count"] + 1
        await async_update("wxapp_post", post_id, {"favorite_count": new_count})

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

        return Response.success(details={
            "favorite_count": new_count,
            "is_favorited": True
        })
    except Exception as e:
        return Response.error(details={"message": f"收藏失败: {str(e)}"})

@router.post("/post/unfavorite")
async def unlike_favorite(
    request: Request,
):
    """取消收藏帖子"""
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

        favorite_record = await async_query_records(
            "wxapp_action",
            {"openid": openid, "action_type": "favorite", "target_id": post_id},
            limit=1
        )
        if not favorite_record:
            return Response.bad_request(details={"message": "未收藏，无法取消收藏"})

        post = await async_get_by_id("wxapp_post", post_id)
        new_count = max(0, post["favorite_count"] - 1) #  防止favorite_count < 0

        # 删除收藏记录
        execute_custom_query(
            "DELETE FROM wxapp_action WHERE openid = %s AND action_type = 'favorite' AND target_id = %s",
            [openid, post_id],
            fetch=False
        )
        
        # 更新帖子收藏数
        await async_update("wxapp_post", post_id, {"favorite_count": new_count})
        
        return Response.success(data={
            "favorite_count": new_count,
            "is_favorited": False
        }, details={"message": "取消收藏成功"})
    except Exception as e:
        return Response.error(details={"message": f"取消收藏失败: {str(e)}"})


@router.post("/user/follow")
async def follow_user(
    request: Request,
):
    """关注用户"""
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
        if existing_follow and existing_follow.get('data'):
            return Response.bad_request(details={"message": "已关注，请勿重复关注"})

        action_data = {
            "openid": openid,
            "action_type": "follow",
            "target_type": "user",
            "target_id": followed_id
        }
        await async_insert("wxapp_action", action_data)

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

        return Response.success(details={"message": "关注成功"})
    except Exception as e:
        return Response.error(details={"message": f"关注用户失败: {str(e)}"})


@router.post("/user/unfollow")
async def unfollow_user(
    request: Request,
):
    """取消关注用户"""
    try:
        req_data = await request.json()
        required_params = ["followed_id", "openid"]
        error_response = validate_params(req_data, required_params)
        if (error_response):
            return error_response

        openid = req_data.get("openid")
        followed_id = req_data.get("followed_id")

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
        if not existing_follow:
            return Response.bad_request(details={"message": "未关注，无法取消关注"})

        # 使用直接的原始SQL查询，确保类型匹配
        execute_custom_query(
            "DELETE FROM wxapp_action WHERE openid = %s AND action_type = %s AND target_type = %s AND target_id = %s",
            [openid, "follow", "user", followed_id],
            fetch=False
        )
        return Response.success(details={"message": "取消关注成功"})
    except Exception as e:
        return Response.error(details={"message": f"取消关注用户失败: {str(e)}"})