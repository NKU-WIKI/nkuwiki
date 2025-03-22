# 微信小程序 API 接口文档

## 基本信息

- 基础路径: `/wxapp`
- API 描述: 南开百科知识平台微信小程序API接口
- 版本: 1.0.0

## 用户接口

### 1. 创建用户

- **接口**: `POST /users`
- **描述**: 创建新用户
- **请求体**: `UserCreate`
  ```json
  {
    "wxapp_id": "微信小程序原始ID",
    "openid": "微信用户唯一标识",
    "unionid": "微信开放平台唯一标识",
    "nickname": "用户昵称",
    "avatar_url": "头像URL",
    "gender": 0,
    "country": "国家",
    "province": "省份",
    "city": "城市",
    "language": "语言"
  }
  ```
- **参数说明**:
  - `wxapp_id` (必填): 微信小程序原始ID
  - 其他字段为可选
- **返回**: `UserResponse`
  ```json
  {
    "id": 1,
    "wxapp_id": "微信小程序原始ID",
    "openid": "微信用户唯一标识",
    "unionid": "微信开放平台唯一标识",
    "nickname": "用户昵称",
    "avatar_url": "头像URL",
    "gender": 0,
    "country": "国家",
    "province": "省份",
    "city": "城市",
    "language": "语言",
    "create_time": "2023-05-20 12:34:56",
    "update_time": "2023-05-20 12:34:56",
    "last_login": null,
    "status": 1
  }
  ```

### 2. 获取用户信息

- **接口**: `GET /users/{user_id}`
- **描述**: 获取指定用户信息
- **参数**:
  - `user_id` (path): 用户ID
- **返回**: `UserResponse`

### 3. 查询用户列表

- **接口**: `GET /users`
- **描述**: 获取用户列表
- **参数**:
  - `limit` (query, 可选): 返回记录数量限制，默认20，最大100
  - `offset` (query, 可选): 分页偏移量，默认0
  - `status` (query, 可选): 用户状态: 1-正常, 0-禁用
- **返回**: `UserResponse[]`

### 4. 更新用户信息

- **接口**: `PUT /users/{user_id}`
- **描述**: 更新用户信息
- **参数**:
  - `user_id` (path): 用户ID
- **请求体**: `UserUpdate`
  ```json
  {
    "nickname": "新昵称",
    "avatar_url": "新头像URL",
    "gender": 1,
    "country": "中国",
    "province": "天津",
    "city": "天津",
    "language": "zh-CN",
    "status": 1
  }
  ```
- **返回**: `UserResponse`

### 5. 删除用户

- **接口**: `DELETE /users/{user_id}`
- **描述**: 删除用户（标记删除）
- **参数**:
  - `user_id` (path): 用户ID
- **返回**:
  ```json
  {
    "success": true,
    "message": "用户已删除"
  }
  ```

## 帖子接口

### 1. 创建帖子

- **接口**: `POST /posts`
- **描述**: 创建新帖子
- **请求体**: `PostCreate`
  ```json
  {
    "wxapp_id": "帖子唯一标识",
    "author_id": "作者ID",
    "author_name": "作者名称",
    "author_avatar": "作者头像URL",
    "content": "帖子内容",
    "title": "帖子标题",
    "images": ["图片URL1", "图片URL2"],
    "tags": ["标签1", "标签2"]
  }
  ```
- **参数说明**:
  - `wxapp_id` (必填): 帖子唯一标识
  - `author_id` (必填): 作者ID
  - 其他字段为可选
- **返回**: `PostResponse`
  ```json
  {
    "id": 1,
    "wxapp_id": "帖子唯一标识",
    "author_id": "作者ID",
    "author_name": "作者名称",
    "author_avatar": "作者头像URL",
    "content": "帖子内容",
    "title": "帖子标题",
    "images": ["图片URL1", "图片URL2"],
    "tags": ["标签1", "标签2"],
    "likes": 0,
    "comment_count": 0,
    "create_time": "2023-05-20 12:34:56",
    "update_time": "2023-05-20 12:34:56",
    "status": 1
  }
  ```

### 2. 获取帖子信息

- **接口**: `GET /posts/{post_id}`
- **描述**: 获取指定帖子信息
- **参数**:
  - `post_id` (path): 帖子ID
- **返回**: `PostResponse`

### 3. 查询帖子列表

- **接口**: `GET /posts`
- **描述**: 获取帖子列表
- **参数**:
  - `limit` (query, 可选): 返回记录数量限制，默认20，最大100
  - `offset` (query, 可选): 分页偏移量，默认0
  - `author_id` (query, 可选): 作者ID
  - `tag` (query, 可选): 帖子标签
  - `status` (query, 可选): 帖子状态: 1-正常, 0-禁用
- **返回**: `PostResponse[]`

### 4. 更新帖子

- **接口**: `PUT /posts/{post_id}`
- **描述**: 更新帖子信息
- **参数**:
  - `post_id` (path): 帖子ID
