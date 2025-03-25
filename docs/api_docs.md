# 南开Wiki API文档


本文档包含南开Wiki平台的所有API接口，主要分为两类：
1. 微信小程序API：提供给微信小程序客户端使用的API
2. Agent智能体API：提供AI聊天和知识检索功能

## 接口前缀

所有API都有对应的前缀路径：
- 微信小程序API：`/api/wxapp/*`
- Agent智能体API：`/api/agent/*`

如，用户接口的完整路径为 `/api/wxapp/users/me`


## 后端响应标准格式：
```json
{
  "code": 200,
  "message": "success",
  "data": {
    
  },
  "details": null,
  "timestamp": "2023-01-01 12:00:00"
}
```

响应字段说明：
- `code` - 状态码：200表示成功，4xx表示客户端错误，5xx表示服务器错误
- `message` - 响应消息，成功或错误描述
- `data` - 响应数据，可能是对象、数组或null
- `details` - 额外详情，通常在发生错误时提供更详细的信息
- `timestamp` - 响应时间戳

## 错误响应格式：

```json
{
  "code": 400,
  "message": "请求参数错误",
  "data": null,
  "details": {
    "errors": [
      {
        "loc": ["body", "field_name"],
        "msg": "错误描述",
        "type": "错误类型"
      }
    ]
  },
  "timestamp": "2023-01-01 12:00:00"
}
```


## 一、用户接口

### 1.1 同步微信云用户

**接口**：`POST /api/wxapp/users/sync`  
**描述**：同步微信用户openid到服务器数据库，只会在用户不存在时添加新用户，不会更新已存在用户的信息  
**请求头**：
- `X-Cloud-Source` - 可选，标记来源
- `X-Prefer-Cloud-ID` - 可选，标记优先使用云ID

**请求体**：

```json
{
  "openid": "微信用户唯一标识", // 必填
  "unionid": "微信开放平台唯一标识（可选）", // 不会被保存
  "nick_name": "用户昵称（可选）", // 不会被保存
  "avatar": "头像URL（可选）", // 不会被保存
  "gender": 0, // 不会被保存
  "bio": "个人简介（可选）", // 不会被保存
  "country": "国家（可选）", // 不会被保存
  "province": "省份（可选）", // 不会被保存
  "city": "城市（可选）", // 不会被保存
  "language": "语言（可选）", // 不会被保存
  "birthday": "2004-06-28（可选）", // 不会被保存
  "wechatId": "微信号（可选）", // 不会被保存
  "qqId": "QQ号（可选）", // 不会被保存
  "platform": "wxapp", // 不会被保存
  "extra": {} // 不会被保存
}
```

**响应**：返回用户信息，仅包含数据库中的实际值。新用户只会有openid和系统默认字段。

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 10001,
    "openid": "微信用户唯一标识",
    "unionid": null,
    "nick_name": null,
    "avatar": null,
    "gender": 0,
    "bio": null,
    "country": null,
    "province": null,
    "city": null,
    "language": null,
    "birthday": null,
    "wechatId": null,
    "qqId": null,
    "token_count": 0,
    "likes_count": 0,
    "favorites_count": 0,
    "posts_count": 0,
    "followers_count": 0,
    "following_count": 0,
    "create_time": "2023-01-01 12:00:00",
    "update_time": "2023-01-01 12:00:00",
    "last_login": "2023-01-01 12:00:00",
    "platform": "wxapp",
    "status": 1,
    "is_deleted": 0,
    "extra": null
  },
  "details": null,
  "timestamp": "2023-01-01 12:00:00"
}
```

### 1.2 获取用户信息

**接口**：`GET /api/wxapp/users/{openid}`  
**描述**：获取指定用户的信息  
**参数**：
- `openid` - 路径参数，用户openid

**响应**：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 1,
    "openid": "微信用户唯一标识",
    "unionid": "微信开放平台唯一标识",
    "nick_name": "用户昵称",
    "avatar": "头像URL",
    "gender": 0,
    "bio": "个人简介",
    "country": "国家",
    "province": "省份",
    "city": "城市",
    "language": "语言",
    "birthday": "2004-06-28",
    "wechatId": "微信号",
    "qqId": "QQ号",
    "token_count": 0,
    "likes_count": 0,
    "favorites_count": 0,
    "posts_count": 0,
    "followers_count": 0,
    "following_count": 0,
    "create_time": "2023-01-01 12:00:00",
    "update_time": "2023-01-01 12:00:00",
    "last_login": "2023-01-01 12:00:00",
    "platform": "wxapp",
    "status": 1,
    "is_deleted": 0,
    "extra": {}
  },
  "details": null,
  "timestamp": "2023-01-01 12:00:00"
}
```

### 1.3 获取当前用户信息

**接口**：`GET /api/wxapp/users/me`  
**描述**：获取当前登录用户的信息  
**参数**：
- `openid` - 查询参数，用户openid

