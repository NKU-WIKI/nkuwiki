"""
帖子相关API接口
处理帖子创建、查询、更新、删除、点赞、收藏等功能
"""
import time
from typing import Dict, Any, Optional, List
from fastapi import Depends, HTTPException, Query, Path
from loguru import logger

from api import wxapp_router
from api.common import handle_api_errors, get_api_logger_dep
from api.models.common import SimpleOperationResponse
from api.models.wxapp.post import (
    PostModel, 
    PostCreateRequest, 
    PostUpdateRequest, 
    PostQueryParams,
    PostListResponse,
    PostActionResponse
)
from api.database.wxapp import notification_dao, post_dao, user_dao
from config import Config

# 获取配置
config = Config()

@wxapp_router.post("/posts", response_model=PostModel)
@handle_api_errors("创建帖子")
async def create_post(
    request: PostCreateRequest,
    openid: str = Query(..., description="发布用户openid"),
    nick_name: Optional[str] = Query(None, description="用户昵称"),
    avatar: Optional[str] = Query(None, description="用户头像URL"),
    api_logger=Depends(get_api_logger_dep)
):
    """
    创建帖子
    
    发布新帖子，内容包括标题、正文、图片等
    """
    from api.database.wxapp import post_dao, user_dao
    
    api_logger.debug(f"创建新帖子 (用户: {openid[:8]}...)")
    
    # 如果没有提供昵称和头像，从用户表获取
    if not nick_name or not avatar:
        user = await user_dao.get_user_by_openid(openid)
        if user:
            nick_name = nick_name or user.get("nick_name", "微信用户")
            avatar = avatar or user.get("avatar")
    
    # 构建帖子数据
    post_data = {
        "openid": openid,
        "nick_name": nick_name or "微信用户",
        "avatar": avatar,
        "title": request.title,
        "content": request.content,
        "images": request.images or [],
        "tags": request.tags or [],
        "category_id": request.category_id,
        "location": request.location,
    }
    
    # 创建帖子
    post_id = await post_dao.create_post(post_data)
    
    # 获取创建的帖子
    post = await post_dao.get_post_by_id(post_id)
    
    if not post:
        raise HTTPException(status_code=500, detail="帖子创建失败，无法获取帖子信息")
    
    # 处理datetime对象
    if "create_time" in post and post["create_time"]:
        post["create_time"] = post["create_time"].strftime("%Y-%m-%d %H:%M:%S")
    if "update_time" in post and post["update_time"]:
        post["update_time"] = post["update_time"].strftime("%Y-%m-%d %H:%M:%S")
    
    api_logger.debug(f"帖子创建成功，ID: {post_id}")
    return post

@wxapp_router.get("/posts/{post_id}", response_model=PostModel)
@handle_api_errors("获取帖子详情")
async def get_post_detail(
    post_id: int = Path(..., description="帖子ID"),
    update_view: bool = Query(True, description="是否更新浏览量"),
    api_logger=Depends(get_api_logger_dep)
):
    """
    获取帖子详情
    
    根据ID获取帖子的详细信息
    """
    from api.database.wxapp import post_dao
    
    api_logger.debug(f"获取帖子详情 (ID: {post_id})")
    
    # 获取帖子信息
    post = await post_dao.get_post_by_id(post_id)
    
    if not post:
        raise HTTPException(status_code=404, detail="帖子不存在")
    
    # 更新浏览量
    if update_view:
        await post_dao.update_post_view_count(post_id)
        post["view_count"] += 1
    
    # 处理datetime对象
    if "create_time" in post and post["create_time"]:
        post["create_time"] = post["create_time"].strftime("%Y-%m-%d %H:%M:%S")
    if "update_time" in post and post["update_time"]:
        post["update_time"] = post["update_time"].strftime("%Y-%m-%d %H:%M:%S")
    
    return post

