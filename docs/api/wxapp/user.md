# 用户接口

本模块包含与用户相关的操作，如获取用户信息、关注/取消关注等。

### 1. 获取用户公开信息

**接口**：`GET /wxapp/user/profile`

**功能描述**：获取指定用户的公开信息，包括昵称、头像、简介和各项统计数据。

**请求参数 (Query)**:

| 参数 | 类型 | 是否必须 | 描述 |
| --- | --- | --- | --- |
| `openid` | `string` | 是 | 要查询的用户的OpenID。 |
| `current_openid` | `string` | 否 | 当前登录用户的OpenID，用于查询关注状态。 |

**成功响应示例**:

```json
{
    "code": 200,
    "message": "success",
    "data": {
        "id": 1,
        "openid": "oLx8G7ADjzh23EzAJavndryh76rE",
        "nickname": "南开小透明",
        "avatar": null,
        "unionid": null,
        "gender": 0,
        "bio": "你好，nkuwiki！",
        "country": null,
        "province": null,
        "city": null,
        "language": null,
        "birthday": null,
        "wechatId": null,
        "qqId": null,
        "university": null,
        "token_count": 0,
        "like_count": 0,
        "favorite_count": 0,
        "post_count": 7,
        "follower_count": 1,
        "following_count": 0,
        "create_time": "2025-06-09T13:24:10",
        "update_time": "2025-06-21T08:32:57",
        "last_login": null,
        "status": 1,
        "role": null
    },
    "details": null,
    "timestamp": "2025-06-21T16:55:05.987304",
    "pagination": null
}
```

### 2. 获取当前登录用户的完整信息

**接口**：`GET /wxapp/user/my/profile`

**功能描述**：获取当前登录用户的完整个人信息，通常用于"我的"页面或个人资料编辑页。返回的数据比公开信息更完整。

**请求参数 (Query)**:

| 参数 | 类型 | 是否必须 | 描述 |
| --- | --- | --- | --- |
| `openid` | `string` | 是 | 当前登录用户的OpenID。 |

**成功响应示例**:

```json
{
    "code": 200,
    "message": "success",
    "data": {
        "id": 1,
        "openid": "oLx8G7ADjzh23EzAJavndryh76rE",
        "nickname": "南开小透明",
        "avatar": null,
        "unionid": null,
        "gender": 0,
        "bio": "你好，nkuwiki！",
        "country": null,
        "province": null,
        "city": null,
        "language": null,
        "birthday": null,
        "wechatId": null,
        "qqId": null,
        "university": null,
        "token_count": 0,
        "like_count": 0,
        "favorite_count": 0,
        "post_count": 7,
        "follower_count": 1,
        "following_count": 0,
        "create_time": "2025-06-09T13:24:10",
        "update_time": "2025-06-21T08:32:57",
        "last_login": null,
        "status": 1,
        "role": null
    },
    "details": null,
    "timestamp": "2025-06-21T16:55:16.046210",
    "pagination": null
}
```

### 3. 更新用户信息

**接口**：`POST /wxapp/user/update`

**功能描述**：更新当前登录用户的个人信息。只传递需要更新的字段即可。

**请求体**:

| 参数 | 类型 | 是否必须 | 描述 |
| --- | --- | --- | --- |
| `openid` | `string` | 是 | 要更新的用户的OpenID。 |
| `nickname` | `string` | 否 | 新的用户昵称。 |
| `avatar` | `string` | 否 | 新的头像URL。 |
| `gender` | `integer` | 否 | 性别：0-未知, 1-男, 2-女。 |
| `bio` | `string` | 否 | 新的个人简介。 |
| `birthday` | `string` | 否 | 生日，格式为 'YYYY-MM-DD'。 |
| `wechatId` | `string` | 否 | 微信号。 |
| `qqId` | `string` | 否 | QQ号。 |
| `phone` | `string` | 否 | 手机号。 |
| `university`| `string` | 否 | 毕业院校。 |
| `...` | `...` | 否 | 其他 wxapp_user 表中允许更新的字段。 |


**成功响应示例**:

```json
{
    "code": 200,
    "message": "success",
    "data": {
        "id": 1,
        "openid": "oLx8G7ADjzh23EzAJavndryh76rE",
        "nickname": "南开小透明",
        "avatar": null,
        "bio": "A new bio for testing.",
        "gender": 0,
        "country": null,
        "province": null,
        "city": null,
        "role": null
    },
    "details": {
        "message": "用户信息更新成功"
    },
    "timestamp": "2025-06-21T16:55:24.703110",
    "pagination": null
}
```

### 4. 获取用户列表

**接口**：`GET /wxapp/user/list`

**功能描述**：获取用户列表，支持分页和排序。

**请求参数 (Query)**:

| 参数 | 类型 | 是否必须 | 默认值 | 描述 |
| --- | --- | --- | --- | --- |
| `page` | `integer` | 否 | 1 | 页码。 |
| `page_size` | `integer` | 否 | 10 | 每页数量。 |
| `nickname` | `string` | 否 | null | 按昵称模糊搜索。 |
| `sort_by` | `string` | 否 | `latest` | 排序方式，可选值为 `latest` (最新) 或 `popular` (热门)。 |

**成功响应示例**:

```json
{
    "code": 200,
    "message": "success",
    "data": [
        {
            "id": 2,
            "openid": "test_user_005",
            "nickname": "我是修改后的5号",
            "avatar": "http://example.com/avatar.png",
            "bio": "这是我的新简介！",
            "create_time": "2025-06-21T08:28:24",
            "update_time": "2025-06-21T08:32:57",
            "role": null
        },
        {
            "id": 1,
            "openid": "oLx8G7ADjzh23EzAJavndryh76rE",
            "nickname": "南开小透明",
            "avatar": null,
            "bio": "A new bio for testing.",
            "create_time": "2025-06-09T13:24:10",
            "update_time": "2025-06-21T08:55:24",
            "role": null
        }
    ],
    "details": {
        "message": "获取用户列表成功"
    },
    "timestamp": "2025-06-21T16:55:29.922614",
    "pagination": {
        "total": 2,
        "page": 1,
        "page_size": 10,
        "total_pages": 1,
        "has_more": false
    }
}
```

### 5. 获取粉丝列表

**接口**：`GET /wxapp/user/followers`

**功能描述**：获取指定用户的粉丝列表，返回关注者的简要信息。

**请求参数 (Query)**:

| 参数 | 类型 | 是否必须 | 默认值 | 描述 |
| --- | --- | --- | --- | --- |
| `openid` | `string` | 是 | null | 要查询的用户的OpenID。 |
| `page` | `integer` | 否 | 1 | 页码。 |
| `page_size` | `integer` | 否 | 10 | 每页数量。 |

**成功响应示例**:

```json
{
    "code": 200,
    "message": "success",
    "data": [
        {
            "openid": "test_user_005",
            "nickname": "我是修改后的5号",
            "avatar": "http://example.com/avatar.png",
            "bio": "这是我的新简介！",
            "follow_time": "2025-06-21T08:32:57"
        }
    ],
    "details": null,
    "timestamp": "2025-06-21T16:55:40.490858",
    "pagination": {
        "total": 1,
        "page": 1,
        "page_size": 10,
        "total_pages": 1,
        "has_more": false
    }
}
```

### 6. 获取关注列表

**接口**：`GET /wxapp/user/following`

**功能描述**：获取指定用户正在关注的用户列表。

**请求参数 (Query)**:

| 参数 | 类型 | 是否必须 | 默认值 | 描述 |
| --- | --- | --- | --- | --- |
| `openid` | `string` | 是 | null | 要查询的用户的OpenID。 |
| `page` | `integer` | 否 | 1 | 页码。 |
| `page_size` | `integer` | 否 | 10 | 每页数量。 |

**成功响应示例**:

```json
{
    "code": 200,
    "message": "success",
    "data": [
        {
            "openid": "oLx8G7ADjzh23EzAJavndryh76rE",
            "nickname": "南开小透明",
            "avatar": null,
            "bio": "A new bio for testing.",
            "follow_time": "2025-06-21T08:32:57"
        }
    ],
    "details": null,
    "timestamp": "2025-06-21T16:55:52.311754",
    "pagination": {
        "total": 1,
        "page": 1,
        "page_size": 10,
        "total_pages": 1,
        "has_more": false
    }
}
```

### 7. 获取用户收藏的帖子列表

**接口**：`GET /wxapp/user/favorite`

**功能描述**：获取用户收藏的帖子列表。

**请求参数 (Query)**:

| 参数 | 类型 | 是否必须 | 默认值 | 描述 |
| --- | --- | --- | --- | --- |
| `openid` | `string` | 是 | null | 用户的OpenID。 |
| `page` | `integer` | 否 | 1 | 页码。 |
| `page_size` | `integer` | 否 | 10 | 每页数量。 |

**成功响应示例**:

```json
{
    "code": 200,
    "message": "success",
    "data": [
        {
            "id": 1,
            "title": "发帖",
            "content": "# 发帖\n\n123",
            "image": null,
            "view_count": 0,
            "like_count": 0,
            "comment_count": 3,
            "create_time": "2025-06-12T08:19:10"
        }
    ],
    "details": {
        "message": "获取收藏列表成功"
    },
    "timestamp": "2025-06-21T16:56:11.364391",
    "pagination": {
        "total": 1,
        "page": 1,
        "page_size": 10,
        "total_pages": 1,
        "has_more": false
    }
}
```

### 8. 获取用户点赞的帖子列表

**接口**：`GET /wxapp/user/like`

**功能描述**：获取用户点赞过的帖子列表。

**请求参数 (Query)**:

| 参数 | 类型 | 是否必须 | 默认值 | 描述 |
| --- | --- | --- | --- | --- |
| `openid` | `string` | 是 | null | 用户的OpenID。 |
| `page` | `integer` | 否 | 1 | 页码。 |
| `page_size` | `integer` | 否 | 10 | 每页数量。 |

**成功响应示例**:

```json
{
    "code": 200,
    "message": "success",
    "data": [
        {
            "id": 1,
            "title": "发帖",
            "content": "# 发帖\n\n123",
            "image": null,
            "view_count": 0,
            "like_count": 0,
            "comment_count": 3,
            "create_time": "2025-06-12T08:19:10"
        }
    ],
    "details": {
        "message": "获取点赞列表成功"
    },
    "timestamp": "2025-06-21T16:56:21.853385",
    "pagination": {
        "total": 1,
        "page": 1,
        "page_size": 10,
        "total_pages": 1,
        "has_more": false
    }
}
```

### 9. 获取用户的评论列表

**接口**：`GET /wxapp/user/comment`

**功能描述**：获取指定用户发表过的所有评论。

**请求参数 (Query)**:

| 参数 | 类型 | 是否必须 | 默认值 | 描述 |
| --- | --- | --- | --- | --- |
| `openid` | `string` | 是 | null | 用户的OpenID。 |
| `page` | `integer` | 否 | 1 | 页码。 |
| `page_size` | `integer` | 否 | 10 | 每页数量。 |

**成功响应示例**:

```json
{
    "code": 200,
    "message": "success",
    "data": [
        {
            "id": 7,
            "resource_id": 1,
            "resource_type": "post",
            "parent_id": 2,
            "openid": "oLx8G7ADjzh23EzAJavndryh76rE",
            "nickname": null,
            "avatar": null,
            "content": "这是另一条对父评论的回复",
            "image": null,
            "like_count": 0,
            "reply_count": 0,
            "status": 1,
            "is_deleted": 0,
            "create_time": "2025-06-21T07:56:50",
            "update_time": "2025-06-21T07:56:50"
        }
    ],
    "details": {
        "message": "获取评论列表成功"
    },
    "timestamp": "2025-06-21T16:56:31.669881",
    "pagination": {
        "total": 7,
        "page": 1,
        "page_size": 10,
        "total_pages": 1,
        "has_more": false
    }
}
```

### 10. 查询用户关系状态

**接口**：`GET /wxapp/user/status`

**功能描述**：查询当前登录用户与目标用户的关系状态，例如是否关注了对方。

**请求参数 (Query)**:

| 参数 | 类型 | 是否必须 | 描述 |
| --- | --- | --- | --- |
| `openid` | `string` | 是 | 当前登录用户的OpenID。 |
| `target_id` | `string` | 是 | 目标用户的OpenID。 |

**成功响应示例**:

```json
{
    "code": 200,
    "message": "success",
    "data": {
        "is_following": true,
        "is_self": false,
        "post_count": 7,
        "follower_count": 1,
        "following_count": 0,
        "like_count": 0
    },
    "details": null,
    "timestamp": "2025-06-21T16:57:55.740471",
    "pagination": null
}
```

### 11. 同步微信用户信息（登录/注册）

**接口**：`POST /wxapp/user/sync`

**功能描述**：接收小程序端发送的临时登录凭证（code）和用户信息，在后端完成登录或注册。如果用户不存在，则创建新用户；如果存在，则更新用户信息并返回登录态。

**请求体**:

| 参数 | 类型 | 是否必须 | 描述 |
| --- | --- | --- | --- |
| `code` | `string` | 是 | 小程序端通过 `wx.login()` 获取的临时登录凭证。 |
| `userInfo` | `object` | 是 | 包含用户基本信息的对象，结构同 `wx.getUserProfile` 返回值。 |
| `userInfo.nickName` | `string` | 是 | 用户昵称。 |
| `userInfo.avatarUrl` | `string` | 是 | 用户头像 URL。 |
| `userInfo.gender` | `integer` | 否 | 性别。 |
| `...` | `...` | 否 | 其他 `userInfo` 中可能包含的字段。 |


**成功响应示例 (登录成功)**:

```json
{
    "code": 200,
    "message": "success",
    "data": {
        "id": 1,
        "openid": "oLx8G7ADjzh23EzAJavndryh76rE",
        "nickname": "南开小透明",
        "avatar": "http://example.com/avatar.png",
        "is_new_user": false
    },
    "details": {
        "message": "登录成功"
    },
    "timestamp": "2025-06-21T17:00:00.000000",
    "pagination": null
}
```

**失败响应示例 (无效Code)**:

```json
{
    "code": 400,
    "message": "Bad request",
    "data": null,
    "details": {
        "message": "缺少openid参数"
    },
    "timestamp": "2025-06-21T16:58:06.379535",
    "pagination": null
}
``` 