**响应**：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 1,
    "openid": "微信用户唯一标识",
    "unionid": "微信开放平台唯一标识",
    "nick_name": "用户昵称",
    "avatar": "头像URL",
    "gender": 0,
    "bio": "个人简介",
    "country": "国家",
    "province": "省份",
    "city": "城市",
    "language": "语言",
    "birthday": "2004-06-28",
    "wechatId": "微信号",
    "qqId": "QQ号",
    "token_count": 0,
    "likes_count": 0,
    "favorites_count": 0,
    "posts_count": 0,
    "followers_count": 0,
    "following_count": 0,
    "create_time": "2023-01-01 12:00:00",
    "update_time": "2023-01-01 12:00:00",
    "last_login": "2023-01-01 12:00:00",
    "platform": "wxapp",
    "status": 1,
    "is_deleted": 0,
    "extra": {}
  },
  "details": null,
  "timestamp": "2023-01-01 12:00:00"
}
```

### 1.4 查询用户列表

**接口**：`GET /api/wxapp/users`  
**描述**：获取用户列表  
**参数**：
- `limit` - 查询参数，返回记录数量限制，默认10，最大100
- `offset` - 查询参数，分页偏移量，默认0

**响应**：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "users": [
      {
        "id": 1,
        "openid": "微信用户唯一标识",
        "unionid": "微信开放平台唯一标识",
        "nick_name": "用户昵称",
        "avatar": "头像URL",
        "gender": 0,
        "bio": "个人简介",
        "country": "国家",
        "province": "省份",
        "city": "城市",
        "language": "语言",
        "birthday": "2004-06-28",
        "wechatId": "微信号",
        "qqId": "QQ号",
        "token_count": 0,
        "likes_count": 0,
        "favorites_count": 0,
        "posts_count": 0,
        "followers_count": 0,
        "following_count": 0,
        "create_time": "2023-01-01 12:00:00",
        "update_time": "2023-01-01 12:00:00",
        "last_login": "2023-01-01 12:00:00",
        "platform": "wxapp",
        "status": 1,
        "is_deleted": 0,
        "extra": {}
      }
    ],
    "total": 100,
    "limit": 10,
    "offset": 0
  },
  "details": null,
  "timestamp": "2023-01-01 12:00:00"
}
```

### 1.5 更新用户信息

**接口**：`PUT /api/wxapp/users/{openid}`  
**描述**：更新用户信息  
**参数**：
- `openid` - 路径参数，用户openid

**请求体**：

```json
{
  "nick_name": "新昵称",              // 可选，用户昵称
  "avatar": "新头像URL",              // 可选，头像URL
  "gender": 1,                        // 可选，性别：0-未知, 1-男, 2-女
  "bio": "新个人简介",                // 可选，个人简介
  "country": "新国家",                // 可选，国家
  "province": "新省份",               // 可选，省份
  "city": "新城市",                   // 可选，城市
  "language": "新语言",               // 可选，语言
  "birthday": "2004-06-28",           // 可选，生日
  "wechatId": "微信号",               // 可选，微信号
  "qqId": "QQ号",                     // 可选，QQ号
  "status": 1,                        // 可选，用户状态：1-正常, 0-禁用
  "extra": {                          // 可选，扩展字段
    "school": "南开大学",
    "major": "计算机科学与技术"
  }
}
```

**响应**：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 1,
    "openid": "微信用户唯一标识",
    "unionid": "微信开放平台唯一标识",
    "nick_name": "新昵称",
    "avatar": "新头像URL",
    "gender": 1,
    "bio": "新个人简介",
    "country": "新国家",
    "province": "新省份",
    "city": "新城市",
    "language": "新语言",
    "birthday": "2004-06-28",
    "wechatId": "微信号",
    "qqId": "QQ号",
    "token_count": 0,
    "likes_count": 0,
    "favorites_count": 0,
    "posts_count": 0,
    "followers_count": 0,
    "following_count": 0,
    "create_time": "2023-01-01 12:00:00",
    "update_time": "2023-01-01 12:30:00",
    "last_login": "2023-01-01 12:00:00",
    "platform": "wxapp",
    "status": 1,
    "is_deleted": 0,
    "extra": {
      "school": "南开大学",
      "major": "计算机科学与技术"
    }
  },
  "details": null,
  "timestamp": "2023-01-01 12:30:00"
}
```

### 1.6 获取用户关注统计

**接口**：`GET /api/wxapp/users/{openid}/follow-stats`  
**描述**：获取用户的关注数量和粉丝数量  
**参数**：
- `openid` - 路径参数，用户openid

**响应**：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "following": 10,
    "followers": 20
  },
  "details": null,
  "timestamp": "2023-01-01 12:00:00"
}
```

### 1.7 关注用户

**接口**：`POST /api/wxapp/users/{follower_id}/follow/{followed_id}`  
**描述**：将当前用户设为目标用户的粉丝  
**参数**：
- `follower_id` - 路径参数，关注者的openid
- `followed_id` - 路径参数，被关注者的openid

**响应**：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "status": "success",
    "following_count": 11,
    "followers_count": 21,
    "is_following": true
  },
  "details": null,
  "timestamp": "2023-01-01 12:00:00"
}
```

### 1.8 取消关注用户

**接口**：`POST /api/wxapp/users/{follower_id}/unfollow/{followed_id}`  
**描述**：将当前用户从目标用户的粉丝列表中移除  
**参数**：
- `follower_id` - 路径参数，关注者的openid
- `followed_id` - 路径参数，被关注者的openid

**响应**：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "status": "success",
    "following_count": 10,
    "followers_count": 20,
    "is_following": false
  },
  "details": null,
  "timestamp": "2023-01-01 12:00:00"
}
```

