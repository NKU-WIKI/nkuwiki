"""
微信小程序API接口
提供对微信小程序用户、帖子、评论等数据的操作接口
"""
import re
import time
from datetime import datetime
from fastapi import APIRouter, HTTPException, Path as PathParam, Depends, Query, Body
from pydantic import BaseModel, Field, validator
from typing import List, Dict, Any, Optional, Union, Callable, TypeVar, Generic
from loguru import logger
from fastapi.responses import JSONResponse

# 导入标准响应模块
from core.api.response import StandardResponse, create_standard_response, get_schema_api_router

# 数据库相关导入
from etl.load.py_mysql import (
    insert_record, update_record, delete_record, 
    query_records, count_records, get_record_by_id,
    batch_insert, upsert_record
)
# 导入JSON字段处理工具函数
from etl.load.process_json import process_post_json_fields, process_post_create_data

# 定义泛型类型变量
T = TypeVar('T')

# 创建专用API路由（使用适配器函数）
wxapp_router = get_schema_api_router(
    prefix="/wxapp",
    tags=["微信小程序"],
    responses={404: {"description": "Not found"}},
)

# 添加异常处理中间件
# 注释掉路由器上的异常处理器，移动到全局异常处理
'''
@wxapp_router.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """自定义HTTP异常处理器，确保异常也返回标准格式"""
    return JSONResponse(
        status_code=exc.status_code,
        content=create_standard_response(
            data=None,
            code=exc.status_code,
            message=str(exc.detail)
        )
    )

@wxapp_router.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """通用异常处理器，确保所有异常都返回标准格式"""
    logger.error(f"未捕获的异常: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content=create_standard_response(
            data=None,
            code=500,
            message=f"服务器内部错误: {str(exc)}"
        )
    )
'''

# 请求和响应模型
class UserBase(BaseModel):
    """用户基础信息"""
    wxapp_id: str = Field(..., description="微信小程序原始ID")
    openid: Optional[str] = Field(None, description="微信用户唯一标识")
    unionid: Optional[str] = Field(None, description="微信开放平台唯一标识")
    nickname: Optional[str] = Field(None, description="用户昵称")
    avatar_url: Optional[str] = Field(None, description="头像URL")
    gender: Optional[int] = Field(0, description="性别：0-未知, 1-男, 2-女")
    country: Optional[str] = Field(None, description="国家")
    province: Optional[str] = Field(None, description="省份")
    city: Optional[str] = Field(None, description="城市")
    language: Optional[str] = Field(None, description="语言")
    
    @validator('wxapp_id')
    def validate_wxapp_id(cls, v):
        if not v or not v.strip():
            raise ValueError("微信小程序ID不能为空")
        return v.strip()

class UserCreate(UserBase):
    """创建用户请求"""
    pass

class UserUpdate(BaseModel):
    """更新用户请求"""
    nickname: Optional[str] = None
    avatar_url: Optional[str] = None
    gender: Optional[int] = None
    country: Optional[str] = None
    province: Optional[str] = None
    city: Optional[str] = None
    language: Optional[str] = None
    status: Optional[int] = None

class UserResponse(UserBase):
    """用户响应"""
    id: int
    create_time: datetime
    update_time: datetime
    last_login: Optional[datetime] = None
    status: int = 1

class PostBase(BaseModel):
    """帖子基础信息"""
    wxapp_id: str = Field(..., description="微信小程序原始ID")
    author_id: str = Field(..., description="作者ID")
    author_name: Optional[str] = Field(None, description="作者名称")
    author_avatar: Optional[str] = Field(None, description="作者头像URL")
    content: Optional[str] = Field(None, description="帖子内容")
    title: Optional[str] = Field(None, description="帖子标题")
    images: Optional[List[str]] = Field(None, description="图片列表")
    tags: Optional[List[str]] = Field(None, description="标签列表")
    
    @validator('wxapp_id', 'author_id')
    def validate_required(cls, v, values, **kwargs):
        if not v or not v.strip():
            field_name = kwargs.get('field').name
            raise ValueError(f"{field_name}不能为空")
        return v.strip()

class PostCreate(PostBase):
    """创建帖子请求"""
    pass

class PostUpdate(BaseModel):
    """更新帖子请求"""
    content: Optional[str] = None
    title: Optional[str] = None
    images: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    status: Optional[int] = None

