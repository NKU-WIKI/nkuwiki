"""
微信小程序用户API
提供用户管理相关的API接口
"""
from datetime import datetime
from fastapi import HTTPException, Path as PathParam, Depends, Query, Body, APIRouter, Request, Header
from pydantic import BaseModel, Field, validator
from typing import Dict, Any, Optional, List
import json
import traceback

# 导入通用组件
from core.api.common import get_api_logger, handle_api_errors, create_standard_response
from core.api.wxapp.common_utils import format_datetime, prepare_db_data, process_json_fields

# 获取API路由器
from core.api import wxapp_router as router

# 导入数据库操作函数
from etl.load.py_mysql import (
    insert_record, update_record, delete_record, 
    query_records, count_records, get_record_by_id
)

# 用户模型
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

class UserSyncRequest(BaseModel):
    """云函数同步用户请求"""
    id: str = Field(..., description="微信云数据库ID")
    cloud_id_alias: Optional[str] = Field(None, description="微信云数据库ID（别名）")
    wxapp_id: str = Field(..., description="微信小程序原始ID")
    openid: str = Field(..., description="微信用户唯一标识")
    nickname: Optional[str] = Field(None, description="用户昵称")
    avatar_url: Optional[str] = Field(None, description="头像URL")
    university: Optional[str] = Field("南开大学", description="用户学校")
    login_type: Optional[str] = Field("wechat", description="登录类型")
    cloud_source: Optional[bool] = Field(False, description="是否来自云数据库")
    use_cloud_id: Optional[bool] = Field(False, description="是否使用云ID")

# API端点
@router.get("/users/me", response_model=Dict[str, Any], summary="获取当前用户信息")
@handle_api_errors("获取当前用户信息")
async def get_current_user(
    user_id: str = Query(..., description="用户ID"),
    api_logger=Depends(get_api_logger)
):
    """获取当前登录用户信息"""
    api_logger.info(f"Request: GET /users/me with user_id={user_id}")
    
    try:
        # 查询用户信息 - 先尝试直接ID查询
        api_logger.debug(f"查询用户信息: user_id={user_id}")
        user = get_record_by_id('wxapp_users', user_id)
        
        # 如果找不到，尝试通过cloud_id查询
        if not user:
            api_logger.debug(f"通过ID未找到用户 {user_id}，尝试通过cloud_id查询")
            cloud_id_users = query_records(
                'wxapp_users',
                conditions={'cloud_id': user_id}
            )
            if cloud_id_users:
                user = cloud_id_users[0]
                api_logger.debug(f"通过cloud_id找到用户: {user['id']}")
        
        if not user:
            api_logger.warning(f"用户不存在: user_id={user_id}")
            raise HTTPException(status_code=404, detail="用户不存在")
        
        # 处理用户信息中的JSON字段
        user = process_json_fields(user)
        api_logger.debug(f"用户信息获取成功: {user['id']}")
        
        # 返回用户信息
        api_logger.info(f"Response: 用户信息获取成功")
        return create_standard_response(user)
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        
        error_details = traceback.format_exc()
        api_logger.error(f"Error: 获取用户信息失败: {str(e)}\n{error_details}")
        raise HTTPException(status_code=500, detail=f"获取用户信息失败: {str(e)}")

@router.get("/users/{user_id}", response_model=Dict[str, Any], summary="获取用户信息")
@handle_api_errors("获取用户")
async def get_user(
    user_id: str = PathParam(..., description="用户ID"),
    api_logger=Depends(get_api_logger)
):
    """获取指定用户信息，支持通过ID或云ID查询"""
    api_logger.info(f"Request: GET /users/{user_id}")
    
    # 首先尝试直接通过ID查询
    user = get_record_by_id('wxapp_users', user_id)
    
    # 如果找不到，尝试通过cloud_id查询
    if not user:
        api_logger.debug(f"通过ID未找到用户 {user_id}，尝试通过cloud_id查询")
        cloud_id_users = query_records(
            'wxapp_users',
            conditions={'cloud_id': user_id}
        )
        if cloud_id_users:
            user = cloud_id_users[0]
            api_logger.debug(f"通过cloud_id找到用户: {user['id']}")
    
    if not user:
        api_logger.warning(f"用户不存在: {user_id}")
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 确保返回前处理JSON字段
    user = process_json_fields(user)
    api_logger.info(f"Response: 成功获取用户 {user['id']}")
    return create_standard_response(user)

