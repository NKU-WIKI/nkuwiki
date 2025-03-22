"""
微信小程序帖子API
提供帖子管理相关的API接口
"""
from fastapi import HTTPException, Path as PathParam, Depends, Query
from pydantic import BaseModel, Field, validator, root_validator
from typing import Dict, Any, Optional, List
import json
import traceback
from datetime import datetime

# 导入通用组件
from core.api.common import get_api_logger, handle_api_errors, create_standard_response
from core.api import wxapp_router as router
from core.api.wxapp.common_utils import format_datetime, prepare_db_data, process_json_fields

# 导入数据库操作函数
from etl.load.py_mysql import (
    insert_record, update_record, delete_record, 
    query_records, count_records, get_record_by_id
)

# 帖子模型
class PostBase(BaseModel):
    """帖子基础信息"""
    user_id: Optional[str] = Field(None, description="发布用户ID")
    title: str = Field(..., description="帖子标题", min_length=1, max_length=100)
    content: str = Field(..., description="帖子内容")
    images: Optional[List[str]] = Field(default=[], description="图片URL列表")
    tags: Optional[List[str]] = Field(default=[], description="标签列表")
    category_id: Optional[int] = Field(None, description="分类ID")
    location: Optional[str] = Field(None, description="位置信息")
    author_name: Optional[str] = Field(None, description="作者名称")
    author_avatar: Optional[str] = Field(None, description="作者头像")
    
    @validator('user_id')
    def validate_user_id(cls, v):
        """确保user_id不为空"""
        if not v:
            raise ValueError("用户ID不能为空")
        return v
    
    @validator('title')
    def validate_title(cls, v):
        if not v or not v.strip():
            raise ValueError("帖子标题不能为空")
        return v.strip()
    
    @validator('content')
    def validate_content(cls, v):
        if not v or not v.strip():
            raise ValueError("帖子内容不能为空")
        return v.strip()

class PostCreate(PostBase):
    """创建帖子请求"""
    pass

class PostUpdate(BaseModel):
    """更新帖子请求"""
    title: Optional[str] = None
    content: Optional[str] = None
    images: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    category_id: Optional[int] = None
    location: Optional[str] = None
    status: Optional[int] = None
    
    @validator('title')
    def validate_title(cls, v):
        if v is not None and not v.strip():
            raise ValueError("帖子标题不能为空")
        return v.strip() if v else None
    
    @validator('content')
    def validate_content(cls, v):
        if v is not None and not v.strip():
            raise ValueError("帖子内容不能为空")
        return v.strip() if v else None

class PostResponse(PostBase):
    """帖子响应"""
    id: int
    create_time: str
    update_time: str
    view_count: int = 0
    like_count: int = 0
    comment_count: int = 0
    liked_users: List[int] = []
    favorite_users: List[int] = []
    status: int = 1

# API端点
@router.post("/posts", response_model=Dict[str, Any], summary="创建帖子")
@handle_api_errors("创建帖子")
async def create_post(
    post: PostCreate,
    api_logger=Depends(get_api_logger)
):
    """创建新帖子"""
    # 准备数据
    post_data = post.dict()
    
    # 记录请求详情
    api_logger.debug(f"创建帖子请求数据: {post_data}")
    
    # 处理JSON字段
    if 'images' in post_data and post_data['images']:
        post_data['images'] = json.dumps(post_data['images'])
    else:
        post_data['images'] = json.dumps([])
        
    if 'tags' in post_data and post_data['tags']:
        post_data['tags'] = json.dumps(post_data['tags'])
    else:
        post_data['tags'] = json.dumps([])
    
    # 适配数据库表字段
    if 'author_name' in post_data and post_data['author_name']:
        post_data['user_name'] = post_data['author_name']
        
    if 'author_avatar' in post_data and post_data['author_avatar']:
        post_data['user_avatar'] = post_data['author_avatar']
    
    # 如果wxapp_id不存在，生成一个唯一ID
    if 'wxapp_id' not in post_data or not post_data['wxapp_id']:
        import time
        post_data['wxapp_id'] = f"post_{int(time.time() * 1000)}"
        
    # 初始化点赞和收藏用户
    post_data['liked_users'] = json.dumps([])
    post_data['favorite_users'] = json.dumps([])
    
    # 添加其他默认值
    post_data['view_count'] = 0
    post_data['like_count'] = 0
    post_data['comment_count'] = 0
    post_data['status'] = 1
    post_data['is_deleted'] = 0
    post_data['platform'] = 'wxapp'
    
    # 准备数据库数据
    post_data = prepare_db_data(post_data, is_create=True)
    
    # 移除数据库不需要的字段
    for field in ['author_name', 'author_avatar']:
        if field in post_data:
            post_data.pop(field, None)
    
    # 数据库中user_id现在是VARCHAR类型，不需要转换为整数
    
    api_logger.debug(f"准备插入数据库的数据: {post_data}")
    
    # 插入记录
    post_id = insert_record('wxapp_posts', post_data)
    if not post_id:
        raise HTTPException(status_code=500, detail="创建帖子失败")
    
    # 获取创建的帖子
    created_post = get_record_by_id('wxapp_posts', post_id)
    if not created_post:
        raise HTTPException(status_code=404, detail="找不到创建的帖子")
    
    # 处理JSON字段显示
    created_post = process_json_fields(created_post)
    
    api_logger.info(f"帖子创建成功: ID={post_id}")
    return create_standard_response(created_post)