@wxapp_router.get("/posts", response_model=PostListResponse)
@handle_api_errors("查询帖子列表")
async def get_posts(
    limit: int = Query(20, description="返回记录数量限制", ge=1, le=100),
    offset: int = Query(0, description="分页偏移量", ge=0),
    openid: Optional[str] = Query(None, description="按用户openid筛选"),
    category_id: Optional[int] = Query(None, description="按分类ID筛选"),
    tag: Optional[str] = Query(None, description="按标签筛选"),
    status: int = Query(1, description="帖子状态：1-正常，0-禁用"),
    order_by: str = Query("update_time DESC", description="排序方式"),
    api_logger=Depends(get_api_logger_dep)
):
    """
    查询帖子列表
    
    根据条件筛选帖子列表，支持分页
    """
    from api.database.wxapp import post_dao
    
    api_logger.debug(f"查询帖子列表 (limit: {limit}, offset: {offset})")
    
    # 构建查询条件
    conditions = {
        "status": status,
        "is_deleted": 0
    }
    
    if openid:
        conditions["openid"] = openid
        
    if category_id:
        conditions["category_id"] = category_id
    
    # 获取帖子列表
    posts, total = await post_dao.get_posts(
        conditions=conditions, 
        tag=tag,
        limit=limit, 
        offset=offset, 
        order_by=order_by
    )
    
    # 处理datetime对象
    for post in posts:
        if "create_time" in post and post["create_time"]:
            post["create_time"] = post["create_time"].strftime("%Y-%m-%d %H:%M:%S")
        if "update_time" in post and post["update_time"]:
            post["update_time"] = post["update_time"].strftime("%Y-%m-%d %H:%M:%S")
    
    return {
        "posts": posts,
        "total": total,
        "limit": limit,
        "offset": offset
    }

@wxapp_router.put("/posts/{post_id}", response_model=PostModel)
@handle_api_errors("更新帖子")
async def update_post(
    request: PostUpdateRequest,
    post_id: int = Path(..., description="帖子ID"),
    openid: str = Query(..., description="用户openid"),
    api_logger=Depends(get_api_logger_dep)
):
    """
    更新帖子
    
    更新帖子的标题、内容、图片等信息
    """
    from api.database.wxapp import post_dao
    
    api_logger.debug(f"更新帖子 (ID: {post_id}, 用户: {openid[:8]}...)")
    
    # 检查帖子是否存在
    post = await post_dao.get_post_by_id(post_id)
    
    if not post:
        raise HTTPException(status_code=404, detail="帖子不存在")
    
    # 检查是否是帖子作者
    if post["openid"] != openid:
        raise HTTPException(status_code=403, detail="无权更新该帖子")
    
    # 更新帖子
    update_data = request.dict(exclude_unset=True)
    
    # 处理列表类型
    import json
    if "images" in update_data and update_data["images"] is not None:
        update_data["images"] = json.dumps(update_data["images"])
    
    if "tags" in update_data and update_data["tags"] is not None:
        update_data["tags"] = json.dumps(update_data["tags"])
    
    if "location" in update_data and update_data["location"] is not None:
        update_data["location"] = json.dumps(update_data["location"])
    
    if update_data:
        await post_dao.update_post(post_id, update_data)
        
    # 获取更新后的帖子
    updated_post = await post_dao.get_post_by_id(post_id)
    
    # 处理datetime对象
    if "create_time" in updated_post and updated_post["create_time"]:
        updated_post["create_time"] = updated_post["create_time"].strftime("%Y-%m-%d %H:%M:%S")
    if "update_time" in updated_post and updated_post["update_time"]:
        updated_post["update_time"] = updated_post["update_time"].strftime("%Y-%m-%d %H:%M:%S")
    
    return updated_post

