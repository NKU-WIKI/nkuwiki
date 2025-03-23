"""
微信小程序评论API
提供评论相关的API接口
"""
from datetime import datetime
from fastapi import HTTPException, Path as PathParam, Depends, Query, Body
from pydantic import BaseModel, Field, validator
from typing import Dict, Any, Optional, List
import json

# 导入通用组件
from api.common import get_api_logger, handle_api_errors, create_standard_response
from api import wxapp_router as router
from api.wxapp.common_utils import format_datetime, prepare_db_data, process_json_fields

# 导入数据库操作函数
from etl.load.py_mysql import (
    insert_record, update_record, delete_record, 
    query_records, count_records, get_record_by_id
)

# 评论基础模型
class CommentBase(BaseModel):
    """评论基础信息"""
    openid: str = Field(..., description="评论用户openid")
    nick_name: Optional[str] = Field(None, description="用户昵称")
    avatar: Optional[str] = Field(None, description="用户头像URL")
    post_id: int = Field(..., description="帖子ID")
    content: str = Field(..., description="评论内容")
    parent_id: Optional[int] = Field(None, description="父评论ID，如果是回复另一条评论")
    
    @validator('content')
    def validate_content(cls, v):
        if not v or len(v.strip()) < 1:
            raise ValueError("评论内容不能为空")
        return v.strip()

class CommentCreate(CommentBase):
    """创建评论请求"""
    pass

class CommentUpdate(BaseModel):
    """更新评论请求"""
    content: Optional[str] = None
    extra: Optional[Dict[str, Any]] = None

class CommentResponse(CommentBase):
    """评论响应"""
    id: int
    create_time: datetime
    update_time: datetime
    like_count: int = 0
    liked_users: List[str] = []
    replies: Optional[List[Dict[str, Any]]] = None
    platform: str = "wxapp"
    is_deleted: int = 0
    extra: Optional[Dict[str, Any]] = None

# 辅助函数，根据openid获取用户信息
def get_user_info_by_openid(openid, api_logger):
    """
    根据openid获取用户信息
    如果用户不存在，将返回带有默认值的用户信息
    """
    try:
        # 通过openid查询用户
        users = query_records(
            'wxapp_users',
            conditions={'openid': openid, 'is_deleted': 0}
        )
        
        if users and len(users) > 0:
            user = users[0]
            return {
                'nick_name': user.get('nick_name', f"用户{openid[-4:]}"),
                'avatar': user.get('avatar', "/assets/icons/default-avatar.png")
            }
        else:
            # 用户不存在，返回默认值
            return {
                'nick_name': f"用户{openid[-4:]}",
                'avatar': "/assets/icons/default-avatar.png"
            }
    except Exception as e:
        api_logger.error(f"获取用户信息失败: {str(e)}")
        # 出错时也返回默认值
        return {
            'nick_name': f"用户{openid[-4:]}",
            'avatar': "/assets/icons/default-avatar.png"
        }

