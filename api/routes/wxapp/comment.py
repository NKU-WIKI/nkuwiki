"""
评论相关API接口
处理评论创建、查询、更新、删除和点赞等功能
"""
from typing import Dict, Any, Optional, List
from fastapi import Depends, HTTPException, Query, Path

from api import wxapp_router
from api.common import handle_api_errors, get_api_logger_dep
from api.models.wxapp.comment import (
    CommentModel, 
    CommentCreateRequest, 
    CommentUpdateRequest,
    CommentListResponse,
    CommentActionResponse
)
from api.models.common import SimpleOperationResponse

@wxapp_router.post("/comments", response_model=CommentModel)
@handle_api_errors("创建评论")
async def create_comment(
    request: CommentCreateRequest,
    openid: str = Query(..., description="评论用户openid"),
    nick_name: Optional[str] = Query(None, description="用户昵称"),
    avatar: Optional[str] = Query(None, description="用户头像URL"),
    api_logger=Depends(get_api_logger_dep)
):
    """
    创建新评论
    
    发布评论或回复其他评论
    """
    from api.database.wxapp import comment_dao, post_dao, user_dao, notification_dao
    
    api_logger.debug(f"创建新评论 (用户: {openid[:8]}...)")
    
    # 检查帖子是否存在
    post = await post_dao.get_post_by_id(request.post_id)
    if not post:
        raise HTTPException(status_code=404, detail="帖子不存在")
    
    # 如果是回复，检查父评论是否存在
    if request.parent_id:
        parent_comment = await comment_dao.get_comment_by_id(request.parent_id)
        if not parent_comment:
            raise HTTPException(status_code=404, detail="回复的评论不存在")
    
    # 如果没有提供昵称和头像，从用户表获取
    if not nick_name or not avatar:
        user = await user_dao.get_user_by_openid(openid)
        if user:
            nick_name = nick_name or user.get("nick_name", "微信用户")
            avatar = avatar or user.get("avatar")
    
    # 构建评论数据
    comment_data = {
        "post_id": request.post_id,
        "openid": openid,
        "nick_name": nick_name or "微信用户",
        "avatar": avatar,
        "content": request.content,
        "parent_id": request.parent_id,
        "images": request.images or []
    }
    
    # 创建评论
    comment_id = await comment_dao.create_comment(comment_data)
    
    if not comment_id:
        raise HTTPException(status_code=500, detail="评论创建失败")
    
    # 获取创建的评论
    comment = await comment_dao.get_comment_by_id(comment_id)
    
    # 处理datetime类型字段
    if comment and "create_time" in comment and comment["create_time"]:
        comment["create_time"] = comment["create_time"].strftime("%Y-%m-%d %H:%M:%S")
    if comment and "update_time" in comment and comment["update_time"]:
        comment["update_time"] = comment["update_time"].strftime("%Y-%m-%d %H:%M:%S")
    
    # 创建通知
    if comment:
        # 如果是回复其他评论，通知被回复的用户
        if request.parent_id:
            parent_comment = await comment_dao.get_comment_by_id(request.parent_id)
            if parent_comment and parent_comment["openid"] != openid:
                notification_data = {
                    "openid": parent_comment["openid"],
                    "title": "收到新回复",
                    "content": f"{nick_name or '微信用户'} 回复了你的评论",
                    "type": "comment",
                    "sender_openid": openid,
                    "related_id": str(comment_id),
                    "related_type": "comment"
                }
                await notification_dao.create_notification(notification_data)
        # 如果是评论帖子，通知帖子作者
        elif post["openid"] != openid:
            notification_data = {
                "openid": post["openid"],
                "title": "收到新评论",
                "content": f"{nick_name or '微信用户'} 评论了你的帖子「{post.get('title', '无标题')}」",
                "type": "comment",
                "sender_openid": openid,
                "related_id": str(comment_id),
                "related_type": "comment"
            }
            await notification_dao.create_notification(notification_data)
    
    return comment

@wxapp_router.get("/comments/{comment_id}", response_model=CommentModel)
@handle_api_errors("获取评论详情")
async def get_comment_detail(
    comment_id: int = Path(..., description="评论ID"),
    api_logger=Depends(get_api_logger_dep)
):
    """
    获取评论详情
    
    根据ID获取评论的详细信息
    """
    from api.database.wxapp import comment_dao
    
    api_logger.debug(f"获取评论详情 (ID: {comment_id})")
    
    # 获取评论信息
    comment = await comment_dao.get_comment_by_id(comment_id)
    
    if not comment:
        raise HTTPException(status_code=404, detail="评论不存在")
    
    # 处理datetime类型字段
    if "create_time" in comment and comment["create_time"]:
        comment["create_time"] = comment["create_time"].strftime("%Y-%m-%d %H:%M:%S")
    if "update_time" in comment and comment["update_time"]:
        comment["update_time"] = comment["update_time"].strftime("%Y-%m-%d %H:%M:%S")
    
    return comment