@router.get("/users", response_model=Dict[str, Any], summary="查询用户列表")
@handle_api_errors("查询用户列表")
async def list_users(
    limit: int = Query(20, description="返回记录数量限制", ge=1, le=100),
    offset: int = Query(0, description="分页偏移量", ge=0),
    status: Optional[int] = Query(None, description="用户状态: 1-正常, 0-禁用"),
    order_by: str = Query("create_time DESC", description="排序方式"),
    api_logger=Depends(get_api_logger)
):
    """获取用户列表"""
    api_logger.info(f"Request: GET /users with params: limit={limit}, offset={offset}, status={status}, order_by={order_by}")
    
    try:
        # 构建查询条件
        conditions = {}
        if status is not None:
            conditions['status'] = status
            
        # 添加未删除条件
        conditions['is_deleted'] = 0
        
        api_logger.debug(f"查询条件: {conditions}")
        
        # 查询用户列表
        api_logger.debug(f"执行查询: 表=wxapp_users, 条件={conditions}, 排序={order_by}, 限制={limit}, 偏移={offset}")
        users = query_records(
            'wxapp_users',
            conditions=conditions,
            order_by=order_by,
            limit=limit,
            offset=offset
        )
        api_logger.debug(f"查询结果数量: {len(users)}")
        
        # 处理所有用户的JSON字段
        users = [process_json_fields(user) for user in users]
            
        # 获取总数
        total_count = count_records('wxapp_users', conditions)
        api_logger.debug(f"总记录数: {total_count}")
        
        # 返回用户列表
        api_logger.info(f"Response: 用户列表查询成功，返回{len(users)}条记录")
        return create_standard_response({
            "users": users,
            "total": total_count,
            "limit": limit,
            "offset": offset
        })
    except Exception as e:
        error_details = traceback.format_exc()
        api_logger.error(f"Error: 查询用户列表失败: {str(e)}\n{error_details}")
        raise HTTPException(status_code=500, detail=f"查询用户列表失败: {str(e)}")

@router.put("/users/{user_id}", response_model=UserResponse, summary="更新用户信息")
@handle_api_errors("更新用户")
async def update_user(
    user_update: UserUpdate,
    user_id: str = PathParam(..., description="用户ID"),
    api_logger=Depends(get_api_logger)
):
    """更新用户信息"""
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
        api_logger.debug(f"检测到微信云存储fileID: {update_data['avatar_url']}")
    
    # 添加更新时间
    update_data['update_time'] = format_datetime(datetime.now())
    
    # 更新记录
    success = update_record('wxapp_users', user_id, update_data)
    if not success:
        raise HTTPException(status_code=500, detail="更新用户失败")
    
    # 获取更新后的用户
    updated_user = get_record_by_id('wxapp_users', user_id)
    return updated_user

@router.delete("/users/{user_id}", response_model=dict, summary="删除用户")
@handle_api_errors("删除用户")
async def delete_user(
    user_id: str = PathParam(..., description="用户ID"),
    api_logger=Depends(get_api_logger)
):
    """删除用户（标记删除）"""
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

@router.get("/users/{user_id}/follow-stats", response_model=Dict[str, Any], summary="获取用户关注统计")
@handle_api_errors("获取用户关注统计")
async def get_user_follow_stats(
    user_id: str = PathParam(..., description="用户ID"),
    api_logger=Depends(get_api_logger)
):
    """
    获取用户关注和粉丝数量统计
    - 返回用户关注的人数和粉丝数量
    """
    api_logger.debug(f"获取用户ID={user_id}的关注统计")
    
    # 查询用户关注的人数
    try:
        # 使用适当的条件查询
        followed_result = query_records("wxapp_user_follows", {"follower_id": user_id})
        followed_count = len(followed_result) if followed_result else 0
        api_logger.debug(f"用户ID={user_id}关注了{followed_count}人")
    except Exception as e:
        api_logger.error(f"查询用户关注数失败: {str(e)}")
        followed_count = 0
    
    # 查询用户的粉丝数
    try:
        # 使用适当的条件查询
        follower_result = query_records("wxapp_user_follows", {"followed_id": user_id})
        follower_count = len(follower_result) if follower_result else 0
        api_logger.debug(f"用户ID={user_id}有{follower_count}个粉丝")
    except Exception as e:
        api_logger.error(f"查询用户粉丝数失败: {str(e)}")
        follower_count = 0
    
    # 返回标准响应
    return create_standard_response({
        "followedCount": followed_count,
        "followerCount": follower_count
    })

