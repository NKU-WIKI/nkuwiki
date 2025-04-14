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

### 错误代码说明

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
  "openid": "微信用户唯一标识",         // 必填，微信小程序用户唯一标识
  "unionid": "微信开放平台唯一标识",    // 可选，微信开放平台唯一标识
  "nickname": "用户昵称",             // 可选，用户昵称（如不提供则自动生成默认昵称）
  "avatar": "头像URL",                // 可选，头像URL（若为空则使用默认头像）
  "gender": 1,                        // 可选，性别：0-未知, 1-男, 2-女
  "bio": "个人简介",                   // 可选，个人简介
  "country": "国家",                   // 可选，国家
  "province": "省份",                  // 可选，省份
  "city": "城市",                      // 可选，城市
  "language": "语言",                  // 可选，语言
  "birthday": "2004-06-28",           // 可选，生日
  "wechatId": "微信号",                // 可选，微信号
  "qqId": "QQ号",                      // 可选，QQ号
  "phone": "手机号",                   // 可选，手机号
  "university": "大学",                // 可选，大学
  "extra": {                          // 可选，扩展字段
    "school": "南开大学"
  }
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
    "unionid": "微信开放平台唯一标识",
    "nickname": "用户昵称",
    "avatar": "头像URL（如果为空，会自动设置为默认头像）",
    "gender": 1,
    "bio": "个人简介",
    "country": "国家",
    "province": "省份",
    "city": "城市",
    "language": "语言",
    "birthday": "2004-06-28",
    "wechatId": "微信号",
    "qqId": "QQ号",
    "phone": "手机号",
    "university": "大学",
    "token_count": 100,
    "like_count": 10,
    "favorite_count": 5,
    "post_count": 8,
    "follower_count": 20,
    "follow_count": 15,
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
    "bio": null,
    "country": null,
    "province": null,
    "city": null,
    "language": null,
    "birthday": null,
    "wechatId": null,
    "qqId": null,
    "phone": null,
    "university": null,
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
    "phone": "手机号",
    "university": "大学",
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
  "data": [
    {
      "id": 1,
      "openid": "微信用户唯一标识",
      "unionid": "微信开放平台唯一标识",
      "nickname": "用户昵称",
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
      "phone": "手机号",
      "university": "大学",
      "token_count": 0,
      "like_count": 0,
      "favorite_count": 0,
      "post_count": 0,
      "follower_count": 0,
      "follow_count": 0,
      "create_time": "2023-01-01 12:00:00",
      "update_time": "2023-01-01 12:00:00",
      "last_login": "2023-01-01 12:00:00",
      "platform": "wxapp",
      "status": 1,
      "is_deleted": 0,
      "extra": {}
    }
  ],
  "pagination": {
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
  "phone": "手机号",                  // 可选，手机号
  "university": "大学",               // 可选，大学
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
    "phone": "手机号",
    "university": "大学",
    "token_count": 100,
    "like_count": 10,
    "favorite_count": 5,
    "post_count": 8,
    "follower_count": 20,
    "follow_count": 15,
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
{"code":200,"message":"success","data":{"success":true,"status":"followed","is_following":true},"details":{"message":"关注成功"},"timestamp":"2025-04-12T21:10:26.320996","pagination":null}
{"code":200,"message":"success","data":{"success":true,"status":"unfollowed","is_following":false},"details":{"message":"取消关注成功"},"timestamp":"2025-04-12T21:10:01.431815","pagination":null}
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

**接口**：`GET /api/wxapp/user/following`  
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

**接口**：`GET /api/wxapp/user/follower`  
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
  "image": ["图片URL1", "图片URL2"], // 可选
  "tag": ["标签1", "标签2"], // 可选
  "category_id": 1, // 可选，默认为0
  "location": { // 可选
    "latitude": 39.12345,
    "longitude": 116.12345,
    "name": "位置名称",
    "address": "详细地址"
  },
  "phone": "手机号", // 可选
  "wechatId": "微信号", // 可选
  "qqId": "QQ号", // 可选
  "nickname": "用户昵称", // 可选，如不提供则从用户表获取
  "avatar": "用户头像URL" // 可选，如不提供则从用户表获取
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
    "phone": "手机号",
    "wechatId": "微信号",
    "qqId": "QQ号",
    "nickname": "用户昵称",
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
    "phone": "手机号",
    "wechatId": "微信号",
    "qqId": "QQ号",
    "nickname": "用户昵称",
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
  "post_id": 1, // 必填，整数类型
  "openid": "发帖用户openid", // 必填
  "content": "更新后的内容", // 可选，帖子内容
  "title": "更新后的标题", // 可选，帖子标题
  "category_id": 2, // 可选，整数类型，分类ID
  "image": ["图片URL1","图片URL2"], // 可选，图片URL数组
  "tag": ["标签1","标签2"], // 可选，标签数组
  "phone": "手机号", // 可选
  "wechatId": "微信号", // 可选
  "qqId": "QQ号" // 可选
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
    "phone": "手机号",
    "wechatId": "微信号",
    "qqId": "QQ号",
    "nickname": "用户昵称", 
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
{"code":200,"message":"success","data":{"success":true,"status":"liked","like_count":1,"is_liked":true},"details":{"message":"点赞成功"},"timestamp":"2025-04-12T20:56:23.008762","pagination":null}
{"code":200,"message":"success","data":{"success":true,"status":"unliked","like_count":0,"is_liked":false},"details":{"message":"取消点赞成功"},"timestamp":"2025-04-12T20:56:14.207527","pagination":null}

```

### 2.7 收藏帖子

**接口**：`POST /api/wxapp/post/favorite`  
**描述**：收藏帖子或取消收藏（如果已收藏）  
**请求体**：

```json
{
  "post_id": 1, // 必填，整数类型
  "openid": "收藏用户的openid" // 必填
}
```

**响应**：

```json
{"code":200,"message":"success","data":{"success":true,"status":"favorited","favorite_count":1,"is_favorited":true},"details":{"message":"收藏成功"},"timestamp":"2025-04-12T20:54:08.462333","pagination":null}
```
```json
{"code":200,"message":"success","data":{"success":true,"status":"unfavorited","favorite_count":0,"is_favorited":false},"details":{"message":"取消收藏成功"},"timestamp":"2025-04-12T20:54:22.807428","pagination":null}
```    

### 2.8 获取帖子互动状态

**接口**：`POST /api/wxapp/posts/{post_id}/unfavorite`  
**描述**：取消收藏帖子  
**说明**：该操作会同时更新帖子作者的favorites_count（当被其他用户取消收藏时）  
**参数**：
- `post_id` - 路径参数，帖子ID
- `openid` - 查询参数，用户openid

**响应**：

```json
{"code":200,"message":"success","data":{"20":{"exist":true,"is_liked":false,"is_favorited":false,"is_author":false,"is_following":false,"like_count":0,"favorite_count":0,"comment_count":0,"view_count":2}},"details":null,"timestamp":"2025-04-12T21:08:44.098526","pagination":null}
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
        "sender": {
          "openid": "发送者openid",
          "avatar": "发送者头像URL",
          "nickname": "发送者昵称"
        },
        "target_id": "123",
        "target_type": "post",
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
    "sender": {
      "openid": "发送者openid",
      "avatar": "发送者头像URL",
      "nickname": "发送者昵称"
    },
    "target_id": "123",
    "target_type": "post",
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
    "sender": {
      "openid": "发送者openid",
      "avatar": "发送者头像URL",
      "nickname": "发送者昵称"
    },
    "target_id": "123",
    "target_type": "post",
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

## 六、Agent智能体API

### 6.1 智能体聊天接口

**接口**：`POST /api/agent/chat`  
**描述**：与智能体进行对话，支持普通文本和流式响应  
**请求体**：

```json
{
  "query": "用户提问内容",
  "openid": "用户唯一标识",
  "stream": false,
  "format": "markdown",
  "bot_tag": "default"
}
```

**请求参数说明**：
- `query` - 字符串，必填，用户的提问内容
- `openid` - 字符串，必填，用户的唯一标识，用于区分不同用户
- `stream` - 布尔值，可选，默认false，是否使用流式响应(服务器发送事件SSE)
- `format` - 字符串，可选，默认"markdown"，响应格式，支持"markdown"、"text"、"html"
- `bot_tag` - 字符串，可选，默认"default"，用于指定使用哪个机器人，配置在config中

**非流式响应**：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "message": "AI回复的内容",
    "sources": [],
    "format": "markdown",
    "usage": {},
    "finish_reason": null
  },
  "details": null,
  "timestamp": "2025-03-27 16:47:42"
}
```

**流式响应**：
使用服务器发送事件(SSE)格式，每个事件包含部分回复内容，格式如下：

```
data: {"content": "内容片段1"}

