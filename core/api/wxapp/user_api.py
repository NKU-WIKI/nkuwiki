"""
微信小程序用户API
提供用户管理相关的API接口
"""
from datetime import datetime
from fastapi import HTTPException, Path as PathParam, Depends, Query, Body
from pydantic import BaseModel, Field, validator
from typing import Dict, Any, Optional, List

# 导入通用组件
from core.api.common import get_api_logger, handle_api_errors, create_standard_response
from core.api.wxapp import router
from core.api.wxapp.common_utils import format_datetime, prepare_db_data, process_json_fields

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

# API端点
@router.post("/users", response_model=Dict[str, Any], summary="创建用户")
@handle_api_errors("创建用户")
async def create_user(
    user: UserCreate,
    api_logger=Depends(get_api_logger)
):
    """创建新用户"""
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

@router.get("/users/{user_id}", response_model=Dict[str, Any], summary="获取用户信息")
@handle_api_errors("获取用户")
async def get_user(
    user_id: str = PathParam(..., description="用户ID"),
    api_logger=Depends(get_api_logger)
):
    """获取指定用户信息"""
    user = get_record_by_id('wxapp_users', user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return create_standard_response(user)

@router.get("/users", response_model=Dict[str, Any], summary="查询用户列表")
@handle_api_errors("查询用户列表")
async def list_users(
    limit: int = Query(20, description="返回记录数量限制", ge=1, le=100),
    offset: int = Query(0, description="分页偏移量", ge=0),
    status: Optional[int] = Query(None, description="用户状态: 1-正常, 0-禁用"),
    api_logger=Depends(get_api_logger)
):
    """获取用户列表"""
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
    followed_query = "SELECT COUNT(*) as count FROM wxapp_user_follows WHERE follower_id = %s"
    try:
        followed_result = query_records("wxapp_user_follows", {"follower_id": user_id}, limit=1) 
        # 如果上面的方法不适用，可以使用自定义查询
        # followed_result = execute_custom_query(followed_query, [user_id])
        followed_count = len(followed_result)
    except Exception as e:
        api_logger.error(f"查询用户关注数失败: {str(e)}")
        followed_count = 0
    
    # 查询用户的粉丝数
    try:
        follower_result = query_records("wxapp_user_follows", {"followed_id": user_id}, limit=1000)
        # 如果上面的方法不适用，可以使用自定义查询
        # follower_query = "SELECT COUNT(*) as count FROM wxapp_user_follows WHERE followed_id = %s"
        # follower_result = execute_custom_query(follower_query, [user_id])
        follower_count = len(follower_result)
    except Exception as e:
        api_logger.error(f"查询用户粉丝数失败: {str(e)}")
        follower_count = 0
    
    # 返回标准响应
    return create_standard_response(
        code=200,
        message="获取用户关注统计成功",
        data={
            "followedCount": followed_count,
            "followerCount": follower_count
        }
    )

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
            return create_standard_response(
                code=404,
                message="用户不存在",
                data={"token": 0}
            )
        
        # 获取token字段，如果不存在则默认为0
        token = user_record.get("token", 0)
        api_logger.debug(f"用户ID={user_id}的Token数量为{token}")
        
        return create_standard_response(
            code=200,
            message="获取用户Token成功",
            data={"token": token}
        )
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