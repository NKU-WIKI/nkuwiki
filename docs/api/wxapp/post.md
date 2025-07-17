# 微信小程序：帖子接口

本文档详细说明了与微信小程序中帖子功能相关的所有API接口。

## 1. 创建新帖子

- **Endpoint**: `POST /wxapp/post/create`
- **Permissions**: `Authenticated User` (需要JWT)
- **Tags**: `wxapp-post`
- **Summary**: 创建新帖子

### 请求体 (Body)

| 参数 | 类型 | 是否必须 | 描述 |
| --- | --- | --- | --- |
| `title` | `string` | 是 | 帖子标题。 |
| `content` | `string` | 是 | 帖子正文内容。 |
| `category_id` | `integer`| 否 | 分类ID，默认为1。 |
| `image` | `array` | 否 | 图片URL列表, e.g., `["url1", "url2"]`。 |
| `tag` | `array` | 否 | 标签列表, e.g., `["tag1", "tag2"]`。 |
| `location` | `object` | 否 | 地理位置信息。 |
| `allow_comment`| `boolean`| 否 | 是否允许评论, 默认为 `true`。 |
| `is_public` | `boolean`| 否 | 是否公开, 默认为 `true`。 |
| `phone` | `string` | 否 | 联系电话。 |
| `wechatId` | `string` | 否 | 微信号。 |
| `qqId` | `string` | 否 | QQ号。 |

### 响应 (200 OK)

```json
{
    "code": 200,
    "message": "success",
    "data": {
        "id": 123
    }
}
```

---

## 2. 获取帖子详情

- **Endpoint**: `GET /wxapp/post/detail`
- **Permissions**: `Optional Auth` (公开可访问，提供JWT可获取互动状态)
- **Tags**: `wxapp-post`
- **Summary**: 获取帖子详情

### 查询参数 (Query)

| 参数 | 类型 | 是否必须 | 描述 |
| --- | --- | --- | --- |
| `post_id` | `integer` | 是 | 要查询的帖子ID。 |

### 响应 (200 OK)

响应中的 `is_liked`, `is_favorited`, `is_following_author` 字段仅在用户通过JWT认证后才会准确返回。

```json
{
    "code": 200,
    "message": "success",
    "data": {
        "id": 12,
        "openid": "oLx8G7ADjzh23EzAJavndryh76rE",
        "nickname": "南开小透明",
        "avatar": "...",
        "bio": "A new bio for testing.",
        "category_id": 1,
        "title": "My First Post",
        "content": "This is the content of my first post.",
        "image": "[\"url1\"]",
        "tag": "[\"tag1\"]",
        "location": "{\"name\": \"Nankai University\"}",
        "allow_comment": true,
        "is_public": true,
        "view_count": 2,
        "like_count": 0,
        "comment_count": 0,
        "favorite_count": 0,
        "create_time": "2025-06-21T08:59:26",
        "update_time": "2025-06-21T08:59:33",
        "post_count": 8,
        "follower_count": 1,
        "following_count": 0,
        "is_liked": false,
        "is_favorited": false,
        "is_following_author": false
    }
}
```

---

## 3. 获取帖子列表 (分页)

获取帖子列表，支持按分类、热度、收藏、关注等多种方式筛选和排序。

- **Endpoint**: `GET /wxapp/post/list`
- **Permissions**: `Optional Auth`
- **Tags**: `wxapp-post`
- **Summary**: 获取帖子列表

### 查询参数 (Query)

| 参数 | 类型 | 是否必须 | 默认值 | 描述 |
| --- | --- | --- | --- | --- |
| `page` | `integer` | 否 | 1 | 页码。 |
| `page_size` | `integer` | 否 | 10 | 每页数量。 |
| `category_id`| `integer` | 否 | `null` | 按分类ID筛选。 |
| `sort_by` | `string` | 否 | `latest` | 排序方式: `latest` (最新), `popular` (热门)。 |
| `favorite` | `boolean` | 否 | `false` | `true`时，只看当前用户收藏的帖子 (**需要JWT, 此功能尚未完全实现**)。 |
| `following` | `boolean` | 否 | `false` | `true`时，只看当前用户关注的人发的帖子 (**需要JWT, 此功能尚未完全实现**)。 |

### 响应 (200 OK)

```json
{
    "code": 200,
    "message": "success",
    "data": [
        {
            "id": 12,
            "user_id": 1,
            "title": "My First Post",
            "content": "This is the content of my first post.",
            "image": null,
            "tag": null,
            "location": null,
            "view_count": 1,
            "like_count": 0,
            "comment_count": 0,
            "favorite_count": 0,
            "create_time": "2025-06-21T08:59:26",
            "author_info": {
                "id": 1,
                "nickname": "南开小透明",
                "avatar": "...",
                "bio": "A developer"
            },
            "is_liked": false,
            "is_favorited": false,
            "is_following_author": false
        }
    ],
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

根据关键词等条件搜索帖子。

- **Endpoint**: `GET /wxapp/post/search`
- **Permissions**: `Optional Auth`
- **Tags**: `wxapp-post`
- **Summary**: 搜索帖子

### 查询参数 (Query)

| 参数 | 类型 | 是否必须 | 默认值 | 描述 |
| --- | --- | --- | --- | --- |
| `keywords` | `string` | 否 | `null` | 搜索关键词。 |
| `page` | `integer` | 否 | 1 | 页码。 |
| `page_size` | `integer` | 否 | 10 | 每页数量。 |
| `favorite` | `boolean` | 否 | `false` | `true`时，在收藏的帖子中搜索 (**需要JWT**)。 |
| `following` | `boolean` | 否 | `false` | `true`时，在关注的人的帖子中搜索 (**需要JWT**)。 |


### 响应 (200 OK)

与 `GET /wxapp/post/list` 响应结构相同。

---

## 5. 更新帖子

- **Endpoint**: `POST /wxapp/post/update`
- **Permissions**: `Post Author` (需要JWT)
- **Tags**: `wxapp-post`
- **Summary**: 更新帖子

### 请求体 (Body)

| 参数 | 类型 | 是否必须 | 描述 |
| --- | --- | --- | --- |
| `id` | `integer` | 是 | 要更新的帖子ID。 |
| `title` | `string` | 否 | 新的帖子标题。 |
| `content` | `string` | 否 | 新的帖子正文内容。 |
| `category_id` | `integer`| 否 | 新的分类ID。 |
| ... | | | (其他可更新字段同创建接口) |

### 响应 (200 OK)

```json
{
    "code": 200,
    "message": "success",
    "data": {
        "id": 1,
        "user_id": 1,
        "title": "一个被更新的测试帖子...",
        "content": "内容已被更新。",
        "..." : "..."
    },
    "details": {
      "message": "帖子更新成功"
    }
}
```

---

## 6. 删除帖子

- **Endpoint**: `POST /wxapp/post/delete`
- **Permissions**: `Post Author` (需要JWT)
- **Tags**: `wxapp-post`
- **Summary**: 删除帖子

### 请求体 (Body)

| 参数 | 类型 | 是否必须 | 描述 |
| --- | --- | --- | --- |
| `id` | `integer` | 是 | 要删除的帖子ID。 |

### 响应 (200 OK)

```json
{
    "code": 200,
    "message": "success",
    "data": {
        "deleted": true
    }
}
```

---