# API端点
@router.post("/comments", response_model=Dict[str, Any], summary="创建评论")
@handle_api_errors("创建评论")
async def create_comment(
    comment: CommentCreate,
    api_logger=Depends(get_api_logger)
):
    """创建新评论或回复已有评论"""
    # 准备数据
    comment_data = comment.dict()
    
    # 检查用户信息，如果缺少昵称或头像则自动获取
    if not comment_data.get('nick_name') or not comment_data.get('avatar'):
        api_logger.debug(f"评论缺少用户信息，自动获取: openid={comment_data['openid']}")
        user_info = get_user_info_by_openid(comment_data['openid'], api_logger)
        if not comment_data.get('nick_name'):
            comment_data['nick_name'] = user_info['nick_name']
        if not comment_data.get('avatar'):
            comment_data['avatar'] = user_info['avatar']
    
    # 添加默认值
    comment_data['like_count'] = 0
    comment_data['liked_users'] = json.dumps([])
    comment_data['platform'] = 'wxapp'
    comment_data['is_deleted'] = 0
    comment_data['extra'] = json.dumps({})
    
    comment_data = prepare_db_data(comment_data, is_create=True)
    
    # 检查帖子是否存在
    post = get_record_by_id('wxapp_posts', comment_data['post_id'])
    if not post:
        raise HTTPException(status_code=404, detail="帖子不存在")
    
    # 如果是回复评论，检查父评论是否存在
    if comment_data.get('parent_id'):
        parent_comment = get_record_by_id('wxapp_comments', comment_data['parent_id'])
        if not parent_comment:
            raise HTTPException(status_code=404, detail="回复的评论不存在")
    
    # 插入记录
    api_logger.debug(f"创建评论: {comment_data}")
    comment_id = insert_record('wxapp_comments', comment_data)
    if not comment_id:
        raise HTTPException(status_code=500, detail="创建评论失败")
    
    # 更新帖子评论数
    try:
        post_update = {'comment_count': post.get('comment_count', 0) + 1}
        update_record('wxapp_posts', comment_data['post_id'], post_update)
    except Exception as e:
        api_logger.error(f"更新帖子评论计数失败: {str(e)}")
    
    # 获取创建的评论
    created_comment = get_record_by_id('wxapp_comments', comment_id)
    if not created_comment:
        raise HTTPException(status_code=404, detail="找不到创建的评论")
    
    # 处理JSON字段
    created_comment = process_json_fields(created_comment)
    
    # 获取父评论信息(如果存在)
    if comment_data.get('parent_id'):
        try:
            parent = get_record_by_id('wxapp_comments', comment_data['parent_id'])
            if parent:
                parent = process_json_fields(parent)
                created_comment['parent'] = parent
        except Exception as e:
            api_logger.error(f"获取父评论失败: {str(e)}")
    
    # 创建通知
    try:
        if comment_data.get('parent_id'):
            # 回复通知
            parent = get_record_by_id('wxapp_comments', comment_data['parent_id'])
            if parent and parent.get('openid') != comment_data.get('openid'):
                notification_data = {
                    'openid': parent.get('openid'),
                    'title': '收到新回复',
                    'content': f"{comment_data.get('nick_name')}回复了您的评论: {comment_data.get('content')[:20]}...",
                    'type': 'comment',
                    'sender_openid': comment_data.get('openid'),
                    'related_id': str(comment_id),
                    'related_type': 'comment',
                    'platform': 'wxapp',
                    'is_deleted': 0,
                    'extra': json.dumps({
                        'post_id': comment_data.get('post_id')
                    })
                }
                insert_record('wxapp_notifications', prepare_db_data(notification_data, is_create=True))
        else:
            # 评论通知
            if post.get('openid') != comment_data.get('openid'):
                notification_data = {
                    'openid': post.get('openid'),
                    'title': '收到新评论',
                    'content': f"{comment_data.get('nick_name')}评论了您的帖子: {comment_data.get('content')[:20]}...",
                    'type': 'comment',
                    'sender_openid': comment_data.get('openid'),
                    'related_id': str(post.get('id')),
                    'related_type': 'post',
                    'platform': 'wxapp',
                    'is_deleted': 0,
                    'extra': json.dumps({
                        'comment_id': comment_id
                    })
                }
                insert_record('wxapp_notifications', prepare_db_data(notification_data, is_create=True))
    except Exception as e:
        api_logger.error(f"创建评论通知失败: {str(e)}")
    
    return create_standard_response(created_comment)

@router.get("/comments/{comment_id}", response_model=Dict[str, Any], summary="获取评论详情")
@handle_api_errors("获取评论")
async def get_comment(
    comment_id: int = PathParam(..., description="评论ID"),
    api_logger=Depends(get_api_logger)
):
    """获取指定评论详情"""
    comment = get_record_by_id('wxapp_comments', comment_id)
    if not comment or comment.get('is_deleted', 0) == 1:
        raise HTTPException(status_code=404, detail="评论不存在或已删除")
    
    # 处理JSON字段
    comment = process_json_fields(comment)
    
    # 获取回复列表
    try:
        replies = query_records(
            'wxapp_comments',
            conditions={"parent_id": comment_id, "is_deleted": 0},
            order_by="create_time ASC"
        )
        
        if replies:
            # 处理回复中的JSON字段
            processed_replies = []
            for reply in replies:
                processed_reply = process_json_fields(reply)
                processed_replies.append(processed_reply)
            
            comment['replies'] = processed_replies
    except Exception as e:
        api_logger.error(f"获取评论回复列表失败: {str(e)}")
        comment['replies'] = []
    
    return create_standard_response(comment)