@router.get("/posts/{post_id}", response_model=Dict[str, Any], summary="获取帖子详情")
@handle_api_errors("获取帖子")
async def get_post(
    post_id: int = PathParam(..., description="帖子ID"),
    update_view: bool = Query(True, description="是否更新浏览量"),
    api_logger=Depends(get_api_logger)
):
    """获取指定帖子详情"""
    post = get_record_by_id('wxapp_posts', post_id)
    if not post:
        raise HTTPException(status_code=404, detail="帖子不存在")
    
    # 处理JSON字段
    post = process_json_fields(post)
    
    # 更新浏览量
    if update_view:
        update_record('wxapp_posts', post_id, {
            'view_count': post['view_count'] + 1,
            'update_time': format_datetime(None)  # 使用当前时间
        })
        post['view_count'] += 1
    
    return create_standard_response(post)

@router.get("/posts", response_model=Dict[str, Any], summary="查询帖子列表")
@handle_api_errors("查询帖子列表")
async def list_posts(
    limit: int = Query(20, description="返回记录数量限制", ge=1, le=100),
    offset: int = Query(0, description="分页偏移量", ge=0),
    user_id: Optional[str] = Query(None, description="按用户ID筛选"),
    category_id: Optional[int] = Query(None, description="按分类ID筛选"),
    tag: Optional[str] = Query(None, description="按标签筛选"),
    status: Optional[int] = Query(1, description="帖子状态: 1-正常, 0-禁用"),
    order_by: str = Query("update_time DESC", description="排序方式"),
    api_logger=Depends(get_api_logger)
):
    """获取帖子列表"""
    # 详细记录请求参数
    api_logger.info(f"Request: GET /posts with params: limit={limit}, offset={offset}, user_id={user_id}, category_id={category_id}, tag={tag}, status={status}, order_by={order_by}")
    
    try:
        # 构建查询条件
        conditions = {}
        if user_id is not None:
            # user_id现在是字符串类型，不需要转换
            conditions['user_id'] = user_id
                
        if category_id is not None:
            conditions['category_id'] = category_id
            
        if status is not None:
            conditions['status'] = status
            
        # 添加未删除条件
        conditions['is_deleted'] = 0
        
        # 记录查询条件
        api_logger.debug(f"查询条件: {conditions}")
        
        # 查询帖子列表
        api_logger.debug(f"执行查询: 表=wxapp_posts, 条件={conditions}, 排序={order_by}, 限制={limit}, 偏移={offset}")
        posts = query_records(
            'wxapp_posts',
            conditions=conditions,
            order_by=order_by,
            limit=limit,
            offset=offset
        )
        api_logger.debug(f"查询结果数量: {len(posts)}")
        
        # 处理标签筛选（数据库级别无法直接处理JSON字段）
        if tag and posts:
            api_logger.debug(f"按标签筛选: {tag}")
            filtered_posts = []
            for post in posts:
                post = process_json_fields(post)
                if 'tags' in post and tag in post['tags']:
                    filtered_posts.append(post)
            posts = filtered_posts
            api_logger.debug(f"标签筛选后数量: {len(posts)}")
        else:
            # 处理所有帖子的JSON字段
            posts = [process_json_fields(post) for post in posts]
            
        # 获取总数
        total_count = count_records('wxapp_posts', conditions)
        api_logger.debug(f"总记录数: {total_count}")
        
        # 构建响应数据
        response_data = {
            "posts": posts,
            "total": total_count,
            "limit": limit,
            "offset": offset
        }
        
        # 将结果转换为前端期望的格式
        api_logger.info(f"Response: 帖子列表查询成功，返回{len(posts)}条记录")
        
        # 返回标准响应，确保结果在data字段中
        return {
            "code": 200,
            "message": "success",
            "data": posts
        }
    except Exception as e:
        error_details = traceback.format_exc()
        api_logger.error(f"Error: 查询帖子列表失败: {str(e)}\n{error_details}")
        # 重新抛出异常让handle_api_errors装饰器处理
        raise HTTPException(status_code=500, detail=f"查询帖子失败: {str(e)}")

