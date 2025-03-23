# 南开Wiki API文档

## 更新记录

- **2023-03-26**: 增加RAG（检索增强生成）相关接口（8.4-8.5），添加suggested_questions字段到返回结果

本文档包含南开Wiki平台的所有API接口，主要分为三类：
1. 微信小程序API：提供给微信小程序客户端使用的API
2. MySQL查询API：提供对数据库的查询功能
3. Agent智能体API：提供AI聊天和知识检索功能

## 接口前缀

所有API都有对应的前缀路径：
- 微信小程序API：`/wxapp/*`
- MySQL查询API：`/mysql/*`
- Agent智能体API：`/agent/*`

如，用户接口的完整路径为 `/wxapp/users/me`


## 后端响应标准格式：
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "key1": value1
  }
}
```


## 一、用户接口

### 1.1 同步微信云用户

**接口**：`POST /wxapp/users/sync`  
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
  }
}
```

### 1.2 获取用户信息

**接口**：`GET /wxapp/users/{openid}`  
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
  }
}
```

### 1.3 获取当前用户信息

**接口**：`GET /wxapp/users/me`  
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
  }
}
```

### 1.4 查询用户列表

**接口**：`GET /wxapp/users`  
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
  }
}
```

### 1.5 更新用户信息

**接口**：`PUT /wxapp/users/{openid}`  
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
  }
}
```

### 1.6 删除用户

**接口**：`DELETE /wxapp/users/{openid}`  
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
  }
}
```

## 二、帖子接口

### 2.1 创建帖子

**接口**：`POST /wxapp/posts`  
**描述**：创建新帖子  
**请求体**：

```json
{
  "openid": "发布用户openid",
  "title": "帖子标题",
  "content": "帖子内容",
  "images": ["图片URL1", "图片URL2"],
  "tags": ["标签1", "标签2"],
  "category_id": 1,
  "location": "位置信息",
  "nick_name": "用户昵称",
  "avatar": "用户头像URL"
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
    "location": "位置信息",
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
  }
}
```

### 2.2 获取帖子详情

**接口**：`GET /wxapp/posts/{post_id}`  
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
  }
}
```

### 2.3 查询帖子列表

**接口**：`GET /wxapp/posts`  
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
  }
}
```

### 2.4 更新帖子

**接口**：`PUT /wxapp/posts/{post_id}`  
**描述**：更新帖子信息  
**参数**：
- `post_id` - 路径参数，帖子ID

**请求体**：

```json
{
  "title": "新标题",
  "content": "新内容",
  "images": ["新图片URL1", "新图片URL2"],
  "tags": ["新标签1", "新标签2"],
  "category_id": 2,
  "location": "新位置信息",
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
    "openid": "发布用户openid",
    "title": "新标题",
    "content": "新内容",
    "images": ["新图片URL1", "新图片URL2"],
    "tags": ["新标签1", "新标签2"],
    "category_id": 2,
    "location": "新位置信息",
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
    "extra": {}
  }
}
```

### 2.5 删除帖子

**接口**：`DELETE /wxapp/posts/{post_id}`  
**描述**：删除帖子（标记删除）  
**参数**：
- `post_id` - 路径参数，帖子ID

**响应**：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "success": true,
    "message": "帖子已删除"
  }
}
```

### 2.6 点赞/取消点赞帖子

**接口**：`POST /wxapp/posts/{post_id}/like`  
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
  }
}
```

### 2.7 收藏/取消收藏帖子

**接口**：`POST /wxapp/posts/{post_id}/favorite`  
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
  }
}
```

## 三、评论接口

### 3.1 创建评论

**接口**：`POST /wxapp/comments`  
**描述**：创建新评论  
**请求体**：

```json
{
  "openid": "评论用户openid",
  "nick_name": "用户昵称",
  "avatar": "用户头像URL",
  "post_id": 1,
  "content": "评论内容",
  "parent_id": null
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
  }
}
```

### 3.2 获取评论详情

**接口**：`GET /wxapp/comments/{comment_id}`  
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
  }
}
```

### 3.3 获取帖子评论列表

**接口**：`GET /wxapp/posts/{post_id}/comments`  
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
  }
}
```

### 3.4 更新评论

**接口**：`PUT /wxapp/comments/{comment_id}`  
**描述**：更新评论信息  
**参数**：
- `comment_id` - 路径参数，评论ID