class PostResponse(PostBase):
    """帖子响应"""
    id: int
    likes: int = 0
    comment_count: int = 0
    create_time: datetime
    update_time: datetime
    status: int = 1

class CommentBase(BaseModel):
    """评论基础信息"""
    wxapp_id: str = Field(..., description="微信小程序原始ID")
    post_id: str = Field(..., description="帖子ID")
    author_id: str = Field(..., description="作者ID")
    author_name: Optional[str] = Field(None, description="作者名称")
    author_avatar: Optional[str] = Field(None, description="作者头像URL")
    content: Optional[str] = Field(None, description="评论内容")
    images: Optional[List[str]] = Field(None, description="图片列表")
    
    @validator('wxapp_id', 'post_id', 'author_id')
    def validate_required(cls, v, values, **kwargs):
        if not v or not v.strip():
            field_name = kwargs.get('field').name
            raise ValueError(f"{field_name}不能为空")
        return v.strip()

class CommentCreate(CommentBase):
    """创建评论请求"""
    pass

class CommentUpdate(BaseModel):
    """更新评论请求"""
    content: Optional[str] = None
    images: Optional[List[str]] = None
    status: Optional[int] = None

class CommentResponse(CommentBase):
    """评论响应"""
    id: int
    likes: int = 0
    create_time: datetime
    update_time: datetime
    status: int = 1

# 工具函数
def format_datetime(dt):
    """格式化日期时间"""
    if not dt:
        return None
    return dt.strftime("%Y-%m-%d %H:%M:%S")

def prepare_db_data(data_dict, is_create=False):
    """准备数据库数据"""
    result = dict(data_dict)
    
    # 处理JSON字段
    for field in ['images', 'tags', 'liked_users', 'favorite_users']:
        if field in result and result[field] is not None:
            result[field] = str(result[field])
    
    # 添加创建/更新时间
    current_time = format_datetime(datetime.now())
    if is_create:
        result['create_time'] = current_time
    result['update_time'] = current_time
    
    return result

def process_json_fields(post_data):
    """处理帖子的JSON字段，确保格式正确
    
    Args:
        post_data: 帖子数据字典
        
    Returns:
        处理后的帖子数据字典
    """
    # 使用新的工具函数处理JSON字段
    return process_post_json_fields(post_data)

# ====================== 用户接口 ======================
@wxapp_router.post("/users", response_model=Dict[str, Any], summary="创建用户")
async def create_user(user: UserCreate):
    """创建新用户"""
    try:
        # 检查用户是否已存在
        existing_users = query_records(
            'wxapp_users', 
            conditions={'wxapp_id': user.wxapp_id}
        )
        if existing_users:
            raise HTTPException(status_code=400, detail="该用户已存在")
        
        # 准备数据
        user_data = prepare_db_data(user.dict(), is_create=True)
        
        # 插入记录
        user_id = insert_record('wxapp_users', user_data)
        if not user_id:
            raise HTTPException(status_code=500, detail="创建用户失败")
        
        # 获取创建的用户
        created_user = get_record_by_id('wxapp_users', user_id)
        if not created_user:
            raise HTTPException(status_code=404, detail="找不到创建的用户")
        
        return create_standard_response(created_user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建用户失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"创建用户失败: {str(e)}")