### 1.9 检查关注状态

**接口**：`GET /api/wxapp/users/{follower_id}/check-follow/{followed_id}`  
**描述**：检查用户是否已关注某用户  
**参数**：
- `follower_id` - 路径参数，关注者的openid
- `followed_id` - 路径参数，被关注者的openid

**响应**：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "is_following": true
  },
  "details": null,
  "timestamp": "2023-01-01 12:00:00"
}
```

### 1.10 获取用户关注列表

**接口**：`GET /api/wxapp/users/{openid}/followings`  
**描述**：获取用户关注的所有用户  
**参数**：
- `openid` - 路径参数，用户openid
- `limit` - 查询参数，返回记录数量限制，默认20，最大100
- `offset` - 查询参数，分页偏移量，默认0

**响应**：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "users": [
      {
        "id": 2,
        "openid": "被关注用户的openid",
        "unionid": "微信开放平台唯一标识",
        "nick_name": "用户昵称",
        "avatar": "头像URL",
        "gender": 1,
        "bio": "个人简介",
        "country": "国家",
        "province": "省份",
        "city": "城市",
        "language": "语言",
        "birthday": "2004-06-28",
        "wechatId": "微信号",
        "qqId": "QQ号",
        "token_count": 0,
        "likes_count": 0,
        "favorites_count": 0,
        "posts_count": 0,
        "followers_count": 0,
        "following_count": 0,
        "create_time": "2023-01-01 12:00:00",
        "update_time": "2023-01-01 12:00:00",
        "last_login": "2023-01-01 12:00:00",
        "platform": "wxapp",
        "status": 1,
        "is_deleted": 0,
        "extra": {}
      }
    ],
    "total": 50,
    "limit": 20,
    "offset": 0
  },
  "details": null,
  "timestamp": "2023-01-01 12:00:00"
}
```

### 1.11 获取用户粉丝列表

**接口**：`GET /api/wxapp/users/{openid}/followers`  
**描述**：获取关注该用户的所有用户  
**参数**：
- `openid` - 路径参数，用户openid
- `limit` - 查询参数，返回记录数量限制，默认20，最大100
- `offset` - 查询参数，分页偏移量，默认0

**响应**：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "users": [
      {
        "id": 3,
        "openid": "粉丝用户的openid",
        "unionid": "微信开放平台唯一标识",
        "nick_name": "粉丝昵称",
        "avatar": "头像URL",
        "gender": 2,
        "bio": "个人简介",
        "country": "国家",
        "province": "省份",
        "city": "城市",
        "language": "语言",
        "birthday": "2004-06-28",
        "wechatId": "微信号",
        "qqId": "QQ号",
        "token_count": 0,
        "likes_count": 0,
        "favorites_count": 0,
        "posts_count": 0,
        "followers_count": 2,
        "following_count": 15,
        "create_time": "2023-01-01 12:00:00",
        "update_time": "2023-01-01 12:00:00",
        "last_login": "2023-01-01 12:00:00",
        "platform": "wxapp",
        "status": 1,
        "is_deleted": 0,
        "extra": {}
      }
    ],
    "total": 20,
    "limit": 20,
    "offset": 0
  },
  "details": null,
  "timestamp": "2023-01-01 12:00:00"
}
```

### 1.12 获取用户令牌

**接口**：`GET /api/wxapp/users/{openid}/token`  
**描述**：获取用户的访问令牌  
**参数**：
- `openid` - 路径参数，用户openid

**响应**：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "token": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
    "expires_at": "2023-01-02 12:00:00"
  },
  "details": null,
  "timestamp": "2023-01-01 12:00:00"
}
```

## 二、帖子接口

### 2.1 创建帖子

**接口**：`POST /api/wxapp/posts`  
**描述**：创建新帖子，成功后会增加用户的发帖计数(posts_count)  
**查询参数**：
- `openid`: 发布用户openid (必填)
- `nick_name`: 用户昵称 (可选，如不提供则从用户表获取)
- `avatar`: 用户头像URL (可选，如不提供则从用户表获取)

**请求体**：

```json
{
  "title": "帖子标题", // 必填
  "content": "帖子内容", // 必填
  "images": ["图片URL1", "图片URL2"], // 可选
  "tags": ["标签1", "标签2"], // 可选
  "category_id": 1, // 可选，默认为0
  "location": { // 可选
    "latitude": 39.12345,
    "longitude": 116.12345,
    "name": "位置名称",
    "address": "详细地址"
  }
}
```