@wxapp_router.delete("/posts/{post_id}", response_model=SimpleOperationResponse)
@handle_api_errors("删除帖子")
async def delete_post(
    post_id: int = Path(..., description="帖子ID"),
    openid: str = Query(..., description="用户openid"),
    api_logger=Depends(get_api_logger_dep)
):
    """
    删除帖子
    
    标记删除指定帖子
    """
    from api.database.wxapp import post_dao
    
    api_logger.debug(f"删除帖子 (ID: {post_id}, 用户: {openid[:8]}...)")
    
    # 检查帖子是否存在
    post = await post_dao.get_post_by_id(post_id)
    
    if not post:
        raise HTTPException(status_code=404, detail="帖子不存在")
    
    # 检查是否是帖子作者
    if post["openid"] != openid:
        raise HTTPException(status_code=403, detail="无权删除该帖子")
    
    # 标记删除帖子
    await post_dao.mark_post_deleted(post_id)
    
    return SimpleOperationResponse(
        success=True,
        message="帖子已删除",
        affected_items=1
    )

@wxapp_router.post("/posts/{post_id}/like", response_model=PostActionResponse)
@handle_api_errors("点赞帖子")
async def like_post(
    post_id: int = Path(..., description="帖子ID"),
    openid: str = Query(..., description="用户openid"),
    api_logger=Depends(get_api_logger_dep)
):
    """
    点赞帖子
    
    为指定帖子点赞，同一用户只能点赞一次
    """
    from api.database.wxapp import post_dao, notification_dao
    
    api_logger.debug(f"点赞帖子 (ID: {post_id}, 用户: {openid[:8]}...)")
    
    # 检查帖子是否存在
    post = await post_dao.get_post_by_id(post_id)
    
    if not post:
        raise HTTPException(status_code=404, detail="帖子不存在")
    
    # 检查用户是否已点赞
    liked_users = post.get("liked_users", [])
    if openid in liked_users:
        # 已点赞，取消点赞
        await post_dao.unlike_post(post_id, openid)
        result = {
            "success": True,
            "message": "取消点赞成功",
            "liked": False,
            "like_count": post["like_count"] - 1
        }
    else:
        # 未点赞，添加点赞
        await post_dao.like_post(post_id, openid)
        
        # 如果点赞的不是自己的帖子，创建通知
        if post["openid"] != openid:
            from api.database.wxapp import user_dao
            
            # 获取点赞用户信息
            liker = await user_dao.get_user_by_openid(openid)
            liker_name = liker.get("nick_name", "微信用户") if liker else "微信用户"
            
            # 创建通知
            notification_data = {
                "openid": post["openid"],  # 帖子作者
                "title": "收到新点赞",
                "content": f"{liker_name} 点赞了你的帖子「{post.get('title', '无标题')}」",
                "type": "like",
                "sender_openid": openid,
                "related_id": str(post_id),
                "related_type": "post"
            }
            await notification_dao.create_notification(notification_data)
        
        result = {
            "success": True,
            "message": "点赞成功",
            "liked": True,
            "like_count": post["like_count"] + 1
        }
    
    return PostActionResponse(**result)

@wxapp_router.post("/posts/{post_id}/unlike", response_model=PostActionResponse)
@handle_api_errors("取消点赞")
async def unlike_post(
    post_id: int = Path(..., description="帖子ID"),
    openid: str = Query(..., description="用户openid"),
    api_logger=Depends(get_api_logger_dep)
):
    """
    取消点赞
    
    取消对指定帖子的点赞
    """
    from api.database.wxapp import post_dao
    
    api_logger.debug(f"取消点赞帖子 (ID: {post_id}, 用户: {openid[:8]}...)")
    
    # 检查帖子是否存在
    post = await post_dao.get_post_by_id(post_id)
    
    if not post:
        raise HTTPException(status_code=404, detail="帖子不存在")
    
    # 检查用户是否已点赞
    liked_users = post.get("liked_users", [])
    if openid in liked_users:
        # 已点赞，取消点赞
        await post_dao.unlike_post(post_id, openid)
        result = {
            "success": True,
            "message": "取消点赞成功",
            "liked": False,
            "like_count": post["like_count"] - 1
        }
    else:
        # 未点赞，添加点赞
        await post_dao.like_post(post_id, openid)
        
        # 如果点赞的不是自己的帖子，创建通知
        if post["openid"] != openid:
            from api.database.wxapp import user_dao
            
            # 获取点赞用户信息
            liker = await user_dao.get_user_by_openid(openid)
            liker_name = liker.get("nick_name", "微信用户") if liker else "微信用户"
            
            # 创建通知
            notification_data = {
                "openid": post["openid"],  # 帖子作者
                "title": "收到新点赞",
                "content": f"{liker_name} 点赞了你的帖子「{post.get('title', '无标题')}」",
                "type": "like",
                "sender_openid": openid,
                "related_id": str(post_id),
                "related_type": "post"
            }
            await notification_dao.create_notification(notification_data)
        
        result = {
            "success": True,
            "message": "点赞成功",
            "liked": True,
            "like_count": post["like_count"] + 1
        }
    
    return PostActionResponse(**result)