@wxapp_router.get("/users/{user_id}", response_model=Dict[str, Any], summary="获取用户信息")
async def get_user(user_id: int = PathParam(..., description="用户ID")):
    """获取指定用户信息"""
    try:
        user = get_record_by_id('wxapp_users', user_id)
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
        return create_standard_response(user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取用户失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取用户失败: {str(e)}")

@wxapp_router.get("/users", response_model=Dict[str, Any], summary="查询用户列表")
async def list_users(
    limit: int = Query(20, description="返回记录数量限制", ge=1, le=100),
    offset: int = Query(0, description="分页偏移量", ge=0),
    status: Optional[int] = Query(None, description="用户状态: 1-正常, 0-禁用")
):
    """获取用户列表"""
    try:
        conditions = {}
        if status is not None:
            conditions['status'] = status
        
        users = query_records(
            'wxapp_users',
            conditions=conditions,
            order_by='id DESC',
            limit=limit,
            offset=offset
        )
        return create_standard_response(users)
    except Exception as e:
        logger.error(f"查询用户列表失败: {str(e)}")
        return create_standard_response([], code=500, message=f"查询用户列表失败: {str(e)}")

@wxapp_router.put("/users/{user_id}", response_model=UserResponse, summary="更新用户信息")
async def update_user(
    user_update: UserUpdate,
    user_id: int = PathParam(..., description="用户ID")
):
    """更新用户信息"""
    try:
        # 检查用户是否存在
        user = get_record_by_id('wxapp_users', user_id)
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        # 过滤掉None值
        update_data = {k: v for k, v in user_update.dict().items() if v is not None}
        if not update_data:
            return user
        
        # 处理微信云存储的fileID
        if "avatar_url" in update_data and update_data["avatar_url"] and update_data["avatar_url"].startswith("cloud://"):
            # 保存微信云存储的fileID，不进行额外处理
            logger.debug(f"检测到微信云存储fileID: {update_data['avatar_url']}")
            # 如果需要，可以在此转换为临时URL后再保存，但简单起见，直接保存fileID
        
        # 添加更新时间
        update_data['update_time'] = format_datetime(datetime.now())
        
        # 更新记录
        success = update_record('wxapp_users', user_id, update_data)
        if not success:
            raise HTTPException(status_code=500, detail="更新用户失败")
        
        # 获取更新后的用户
        updated_user = get_record_by_id('wxapp_users', user_id)
        return updated_user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新用户失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"更新用户失败: {str(e)}")

@wxapp_router.delete("/users/{user_id}", response_model=dict, summary="删除用户")
async def delete_user(user_id: int = PathParam(..., description="用户ID")):
    """删除用户（标记删除）"""
    try:
        # 检查用户是否存在
        user = get_record_by_id('wxapp_users', user_id)
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        # 标记删除
        success = update_record('wxapp_users', user_id, {
            'is_deleted': 1,
            'status': 0,
            'update_time': format_datetime(datetime.now())
        })
        
        if not success:
            raise HTTPException(status_code=500, detail="删除用户失败")
        
        return {"success": True, "message": "用户已删除"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除用户失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"删除用户失败: {str(e)}")

# ====================== 帖子接口 ======================
@wxapp_router.post("/posts", response_model=PostResponse, summary="创建帖子")
async def create_post(post: PostCreate):
    """创建新帖子"""
    try:
        # 验证并确保JSON字段格式正确
        post_dict = post.dict()
        
        # 使用新的工具函数处理创建帖子的数据
        post_data = process_post_create_data(post_dict)
        
        # 准备数据
        post_data = prepare_db_data(post_data, is_create=True)
        
        # 插入记录
        post_id = insert_record('wxapp_posts', post_data)
        if not post_id:
            raise HTTPException(status_code=500, detail="创建帖子失败")
        
        # 获取创建的帖子
        created_post = get_record_by_id('wxapp_posts', post_id)
        if not created_post:
            raise HTTPException(status_code=404, detail="找不到创建的帖子")
            
        # 处理返回的JSON字段
        created_post = process_post_json_fields(created_post)
        
        return created_post
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建帖子失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"创建帖子失败: {str(e)}")

@wxapp_router.get("/posts/{post_id}", response_model=Dict[str, Any], summary="获取帖子信息")
async def get_post(post_id: int = PathParam(..., description="帖子ID")):
    """获取指定帖子信息"""
    try:
        post = get_record_by_id('wxapp_posts', post_id)
        if not post:
            raise HTTPException(status_code=404, detail="帖子不存在")
            
        # 处理JSON字段，使用新的工具函数
        post = process_post_json_fields(post)
        
        return create_standard_response(post)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取帖子失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取帖子失败: {str(e)}")