**响应**：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 1,
    "openid": "发布用户openid",
    "title": "帖子标题",
    "content": "帖子内容",
    "images": ["图片URL1", "图片URL2"],
    "tags": ["标签1", "标签2"],
    "category_id": 1,
    "location": {
      "latitude": 39.12345,
      "longitude": 116.12345,
      "name": "位置名称",
      "address": "详细地址"
    },
    "nick_name": "用户昵称",
    "avatar": "用户头像URL",
    "view_count": 0,
    "like_count": 0,
    "comment_count": 0,
    "favorite_count": 0,
    "liked_users": [],
    "favorite_users": [],
    "create_time": "2023-01-01 12:00:00",
    "update_time": "2023-01-01 12:00:00",
    "status": 1,
    "platform": "wxapp",
    "is_deleted": 0,
    "posts_count": 1
  },
  "details": null,
  "timestamp": "2023-01-01 12:00:00"
}
```

### 2.2 获取帖子详情

**接口**：`GET /api/wxapp/posts/{post_id}`  
**描述**：获取指定帖子的详情  
**参数**：
- `post_id` - 路径参数，帖子ID
- `update_view` - 查询参数，是否更新浏览量，默认true

**响应**：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 1,
    "openid": "发布用户openid",
    "title": "帖子标题",
    "content": "帖子内容",
    "images": ["图片URL1", "图片URL2"],
    "tags": ["标签1", "标签2"],
    "category_id": 1,
    "location": "位置信息",
    "nick_name": "用户昵称",
    "avatar": "用户头像URL",
    "view_count": 1,
    "like_count": 0,
    "comment_count": 0,
    "favorite_count": 0,
    "liked_users": [],
    "favorite_users": [],
    "create_time": "2023-01-01 12:00:00",
    "update_time": "2023-01-01 12:00:00",
    "status": 1,
    "platform": "wxapp",
    "is_deleted": 0,
    "posts_count": 1
  },
  "details": null,
  "timestamp": "2023-01-01 12:00:00"
}
```

### 2.3 查询帖子列表

**接口**：`GET /api/wxapp/posts`  
**描述**：获取帖子列表  
**参数**：
- `limit` - 查询参数，返回记录数量限制，默认20，最大100
- `offset` - 查询参数，分页偏移量，默认0
- `openid` - 查询参数，按用户openid筛选，可选
- `category_id` - 查询参数，按分类ID筛选，可选
- `tag` - 查询参数，按标签筛选，可选
- `status` - 查询参数，帖子状态：1-正常，0-禁用，默认1
- `order_by` - 查询参数，排序方式，默认"update_time DESC"

**响应**：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "posts": [
      {
        "id": 1,
        "openid": "发布用户openid",
        "title": "帖子标题",
        "content": "帖子内容",
        "images": ["图片URL1", "图片URL2"],
        "tags": ["标签1", "标签2"],
        "category_id": 1,
        "location": "位置信息",
        "nick_name": "用户昵称",
        "avatar": "用户头像URL",
        "view_count": 10,
        "like_count": 5,
        "comment_count": 3,
        "favorite_count": 0,
        "liked_users": ["用户openid1", "用户openid2", "用户openid3", "用户openid4", "用户openid5"],
        "favorite_users": [],
        "create_time": "2023-01-01 12:00:00",
        "update_time": "2023-01-01 12:00:00",
        "status": 1,
        "platform": "wxapp",
        "is_deleted": 0,
        "posts_count": 1
      }
    ],
    "total": 100,
    "limit": 20,
    "offset": 0
  },
  "details": null,
  "timestamp": "2023-01-01 12:00:00"
}
```

### 2.4 更新帖子

**接口**：`PUT /api/wxapp/posts/{post_id}`  
**描述**：更新帖子信息  
**参数**：
- `post_id` - 路径参数，帖子ID
- `openid` - 查询参数，用户openid（必填，用于验证操作权限）

**请求体**：

```json
{
  "title": "新标题",
  "content": "新内容",
  "images": ["新图片URL1", "新图片URL2"],
  "tags": ["新标签1", "新标签2"],
  "category_id": 2,
  "location": {
    "latitude": 39.12345,
    "longitude": 116.12345,
    "name": "位置名称",
    "address": "详细地址"
  },
  "status": 1
}
```

**响应**：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 1,
    "openid": "发布用户openid",
    "title": "新标题",
    "content": "新内容",
    "images": ["新图片URL1", "新图片URL2"],
    "tags": ["新标签1", "新标签2"],
    "category_id": 2,
    "location": {
      "latitude": 39.12345,
      "longitude": 116.12345,
      "name": "位置名称",
      "address": "详细地址"
    },
    "nick_name": "用户昵称", 
    "avatar": "用户头像URL",
    "view_count": 10,
    "like_count": 5,
    "comment_count": 3,
    "favorite_count": 0,
    "liked_users": ["用户openid1", "用户openid2", "用户openid3", "用户openid4", "用户openid5"],
    "favorite_users": [],
    "create_time": "2023-01-01 12:00:00",
    "update_time": "2023-01-01 13:00:00",
    "status": 1,
    "platform": "wxapp",
    "is_deleted": 0,
    "posts_count": 1
  },
  "details": null,
  "timestamp": "2023-01-01 13:00:00"
}
```

### 2.5 删除帖子

**接口**：`DELETE /api/wxapp/posts/{post_id}`  
**描述**：删除帖子（标记删除），同时会减少用户的发帖计数(posts_count)  
**参数**：
- `post_id` - 路径参数，帖子ID
- `openid` - 查询参数，用户openid（必填，用于验证操作权限）