data: {"content": "内容片段2"}

...

data: {"content": "内容片段n"}
```

**响应参数说明**：
- `message` - 字符串，AI回复的内容
- `sources` - 数组，知识来源，目前为空数组
- `format` - 字符串，输出格式
- `usage` - 对象，token使用情况
- `finish_reason` - 字符串或null，完成原因

**错误码**：
- `400` - 请求参数错误
- `500` - 服务器内部错误

**示例**：

请求：
```bash
curl -X POST "http://localhost:8001/api/agent/chat" \
  -H "Content-Type: application/json" \
  -d '{"query": "南开大学有什么特色专业", "openid": "test_user", "stream": false, "format": "markdown", "bot_tag": "default"}'
```

流式请求：
```bash
curl -N -X POST "http://localhost:8001/api/agent/chat" \
  -H "Content-Type: application/json" \
  -d '{"query": "南开大学有什么特色专业", "openid": "test_user", "stream": true, "format": "markdown", "bot_tag": "default"}'
```

### 6.2 知识库搜索

**接口**：`POST /api/agent/search`  
**描述**：搜索知识库内容，支持跨表搜索和相关度排序，采用优化的相关度算法  
**请求体**：

```json
{
  "keyword": "南开大学历史",
  "limit": 10,
  "include_content": false,
  "tables": ["wxapp_posts", "website_nku", "wechat_nku"]
}
```

**请求参数说明**：
- `keyword` - 字符串，必填，搜索关键词
- `limit` - 整数，可选，默认10，最大50，返回结果数量限制
- `include_content` - 布尔值，可选，默认false，是否包含完整内容
- `tables` - 字符串数组，可选，要搜索的表名列表，支持以下表：
  - `wxapp_posts` - 微信小程序帖子表（默认）
  - `website_nku` - 南开大学网站内容
  - `wechat_nku` - 南开大学微信公众号内容
  - `market_nku` - 南开大学校园集市内容

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
        "relevance": 0.95,
        "source": "wxapp_posts",
        "content": "南开大学创建于1919年，由著名爱国教育家张伯苓先生创办..."  // 仅当include_content=true时包含
      },
      {
        "id": 2,
        "title": "南开大学百年校庆",
        "content_preview": "2019年，南开大学迎来百年华诞...",
        "author": "南开校友",
        "create_time": "2023-01-02 12:00:00",
        "type": "网站",
        "view_count": 986,
        "like_count": 76,
        "comment_count": 12,
        "relevance": 0.85,
        "source": "website_nku"
      }
    ],
    "keyword": "南开大学历史",
    "total": 2
  },
  "details": null,
  "timestamp": "2023-01-01 12:00:00"
}
```