@wxapp_router.get("/posts", response_model=Dict[str, Any], summary="查询帖子列表")
async def list_posts(
    limit: int = Query(20, description="返回记录数量限制", ge=1, le=100),
    offset: int = Query(0, description="分页偏移量", ge=0),
    author_id: Optional[str] = Query(None, description="作者ID"),
    tag: Optional[str] = Query(None, description="标签"),
    status: Optional[int] = Query(None, description="帖子状态: 1-正常, 0-禁用")
):
    """获取帖子列表"""
    try:
        conditions = {"is_deleted": 0}
        if author_id:
            conditions['author_id'] = author_id
        if status is not None:
            conditions['status'] = status
        
        posts = query_records(
            'wxapp_posts',
            conditions=conditions,
            order_by='id DESC',
            limit=limit,
            offset=offset
        )
        
        logger.debug(f"查询到 {len(posts)} 条帖子记录")
        
        # 处理返回的帖子列表，确保JSON字段正确解析
        processed_posts = []
        for post in posts:
            try:
                # 处理帖子JSON字段，使用新的工具函数
                processed_post = process_post_json_fields(post)
                processed_posts.append(processed_post)
            except Exception as e:
                logger.error(f"处理帖子数据失败: {str(e)}, 跳过该帖子")
                # 继续处理下一个帖子而不中断整个过程
        
        # 如果有标签过滤，需要在内存中处理
        if tag and processed_posts:
            filtered_posts = []
            for post in processed_posts:
                post_tags = post.get('tags', [])
                if post_tags and tag in post_tags:
                    filtered_posts.append(post)
            processed_posts = filtered_posts
        
        return create_standard_response(processed_posts)
    except Exception as e:
        logger.error(f"查询帖子列表失败: {str(e)}")
        # 返回空列表而不是抛出异常，避免前端崩溃
        return create_standard_response([], code=500, message=f"查询帖子列表失败: {str(e)}")

@wxapp_router.put("/posts/{post_id}", response_model=Dict[str, Any], summary="更新帖子")
async def update_post(
    post_update: PostUpdate,
    post_id: int = PathParam(..., description="帖子ID")
):
    """更新帖子信息"""
    try:
        # 检查帖子是否存在
        post = get_record_by_id('wxapp_posts', post_id)
        if not post:
            raise HTTPException(status_code=404, detail="帖子不存在")
        
        # 过滤掉None值
        update_data = {k: v for k, v in post_update.dict().items() if v is not None}
        if not update_data:
            return create_standard_response(process_post_json_fields(post))
        
        # 处理JSON字段
        for field in ['images', 'tags']:
            if field in update_data and update_data[field] is not None:
                update_data[field] = str(update_data[field])
        
        # 添加更新时间
        update_data['update_time'] = format_datetime(datetime.now())
        
        # 更新记录
        success = update_record('wxapp_posts', post_id, update_data)
        if not success:
            raise HTTPException(status_code=500, detail="更新帖子失败")
        
        # 获取更新后的帖子
        updated_post = get_record_by_id('wxapp_posts', post_id)
        
        # 处理返回的JSON字段
        updated_post = process_post_json_fields(updated_post)
        
        return create_standard_response(updated_post)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新帖子失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"更新帖子失败: {str(e)}")

@wxapp_router.delete("/posts/{post_id}", response_model=Dict[str, Any], summary="删除帖子")
async def delete_post(post_id: int = PathParam(..., description="帖子ID")):
    """删除帖子（标记删除）"""
    try:
        # 检查帖子是否存在
        post = get_record_by_id('wxapp_posts', post_id)
        if not post:
            raise HTTPException(status_code=404, detail="帖子不存在")
        
        # 标记删除
        success = update_record('wxapp_posts', post_id, {
            'is_deleted': 1,
            'status': 0,
            'update_time': format_datetime(datetime.now())
        })
        
        if not success:
            raise HTTPException(status_code=500, detail="删除帖子失败")
        
        return create_standard_response({"success": True, "message": "帖子已删除"})
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除帖子失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"删除帖子失败: {str(e)}")

@wxapp_router.post("/posts/{post_id}/like", response_model=Dict[str, Any], summary="点赞帖子")
async def like_post(
    post_id: int = PathParam(..., description="帖子ID"),
    user_id: str = Body(..., embed=True, description="用户ID")
):
    """点赞帖子"""
    try:
        # 检查帖子是否存在
        post = get_record_by_id('wxapp_posts', post_id)
        if not post:
            raise HTTPException(status_code=404, detail="帖子不存在")
        
        # 处理帖子中的JSON字段，确保liked_users格式正确
        processed_post = process_json_fields(post)
        
        # 获取当前点赞信息
        liked_users = processed_post.get('liked_users', [])
        
        # 检查是否已点赞
        if user_id in liked_users:
            return create_standard_response({"success": True, "message": "已经点赞过了", "likes": len(liked_users)})
        
        # 添加用户到点赞列表
        liked_users.append(user_id)
        
        # 更新帖子
        update_data = {
            'likes': len(liked_users),
            'liked_users': str(liked_users),
            'update_time': format_datetime(datetime.now())
        }
        
        success = update_record('wxapp_posts', post_id, update_data)
        if not success:
            raise HTTPException(status_code=500, detail="点赞失败")
        
        return create_standard_response({"success": True, "message": "点赞成功", "likes": len(liked_users)})
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"点赞帖子失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"点赞帖子失败: {str(e)}")