@wxapp_router.get("/posts/{post_id}/comments", response_model=CommentListResponse)
@handle_api_errors("获取帖子评论列表")
async def get_post_comments(
    post_id: int = Path(..., description="帖子ID"),
    parent_id: Optional[int] = Query(None, description="父评论ID，为空时获取一级评论"),
    limit: int = Query(20, description="返回记录数量限制", ge=1, le=100),
    offset: int = Query(0, description="分页偏移量", ge=0),
    sort_by: str = Query("latest", description="排序方式：latest-最新, oldest-最早, likes-最多点赞"),
    api_logger=Depends(get_api_logger_dep)
):
    """
    获取帖子评论列表
    
    获取帖子的评论列表，支持分页和按父评论ID筛选
    """
    from api.database.wxapp import comment_dao, post_dao
    
    api_logger.debug(f"获取帖子评论列表 (帖子ID: {post_id}, 父评论ID: {parent_id})")
    
    # 检查帖子是否存在
    post = await post_dao.get_post_by_id(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="帖子不存在")
    
    # 如果指定了父评论，检查是否存在
    if parent_id:
        parent_comment = await comment_dao.get_comment_by_id(parent_id)
        if not parent_comment:
            raise HTTPException(status_code=404, detail="父评论不存在")
    
    # 转换排序方式
    order_by_map = {
        "latest": "create_time DESC",
        "oldest": "create_time ASC",
        "likes": "like_count DESC, create_time DESC"
    }
    order_by = order_by_map.get(sort_by, "create_time DESC")
    
    # 获取评论列表
    comments, total = await comment_dao.get_post_comments(
        post_id=post_id,
        parent_id=parent_id,
        limit=limit,
        offset=offset,
        sort_by=order_by
    )
    
    # 处理datetime类型字段
    for comment in comments:
        if "create_time" in comment and comment["create_time"]:
            comment["create_time"] = comment["create_time"].strftime("%Y-%m-%d %H:%M:%S")
        if "update_time" in comment and comment["update_time"]:
            comment["update_time"] = comment["update_time"].strftime("%Y-%m-%d %H:%M:%S")
        
        # 处理回复预览中的datetime
        if "reply_preview" in comment and comment["reply_preview"]:
            for reply in comment["reply_preview"]:
                if "create_time" in reply and reply["create_time"]:
                    reply["create_time"] = reply["create_time"].strftime("%Y-%m-%d %H:%M:%S")
                if "update_time" in reply and reply["update_time"]:
                    reply["update_time"] = reply["update_time"].strftime("%Y-%m-%d %H:%M:%S")
    
    return {
        "comments": comments,
        "total": total,
        "limit": limit,
        "offset": offset,
        "post_id": post_id,
        "parent_id": parent_id
    }

@wxapp_router.put("/comments/{comment_id}", response_model=CommentModel)
@handle_api_errors("更新评论")
async def update_comment(
    request: CommentUpdateRequest,
    comment_id: int = Path(..., description="评论ID"),
    openid: str = Query(..., description="用户openid"),
    api_logger=Depends(get_api_logger_dep)
):
    """
    更新评论
    
    修改评论内容
    """
    from api.database.wxapp import comment_dao
    import json
    
    api_logger.debug(f"更新评论 (ID: {comment_id}, 用户: {openid[:8]}...)")
    
    # 检查评论是否存在
    comment = await comment_dao.get_comment_by_id(comment_id)
    
    if not comment:
        raise HTTPException(status_code=404, detail="评论不存在")
    
    # 检查是否是评论作者
    if comment["openid"] != openid:
        raise HTTPException(status_code=403, detail="无权更新该评论")
    
    # 更新评论
    update_data = request.dict(exclude_unset=True)
    
    # 处理列表和字典类型
    if "images" in update_data and update_data["images"] is not None:
        update_data["images"] = json.dumps(update_data["images"])
    
    if update_data:
        await comment_dao.update_comment(comment_id, update_data)
        
    # 获取更新后的评论
    updated_comment = await comment_dao.get_comment_by_id(comment_id)
    
    # 处理datetime类型字段
    if "create_time" in updated_comment and updated_comment["create_time"]:
        updated_comment["create_time"] = updated_comment["create_time"].strftime("%Y-%m-%d %H:%M:%S")
    if "update_time" in updated_comment and updated_comment["update_time"]:
        updated_comment["update_time"] = updated_comment["update_time"].strftime("%Y-%m-%d %H:%M:%S")
    
    return updated_comment