**响应参数说明**：
- `results` - 数组，搜索结果列表，按相关度排序
  - `id` - 整数，记录ID
  - `title` - 字符串，标题
  - `content_preview` - 字符串，内容预览，会智能截取关键词上下文
  - `author` - 字符串，作者/发布者
  - `create_time` - 字符串，创建/发布时间
  - `type` - 字符串，内容类型，如"文章"、"网站"、"公众号"等
  - `view_count` - 整数，浏览次数
  - `like_count` - 整数，点赞次数
  - `comment_count` - 整数，评论数量
  - `relevance` - 浮点数，相关度得分，范围0~1
  - `source` - 字符串，数据来源表名
  - `content` - 字符串，完整内容（仅当include_content=true时包含）
- `keyword` - 字符串，搜索关键词
- `total` - 整数，结果总数

**相关度计算优化**：
- 标题匹配优先于内容匹配
- 完整关键词匹配优先于部分关键词匹配
- 考虑关键词出现位置，靠前位置有更高权重
- 考虑关键词出现频率
- 考虑内容长度因素，中等长度内容有轻微加权
- 文档已删除状态自动排除

**错误码**：
- `400` - 请求参数错误（如不支持的表名）
- `422` - 请求验证失败（如空关键词或超出限制）
- `500` - 服务器内部错误

**示例**：

请求：
```bash
curl -X POST "http://localhost:8001/api/agent/search" \
  -H "Content-Type: application/json" \
  -d '{"keyword": "南开大学历史", "limit": 10, "tables": ["wxapp_posts", "website_nku"]}'
```

包含完整内容的请求：
```bash
curl -X POST "http://localhost:8001/api/agent/search" \
  -H "Content-Type: application/json" \
  -d '{"keyword": "南开大学历史", "limit": 5, "include_content": true, "tables": ["wxapp_posts"]}'
```

### 6.3 高级知识库搜索