@wxapp_router.post("/posts/{post_id}/unlike", response_model=Dict[str, Any], summary="取消点赞帖子")
async def unlike_post(
    post_id: int = PathParam(..., description="帖子ID"),
    user_id: str = Body(..., embed=True, description="用户ID")
):
    """取消点赞帖子"""
    try:
        # 获取帖子信息
        post = get_record_by_id('wxapp_posts', post_id)
        if not post:
            raise HTTPException(status_code=404, detail="帖子不存在")
        
        # 处理JSON字段
        processed_post = process_json_fields(post)
        
        # 移除用户ID
        liked_users = processed_post.get('liked_users', [])
        if user_id in liked_users:
            liked_users.remove(user_id)
        
        # 更新帖子
        update_data = {
            'liked_users': str(liked_users),
            'likes': max(0, len(liked_users)),
            'update_time': format_datetime(datetime.now())
        }
        
        updated = update_record('wxapp_posts', post_id, update_data)
        if not updated:
            raise HTTPException(status_code=500, detail="取消点赞失败")
        
        return create_standard_response({"success": True, "message": "取消点赞成功", "likes": len(liked_users)})
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"取消点赞帖子失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"取消点赞帖子失败: {str(e)}")

# 添加收藏帖子接口
@wxapp_router.post("/posts/{post_id}/favorite", response_model=Dict[str, Any], summary="收藏帖子")
async def favorite_post(
    post_id: int = PathParam(..., description="帖子ID"),
    user_id: str = Body(..., embed=True, description="用户ID")
):
    """收藏帖子"""
    try:
        # 获取帖子信息
        post = get_record_by_id('wxapp_posts', post_id)
        if not post:
            raise HTTPException(status_code=404, detail="帖子不存在")
        
        # 处理JSON字段，使用新的工具函数
        processed_post = process_post_json_fields(post)
        
        # 添加用户ID到收藏列表
        favorite_users = processed_post.get('favorite_users', [])
        if user_id not in favorite_users:
            favorite_users.append(user_id)
        
        # 更新帖子
        update_data = {
            'favorite_users': str(favorite_users),
            'favorite_count': len(favorite_users),
            'update_time': format_datetime(datetime.now())
        }
        
        logger.debug(f"收藏帖子，帖子ID: {post_id}, 用户ID: {user_id}, 收藏用户列表: {favorite_users}")
        
        updated = update_record('wxapp_posts', post_id, update_data)
        if not updated:
            raise HTTPException(status_code=500, detail="收藏失败")
        
        return create_standard_response({"success": True, "message": "收藏成功", "favorite_count": len(favorite_users)})
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"收藏帖子失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"收藏帖子失败: {str(e)}")

# 添加取消收藏帖子接口
@wxapp_router.post("/posts/{post_id}/unfavorite", response_model=Dict[str, Any], summary="取消收藏帖子")
async def unfavorite_post(
    post_id: int = PathParam(..., description="帖子ID"),
    user_id: str = Body(..., embed=True, description="用户ID")
):
    """取消收藏帖子"""
    try:
        # 获取帖子信息
        post = get_record_by_id('wxapp_posts', post_id)
        if not post:
            raise HTTPException(status_code=404, detail="帖子不存在")
        
        # 处理JSON字段，使用新的工具函数
        processed_post = process_post_json_fields(post)
        
        # 移除用户ID从收藏列表
        favorite_users = processed_post.get('favorite_users', [])
        if user_id in favorite_users:
            favorite_users.remove(user_id)
        
        # 更新帖子
        update_data = {
            'favorite_users': str(favorite_users),
            'favorite_count': len(favorite_users),
            'update_time': format_datetime(datetime.now())
        }
        
        logger.debug(f"取消收藏帖子，帖子ID: {post_id}, 用户ID: {user_id}, 收藏用户列表: {favorite_users}")
        
        updated = update_record('wxapp_posts', post_id, update_data)
        if not updated:
            raise HTTPException(status_code=500, detail="取消收藏失败")
        
        return create_standard_response({"success": True, "message": "取消收藏成功", "favorite_count": len(favorite_users)})
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"取消收藏帖子失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"取消收藏帖子失败: {str(e)}")