**请求体**：

```json
{
  "content": "新评论内容",
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
    "is_deleted": 0,
    "extra": {}
  }
}
```

### 3.5 删除评论

**接口**：`DELETE /wxapp/comments/{comment_id}`  
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
  }
}
```

### 3.6 点赞评论

**接口**：`PUT /wxapp/comments/{comment_id}/like`  
**描述**：点赞或取消点赞评论  
**参数**：
- `comment_id` - 路径参数，评论ID

**请求体**：
```json
{
  "openid": "用户openid"
}
```

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
  }
}
```

## 四、通知接口

### 4.1 获取用户通知列表

**接口**：`GET /wxapp/users/{openid}/notifications`  
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
  }
}
```

### 4.2 获取通知详情

**接口**：`GET /wxapp/notifications/{notification_id}`  
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
  }
}
```

### 4.3 标记通知为已读

**接口**：`PUT /wxapp/notifications/{notification_id}`  
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
  }
}
```

### 4.4 批量标记通知为已读

**接口**：`PUT /wxapp/users/{openid}/notifications/read`  
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
  }
}
```

### 4.5 删除通知

**接口**：`DELETE /wxapp/notifications/{notification_id}`  
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
  }
}
```

## 五、反馈接口

### 5.1 提交反馈

**接口**：`POST /wxapp/feedback`  
**描述**：提交意见反馈  
**请求体**：

```json
{
  "openid": "用户openid",
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
  }
}
```

### 5.2 获取用户反馈列表

**接口**：`GET /wxapp/users/{openid}/feedback`  
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
  }
}
```

### 5.3 获取反馈详情

**接口**：`GET /wxapp/feedback/{feedback_id}`  
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
  }
}
```

### 5.4 更新反馈

**接口**：`PUT /wxapp/feedback/{feedback_id}`  
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
  }
}
```

### 5.5 删除反馈

**接口**：`DELETE /wxapp/feedback/{feedback_id}`  
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
  }
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
| 429    | 请求过于频繁 |
| 500    | 服务器内部错误 |
| 502    | 网关错误 |
| 503    | 服务不可用 |
| 504    | 网关超时 |

## 七、MySQL查询API

### 7.1 获取数据库表列表

**接口**：`GET /mysql/tables`  
**描述**：获取数据库中所有表  

**响应**：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "tables": [
      "wxapp_users",
      "wxapp_posts",
      "wxapp_comments",
      "wxapp_notifications",
      "wxapp_feedback"
    ]
  }
}
```

### 7.2 获取表结构

**接口**：`GET /mysql/table/{table_name}/structure`  
**描述**：获取指定表的结构  
**参数**：
- `table_name` - 路径参数，表名

**响应**：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "fields": [
      {
        "Field": "id",
        "Type": "int(11)",
        "Null": "NO",
        "Key": "PRI",
        "Default": null,
        "Extra": "auto_increment"
      },
      {
        "Field": "openid",
        "Type": "varchar(100)",
        "Null": "NO",
        "Key": "UNI",
        "Default": null,
        "Extra": ""
      }
    ]
  }
}
```

### 7.3 查询数据

**接口**：`POST /mysql/query`  
**描述**：按条件查询表数据  
**请求体**：

```json
{
  "table_name": "wxapp_users",
  "conditions": {
    "status": 1,
    "platform": "wxapp"
  },
  "order_by": "create_time DESC",
  "limit": 20,
  "offset": 0
}
```

**响应**：

```json
{
  "code": 200,
  "message": "success",
  "data": [
    {
      "id": 1,
      "openid": "test_openid",
      "nick_name": "测试用户",
      "avatar": "https://example.com/avatar.jpg",
      "status": 1,
      "create_time": "2023-01-01 12:00:00"
    }
  ]
}
```

### 7.4 统计记录

**接口**：`POST /mysql/count`  
**描述**：统计表中的记录数量  
**请求体**：

```json
{
  "table_name": "wxapp_posts",
  "conditions": {
    "status": 1
  }
}
```