@router.get("/posts/{post_id}/comments", response_model=Dict[str, Any], summary="获取帖子评论列表")
@handle_api_errors("获取帖子评论列表")
async def list_post_comments(
    post_id: int = PathParam(..., description="帖子ID"),
    parent_id: Optional[int] = Query(None, description="父评论ID，如果获取指定评论的回复"),
    limit: int = Query(20, description="返回记录数量限制", ge=1, le=100),
    offset: int = Query(0, description="分页偏移量", ge=0),
    sort_by: str = Query("latest", description="排序方式: latest-最新, oldest-最早, likes-最多点赞"),
    api_logger=Depends(get_api_logger)
):
    """获取帖子评论列表或特定评论的回复列表"""
    api_logger.debug(f"获取帖子ID={post_id}的评论列表, 父评论ID={parent_id}, 排序={sort_by}")
    
    # 检查帖子是否存在
    post = get_record_by_id('wxapp_posts', post_id)
    if not post:
        raise HTTPException(status_code=404, detail="帖子不存在")
    
    # 构建查询条件
    conditions = {"post_id": post_id, "is_deleted": 0}
    if parent_id is not None:
        conditions["parent_id"] = parent_id
    else:
        # 如果不指定父评论ID，则只获取顶级评论
        conditions["parent_id"] = None
    
    # 设置排序
    if sort_by == "oldest":
        order_by = "create_time ASC"
    elif sort_by == "likes":
        order_by = "likes DESC, create_time DESC"
    else:  # latest
        order_by = "create_time DESC"
    
    # 查询评论
    try:
        comments = query_records(
            'wxapp_comments',
            conditions=conditions,
            order_by=order_by,
            limit=limit,
            offset=offset
        )
        
        # 查询总评论数量
        total_count = count_records('wxapp_comments', conditions)
        
        # 处理评论数据
        processed_comments = []
        for comment in comments:
            # 处理JSON字段
            processed_comment = process_json_fields(comment)
            
            # 获取回复数量
            if parent_id is None:  # 只对顶级评论获取回复数量
                reply_count = count_records('wxapp_comments', {
                    "parent_id": comment['id'],
                    "is_deleted": 0
                })
                processed_comment['reply_count'] = reply_count
                
                # 获取少量回复预览
                if reply_count > 0:
                    replies = query_records(
                        'wxapp_comments',
                        conditions={"parent_id": comment['id'], "is_deleted": 0},
                        order_by="create_time DESC",
                        limit=3
                    )
                    
                    if replies:
                        processed_replies = []
                        for reply in replies:
                            processed_reply = process_json_fields(reply)
                            processed_replies.append(processed_reply)
                        
                        processed_comment['reply_preview'] = processed_replies
            
            processed_comments.append(processed_comment)
        
        return create_standard_response({
            'comments': processed_comments,
            'total': total_count,
            'limit': limit,
            'offset': offset,
            'post_id': post_id,
            'parent_id': parent_id
        })
    except Exception as e:
        api_logger.error(f"获取评论列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取评论列表失败: {str(e)}")

@router.put("/comments/{comment_id}", response_model=Dict[str, Any], summary="更新评论")
@handle_api_errors("更新评论")
async def update_comment(
    comment_update: CommentUpdate,
    comment_id: int = PathParam(..., description="评论ID"),
    api_logger=Depends(get_api_logger)
):
    """更新评论内容"""
    # 检查评论是否存在
    comment = get_record_by_id('wxapp_comments', comment_id)
    if not comment or comment.get('is_deleted', 0) == 1:
        raise HTTPException(status_code=404, detail="评论不存在或已删除")
    
    # 过滤掉None值
    update_data = {k: v for k, v in comment_update.dict().items() if v is not None}
    if not update_data:
        # 没有需要更新的字段，返回原评论
        return create_standard_response(process_json_fields(comment))
    
    # 验证内容
    if 'content' in update_data and (not update_data['content'] or len(update_data['content'].strip()) < 1):
        raise HTTPException(status_code=400, detail="评论内容不能为空")
    
    # 处理extra字段
    if 'extra' in update_data:
        update_data['extra'] = json.dumps(update_data['extra'])
    
    # 添加更新时间
    update_data = prepare_db_data(update_data, is_create=False)
    
    # 更新记录
    success = update_record('wxapp_comments', comment_id, update_data)
    if not success:
        raise HTTPException(status_code=500, detail="更新评论失败")
    
    # 获取更新后的评论
    updated_comment = get_record_by_id('wxapp_comments', comment_id)
    
    # 处理JSON字段
    updated_comment = process_json_fields(updated_comment)
    
    return create_standard_response(updated_comment)