# ====================== 评论接口 ======================
@wxapp_router.post("/comments", response_model=CommentResponse, summary="创建评论")
async def create_comment(comment: CommentCreate):
    """创建新评论"""
    try:
        # 准备数据
        comment_data = prepare_db_data(comment.dict(), is_create=True)
        
        # 插入记录
        comment_id = insert_record('wxapp_comments', comment_data)
        if not comment_id:
            raise HTTPException(status_code=500, detail="创建评论失败")
        
        # 更新帖子评论数
        post_id = comment.post_id
        post_conditions = {'wxapp_id': post_id}
        posts = query_records('wxapp_posts', conditions=post_conditions)
        
        if posts:
            post = posts[0]
            post_update = {
                'comment_count': post.get('comment_count', 0) + 1,
                'update_time': format_datetime(datetime.now())
            }
            update_record('wxapp_posts', post['id'], post_update)
        
        # 获取创建的评论
        created_comment = get_record_by_id('wxapp_comments', comment_id)
        if not created_comment:
            raise HTTPException(status_code=404, detail="找不到创建的评论")
        
        # 处理评论中的JSON字段
        created_comment = process_json_fields(created_comment)
        
        return created_comment
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建评论失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"创建评论失败: {str(e)}")

@wxapp_router.get("/comments/{comment_id}", response_model=Dict[str, Any], summary="获取评论信息")
async def get_comment(comment_id: int = PathParam(..., description="评论ID")):
    """获取指定评论信息"""
    try:
        comment = get_record_by_id('wxapp_comments', comment_id)
        if not comment:
            raise HTTPException(status_code=404, detail="评论不存在")
        
        # 处理JSON字段
        comment = process_json_fields(comment)
        
        return create_standard_response(comment)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取评论失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取评论失败: {str(e)}")

@wxapp_router.get("/comments", response_model=Dict[str, Any], summary="查询评论列表")
async def list_comments(
    limit: int = Query(20, description="返回记录数量限制", ge=1, le=100),
    offset: int = Query(0, description="分页偏移量", ge=0),
    post_id: Optional[str] = Query(None, description="帖子ID"),
    author_id: Optional[str] = Query(None, description="作者ID"),
    status: Optional[int] = Query(None, description="评论状态: 1-正常, 0-禁用")
):
    """获取评论列表"""
    try:
        conditions = {}
        if post_id:
            conditions['post_id'] = post_id
        if author_id:
            conditions['author_id'] = author_id
        if status is not None:
            conditions['status'] = status
        
        comments = query_records(
            'wxapp_comments',
            conditions=conditions,
            order_by='id DESC',
            limit=limit,
            offset=offset
        )
        
        # 处理返回的评论列表，确保JSON字段正确解析
        processed_comments = []
        for comment in comments:
            try:
                processed_comment = process_json_fields(comment)
                processed_comments.append(processed_comment)
            except Exception as e:
                logger.error(f"处理评论数据失败: {str(e)}, 跳过该评论")
                # 继续处理下一个评论而不中断整个过程
        
        return create_standard_response(processed_comments)
    except Exception as e:
        logger.error(f"查询评论列表失败: {str(e)}")
        return create_standard_response([], code=500, message=f"查询评论列表失败: {str(e)}")

@wxapp_router.put("/comments/{comment_id}", response_model=CommentResponse, summary="更新评论")
async def update_comment(
    comment_update: CommentUpdate,
    comment_id: int = PathParam(..., description="评论ID")
):
    """更新评论信息"""
    try:
        # 检查评论是否存在
        comment = get_record_by_id('wxapp_comments', comment_id)
        if not comment:
            raise HTTPException(status_code=404, detail="评论不存在")
        
        # 过滤掉None值
        update_data = {k: v for k, v in comment_update.dict().items() if v is not None}
        if not update_data:
            return comment
        
        # 处理JSON字段
        if 'images' in update_data and update_data['images'] is not None:
            update_data['images'] = str(update_data['images'])
        
        # 添加更新时间
        update_data['update_time'] = format_datetime(datetime.now())
        
        # 更新记录
        success = update_record('wxapp_comments', comment_id, update_data)
        if not success:
            raise HTTPException(status_code=500, detail="更新评论失败")
        
        # 获取更新后的评论
        updated_comment = get_record_by_id('wxapp_comments', comment_id)
        
        # 处理评论中的JSON字段
        updated_comment = process_json_fields(updated_comment)
        
        return updated_comment
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新评论失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"更新评论失败: {str(e)}")

