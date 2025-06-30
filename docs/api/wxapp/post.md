# 微信小程序：帖子接口

本文档详细说明了与微信小程序中帖子功能相关的所有API接口。

## 1. 创建新帖子

- **Endpoint**: `POST /wxapp/post/create`
- **Permissions**: `Authenticated User`
- **Tags**: `wxapp-post`
- **Summary**: 创建新帖子

### 请求体 (Body)

| 参数 | 类型 | 是否必须 | 描述 |
| --- | --- | --- | --- |
| `openid` | `string` | 是 | 发帖用户的OpenID。 |
| `title` | `string` | 是 | 帖子标题。 |
| `content` | `string` | 是 | 帖子正文内容。 |
| `category_id` | `integer`| 否 | 分类ID，默认为1。 |
| `image` | `string` | 否 | 图片URL列表 (JSON字符串或数组)。 |
| `tag` | `string` | 否 | 标签列表 (JSON字符串或数组)。 |
| `location` | `string` | 否 | 地理位置信息 (JSON字符串或对象)。 |
| `allow_comment`| `boolean`| 否 | 是否允许评论, 默认为 `false`。 |
| `is_public` | `boolean`| 否 | 是否公开, 默认为 `false`。 |
| `phone` | `string` | 否 | 联系电话。 |
| `wechatId` | `string` | 否 | 微信号。 |
| `qqId` | `string` | 否 | QQ号。 |
| `nickname` | `string` | 否 | 用户昵称 (冗余字段)。 |
| `avatar` | `string` | 否 | 用户头像 (冗余字段)。 |
| `bio` | `string` | 否 | 用户简介 (冗余字段)。 |

### 响应 (200 OK)

```json
{
    "code": 200,
    "message": "success",
    "data": {
        "id": 12
    },
    "details": {
        "message": "创建帖子成功"
    },
    "timestamp": "2025-06-21T16:59:26.819038",
    "pagination": null
}
```

---

## 2. 获取帖子详情

- **Endpoint**: `GET /wxapp/post/detail`
- **Permissions**: `Public`
- **Tags**: `wxapp-post`
- **Summary**: 获取帖子详情

### 查询参数 (Query)

| 参数 | 类型 | 是否必须 | 描述 |
| --- | --- | --- | --- |
| `post_id` | `integer` | 是 | 要查询的帖子ID。 |
| `openid` | `string` | 否 | 当前用户的OpenID，用于获取互动状态(是否点赞/收藏/关注作者)。 |

### 响应 (200 OK)

```json
{
    "code": 200,
    "message": "success",
    "data": {
        "id": 12,
        "openid": "oLx8G7ADjzh23EzAJavndryh76rE",
        "nickname": "",
        "avatar": "",
        "phone": null,
        "wechatId": null,
        "qqId": null,
        "bio": "",
        "category_id": 1,
        "title": "My First Post",
        "content": "This is the content of my first post.",
        "image": null,
        "tag": null,
        "location": null,
        "allow_comment": 0,
        "is_public": 0,
        "view_count": 2,
        "like_count": 0,
        "comment_count": 0,
        "favorite_count": 0,
        "status": 1,
        "is_deleted": 0,
        "create_time": "2025-06-21T08:59:26",
        "update_time": "2025-06-21T08:59:33",
        "user_info": {
            "openid": "oLx8G7ADjzh23EzAJavndryh76rE",
            "nickname": "南开小透明",
            "avatar": null,
            "bio": "A new bio for testing.",
            "post_count": 8,
            "follower_count": 1,
            "following_count": 0
        },
        "is_liked": false,
        "is_favorited": false,
        "is_following_author": false
    },
    "details": null,
    "timestamp": "2025-06-21T17:01:21.056087",
    "pagination": null
}
```

---

## 3. 获取帖子列表 (分页)

获取帖子列表，支持按分类、热度、收藏、关注等多种方式筛选和排序。