**响应**：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "success": true,
    "message": "帖子已删除"
  },
  "details": null,
  "timestamp": "2023-01-01 12:00:00"
}
```

### 2.6 点赞/取消点赞帖子

**接口**：`POST /api/wxapp/posts/{post_id}/like`  
**描述**：点赞或取消点赞帖子（如果已点赞，则取消点赞）  
**说明**：该操作会同时更新帖子作者的likes_count（当被其他用户点赞或取消点赞时）  
**参数**：
- `post_id` - 路径参数，帖子ID
- `openid` - 查询参数，用户openid

**响应**：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "success": true,
    "message": "点赞成功",
    "liked": true,
    "like_count": 6,
    "post_id": 1,
    "action": "like"
  },
  "details": null,
  "timestamp": "2023-01-01 12:00:00"
}
```

### 2.7 收藏帖子

**接口**：`POST /api/wxapp/posts/{post_id}/favorite`  
**描述**：收藏帖子  
**说明**：该操作会同时更新帖子作者的favorites_count（当被其他用户收藏时）  
**参数**：
- `post_id` - 路径参数，帖子ID
- `openid` - 查询参数，用户openid

**响应**：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "success": true,
    "message": "收藏成功",
    "favorite": true,
    "favorite_count": 3,
    "post_id": 1,
    "action": "favorite"
  },
  "details": null,
  "timestamp": "2023-01-01 12:00:00"
}
```

### 2.8 取消点赞帖子

**接口**：`POST /api/wxapp/posts/{post_id}/unlike`  
**描述**：取消点赞帖子  
**说明**：该操作会同时更新帖子作者的likes_count（当被其他用户取消点赞时）  
**参数**：
- `post_id` - 路径参数，帖子ID
- `openid` - 查询参数，用户openid

**响应**：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "success": true,
    "message": "取消点赞成功",
    "liked": false,
    "like_count": 5,
    "post_id": 1,
    "action": "unlike"
  },
  "details": null,
  "timestamp": "2023-01-01 12:00:00"
}
```

### 2.9 取消收藏帖子

**接口**：`POST /api/wxapp/posts/{post_id}/unfavorite`  
**描述**：取消收藏帖子  
**说明**：该操作会同时更新帖子作者的favorites_count（当被其他用户取消收藏时）  
**参数**：
- `post_id` - 路径参数，帖子ID
- `openid` - 查询参数，用户openid

**响应**：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "success": true,
    "message": "取消收藏成功",
    "favorite": false,
    "favorite_count": 2,
    "post_id": 1,
    "action": "unfavorite"
  },
  "details": null,
  "timestamp": "2023-01-01 12:00:00"
}
```

## 三、评论接口

### 3.1 创建评论

**接口**：`POST /api/wxapp/comments`  
**描述**：创建新评论  
**查询参数**：
- `openid`: 评论用户openid (必填)
- `nick_name`: 用户昵称 (可选，如不提供则从用户表获取)
- `avatar`: 用户头像URL (可选，如不提供则从用户表获取)

**请求体**：

```json
{
  "post_id": 1,
  "content": "评论内容",
  "parent_id": null,
  "images": ["图片URL1", "图片URL2"]
}
```

**响应**：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 1,
    "openid": "评论用户openid",
    "nick_name": "用户昵称",
    "avatar": "用户头像URL",
    "post_id": 1,
    "content": "评论内容",
    "parent_id": null,
    "like_count": 0,
    "liked_users": [],
    "create_time": "2023-01-01 12:00:00",
    "update_time": "2023-01-01 12:00:00",
    "platform": "wxapp",
    "status": 1,
    "is_deleted": 0
  },
  "details": null,
  "timestamp": "2023-01-01 12:00:00"
}
```

### 3.2 获取评论详情

**接口**：`GET /api/wxapp/comments/{comment_id}`  
**描述**：获取指定评论的详情  
**参数**：
- `comment_id` - 路径参数，评论ID

**响应**：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 1,
    "openid": "评论用户openid",
    "nick_name": "用户昵称",
    "avatar": "用户头像URL",
    "post_id": 1,
    "content": "评论内容",
    "parent_id": null,
    "like_count": 3,
    "liked_users": ["用户openid1", "用户openid2", "用户openid3"],
    "replies": [],
    "create_time": "2023-01-01 12:00:00",
    "update_time": "2023-01-01 12:00:00",
    "platform": "wxapp",
    "status": 1,
    "is_deleted": 0
  },
  "details": null,
  "timestamp": "2023-01-01 12:00:00"
}
```

### 3.3 获取帖子评论列表

**接口**：`GET /api/wxapp/posts/{post_id}/comments`  
**描述**：获取指定帖子的评论列表  
**参数**：
- `post_id` - 路径参数，帖子ID
- `parent_id` - 查询参数，父评论ID，可选（为null时获取一级评论）
- `limit` - 查询参数，返回记录数量限制，默认20，最大100
- `offset` - 查询参数，分页偏移量，默认0
- `sort_by` - 查询参数，排序方式，默认"latest"(latest-最新, oldest-最早, likes-最多点赞)

**响应**：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "comments": [
      {
        "id": 1,
        "openid": "评论用户openid",
        "nick_name": "用户昵称",
        "avatar": "用户头像URL",
        "post_id": 1,
        "content": "评论内容",
        "parent_id": null,
        "like_count": 3,
        "liked_users": ["用户openid1", "用户openid2", "用户openid3"],
        "reply_count": 2,
        "reply_preview": [
          {
            "id": 5,
            "openid": "回复用户openid",
            "nick_name": "回复用户昵称",
            "avatar": "回复用户头像URL",
            "content": "回复内容",
            "create_time": "2023-01-01 12:30:00"
          }
        ],
        "create_time": "2023-01-01 12:00:00",
        "update_time": "2023-01-01 12:00:00",
        "platform": "wxapp",
        "status": 1,
        "is_deleted": 0
      }
    ],
    "total": 50,
    "limit": 20,
    "offset": 0,
    "post_id": 1,
    "parent_id": null
  },
  "details": null,
  "timestamp": "2023-01-01 12:00:00"
}
```