@router.put("/posts/{post_id}", response_model=Dict[str, Any], summary="更新帖子")
@handle_api_errors("更新帖子")
async def update_post(
    post_update: PostUpdate,
    post_id: int = PathParam(..., description="帖子ID"),
    api_logger=Depends(get_api_logger)
):
    """更新帖子信息"""
    # 检查帖子是否存在
    post = get_record_by_id('wxapp_posts', post_id)
    if not post:
        raise HTTPException(status_code=404, detail="帖子不存在")
    
    # 过滤掉None值
    update_data = {k: v for k, v in post_update.dict().items() if v is not None}
    if not update_data:
        # 没有需要更新的字段，返回原帖子
        return create_standard_response(process_json_fields(post))
    
    # 处理JSON字段
    if 'images' in update_data:
        update_data['images'] = json.dumps(update_data['images'])
        
    if 'tags' in update_data:
        update_data['tags'] = json.dumps(update_data['tags'])
    
    # 添加更新时间
    update_data = prepare_db_data(update_data, is_create=False)
    
    # 更新记录
    success = update_record('wxapp_posts', post_id, update_data)
    if not success:
        raise HTTPException(status_code=500, detail="更新帖子失败")
    
    # 获取更新后的帖子
    updated_post = get_record_by_id('wxapp_posts', post_id)
    
    # 处理JSON字段
    updated_post = process_json_fields(updated_post)
    
    return create_standard_response(updated_post)

@router.delete("/posts/{post_id}", response_model=Dict[str, Any], summary="删除帖子")
@handle_api_errors("删除帖子")
async def delete_post(
    post_id: int = PathParam(..., description="帖子ID"),
    api_logger=Depends(get_api_logger)
):
    """删除帖子（标记删除）"""
    # 检查帖子是否存在
    post = get_record_by_id('wxapp_posts', post_id)
    if not post:
        raise HTTPException(status_code=404, detail="帖子不存在")
    
    # 标记删除
    success = update_record('wxapp_posts', post_id, {
        'is_deleted': 1,
        'status': 0,
        'update_time': format_datetime(None)  # 使用当前时间
    })
    
    if not success:
        raise HTTPException(status_code=500, detail="删除帖子失败")
    
    return create_standard_response({
        "success": True,
        "message": "帖子已删除"
    })

@router.post("/posts/{post_id}/like", response_model=Dict[str, Any], summary="点赞/取消点赞帖子")
@handle_api_errors("点赞帖子")
async def like_post(
    post_id: int = PathParam(..., description="帖子ID"),
    user_id: str = Query(..., description="用户ID"),
    api_logger=Depends(get_api_logger)
):
    """点赞或取消点赞帖子"""
    # 检查帖子是否存在
    post = get_record_by_id('wxapp_posts', post_id)
    if not post:
        raise HTTPException(status_code=404, detail="帖子不存在")
    
    # 处理JSON字段
    post = process_json_fields(post)
    
    # 获取当前点赞用户列表
    liked_users = post.get('liked_users', [])
    
    # 判断是点赞还是取消点赞
    if user_id in liked_users:
        # 取消点赞
        liked_users.remove(user_id)
        like_count = max(0, post.get('like_count', 0) - 1)
        action = "取消点赞"
    else:
        # 点赞
        liked_users.append(user_id)
        like_count = post.get('like_count', 0) + 1
        action = "点赞"
    
    # 获取当前时间
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 更新帖子
    success = update_record('wxapp_posts', post_id, {
        'liked_users': json.dumps(liked_users),
        'like_count': like_count,
        'update_time': current_time  # 直接使用当前时间字符串
    })
    
    if not success:
        raise HTTPException(status_code=500, detail=f"{action}失败")
    
    return create_standard_response({
        "success": True,
        "message": f"{action}成功",
        "liked": user_id in liked_users,
        "like_count": like_count
    })

@router.post("/posts/{post_id}/favorite", response_model=Dict[str, Any], summary="收藏/取消收藏帖子")
@handle_api_errors("收藏帖子")
async def favorite_post(
    post_id: int = PathParam(..., description="帖子ID"),
    user_id: str = Query(..., description="用户ID"),
    is_favorite: bool = Query(True, description="是否收藏，默认为收藏操作"),
    api_logger=Depends(get_api_logger)
):
    """收藏或取消收藏帖子"""
    # 检查帖子是否存在
    post = get_record_by_id('wxapp_posts', post_id)
    if not post:
        raise HTTPException(status_code=404, detail="帖子不存在")
    
    # 处理JSON字段
    post = process_json_fields(post)
    
    # 获取当前收藏用户列表
    favorite_users = post.get('favorite_users', [])
    
    # 根据is_favorite参数决定是收藏还是取消收藏
    is_already_favorited = user_id in favorite_users
    
    if is_already_favorited and not is_favorite:
        # 取消收藏
        favorite_users.remove(user_id)
        action = "取消收藏"
    elif not is_already_favorited and is_favorite:
        # 收藏
        favorite_users.append(user_id)
        action = "收藏"
    else:
        # 状态已匹配，无需更改
        return create_standard_response({
            "success": True,
            "message": f"已经{'收藏' if is_favorite else '取消收藏'}",
            "favorited": is_favorite
        })
    
    # 获取当前时间
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 更新帖子
    success = update_record('wxapp_posts', post_id, {
        'favorite_users': json.dumps(favorite_users),
        'update_time': current_time  # 直接使用当前时间字符串
    })
    
    if not success:
        raise HTTPException(status_code=500, detail=f"{action}失败")
    
    return create_standard_response({
        "success": True,
        "message": f"{action}成功",
        "favorited": user_id in favorite_users
    }) 