@router.get("/users/{user_id}/token", response_model=Dict[str, Any], summary="获取用户Token数量")
@handle_api_errors("获取用户Token")
async def get_user_token(
    user_id: str = PathParam(..., description="用户ID"),
    api_logger=Depends(get_api_logger)
):
    """
    获取用户Token数量
    - 返回用户的Token余额
    """
    api_logger.debug(f"获取用户ID={user_id}的Token数量")
    
    try:
        # 查询用户Token数量
        user_record = get_record_by_id("wxapp_users", user_id)
        if not user_record:
            return create_standard_response({
                "token": 0
            }, code=404, message="用户不存在")
        
        # 获取token字段，如果不存在则默认为0
        token = user_record.get("token", 0)
        api_logger.debug(f"用户ID={user_id}的Token数量为{token}")
        
        return create_standard_response({
            "token": token
        })
    except Exception as e:
        api_logger.error(f"获取用户Token失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取用户Token失败: {str(e)}")

@router.post("/users/{user_id}/token", response_model=Dict[str, Any], summary="更新用户Token数量")
@handle_api_errors("更新用户Token")
async def update_user_token(
    token_data: Dict[str, Any] = Body(..., description="Token更新数据"),
    user_id: str = PathParam(..., description="用户ID"),
    api_logger=Depends(get_api_logger)
):
    """
    更新用户的Token数量
    
    - 支持增加或设置具体数值
    - 参数:
      - action: "add"表示增加，"set"表示设置
      - amount: 增加或设置的数量
      
    请求示例:
    ```json
    {
        "action": "add",
        "amount": 10
    }
    ```
    """
    api_logger.debug(f"更新用户ID={user_id}的Token数量: {token_data}")
    
    # 验证参数
    action = token_data.get("action", "add")
    amount = token_data.get("amount", 0)
    
    if action not in ["add", "set"]:
        return create_standard_response(
            code=400,
            message="无效的操作类型，必须是'add'或'set'",
            data=None
        )
    
    if not isinstance(amount, (int, float)) or amount < 0:
        return create_standard_response(
            code=400,
            message="无效的Token数量",
            data=None
        )
    
    try:
        # 查询用户当前Token
        user_record = get_record_by_id("wxapp_users", user_id)
        if not user_record:
            return create_standard_response(
                code=404,
                message="用户不存在",
                data=None
            )
        
        current_token = user_record.get("token", 0)
        
        # 根据操作类型计算新的Token数量
        new_token = current_token + amount if action == "add" else amount
        
        # 更新用户Token
        update_data = {
            "token": new_token,
            "update_time": format_datetime(datetime.now())
        }
        
        success = update_record("wxapp_users", user_id, update_data)
        if not success:
            return create_standard_response(
                code=500,
                message="更新用户Token失败",
                data=None
            )
        
        api_logger.debug(f"更新用户ID={user_id}的Token成功: {new_token}")
        
        return create_standard_response(
            code=200,
            message="更新用户Token成功",
            data={"token": new_token}
        )
    except Exception as e:
        api_logger.error(f"更新用户Token失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"更新用户Token失败: {str(e)}")

@router.post("/users/sync", response_model=Dict[str, Any], summary="同步微信云用户")
@handle_api_errors("同步微信云用户")
async def sync_wxapp_user(
    user_data: UserSyncRequest,
    request: Request = Depends(),
    cloud_source: Optional[str] = Header(None, alias="X-Cloud-Source"),
    prefer_cloud_id: Optional[str] = Header(None, alias="X-Prefer-Cloud-ID"),
    api_logger=Depends(get_api_logger)
):
    """
    同步微信云数据库用户到主服务器
    
    支持使用云数据库ID作为主键，而不再使用服务器生成的ID
    
    请求头:
    - X-Cloud-Source: 可选，标记来源
    - X-Prefer-Cloud-ID: 可选，标记优先使用云ID
    """
    api_logger.debug(f"同步微信云用户: {user_data.dict()}, 头信息: cloud_source={cloud_source}, prefer_cloud_id={prefer_cloud_id}")
    
    try:
        # 确保ID字段一致性（使用id作为主键）
        cloud_id = user_data.id
        if not cloud_id:
            api_logger.warning("同步请求中没有提供云ID，使用随机生成ID")
            raise HTTPException(status_code=400, detail="云ID不能为空")
        
        api_logger.debug(f"使用云ID: {cloud_id}")
        
        # 确定是否要使用云ID
        should_use_cloud_id = (
            user_data.use_cloud_id or 
            prefer_cloud_id == "true" or 
            prefer_cloud_id == "True"
        )
        api_logger.debug(f"是否使用云ID: {should_use_cloud_id}")
        
        # 首先通过openid查询用户，这是最可靠的唯一标识
        existing_users = query_records(
            'wxapp_users',
            conditions={'openid': user_data.openid}
        )
        
        # 如果通过openid找不到用户，再通过云ID查询
        if not existing_users:
            api_logger.debug(f"通过openid未找到用户，尝试使用云ID: {cloud_id}")
            existing_users = query_records(
                'wxapp_users',
                conditions={'cloud_id': cloud_id}
            )
        
        # 准备用户数据
        user_update = {
            # 基本信息
            'wxapp_id': user_data.wxapp_id,
            'openid': user_data.openid,
            'nickname': user_data.nickname or f"用户{user_data.openid[-4:]}",
            'avatar_url': user_data.avatar_url or "/assets/icons/default-avatar.png",
            'status': 1,  # 激活状态
            'cloud_id': cloud_id,  # 保存云ID
            # 'university': user_data.university or "南开大学",  # 数据库中不存在此字段
            # 'login_type': user_data.login_type or "wechat",    # 数据库中不存在此字段
            # 更新时间
            'update_time': format_datetime(datetime.now()),
            'last_login': format_datetime(datetime.now())
        }
        
        success = False
        user_id = None
        updated_user = None
        
        if existing_users:
            # 用户存在，更新记录
            existing_user = existing_users[0]
            user_id = existing_user['id']
            
            api_logger.debug(f"找到现有用户: ID={user_id}, openid={existing_user.get('openid')}, cloud_id={existing_user.get('cloud_id')}")
            
            # 如果请求要求使用云ID，并且当前ID与云ID不同，则更新ID关联
            if should_use_cloud_id and str(user_id) != str(cloud_id):
                api_logger.debug(f"更新用户ID关联: 服务器ID={user_id} -> 云ID={cloud_id}")
                user_update['cloud_id'] = cloud_id  # 保存云ID以便映射
            
            api_logger.debug(f"更新用户: ID={user_id}, 数据={user_update}")
            success = update_record('wxapp_users', user_id, user_update)
            
            if success:
                # 获取更新后的用户
                updated_user = get_record_by_id('wxapp_users', user_id)
                api_logger.debug(f"用户更新成功: {updated_user}")
            else:
                api_logger.error(f"更新用户记录失败: ID={user_id}")
                raise HTTPException(status_code=500, detail="更新用户记录失败")
        else:
            # 用户不存在，创建新用户
            api_logger.debug("未找到现有用户，创建新用户")
            
            # 添加创建时间
            user_update['create_time'] = format_datetime(datetime.now())
            
            # 注意：这里不要尝试手动设置ID，让数据库自动分配
            
            # 检查可能的唯一键冲突
            existing_by_wxapp_id = query_records('wxapp_users', conditions={'wxapp_id': user_data.wxapp_id})
            if existing_by_wxapp_id:
                api_logger.warning(f"检测到可能的wxapp_id冲突: {user_data.wxapp_id}")
                # 更新这个用户而不是创建
                user_id = existing_by_wxapp_id[0]['id']
                success = update_record('wxapp_users', user_id, user_update)
                if success:
                    updated_user = get_record_by_id('wxapp_users', user_id)
                    api_logger.debug(f"通过wxapp_id找到并更新用户: {updated_user}")
            else:
                # 尝试插入新记录
                api_logger.debug(f"尝试创建新用户: {user_update}")
                user_id = insert_record('wxapp_users', user_update)
                success = user_id > 0
                
                if success:
                    # 获取创建的用户
                    updated_user = get_record_by_id('wxapp_users', user_id)
                    api_logger.debug(f"用户创建成功: {updated_user}")
                else:
                    api_logger.error("用户创建失败，插入记录返回无效ID")
                    # 详细记录错误原因
                    api_logger.error(f"数据: {user_update}")
                    raise HTTPException(status_code=500, detail="创建用户记录失败")
        
        if not updated_user:
            api_logger.error(f"无法获取同步后的用户: ID={user_id}")
            raise HTTPException(status_code=404, detail="无法获取同步后的用户")
        
        # 处理用户数据中的JSON字段
        updated_user = process_json_fields(updated_user)
        
        # 添加映射信息，确保客户端知道云ID和服务器ID的对应关系
        response_data = {
            "data": updated_user,
            "cloud_id": cloud_id,
            "server_id": updated_user['id'],
            "id_mapping": {
                "cloud_to_server": {cloud_id: updated_user['id']},
                "server_to_cloud": {str(updated_user['id']): cloud_id}
            }
        }
        
        api_logger.info(f"同步用户成功: ID={user_id}, 云ID={cloud_id}")
        return create_standard_response(response_data)
        
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        
        error_details = traceback.format_exc()
        api_logger.error(f"Error: 同步用户失败: {str(e)}\n{error_details}")
        raise HTTPException(status_code=500, detail=f"同步用户失败: {str(e)}") 