### 3.4 更新评论

**接口**：`PUT /api/wxapp/comments/{comment_id}`  
**描述**：更新评论信息  
**参数**：
- `comment_id` - 路径参数，评论ID
- `openid` - 查询参数，用户openid（必填，用于验证操作权限）

**请求体**：

```json
{
  "content": "新评论内容",
  "images": ["图片URL1", "图片URL2"],
  "status": 1
}
```

**响应**：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 1,
    "openid": "评论用户openid",
    "nick_name": "用户昵称",
    "avatar": "用户头像URL",
    "post_id": 1,
    "content": "新评论内容",
    "parent_id": null,
    "like_count": 3,
    "liked_users": ["用户openid1", "用户openid2", "用户openid3"],
    "create_time": "2023-01-01 12:00:00",
    "update_time": "2023-01-01 13:00:00",
    "platform": "wxapp",
    "status": 1,
    "is_deleted": 0
  },
  "details": null,
  "timestamp": "2023-01-01 13:00:00"
}
```

### 3.5 删除评论

**接口**：`DELETE /api/wxapp/comments/{comment_id}`  
**描述**：删除评论（标记删除）  
**参数**：
- `comment_id` - 路径参数，评论ID
- `openid` - 查询参数，用户openid，用于权限验证，可选

**响应**：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "success": true,
    "message": "评论已删除"
  },
  "details": null,
  "timestamp": "2023-01-01 12:00:00"
}
```

### 3.6 点赞评论

**接口**：`POST /api/wxapp/comments/{comment_id}/like`  
**描述**：点赞评论或取消点赞（如果已点赞）  
**说明**：该操作会同时更新评论作者的likes_count（当被其他用户点赞或取消点赞时）  
**参数**：
- `comment_id` - 路径参数，评论ID
- `openid` - 查询参数，用户openid（必填）

**响应**：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "success": true,
    "message": "点赞成功",
    "liked": true,
    "like_count": 4,
    "comment_id": 1,
    "action": "like"
  },
  "details": null,
  "timestamp": "2023-01-01 12:00:00"
}
```

### 3.7 取消点赞评论

**接口**：`POST /api/wxapp/comments/{comment_id}/unlike`  
**描述**：取消点赞评论  
**说明**：该操作会同时更新评论作者的likes_count（当被其他用户取消点赞时）  
**参数**：
- `comment_id` - 路径参数，评论ID
- `openid` - 查询参数，用户openid（必填）

**响应**：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "success": true,
    "message": "取消点赞成功",
    "liked": false,
    "like_count": 3,
    "comment_id": 1,
    "action": "unlike"
  },
  "details": null,
  "timestamp": "2023-01-01 12:00:00"
}
```

## 四、通知接口

### 4.1 获取用户通知列表

**接口**：`GET /api/wxapp/users/{openid}/notifications`  
**描述**：获取用户的通知列表  
**参数**：
- `openid` - 路径参数，用户openid
- `type` - 查询参数，通知类型：system-系统通知, like-点赞, comment-评论, follow-关注，可选
- `is_read` - 查询参数，是否已读：true-已读, false-未读，可选
- `limit` - 查询参数，返回记录数量限制，默认20，最大100
- `offset` - 查询参数，分页偏移量，默认0

**响应**：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "notifications": [
      {
        "id": 1,
        "openid": "接收者用户openid",
        "title": "通知标题",
        "content": "通知内容",
        "type": "comment",
        "is_read": 0,
        "sender_openid": "发送者openid",
        "sender": {
          "id": 2,
          "openid": "发送者openid",
          "nick_name": "发送者昵称",
          "avatar": "发送者头像"
        },
        "related_id": "123",
        "related_type": "post",
        "create_time": "2023-01-01 12:00:00",
        "update_time": "2023-01-01 12:00:00",
        "platform": "wxapp",
        "is_deleted": 0
      }
    ],
    "total": 20,
    "unread": 5,
    "limit": 20,
    "offset": 0
  },
  "details": null,
  "timestamp": "2023-01-01 12:00:00"
}
```

### 4.2 获取通知详情

**接口**：`GET /api/wxapp/notifications/{notification_id}`  
**描述**：获取通知详情  
**参数**：
- `notification_id` - 路径参数，通知ID

**响应**：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 1,
    "openid": "接收者用户openid",
    "title": "通知标题",
    "content": "通知内容",
    "type": "comment",
    "is_read": 0,
    "sender_openid": "发送者openid",
    "related_id": "123",
    "related_type": "post",
    "create_time": "2023-01-01 12:00:00",
    "update_time": "2023-01-01 12:00:00",
    "platform": "wxapp",
    "is_deleted": 0,
    "extra": {}
  },
  "details": null,
  "timestamp": "2023-01-01 12:00:00"
}
```