@wxapp_router.delete("/comments/{comment_id}", response_model=SimpleOperationResponse)
@handle_api_errors("删除评论")
async def delete_comment(
    comment_id: int = Path(..., description="评论ID"),
    openid: str = Query(..., description="用户openid"),
    api_logger=Depends(get_api_logger_dep)
):
    """
    删除评论
    
    标记删除指定评论
    """
    from api.database.wxapp import comment_dao
    
    api_logger.debug(f"删除评论 (ID: {comment_id}, 用户: {openid[:8]}...)")
    
    # 检查评论是否存在
    comment = await comment_dao.get_comment_by_id(comment_id)
    
    if not comment:
        raise HTTPException(status_code=404, detail="评论不存在")
    
    # 检查是否是评论作者
    if comment["openid"] != openid:
        raise HTTPException(status_code=403, detail="无权删除该评论")
    
    # 标记删除评论
    await comment_dao.mark_comment_deleted(comment_id)
    
    return SimpleOperationResponse(
        success=True,
        message="评论已删除",
        affected_items=1
    )

@wxapp_router.post("/comments/{comment_id}/like", response_model=CommentActionResponse)
@handle_api_errors("点赞评论")
async def like_comment(
    comment_id: int = Path(..., description="评论ID"),
    openid: str = Query(..., description="用户openid"),
    api_logger=Depends(get_api_logger_dep)
):
    """
    点赞评论
    
    为指定评论点赞，同一用户只能点赞一次
    """
    from api.database.wxapp import comment_dao, notification_dao
    
    api_logger.debug(f"点赞评论 (ID: {comment_id}, 用户: {openid[:8]}...)")
    
    # 检查评论是否存在
    comment = await comment_dao.get_comment_by_id(comment_id)
    
    if not comment:
        raise HTTPException(status_code=404, detail="评论不存在")
    
    # 检查用户是否已点赞
    liked_users = comment.get("liked_users", [])
    if openid in liked_users:
        # 已点赞，取消点赞
        await comment_dao.unlike_comment(comment_id, openid)
        result = {
            "success": True,
            "message": "取消点赞成功",
            "liked": False,
            "like_count": comment["like_count"] - 1
        }
    else:
        # 未点赞，添加点赞
        await comment_dao.like_comment(comment_id, openid)
        
        # 如果点赞的不是自己的评论，创建通知
        if comment["openid"] != openid:
            from api.database.wxapp import user_dao
            
            # 获取点赞用户信息
            liker = await user_dao.get_user_by_openid(openid)
            liker_name = liker.get("nick_name", "微信用户") if liker else "微信用户"
            
            # 创建通知
            notification_data = {
                "openid": comment["openid"],  # 评论作者
                "title": "收到新点赞",
                "content": f"{liker_name} 点赞了你的评论",
                "type": "like",
                "sender_openid": openid,
                "related_id": str(comment_id),
                "related_type": "comment"
            }
            await notification_dao.create_notification(notification_data)
        
        result = {
            "success": True,
            "message": "点赞成功",
            "liked": True,
            "like_count": comment["like_count"] + 1
        }

@wxapp_router.post("/comments/{comment_id}/unlike", response_model=CommentActionResponse)
@handle_api_errors("取消点赞")
async def unlike_comment(
    comment_id: int = Path(..., description="评论ID"),
    openid: str = Query(..., description="用户openid"),
    api_logger=Depends(get_api_logger_dep)
):
    """
    取消点赞评论
    
    取消对指定评论的点赞
    """
    from api.database.wxapp import comment_dao
    
    api_logger.debug(f"取消点赞评论 (ID: {comment_id}, 用户: {openid[:8]}...)")
    
    # 检查评论是否存在
    comment = await comment_dao.get_comment_by_id(comment_id)
    
    if not comment:
        raise HTTPException(status_code=404, detail="评论不存在")
    
    # 检查用户是否已点赞
    liked_users = comment.get("liked_users", [])
    if openid not in liked_users:
        raise HTTPException(status_code=400, detail="用户未点赞该评论")
    
    # 取消点赞
    await comment_dao.unlike_comment(comment_id, openid)
    
    result = {
        "success": True,
        "message": "取消点赞成功",
        "liked": False,
        "like_count": comment["like_count"] - 1
    }
    
    return result