- **请求体**: `PostUpdate`
  ```json
  {
    "content": "更新后的内容",
    "title": "更新后的标题",
    "images": ["新图片URL1", "新图片URL2"],
    "tags": ["新标签1", "新标签2"],
    "status": 1
  }
  ```
- **返回**: `PostResponse`

### 5. 删除帖子

- **接口**: `DELETE /posts/{post_id}`
- **描述**: 删除帖子（标记删除）
- **参数**:
  - `post_id` (path): 帖子ID
- **返回**:
  ```json
  {
    "success": true,
    "message": "帖子已删除"
  }
  ```

### 6. 点赞帖子

- **接口**: `POST /posts/{post_id}/like`
- **描述**: 给帖子点赞
- **参数**:
  - `post_id` (path): 帖子ID
- **请求体**:
  ```json
  {
    "user_id": "用户ID"
  }
  ```
- **返回**:
  ```json
  {
    "success": true,
    "message": "点赞成功",
    "likes": 1
  }
  ```

### 7. 取消点赞帖子

- **接口**: `POST /posts/{post_id}/unlike`
- **描述**: 取消给帖子点赞
- **参数**:
  - `post_id` (path): 帖子ID
- **请求体**:
  ```json
  {
    "user_id": "用户ID"
  }
  ```
- **返回**:
  ```json
  {
    "success": true,
    "message": "取消点赞成功",
    "likes": 0
  }
  ```

## 评论接口

### 1. 创建评论

- **接口**: `POST /comments`
- **描述**: 创建新评论
- **请求体**: `CommentCreate`
  ```json
  {
    "wxapp_id": "评论唯一标识",
    "post_id": "帖子ID",
    "author_id": "作者ID",
    "author_name": "作者名称",
    "author_avatar": "作者头像URL",
    "content": "评论内容",
    "images": ["图片URL1", "图片URL2"]
  }
  ```
- **参数说明**:
  - `wxapp_id` (必填): 评论唯一标识
  - `post_id` (必填): 帖子ID
  - `author_id` (必填): 作者ID
  - 其他字段为可选
- **返回**: `CommentResponse`
  ```json
  {
    "id": 1,
    "wxapp_id": "评论唯一标识",
    "post_id": "帖子ID",
    "author_id": "作者ID",
    "author_name": "作者名称",
    "author_avatar": "作者头像URL",
    "content": "评论内容",
    "images": ["图片URL1", "图片URL2"],
    "likes": 0,
    "create_time": "2023-05-20 12:34:56",
    "update_time": "2023-05-20 12:34:56",
    "status": 1
  }
  ```

### 2. 获取评论信息

- **接口**: `GET /comments/{comment_id}`
- **描述**: 获取指定评论信息
- **参数**:
  - `comment_id` (path): 评论ID
- **返回**: `CommentResponse`

### 3. 查询评论列表

- **接口**: `GET /comments`
- **描述**: 获取评论列表
- **参数**:
  - `post_id` (query, 可选): 帖子ID
  - `author_id` (query, 可选): 作者ID
  - `limit` (query, 可选): 返回记录数量限制，默认20，最大100
  - `offset` (query, 可选): 分页偏移量，默认0
  - `status` (query, 可选): 评论状态: 1-正常, 0-禁用
- **返回**: `CommentResponse[]`

### 4. 更新评论

- **接口**: `PUT /comments/{comment_id}`
- **描述**: 更新评论信息
- **参数**:
  - `comment_id` (path): 评论ID
- **请求体**: `CommentUpdate`
  ```json
  {
    "content": "更新后的内容",
    "images": ["新图片URL1", "新图片URL2"],
    "status": 1
  }
  ```
- **返回**: `CommentResponse`

### 5. 删除评论

- **接口**: `DELETE /comments/{comment_id}`
- **描述**: 删除评论（标记删除）
- **参数**:
  - `comment_id` (path): 评论ID
- **返回**:
  ```json
  {
    "success": true,
    "message": "评论已删除"
  }
  ```

### 6. 点赞评论

- **接口**: `POST /comments/{comment_id}/like`
- **描述**: 给评论点赞
- **参数**:
  - `comment_id` (path): 评论ID
- **请求体**:
  ```json
  {
    "user_id": "用户ID"
  }
  ```
- **返回**:
  ```json
  {
    "success": true,
    "message": "点赞成功",
    "likes": 1
  }
  ```

### 7. 取消点赞评论

- **接口**: `POST /comments/{comment_id}/unlike`
- **描述**: 取消给评论点赞
- **参数**:
  - `comment_id` (path): 评论ID
- **请求体**:
  ```json
  {
    "user_id": "用户ID"
  }
  ```
- **返回**:
  ```json
  {
    "success": true,
    "message": "取消点赞成功",
    "likes": 0
  }
  ```

## 错误码说明

| 状态码 | 说明 |
| --- | --- |
| 200 | 请求成功 |
| 400 | 请求参数错误 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 