### 4.3 标记通知为已读

**接口**：`PUT /api/wxapp/notifications/{notification_id}`  
**描述**：标记单个通知为已读  
**参数**：
- `notification_id` - 路径参数，通知ID

**请求体**：

```json
{
  "is_read": 1
}
```

**响应**：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 1,
    "openid": "接收者用户openid",
    "title": "通知标题",
    "content": "通知内容",
    "type": "comment",
    "is_read": 1,
    "sender_openid": "发送者openid",
    "related_id": "123",
    "related_type": "post",
    "create_time": "2023-01-01 12:00:00",
    "update_time": "2023-01-01 12:30:00",
    "platform": "wxapp",
    "is_deleted": 0
  },
  "details": null,
  "timestamp": "2023-01-01 12:30:00"
}
```

### 4.4 批量标记通知为已读

**接口**：`PUT /api/wxapp/users/{openid}/notifications/read`  
**描述**：标记用户所有或指定通知为已读  
**参数**：
- `openid` - 路径参数，用户openid

**请求体**：

```json
{
  "notification_ids": [1, 2, 3]
}
```

**响应**：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "success": true,
    "message": "已将5条通知标记为已读",
    "count": 5
  },
  "details": null,
  "timestamp": "2023-01-01 12:00:00"
}
```

### 4.5 删除通知

**接口**：`DELETE /api/wxapp/notifications/{notification_id}`  
**描述**：删除通知（标记删除）  
**参数**：
- `notification_id` - 路径参数，通知ID

**响应**：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "success": true,
    "message": "通知已删除"
  },
  "details": null,
  "timestamp": "2023-01-01 12:00:00"
}
```

### 4.6 获取未读通知数量

**接口**：`GET /api/wxapp/users/{openid}/notifications/count`  
**描述**：获取用户未读通知数量  
**参数**：
- `openid` - 路径参数，用户openid
- `type` - 查询参数，通知类型：system-系统通知, like-点赞, comment-评论, follow-关注，可选

**响应**：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "unread_count": 5,
    "openid": "用户openid",
    "type": "like"
  },
  "details": null,
  "timestamp": "2023-01-01 12:00:00"
}
```

## 五、反馈接口

### 5.1 提交反馈

**接口**：`POST /api/wxapp/feedback`  
**描述**：提交意见反馈  
**查询参数**：
- `openid`: 用户openid (必填)

**请求体**：

```json
{
  "content": "反馈内容",
  "type": "bug",
  "contact": "联系方式",
  "images": ["图片URL1", "图片URL2"],
  "device_info": {
    "model": "设备型号",
    "system": "操作系统",
    "platform": "平台"
  }
}
```

**响应**：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 1,
    "openid": "用户openid",
    "content": "反馈内容",
    "type": "bug",
    "contact": "联系方式",
    "images": ["图片URL1", "图片URL2"],
    "device_info": {
      "model": "设备型号",
      "system": "操作系统",
      "platform": "平台"
    },
    "status": "pending",
    "admin_reply": null,
    "create_time": "2023-01-01 12:00:00",
    "update_time": "2023-01-01 12:00:00",
    "platform": "wxapp",
    "is_deleted": 0,
    "extra": null
  },
  "details": null,
  "timestamp": "2023-01-01 12:00:00"
}
```

### 5.2 获取用户反馈列表

**接口**：`GET /api/wxapp/users/{openid}/feedback`  
**描述**：获取用户的反馈列表  
**参数**：
- `openid` - 路径参数，用户openid
- `type` - 查询参数，反馈类型：bug-问题反馈, suggestion-建议, other-其他，可选
- `status` - 查询参数，反馈状态：pending-待处理, processing-处理中, resolved-已解决, rejected-已拒绝，可选
- `limit` - 查询参数，返回记录数量限制，默认20，最大100
- `offset` - 查询参数，分页偏移量，默认0

**响应**：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "feedback_list": [
      {
        "id": 1,
        "openid": "用户openid",
        "content": "反馈内容",
        "type": "bug",
        "contact": "联系方式",
        "images": ["图片URL1", "图片URL2"],
        "device_info": {
          "model": "设备型号",
          "system": "操作系统",
          "platform": "平台"
        },
        "status": "pending",
        "admin_reply": null,
        "create_time": "2023-01-01 12:00:00",
        "update_time": "2023-01-01 12:00:00",
        "platform": "wxapp",
        "is_deleted": 0,
        "extra": null
      }
    ],
    "total": 5,
    "limit": 20,
    "offset": 0
  },
  "details": null,
  "timestamp": "2023-01-01 12:00:00"
}
```

### 5.3 获取反馈详情

**接口**：`GET /api/wxapp/feedback/{feedback_id}`  
**描述**：获取反馈详情  
**参数**：
- `feedback_id` - 路径参数，反馈ID