**接口**：`POST /api/agent/search/advanced`  
**描述**：高级知识库搜索，支持更多搜索条件和排序方式  
**请求体**：

```json
{
  "keyword": "南开大学",
  "title": "校史",
  "content": "张伯苓",
  "author": "南开百科",
  "start_time": "2023-01-01T00:00:00",
  "end_time": "2023-12-31T23:59:59", 
  "limit": 10,
  "include_content": false,
  "tables": ["wxapp_posts", "website_nku"],
  "sort_by": "time_desc"
}
```

**请求参数说明**：
- `keyword` - 字符串，可选，搜索关键词（标题和内容）
- `title` - 字符串，可选，标题关键词
- `content` - 字符串，可选，内容关键词
- `author` - 字符串，可选，作者关键词
- `start_time` - 字符串，可选，开始时间（ISO格式）
- `end_time` - 字符串，可选，结束时间（ISO格式）
- `limit` - 整数，可选，默认10，最大50，返回结果数量限制
- `include_content` - 布尔值，可选，默认false，是否包含完整内容
- `tables` - 字符串数组，可选，要搜索的表名列表，同普通搜索
- `sort_by` - 字符串，可选，排序方式：
  - `relevance` - 按相关度排序（默认）
  - `time_desc` - 按时间降序（最新的在前）
  - `time_asc` - 按时间升序（最早的在前）
  - `likes` - 按点赞数排序
  - `views` - 按浏览量排序

**说明**：
- 至少需要指定一个搜索条件（keyword, title, content, author中至少一个）
- 如果同时指定多个条件，它们之间是"与"的关系
- 当不指定关键词但指定排序方式时，相关度默认为0.5以保证结果有序
- 响应格式与普通搜索相同，但排序方式可能不同

**响应**：
与普通知识库搜索接口相同的响应格式

**错误码**：
- `400` - 请求参数错误（如不支持的表名）
- `422` - 请求验证失败（如无有效搜索条件或时间范围错误）
- `500` - 服务器内部错误

**示例**：

按时间降序查询请求：
```bash
curl -X POST "http://localhost:8001/api/agent/search/advanced" \
  -H "Content-Type: application/json" \
  -d '{"keyword": "南开大学", "limit": 10, "tables": ["wxapp_posts", "website_nku"], "sort_by": "time_desc"}'
```

多条件查询请求：
```bash
curl -X POST "http://localhost:8001/api/agent/search/advanced" \
  -H "Content-Type: application/json" \
  -d '{"title": "校史", "author": "南开百科", "start_time": "2023-01-01T00:00:00", "limit": 5, "sort_by": "likes"}'
```

### 6.4 获取Agent状态

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

### 智能搜索接口

`POST /api/search`

**请求参数**：
```json
{
  "keyword": "南开",
  "page": 1,
  "page_size": 10,
  "search_type": "all"
}
```