@wxapp_router.post("/posts/{post_id}/favorite", response_model=PostActionResponse)
@handle_api_errors("收藏帖子")
async def favorite_post(
    post_id: int = Path(..., description="帖子ID"),
    openid: str = Query(..., description="用户openid"),
    api_logger=Depends(get_api_logger_dep)
):
    """
    收藏帖子
    
    将指定帖子添加到收藏
    """
    from api.database.wxapp import post_dao, notification_dao
    
    api_logger.debug(f"收藏帖子 (ID: {post_id}, 用户: {openid[:8]}...)")
    
    # 检查帖子是否存在
    post = await post_dao.get_post_by_id(post_id)
    
    if not post:
        raise HTTPException(status_code=404, detail="帖子不存在")
    
    # 获取当前收藏状态
    favorite_users = post.get("favorite_users", [])
    is_currently_favorite = openid in favorite_users
    
    if not is_currently_favorite:
        # 添加收藏
        await post_dao.favorite_post(post_id, openid)
        
        # 如果收藏的不是自己的帖子，创建通知
        if post["openid"] != openid:
            from api.database.wxapp import user_dao
            
            # 获取收藏用户信息
            favoriter = await user_dao.get_user_by_openid(openid)
            favoriter_name = favoriter.get("nick_name", "微信用户") if favoriter else "微信用户"
            
            # 创建通知
            notification_data = {
                "openid": post["openid"],  # 帖子作者
                "title": "收到新收藏",
                "content": f"{favoriter_name} 收藏了你的帖子「{post.get('title', '无标题')}」",
                "type": "favorite",
                "sender_openid": openid,
                "related_id": str(post_id),
                "related_type": "post"
            }
            await notification_dao.create_notification(notification_data)
            
        result = {
            "success": True,
            "message": "收藏成功",
            "favorite": True,
            "favorite_count": post["favorite_count"] + 1
        }
    else:
        # 状态未变
        result = {
            "success": True,
            "message": "收藏状态未变",
            "favorite": True,
            "favorite_count": post["favorite_count"]
        }
    
    return PostActionResponse(**result)

@wxapp_router.post("/posts/{post_id}/unfavorite", response_model=PostActionResponse)
@handle_api_errors("取消收藏")
async def unfavorite_post(
    post_id: int = Path(..., description="帖子ID"),
    openid: str = Query(..., description="用户openid"),
    api_logger=Depends(get_api_logger_dep)
):
    """
    取消收藏
    
    取消对指定帖子的收藏
    """
    from api.database.wxapp import post_dao
    
    api_logger.debug(f"取消收藏帖子 (ID: {post_id}, 用户: {openid[:8]}...)")
    
    # 检查帖子是否存在
    post = await post_dao.get_post_by_id(post_id)
    
    if not post:
        raise HTTPException(status_code=404, detail="帖子不存在")
    
    # 获取当前收藏状态
    favorite_users = post.get("favorite_users", [])
    is_currently_favorite = openid in favorite_users
    
    if is_currently_favorite:
        # 取消收藏
        await post_dao.unfavorite_post(post_id, openid)
        result = {
            "success": True,
            "message": "取消收藏成功",
            "favorite": False,
            "favorite_count": post["favorite_count"] - 1
        }
    else:
        # 状态未变
        result = {
            "success": True,
            "message": "收藏状态未变",
            "favorite": False,
            "favorite_count": post["favorite_count"]
        }
    
    return PostActionResponse(**result) 