- **Endpoint**: `GET /wxapp/post/list`
- **Permissions**: `Public`
- **Tags**: `wxapp-post`
- **Summary**: 获取帖子列表

### 查询参数 (Query)

| 参数 | 类型 | 是否必须 | 默认值 | 描述 |
| --- | --- | --- | --- | --- |
| `page` | `integer` | 否 | 1 | 页码。 |
| `page_size` | `integer` | 否 | 10 | 每页数量。 |
| `category_id`| `integer` | 否 | `null` | 按分类ID筛选。 |
| `sort_by` | `string` | 否 | `latest` | 排序方式: `latest` (最新), `popular` (热门)。 |
| `favorite` | `boolean` | 否 | `false` | `true`时，只看当前用户收藏的帖子 (需提供`openid`)。 |
| `following` | `boolean` | 否 | `false` | `true`时，只看当前用户关注的人发的帖子 (需提供`openid`)。 |
| `openid` | `string` | 否 | `null` | 当前登录用户的OpenID。当 `favorite` 或 `following` 为 `true` 时必须提供。 |

### 响应 (200 OK)

```json
{
    "code": 200,
    "message": "success",
    "data": [
        {
            "id": 12,
            "openid": "oLx8G7ADjzh23EzAJavndryh76rE",
            "nickname": "",
            "avatar": "",
            "phone": null,
            "wechatId": null,
            "qqId": null,
            "bio": "",
            "category_id": 1,
            "title": "My First Post",
            "content": "This is the content of my first post.",
            "image": null,
            "tag": null,
            "location": null,
            "allow_comment": 0,
            "is_public": 0,
            "view_count": 1,
            "like_count": 0,
            "comment_count": 0,
            "favorite_count": 0,
            "status": 1,
            "is_deleted": 0,
            "create_time": "2025-06-21T08:59:26",
            "update_time": "2025-06-21T08:59:33",
            "user_info": {
                "openid": "oLx8G7ADjzh23EzAJavndryh76rE",
                "nickname": "南开小透明",
                "avatar": null,
                "bio": "A new bio for testing."
            },
            "is_liked": false,
            "is_favorited": false,
            "is_following_author": false
        }
    ],
    "details": null,
    "timestamp": "2025-06-21T17:01:24.275412",
    "pagination": {
        "total": 8,
        "page": 1,
        "page_size": 10,
        "total_pages": 1,
        "has_more": false
    }
}
```

---

## 4. 搜索帖子 (分页)

根据关键词、分类、点赞数等条件搜索帖子。

- **Endpoint**: `GET /wxapp/post/search`
- **Permissions**: `Public`
- **Tags**: `wxapp-post`
- **Summary**: 搜索帖子

### 查询参数 (Query)

| 参数 | 类型 | 是否必须 | 默认值 | 描述 |
| --- | --- | --- | --- | --- |
| `keywords` | `string` | 否 | `null` | 搜索关键词。 |
| `category_id`| `integer` | 否 | `null` | 分类ID。 |
| `min_likes` | `integer` | 否 | `null` | 最小点赞数。 |
| `max_likes` | `integer` | 否 | `null` | 最大点赞数。 |
| `page` | `integer` | 否 | 1 | 页码。 |
| `limit` | `integer` | 否 | 10 | 每页数量 (同 `page_size`)。 |
| `order_by` | `string` | 否 | `create_time DESC` | 排序方式，格式为 `字段名 排序方向`。 |
| `favorite` | `boolean` | 否 | `false` | `true`时，只看收藏的帖子 (需提供`openid`)。 |
| `following` | `boolean` | 否 | `false` | `true`时，只看关注的人的帖子 (需提供`openid`)。 |
| `openid` | `string` | 否 | `null` | 当前用户OpenID。 |