@wxapp_router.delete("/comments/{comment_id}", response_model=dict, summary="删除评论")
async def delete_comment(comment_id: int = PathParam(..., description="评论ID")):
    """删除评论（标记删除）"""
    try:
        # 检查评论是否存在
        comment = get_record_by_id('wxapp_comments', comment_id)
        if not comment:
            raise HTTPException(status_code=404, detail="评论不存在")
        
        # 标记删除
        success = update_record('wxapp_comments', comment_id, {
            'is_deleted': 1,
            'status': 0,
            'update_time': format_datetime(datetime.now())
        })
        
        if not success:
            raise HTTPException(status_code=500, detail="删除评论失败")
        
        # 更新帖子评论数
        post_id = comment.get('post_id')
        if post_id:
            post_conditions = {'wxapp_id': post_id}
            posts = query_records('wxapp_posts', conditions=post_conditions)
            
            if posts:
                post = posts[0]
                comment_count = max(0, post.get('comment_count', 0) - 1)
                post_update = {
                    'comment_count': comment_count,
                    'update_time': format_datetime(datetime.now())
                }
                update_record('wxapp_posts', post['id'], post_update)
        
        return {"success": True, "message": "评论已删除"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除评论失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"删除评论失败: {str(e)}")

@wxapp_router.post("/comments/{comment_id}/like", response_model=Dict[str, Any], summary="点赞评论")
async def like_comment(
    comment_id: int = PathParam(..., description="评论ID"),
    user_id: str = Body(..., embed=True, description="用户ID")
):
    """点赞评论"""
    try:
        # 检查评论是否存在
        comment = get_record_by_id('wxapp_comments', comment_id)
        if not comment:
            raise HTTPException(status_code=404, detail="评论不存在")
        
        # 处理评论中的JSON字段，确保liked_users格式正确
        processed_comment = process_json_fields(comment)
        
        # 获取当前点赞信息
        liked_users = processed_comment.get('liked_users', [])
        
        # 检查是否已点赞
        if user_id in liked_users:
            return create_standard_response({"success": True, "message": "已经点赞过了", "likes": len(liked_users)})
        
        # 添加用户到点赞列表
        liked_users.append(user_id)
        
        # 更新评论
        update_data = {
            'likes': len(liked_users),
            'liked_users': str(liked_users),
            'update_time': format_datetime(datetime.now())
        }
        
        success = update_record('wxapp_comments', comment_id, update_data)
        if not success:
            raise HTTPException(status_code=500, detail="点赞失败")
        
        return create_standard_response({"success": True, "message": "点赞成功", "likes": len(liked_users)})
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"点赞评论失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"点赞评论失败: {str(e)}")

@wxapp_router.post("/comments/{comment_id}/unlike", response_model=Dict[str, Any], summary="取消点赞评论")
async def unlike_comment(
    comment_id: int = PathParam(..., description="评论ID"),
    user_id: str = Body(..., embed=True, description="用户ID")
):
    """取消点赞评论"""
    try:
        # 检查评论是否存在
        comment = get_record_by_id('wxapp_comments', comment_id)
        if not comment:
            raise HTTPException(status_code=404, detail="评论不存在")
        
        # 处理评论中的JSON字段，确保liked_users格式正确
        processed_comment = process_json_fields(comment)
        
        # 获取当前点赞信息
        liked_users = processed_comment.get('liked_users', [])
        
        # 检查是否已点赞
        if user_id not in liked_users:
            return create_standard_response({"success": True, "message": "未点赞", "likes": len(liked_users)})
        
        # 从点赞列表移除用户
        liked_users.remove(user_id)
        
        # 更新评论
        update_data = {
            'likes': len(liked_users),
            'liked_users': str(liked_users),
            'update_time': format_datetime(datetime.now())
        }
        
        success = update_record('wxapp_comments', comment_id, update_data)
        if not success:
            raise HTTPException(status_code=500, detail="取消点赞失败")
        
        return create_standard_response({"success": True, "message": "取消点赞成功", "likes": len(liked_users)})
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"取消点赞评论失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"取消点赞评论失败: {str(e)}") 