@router.put("/comments/{comment_id}/like", response_model=Dict[str, Any], summary="点赞评论")
@handle_api_errors("点赞评论")
async def like_comment(
    comment_id: int = PathParam(..., description="评论ID"),
    openid: str = Body(..., embed=True, description="用户openid"),
    api_logger=Depends(get_api_logger)
):
    """点赞或取消点赞评论"""
    # 检查评论是否存在
    comment = get_record_by_id('wxapp_comments', comment_id)
    if not comment or comment.get('is_deleted', 0) == 1:
        raise HTTPException(status_code=404, detail="评论不存在或已删除")
    
    # 处理liked_users字段
    liked_users = []
    if comment.get('liked_users'):
        try:
            liked_users = json.loads(comment['liked_users'])
        except:
            liked_users = []
    
    # 判断用户是否已点赞
    user_liked = openid in liked_users
    
    # 更新点赞状态
    if user_liked:
        # 如果已点赞，则取消点赞
        liked_users.remove(openid)
        like_count = max(0, comment.get('like_count', 0) - 1)
        action = "取消点赞"
    else:
        # 如果未点赞，则添加点赞
        liked_users.append(openid)
        like_count = comment.get('like_count', 0) + 1
        action = "点赞"
    
    # 更新评论
    update_data = {
        'like_count': like_count,
        'liked_users': json.dumps(liked_users)
    }
    success = update_record('wxapp_comments', comment_id, prepare_db_data(update_data, is_create=False))
    
    if not success:
        raise HTTPException(status_code=500, detail=f"{action}评论失败")
    
    # 如果是新增点赞，创建通知
    if action == "点赞" and comment.get('openid') != openid:
        try:
            # 获取用户信息
            user = query_records('wxapp_users', conditions={"openid": openid})
            nick_name = user[0].get('nick_name', '用户') if user and len(user) > 0 else '用户'
            
            notification_data = {
                'openid': comment.get('openid'),
                'title': '收到新点赞',
                'content': f"{nick_name}点赞了您的评论",
                'type': 'like',
                'sender_openid': openid,
                'related_id': str(comment_id),
                'related_type': 'comment',
                'platform': 'wxapp',
                'is_deleted': 0,
                'extra': json.dumps({
                    'post_id': comment.get('post_id')
                })
            }
            insert_record('wxapp_notifications', prepare_db_data(notification_data, is_create=True))
        except Exception as e:
            api_logger.error(f"创建点赞通知失败: {str(e)}")
    
    # 获取更新后的评论
    updated_comment = get_record_by_id('wxapp_comments', comment_id)
    updated_comment = process_json_fields(updated_comment)
    
    return create_standard_response({
        'comment': updated_comment,
        'action': action,
        'user_liked': not user_liked  # 返回更新后的状态
    })

@router.delete("/comments/{comment_id}", response_model=Dict[str, Any], summary="删除评论")
@handle_api_errors("删除评论")
async def delete_comment(
    comment_id: int = PathParam(..., description="评论ID"),
    openid: Optional[str] = Query(None, description="用户openid，用于权限验证"),
    api_logger=Depends(get_api_logger)
):
    """删除评论（标记删除）"""
    # 检查评论是否存在
    comment = get_record_by_id('wxapp_comments', comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail="评论不存在")
    
    # 如果指定了用户ID，检查权限
    if openid and comment.get('openid') != openid:
        # 检查是否为管理员权限
        try:
            user = query_records('wxapp_users', conditions={"openid": openid})
            is_admin = user[0].get('is_admin', 0) if user and len(user) > 0 else 0
            
            if not is_admin:
                raise HTTPException(status_code=403, detail="您无权删除该评论")
        except Exception as e:
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(status_code=403, detail="权限验证失败")
    
    # 标记删除
    update_data = {
        'is_deleted': 1,
        'update_time': format_datetime(None)
    }
    
    success = update_record('wxapp_comments', comment_id, update_data)
    
    if not success:
        raise HTTPException(status_code=500, detail="删除评论失败")
    
    return create_standard_response({
        "success": True,
        "message": "评论已删除"
    }) 