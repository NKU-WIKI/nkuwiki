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
    "key1": value1
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
**描述**：同步微信用户信息到服务器数据库  
**请求头**：
- `X-Cloud-Source` - 可选，标记来源
- `X-Prefer-Cloud-ID` - 可选，标记优先使用云ID

**请求体**：

```json
{
  "openid": "微信用户唯一标识",
  "unionid": "微信开放平台唯一标识（可选）",
  "nick_name": "用户昵称（可选）",
  "avatar": "头像URL（可选）",
  "gender": 0,
  "country": "国家（可选）",
  "province": "省份（可选）",
  "city": "城市（可选）",
  "language": "语言（可选）",
  "university": "南开大学",
  "login_type": "wechat"
}
```

**响应**：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 10001,
    "openid": "微信用户唯一标识",
    "unionid": "微信开放平台唯一标识",
    "nick_name": "用户昵称",
    "avatar": "头像URL",
    "gender": 0,
    "country": "国家",
    "province": "省份",
    "city": "城市",
    "language": "语言",
    "token_count": 0,
    "likes_count": 0,
    "favorites_count": 0,
    "followers_count": 0,
    "following_count": 0,
    "create_time": "2023-01-01 12:00:00",
    "update_time": "2023-01-01 12:00:00",
    "last_login": "2023-01-01 12:00:00",
    "platform": "wxapp",
    "status": 1,
    "is_deleted": 0
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
    "country": "国家",
    "province": "省份",
    "city": "城市",
    "language": "语言",
    "token_count": 0,
    "likes_count": 0,
    "favorites_count": 0,
    "followers_count": 0,
    "following_count": 0,
    "create_time": "2023-01-01 12:00:00",
    "update_time": "2023-01-01 12:00:00",
    "last_login": "2023-01-01 12:00:00",
    "platform": "wxapp",
    "status": 1,
    "is_deleted": 0
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
    "country": "国家",
    "province": "省份",
    "city": "城市",
    "language": "语言",
    "token_count": 0,
    "likes_count": 0,
    "favorites_count": 0,
    "followers_count": 0,
    "following_count": 0,
    "create_time": "2023-01-01 12:00:00",
    "update_time": "2023-01-01 12:00:00",
    "last_login": "2023-01-01 12:00:00",
    "platform": "wxapp",
    "status": 1,
    "is_deleted": 0
  },
  "details": null,
  "timestamp": "2023-01-01 12:00:00"
}
```

### 1.4 查询用户列表

**接口**：`GET /api/wxapp/users`  
**描述**：获取用户列表  
**参数**：
- `limit` - 查询参数，返回记录数量限制，默认20，最大100
- `offset` - 查询参数，分页偏移量，默认0
- `status` - 查询参数，用户状态：1-正常，0-禁用，可选
- `order_by` - 查询参数，排序方式，默认"create_time DESC"

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
        "country": "国家",
        "province": "省份",
        "city": "城市",
        "language": "语言",
        "token_count": 0,
        "likes_count": 0,
        "favorites_count": 0,
        "followers_count": 0,
        "following_count": 0,
        "create_time": "2023-01-01 12:00:00",
        "update_time": "2023-01-01 12:00:00",
        "last_login": "2023-01-01 12:00:00",
        "platform": "wxapp",
        "status": 1,
        "is_deleted": 0
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

### 1.5 更新用户信息

**接口**：`PUT /api/wxapp/users/{openid}`  
**描述**：更新用户信息  
**参数**：
- `openid` - 路径参数，用户openid

**请求体**：

```json
{
  "nick_name": "新昵称",
  "avatar": "新头像URL",
  "gender": 1,
  "country": "新国家",
  "province": "新省份",
  "city": "新城市",
  "language": "新语言",
  "status": 1,
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
    "openid": "微信用户唯一标识",
    "unionid": "微信开放平台唯一标识",
    "nick_name": "新昵称",
    "avatar": "新头像URL",
    "gender": 1,
    "country": "新国家",
    "province": "新省份",
    "city": "新城市",
    "language": "新语言",
    "token_count": 0,
    "likes_count": 0,
    "favorites_count": 0,
    "followers_count": 0,
    "following_count": 0,
    "create_time": "2023-01-01 12:00:00",
    "update_time": "2023-01-01 12:30:00",
    "last_login": "2023-01-01 12:00:00",
    "platform": "wxapp",
    "status": 1,
    "is_deleted": 0,
    "extra": {}
  },
  "details": null,
  "timestamp": "2023-01-01 12:30:00"
}
```

### 1.6 删除用户

**接口**：`DELETE /api/wxapp/users/{openid}`  
**描述**：删除用户（标记删除）  
**参数**：
- `openid` - 路径参数，用户openid

**响应**：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "success": true,
    "message": "用户已删除"
  },
  "details": null,
  "timestamp": "2023-01-01 12:00:00"
}
```

### 1.7 获取用户关注统计

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

### 1.8 关注用户

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

### 1.9 取消关注用户

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

### 1.10 检查关注状态

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