**响应示例**：
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "results": [
      {
        "post_id": 123,
        "title": "南开大学简介",
        "content": "南开大学是著名学府...",
        "highlight_title": "南开...",
        "highlight_content": "...大学是著名学府...",
        "create_time": "2023-05-01 10:00:00",
        "author": "张三",
        "comment_count": 5
      }
    ],
    "total": 15,
    "current_page": 1
  }
}
```

**参数说明**：
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|-----|
| keyword | string | 是 | 搜索关键词，支持布尔模式 |
| page | int | 否 | 页码，默认1 |
| page_size | int | 否 | 每页数量（1-50），默认10 |
| search_type | string | 否 | 搜索类型：all(默认)/post(仅文章)/comment(含评论的文章) |

**搜索建议接口**：
`GET /api/search/suggest?q=南开`

**响应示例**：
```json
{
  "code": 200,
  "message": "success",
  "data": [
    "南开大学简介",
    "南开校园生活指南",
    "南开校史"
  ]
}
```

**高级功能**：
1. 支持高亮显示匹配片段（highlight_title/highlight_content）
2. 支持多表联合搜索（wxapp_posts, website_nku等）
3. 支持按时间范围、作者、分类等过滤
4. 搜索结果自动分页，支持相关度/时间排序

## 七、数据库MCP接口

### 7.1 获取MCP清单

**接口**：`GET /api/mcp`  
**描述**：获取MCP（Model Context Protocol）清单，使用SSE格式返回工具列表  
**返回**：Server-Sent Events (SSE) 流式响应，内容包括：

1. 服务器信息事件
```
event: server_info
data: {
  "name": "nkuwiki-db-mcp",
  "version": "1.0.0",
  "capabilities": {
    "methods": ["execute_sql", "show_tables", "describe_table", "query_table"],
    "streaming": true,
    "tools": true
  },
  "status": "ready",
  "protocol_version": "2023-07-01"
}
```

2. 会话创建事件
```
event: session_created
data: {"session_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"}
```

3. 工具清单事件
```
event: manifest
data: {
  "type": "manifest",
  "tools": [
    {
      "name": "execute_sql",
      "description": "执行SQL查询并返回结果，仅支持SELECT语句",
      "parameters": {
        "type": "object",
        "properties": {
          "sql": {
            "type": "string",
            "description": "SQL查询语句(仅SELECT)"
          },
          "params": {
            "type": "array",
            "description": "查询参数列表",
            "items": {
              "type": "string"
            }
          }
        },
        "required": ["sql"]
      }
    },
    {
      "name": "show_tables",
      "description": "显示数据库中所有表",
      "parameters": {
        "type": "object",
        "properties": {}
      }
    },
    {
      "name": "describe_table",
      "description": "显示表结构",
      "parameters": {
        "type": "object",
        "properties": {
          "table_name": {
            "type": "string",
            "description": "表名"
          }
        },
        "required": ["table_name"]
      }
    },
    {
      "name": "query_table",
      "description": "查询指定表的数据",
      "parameters": {
        "type": "object",
        "properties": {
          "table_name": {
            "type": "string",
            "description": "表名"
          },
          "conditions": {
            "type": "object",
            "description": "查询条件，字段名和值的映射"
          },
          "limit": {
            "type": "integer",
            "description": "返回结果数量限制，默认20"
          },
          "offset": {
            "type": "integer",
            "description": "分页偏移量，默认0"
          },
          "order_by": {
            "type": "string",
            "description": "排序方式，例如'id DESC'"
          }
        },
        "required": ["table_name"]
      }
    }
  ]
}
```

4. 心跳事件（每15秒发送一次）
```
event: heartbeat
data: {"timestamp": 1717027452.123456}
```

### 7.2 执行JSON-RPC调用

**接口**：`POST /api/mcp/jsonrpc`  
**描述**：通过JSON-RPC调用MCP工具，提供标准JSON-RPC 2.0接口  
**请求体**：

```json
{
  "jsonrpc": "2.0",
  "id": "request-id-123",
  "method": "execute_sql",
  "params": {
    "sql": "SELECT * FROM wxapp_posts LIMIT 5",
    "params": []
  }
}
```

**响应**：

```json
{
  "jsonrpc": "2.0",
  "id": "request-id-123",
  "result": {
    "result": [
      {"id": 1, "title": "帖子标题", "content": "帖子内容", "...": "..."},
      {"id": 2, "title": "帖子标题2", "content": "帖子内容2", "...": "..."}
    ],
    "row_count": 2,
    "sql": "SELECT * FROM wxapp_posts LIMIT 5"
  }
}
```

**错误响应**：

```json
{
  "jsonrpc": "2.0",
  "id": "request-id-123",
  "error": {
    "code": -32600,
    "message": "安全限制：只允许SELECT查询"
  }
}
```

**错误码**：
- `-32700` - 无效的JSON请求
- `-32600` - 参数验证错误
- `-32601` - 未知方法
- `-32602` - 非法参数
- `-32603` - 内部错误

**支持的JSON-RPC方法**：
- `listOfferings` - 返回可用工具列表
- `execute_sql` - 执行SQL查询（仅SELECT）
- `show_tables` - 显示所有表
- `describe_table` - 显示表结构
- `query_table` - 查询表数据

### 7.3 工具调用接口

**接口**：`POST /api/mcp/tool`  
**描述**：调用MCP工具（旧版接口，保留兼容性）  
**请求体**：

```json
{
  "tool": "execute_sql",
  "parameters": {
    "sql": "SELECT * FROM wxapp_posts LIMIT 5",
    "params": []
  }
}
```

**响应**：

```json
{
  "result": [
    {"id": 1, "title": "帖子标题", "content": "帖子内容", "...": "..."},
    {"id": 2, "title": "帖子标题2", "content": "帖子内容2", "...": "..."}
  ],
  "row_count": 2
}
```

**错误响应**：

```json
{
  "error": "安全限制：只允许SELECT查询"
}
```

**支持的工具**：
- `execute_sql` - 执行SQL查询
- `show_tables` - 显示所有表
- `describe_table` - 显示表结构
- `query_table` - 查询表数据