**响应**：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "count": 120
  }
}
```

### 7.5 自定义查询

**接口**：`POST /mysql/custom_query`  
**描述**：执行自定义SQL查询  
**请求体**：

```json
{
  "query": "SELECT * FROM wxapp_users WHERE status = %s AND platform = %s LIMIT 10",
  "params": [1, "wxapp"],
  "fetch": true
}
```

**响应**：

```json
{
  "code": 200,
  "message": "success",
  "data": [
    {
      "id": 1,
      "openid": "test_openid",
      "nick_name": "测试用户",
      "avatar": "https://example.com/avatar.jpg",
      "status": 1,
      "create_time": "2023-01-01 12:00:00"
    }
  ]
}
```

## 八、Agent智能体API

### 8.1 与Agent对话

**接口**：`POST /agent/chat`  
**描述**：与AI智能体进行对话  
**请求体**：

```json
{
  "query": "南开大学的校训是什么？",
  "history": [
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
        "title": "南开大学简介",
        "url": "https://nku.wiki/intro",
        "snippet": "南开大学校训为"允公允能，日新月异"，出自《论语》..."
      }
    ],
    "suggested_questions": [
      "南开大学的校徽有什么含义？",
      "南开大学是什么时候创立的？",
      "南开大学的创始人是谁？"
    ],
    "format": "markdown"
  }
}
```

### 8.2 知识库搜索

**接口**：`POST /agent/search`  
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
  "data": [
    {
      "title": "南开大学校史",
      "url": "https://nku.wiki/history",
      "snippet": "南开大学创建于1919年，由著名爱国教育家张伯苓先生创办...",
      "score": 0.95
    },
    {
      "title": "南开大学百年校庆",
      "url": "https://nku.wiki/100years",
      "snippet": "2019年，南开大学迎来百年华诞...",
      "score": 0.85
    }
  ]
}
```

### 8.3 获取Agent状态

**接口**：`GET /agent/status`  
**描述**：获取Agent系统状态  

**响应**：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "status": "running",
    "version": "1.0.0",
    "capabilities": ["chat", "search"],
    "formats": ["markdown", "text", "html"]
  }
}
```

### 8.4 检索增强生成 (RAG)

**接口**：`POST /agent/rag`  
**描述**：从知识库中检索相关信息，并结合大语言模型生成回答  
**请求体**：

```json
{
  "query": "南开大学历史",
  "tables": ["wxapp_posts", "wechat_nku"],
  "max_results": 5,
  "stream": false,
  "format": "markdown",
  "openid": "user_openid"
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

**可用的表名列表**：
- `wxapp_posts`: 小程序帖子
- `wxapp_comments`: 小程序评论
- `wxapp_users`: 小程序用户
- `wechat_nku`: 微信公众号文章
- `website_nku`: 南开网站文章
- `market_nku`: 校园集市帖子

**响应**：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "response": "南开大学创建于1919年，由著名爱国教育家张伯苓和严修创办...",
    "sources": [
      {
        "id": "1",
        "type": "帖子",
        "title": "南开大学创办历史",
        "item_id": 123,
        "author": "南开百科"
      }
    ],
    "suggested_questions": [
      "南开大学的校训是什么？",
      "南开大学有哪些著名校友？",
      "南开大学的学科设置有哪些？"
    ],
    "format": "markdown",
    "retrieved_count": 5,
    "response_time": 0.518
  }
}
```

### 8.5 增强版检索增强生成 (RAG2)

**接口**：`POST /agent/rag2`  
**描述**：使用查询改写和两阶段处理的增强版RAG接口  
**请求体**：

```json
{
  "query": "怎样申请奖学金",
  "tables": ["wxapp_posts", "wechat_nku"],
  "max_results": 5,
  "stream": false,
  "format": "markdown",
  "openid": "user_openid",
  "query_bot_id": "rewriter",
  "flash_bot_id": "flash"
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
| query_bot_id | string | 否 | "rewriter" | 查询改写机器人ID |
| flash_bot_id | string | 否 | "flash" | 回答生成机器人ID |

**响应**：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "response": "在南开大学，申请奖学金的流程如下...",
    "sources": [
      {
        "id": "1",
        "type": "帖子",
        "title": "南开大学奖学金申请指南",
        "item_id": 456,
        "author": "南开学生处"
      }
    ],
    "suggested_questions": [
      "南开大学有哪些类型的奖学金？",
      "奖学金申请的时间节点是什么？",
      "获得奖学金的条件有哪些？"
    ],
    "format": "markdown",
    "retrieved_count": 3,
    "original_query": "怎样申请奖学金",
    "rewritten_query": "南开大学奖学金申请流程和要求",
    "response_time": 0.723
  }
}
``` 