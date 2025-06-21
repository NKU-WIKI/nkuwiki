# 微信小程序：评论接口

本文档详细说明了与微信小程序中评论功能相关的所有API接口。

## 1. 创建评论

发布一条新的评论或者回复另一条评论。

- **Endpoint**: `POST /api/wxapp/comment/create`
- **Tags**: `wxapp-comment`
- **Summary**: 发布评论

### 请求体 (Body)

| 参数 | 类型 | 是否必须 | 描述 |
| --- | --- | --- | --- |
| `resource_id` | `integer` | 是 | 关联资源的ID (例如帖子ID)。 |
| `resource_type` | `string` | 是 | 关联资源的类型 (例如 `post`)。 |
| `content` | `string` | 是 | 评论的具体内容。 |
| `openid` | `string` | 是 | 发表评论用户的OpenID。 |
| `parent_id` | `integer` | 否 | 如果是回复，则为父评论的ID。 |
| `image` | `string` | 否 | 评论中附带的图片URL。 |

### 响应

- **200 OK**:
  ```json
  {
    "code": 200,
    "message": "success",
    "data": {
      "comment_id": 123
    },
    "details": null,
    "timestamp": "..."
  }
  ```
- **404 Not Found**: 如果`openid`对应的用户不存在，或`parent_id`对应的父评论不存在。
- **400 Bad Request**: 如果缺少必要参数。

---

## 2. 获取评论详情

获取单条评论的完整信息，包括其所有嵌套的子评论和当前用户的点赞状态。

- **Endpoint**: `GET /api/wxapp/comment/detail`
- **Tags**: `wxapp-comment`
- **Summary**: 获取单条评论详情

### 查询参数 (Query)

| 参数 | 类型 | 是否必须 | 描述 |
| --- | --- | --- | --- |
| `comment_id` | `integer` | 是 | 要查询的评论ID。 |
| `openid` | `string` | 是 | 当前用户的OpenID，用于判断点赞状态。 |

### 响应 (200 OK)

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 123,
    "content": "这是一条评论。",
    "openid": "user_abc",
    "nickname": "用户昵称",
    "avatar": "...",
    "like_count": 10,
    "reply_count": 2,
    "create_time": "...",
    "liked": true,
    "children": [
      {
        "id": 124,
        "content": "这是对评论的回复。",
        "openid": "user_xyz",
        "nickname": "回复者",
        "avatar": "...",
        "liked": false,
        "children": []
      }
    ]
  },
  "details": null,
  "timestamp": "..."
}
```

---

## 3. 获取评论的回复列表 (分页)

分页获取指定评论下的直接回复。

- **Endpoint**: `GET /api/wxapp/comment/replies`
- **Tags**: `wxapp-comment`
- **Summary**: 获取单条评论的回复列表

### 查询参数 (Query)

| 参数 | 类型 | 是否必须 | 默认值 | 描述 |
| --- | --- | --- | --- | --- |
| `comment_id` | `integer` | 是 | | 父评论的ID。 |
| `openid` | `string` | 是 | | 当前用户的OpenID。 |
| `page` | `integer` | 否 | 1 | 页码。 |
| `page_size` | `integer` | 否 | 5 | 每页数量。 |

### 响应 (200 OK)

```json
{
  "code": 200,
  "message": "success",
  "data": [
    {
      "id": 124,
      "content": "回复内容...",
      "openid": "user_xyz",
      "nickname": "回复者",
      "avatar": "...",
      "is_liked": false
    }
  ],
  "pagination": {
    "total": 20,
    "page": 1,
    "page_size": 5,
    "total_pages": 4,
    "has_more": true
  },
  "details": null,
  "timestamp": "..."
}
```

---

## 4. 获取资源下的评论列表 (分页)

分页获取某个资源（如帖子）下的顶级评论。

- **Endpoint**: `GET /api/wxapp/comment/list`
- **Tags**: `wxapp-comment`
- **Summary**: 获取评论列表

### 查询参数 (Query)

| 参数 | 类型 | 是否必须 | 默认值 | 描述 |
| --- | --- | --- | --- | --- |
| `post_id` | `integer` | 是 | | 帖子ID。 |
| `page` | `integer` | 否 | 1 | 页码。 |
| `page_size` | `integer` | 否 | 10 | 每页数量。 |

### 响应 (200 OK)
与 `/replies` 接口的响应结构类似，包含 `data` 和 `pagination` 字段。

---

## 5. 获取用户的评论列表 (分页)

分页获取指定用户发表的所有评论。

- **Endpoint**: `GET /api/wxapp/comment/user`
- **Tags**: `wxapp-comment`
- **Summary**: 获取用户的评论列表

### 查询参数 (Query)

| 参数 | 类型 | 是否必须 | 默认值 | 描述 |
| --- | --- | --- | --- | --- |
| `target_openid` | `string` | 是 | | 目标用户的OpenID。 |
| `page` | `integer` | 否 | 1 | 页码。 |
| `page_size` | `integer` | 否 | 10 | 每页数量。 |

### 响应 (200 OK)
与 `/replies` 接口的响应结构类似，包含 `data` 和 `pagination` 字段。

---

## 6. 更新评论

更新一条已存在的评论内容。

- **Endpoint**: `POST /api/wxapp/comment/update`
- **Tags**: `wxapp-comment`
- **Summary**: 更新评论

### 请求体 (Body)

| 参数 | 类型 | 是否必须 | 描述 |
| --- | --- | --- | --- |
| `comment_id` | `integer` | 是 | 要更新的评论ID。 |
| `content` | `string` | 是 | 新的评论内容。 |
| `openid` | `string` | 是 | 操作用户的OpenID (需要权限验证)。 |

### 响应 (200 OK)

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "updated": true
  }
}
```

---

## 7. 删除评论

删除一条评论。

- **Endpoint**: `POST /api/wxapp/comment/delete`
- **Tags**: `wxapp-comment`
- **Summary**: 删除评论

### 请求体 (Body)

| 参数 | 类型 | 是否必须 | 描述 |
| --- | --- | --- | --- |
| `comment_id` | `integer` | 是 | 要删除的评论ID。 |
| `openid` | `string` | 是 | 操作用户的OpenID (需要权限验证)。 |

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

## 8. 批量获取评论状态

批量获取多条评论的状态，主要用于判断当前用户是否对这些评论点了赞。

- **Endpoint**: `GET /api/wxapp/comment/status`
- **Tags**: `wxapp-comment`
- **Summary**: 获取评论状态

### 查询参数 (Query)

| 参数 | 类型 | 是否必须 | 描述 |
| --- | --- | --- | --- |
| `comment_ids` | `string` | 是 | 评论ID列表，用逗号分隔 (e.g., "123,124,125")。 |
| `openid` | `string` | 是 | 当前用户的OpenID。 |

### 响应 (200 OK)

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "123": { "is_liked": true },
    "124": { "is_liked": false },
    "125": { "is_liked": true }
  }
}
``` 