### 1.11 获取用户关注列表

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
        "nick_name": "用户昵称",
        "avatar": "头像URL",
        "gender": 1,
        "country": "国家",
        "province": "省份",
        "city": "城市",
        "followers_count": 10,
        "following_count": 5,
        "create_time": "2023-01-01 12:00:00",
        "update_time": "2023-01-01 12:00:00"
      }
    ],
    "total": 10,
    "limit": 20,
    "offset": 0
  },
  "details": null,
  "timestamp": "2023-01-01 12:00:00"
}
```

### 1.12 获取用户粉丝列表

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
        "nick_name": "粉丝昵称",
        "avatar": "头像URL",
        "gender": 2,
        "country": "国家",
        "province": "省份",
        "city": "城市",
        "followers_count": 2,
        "following_count": 15,
        "create_time": "2023-01-01 12:00:00",
        "update_time": "2023-01-01 12:00:00"
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

## 二、帖子接口

### 2.1 创建帖子

**接口**：`POST /api/wxapp/posts`  
**描述**：创建新帖子  
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
    "is_deleted": 0
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
    "is_deleted": 0
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
        "is_deleted": 0
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
    "is_deleted": 0
  },
  "details": null,
  "timestamp": "2023-01-01 13:00:00"
}
```

### 2.5 删除帖子

**接口**：`DELETE /api/wxapp/posts/{post_id}`  
**描述**：删除帖子（标记删除）  
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
**描述**：点赞或取消点赞帖子  
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
    "like_count": 6
  },
  "details": null,
  "timestamp": "2023-01-01 12:00:00"
}
```

### 2.7 收藏/取消收藏帖子

**接口**：`POST /api/wxapp/posts/{post_id}/favorite`  
**描述**：收藏或取消收藏帖子  
**参数**：
- `post_id` - 路径参数，帖子ID
- `openid` - 查询参数，用户openid

**请求体**：

```json
{
  "is_favorite": true
}
```

**响应**：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "success": true,
    "message": "收藏成功",
    "favorite": true,
    "favorite_count": 3
  },
  "details": null,
  "timestamp": "2023-01-01 12:00:00"
}
```

### 2.8 取消点赞帖子

**接口**：`POST /api/wxapp/posts/{post_id}/unlike`  
**描述**：取消点赞帖子  
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
    "like_count": 5
  },
  "details": null,
  "timestamp": "2023-01-01 12:00:00"
}
```

### 2.9 取消收藏帖子

**接口**：`POST /api/wxapp/posts/{post_id}/unfavorite`  
**描述**：取消收藏帖子  
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
    "favorite_count": 2
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
**描述**：点赞评论  
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
    "like_count": 4
  },
  "details": null,
  "timestamp": "2023-01-01 12:00:00"
}
```

### 3.7 取消点赞评论

**接口**：`POST /api/wxapp/comments/{comment_id}/unlike`  
**描述**：取消点赞评论  
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
    "like_count": 3
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

### 7.4 检索增强生成 (RAG)

**接口**：`POST /api/agent/rag`  
**描述**：从知识库中检索相关信息，并结合大语言模型生成回答  
**请求体**：

```json
{
  "query": "南开大学历史",
  "tables": ["wxapp_posts", "wechat_nku"],
  "max_results": 5,
  "stream": false,
  "format": "markdown",
  "openid": "user_openid",
  "rewrite_bot_id": null,
  "knowledge_bot_id": null
}
```

**请求参数说明**：

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|-------|------|------|--------|------|
| query | string | 是 | - | 用户查询问题 |
| tables | array | 否 | ["wxapp_posts"] | 要检索的表名列表 |
| max_results | int | 否 | 5 | 每个表返回的最大结果数 |
| stream | bool | 否 | false | 是否流式返回 |
| format | string | 否 | "markdown" | 回复格式: markdown/text/html |
| openid | string | 否 | null | 用户唯一标识 |
| rewrite_bot_id | string | 否 | null | 查询改写机器人ID，不传则使用默认配置 |
| knowledge_bot_id | string | 否 | null | 知识回答机器人ID，不传则使用默认配置 |

**可用的表名列表**：
- `wxapp_posts`: 小程序帖子
- `wxapp_comments`: 小程序评论
- `wechat_nku`: 微信公众号文章
- `website_nku`: 南开网站文章
- `market_nku`: 校园集市帖子