**响应**：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 1,
    "openid": "用户openid",
    "content": "反馈内容",
    "type": "bug",
    "contact": "联系方式",
    "images": ["图片URL1", "图片URL2"],
    "device_info": {
      "model": "设备型号",
      "system": "操作系统",
      "platform": "平台"
    },
    "status": "resolved",
    "admin_reply": "管理员回复内容",
    "create_time": "2023-01-01 12:00:00",
    "update_time": "2023-01-01 13:00:00",
    "platform": "wxapp",
    "is_deleted": 0,
    "extra": null
  },
  "details": null,
  "timestamp": "2023-01-01 13:00:00"
}
```

### 5.4 更新反馈

**接口**：`PUT /api/wxapp/feedback/{feedback_id}`  
**描述**：更新反馈信息  
**参数**：
- `feedback_id` - 路径参数，反馈ID

**请求体**：

```json
{
  "content": "更新的反馈内容",
  "status": "resolved",
  "admin_reply": "管理员回复内容",
  "extra": {}
}
```

**响应**：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 1,
    "openid": "用户openid",
    "content": "更新的反馈内容",
    "type": "bug",
    "contact": "联系方式",
    "images": ["图片URL1", "图片URL2"],
    "device_info": {
      "model": "设备型号",
      "system": "操作系统",
      "platform": "平台"
    },
    "status": "resolved",
    "admin_reply": "管理员回复内容",
    "create_time": "2023-01-01 12:00:00",
    "update_time": "2023-01-01 13:30:00",
    "platform": "wxapp",
    "is_deleted": 0,
    "extra": {}
  },
  "details": null,
  "timestamp": "2023-01-01 13:30:00"
}
```

### 5.5 删除反馈

**接口**：`DELETE /api/wxapp/feedback/{feedback_id}`  
**描述**：删除反馈（标记删除）  
**参数**：
- `feedback_id` - 路径参数，反馈ID

**响应**：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "success": true,
    "message": "反馈已删除"
  },
  "details": null,
  "timestamp": "2023-01-01 12:00:00"
}
```

## 六、错误代码

| 状态码 | 说明 |
|--------|------|
| 200    | 成功 |
| 400    | 请求参数错误 |
| 401    | 未授权，需要登录 |
| 403    | 禁止访问，无权限 |
| 404    | 资源不存在 |
| 422    | 请求验证失败 |
| 429    | 请求过于频繁 |
| 500    | 服务器内部错误 |
| 502    | 网关错误 |
| 503    | 服务不可用 |
| 504    | 网关超时 |

## 七、Agent智能体API

### 7.1 与Agent对话

**接口**：`POST /api/agent/chat`  
**描述**：与AI智能体进行对话  
**请求体**：

```json
{
  "query": "南开大学的校训是什么？",
  "messages": [
    {"role": "user", "content": "你好"},
    {"role": "assistant", "content": "你好！我是南开Wiki智能助手，有什么可以帮助你的吗？"}
  ],
  "stream": false,
  "format": "markdown",
  "openid": "user_openid"
}
```

**响应**：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "response": "南开大学的校训是"允公允能，日新月异"。这八个字出自《论语》，体现了南开大学追求公能日新的办学理念。",
    "sources": [
      {
        "type": "小程序帖子",
        "title": "南开大学简介",
        "content": "南开大学校训为"允公允能，日新月异"，出自《论语》...",
        "author": "南开百科"
      }
    ],
    "suggested_questions": [
      "南开大学的校徽有什么含义？",
      "南开大学是什么时候创立的？",
      "南开大学的创始人是谁？"
    ],
    "format": "markdown"
  },
  "details": null,
  "timestamp": "2023-01-01 12:00:00"
}
```

### 7.2 知识库搜索

**接口**：`POST /api/agent/search`  
**描述**：搜索知识库内容  
**请求体**：

```json
{
  "keyword": "南开大学历史",
  "limit": 10
}
```

**响应**：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "results": [
      {
        "id": 1,
        "title": "南开大学校史",
        "content_preview": "南开大学创建于1919年，由著名爱国教育家张伯苓先生创办...",
        "author": "南开百科",
        "create_time": "2023-01-01 12:00:00",
        "type": "文章",
        "view_count": 1024,
        "like_count": 89,
        "comment_count": 15,
        "relevance": 0.95
      },
      {
        "id": 2,
        "title": "南开大学百年校庆",
        "content_preview": "2019年，南开大学迎来百年华诞...",
        "author": "南开校友",
        "create_time": "2023-01-02 12:00:00",
        "type": "文章",
        "view_count": 986,
        "like_count": 76,
        "comment_count": 12,
        "relevance": 0.85
      }
    ],
    "keyword": "南开大学历史",
    "total": 2
  },
  "details": null,
  "timestamp": "2023-01-01 12:00:00"
}
```

### 7.3 获取Agent状态

**接口**：`GET /api/agent/status`  
**描述**：获取Agent系统状态  

**响应**：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "status": "running",
    "version": "1.0.0",
    "capabilities": ["chat", "search", "rag"],
    "formats": ["markdown", "text", "html"]
  },
  "details": null,
  "timestamp": "2023-01-01 12:00:00"
}
```