### 响应 (200 OK)
```json
{
    "code": 200,
    "message": "success",
    "data": [
        {
            "id": 5,
            "title": "测试内容审核",
            "content": "# 测试内容审核\n\n好像吃东西",
            "image": "[]",
            "openid": "oLx8G7ADjzh23EzAJavndryh76rE",
            "nickname": "南开小透明",
            "avatar": "",
            "bio": "A new bio for testing.",
            "phone": "",
            "wechatId": null,
            "qqId": null,
            "view_count": 0,
            "like_count": 0,
            "comment_count": 0,
            "favorite_count": 0,
            "allow_comment": 1,
            "is_public": 1,
            "create_time": "2025-06-12T09:33:08",
            "update_time": "2025-06-12T09:33:08",
            "tag": "[]",
            "category_id": 1,
            "status": 1,
            "user": {
                "openid": "oLx8G7ADjzh23EzAJavndryh76rE",
                "nickname": "南开小透明",
                "avatar": null,
                "bio": "A new bio for testing."
            }
        }
    ],
    "details": {
        "message": "查询帖子列表成功"
    },
    "timestamp": "2025-06-21T17:02:49.142581",
    "pagination": {
        "total": 2,
        "page": 1,
        "page_size": 10,
        "total_pages": 1,
        "has_more": false
    }
}
```

---

## 5. 更新帖子

- **Endpoint**: `POST /wxapp/post/update`
- **Permissions**: `Post Author`
- **Tags**: `wxapp-post`
- **Summary**: 更新帖子

### 请求体 (Body)

包含要更新的帖子字段，必须提供 `post_id` 和 `openid` 用于验证。
```json
{
  "post_id": 12,
  "openid": "oLx8G7ADjzh23EzAJavndryh76rE",
  "title": "My Updated Post Title"
}
```

### 响应 (200 OK)

```json
{
    "code": 200,
    "message": "success",
    "data": null,
    "details": {
        "message": "帖子更新成功"
    },
    "timestamp": "2025-06-21T17:01:34.852770",
    "pagination": null
}
```

---

## 6. 删除帖子

- **Endpoint**: `POST /wxapp/post/delete`
- **Permissions**: `Post Author`
- **Tags**: `wxapp-post`
- **Summary**: 删除帖子

### 请求体 (Body)

| 参数 | 类型 | 是否必须 | 描述 |
| --- | --- | --- | --- |
| `post_id` | `integer` | 是 | 要删除的帖子ID。 |
| `openid` | `string` | 是 | 操作用户的OpenID (需要权限验证)。 |

### 响应 (200 OK)

```json
{
    "code": 200,
    "message": "success",
    "data": null,
    "details": {
        "message": "删除帖子成功"
    },
    "timestamp": "2025-06-21T17:01:45.643835",
    "pagination": null
}
```

---

## 7. 批量获取帖子状态

批量获取帖子的互动状态。

- **Endpoint**: `GET /wxapp/post/status`
- **Permissions**: `Public`
- **Tags**: `wxapp-post`
- **Summary**: 获取帖子状态

### 查询参数 (Query)

| 参数 | 类型 | 是否必须 | 描述 |
| --- | --- | --- | --- |
| `post_id` | `string` | 是 | 帖子ID列表，用逗号分隔 (e.g., "123,124,125")。 |
| `openid` | `string` | 是 | 当前用户的OpenID。 |

### 响应 (200 OK)

```json
{
    "code": 200,
    "message": "success",
    "data": {
        "4": {
            "exist": true,
            "is_liked": false,
            "is_favorited": false,
            "is_commented": false,
            "is_author": true,
            "is_following": false,
            "like_count": 0,
            "favorite_count": 0,
            "comment_count": 0,
            "view_count": 0
        },
        "5": {
            "exist": true,
            "is_liked": false,
            "is_favorited": false,
            "is_commented": false,
            "is_author": true,
            "is_following": false,
            "like_count": 0,
            "favorite_count": 0,
            "comment_count": 0,
            "view_count": 0
        }
    },
    "details": null,
    "timestamp": "2025-06-21T17:02:59.407906",
    "pagination": null
}
``` 