**普通响应**：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "original_query": "南开大学历史",
    "rewritten_query": "南开大学历史沿革和发展",
    "response": "南开大学创建于1919年，由著名爱国教育家张伯苓和严修创办...",
    "sources": [
      {
        "type": "小程序帖子",
        "title": "南开大学创办历史",
        "content": "南开大学创建于1919年...",
        "author": "南开百科"
      }
    ],
    "suggested_questions": [
      "南开大学的校训是什么？",
      "南开大学有哪些著名校友？",
      "南开大学的学科设置有哪些？"
    ],
    "format": "markdown"
  },
  "details": {
    "retrieved_count": 5,
    "response_time": 0.518
  },
  "timestamp": "2023-01-01 12:00:00"
}
```

**流式响应**：

当请求参数 `stream=true` 时，接口将以 Server-Sent Events (SSE) 格式返回流式响应，Content-Type为 `text/event-stream`。

每个事件都以 `data: ` 开头，后跟JSON格式数据，数据中包含 `type` 字段标识事件类型：

1. 查询信息事件:
```
data: {"type":"query","original":"原始查询","rewritten":"改写查询"}
```

2. 内容分块事件:
```
data: {"type":"content","chunk":"回答内容片段"}
```

3. 来源信息事件:
```
data: {"type":"sources","sources":[{"type":"小程序帖子","title":"标题","content":"内容摘要","author":"作者"}]}
```

4. 建议问题事件:
```
data: {"type":"suggested","questions":["建议问题1","建议问题2","建议问题3"]}
```

5. 完成事件:
```
data: {"type":"done"}
```

**错误响应**：

```json
{
  "code": 400,
  "message": "错误信息",
  "data": null,
  "details": {
    "errors": [
      {
        "loc": ["body", "query"],
        "msg": "字段不能为空",
        "type": "value_error.missing"
      }
    ]
  },
  "timestamp": "2023-01-01 12:00:00"
}
```

**常见错误码**：
- `400`: 请求参数错误，例如表名不存在
- `422`: 请求验证失败，例如查询为空或表名列表为空
- `500`: 服务器内部错误

### 7.5 API健康检查

**接口**：`GET /api/health`  
**描述**：检查API服务健康状态  

**响应**：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "status": "ok",
    "version": "1.0.0",
    "uptime": 3600,
    "memory_usage": "128MB",
    "timestamp": "2023-01-01T12:00:00Z"
  },
  "details": null,
  "timestamp": "2023-01-01 12:00:00"
}
```

## 八、文件上传API

### 8.1 上传图片

**接口**：`POST /api/wxapp/upload/image`  
**描述**：上传图片到服务器  
**请求头**：
- `Content-Type` - multipart/form-data

**请求表单**：
- `file` - 图片文件
- `type` - 图片类型：post-帖子图片, avatar-头像, feedback-反馈图片
- `openid` - 用户openid

**响应**：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "url": "https://nkuwiki.com/uploads/images/posts/202301/image.jpg",
    "size": 102400,
    "width": 800,
    "height": 600,
    "type": "post"
  },
  "details": null,
  "timestamp": "2023-01-01 12:00:00"
}
```

### 8.2 上传文件

**接口**：`POST /api/wxapp/upload/file`  
**描述**：上传文件到服务器  
**请求头**：
- `Content-Type` - multipart/form-data

**请求表单**：
- `file` - 文件
- `type` - 文件类型：document-文档, other-其他
- `openid` - 用户openid

**响应**：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "url": "https://nkuwiki.com/uploads/files/202301/document.pdf",
    "filename": "document.pdf",
    "size": 1024000,
    "type": "document",
    "mime_type": "application/pdf"
  },
  "details": null,
  "timestamp": "2023-01-01 12:00:00"
}
```

## 九、其他接口

### 9.1 关于信息

**接口**：`GET /api/wxapp/about`  
**描述**：获取系统关于信息  

**响应**：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "app_name": "南开Wiki",
    "version": "1.0.0",
    "description": "南开Wiki是一个校园知识共享平台",
    "contact": "nkuwiki@example.com",
    "website": "https://nkuwiki.com",
    "copyright": "© 2023 南开Wiki",
    "terms_url": "https://nkuwiki.com/terms",
    "privacy_url": "https://nkuwiki.com/privacy",
    "update_log": [
      {
        "version": "1.0.0",
        "date": "2023-01-01",
        "changes": ["初始版本发布"]
      }
    ]
  },
  "details": null,
  "timestamp": "2023-01-01 12:00:00"
}
```

### 9.2 搜索功能

**接口**：`GET /api/wxapp/search`  
**描述**：搜索微信小程序内容  
**参数**：
- `keyword` - 查询参数，搜索关键词
- `type` - 查询参数，搜索类型，可选值：post-帖子, comment-评论, user-用户, all-全部
- `limit` - 查询参数，返回记录数量限制，默认20，最大100
- `offset` - 查询参数，分页偏移量，默认0

**响应**：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "keyword": "南开大学",
    "type": "all",
    "results": [
      {
        "id": 1,
        "type": "post",
        "title": "南开大学校园风光",
        "content_preview": "南开大学的校园风光非常美丽...",
        "author": "南开学生",
        "create_time": "2023-01-01 12:00:00",
        "score": 0.95
      },
      {
        "id": 5,
        "type": "comment",
        "content_preview": "南开大学的历史很悠久...",
        "author": "历史爱好者",
        "create_time": "2023-01-02 15:30:00",
        "score": 0.85
      }
    ],
    "total": 2,
    "limit": 20,
    "offset": 0
  },
  "details": null,
  "timestamp": "2023-01-01 12:00:00"
}
``` 