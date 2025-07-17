# 微信小程序：评论接口

本文档详细说明了与微信小程序中评论功能相关的所有API接口。

## 1. 创建评论

发布一条新的评论或者回复另一条评论。

- **Endpoint**: `POST /wxapp/comment/create`
- **Tags**: `wxapp-comment`
- **Summary**: 发布评论
- **Permissions**: `Authenticated User` (需要JWT)

### 请求体 (Body)

| 参数 | 类型 | 是否必须 | 描述 |
| --- | --- | --- | --- |
| `resource_id` | `integer` | 是 | 关联资源的ID (例如帖子ID)。 |
| `resource_type` | `string` | 是 | 关联资源的类型 (例如 `post`)。 |
| `content` | `string` | 是 | 评论的具体内容。 |
| `parent_id` | `integer` | 否 | 如果是回复，则为父评论的ID。 |
| `image` | `array` | 否 | 评论中包含的图片URL列表。 e.g. `["url1"]` |

### 响应

- **200 OK**:
  ```json
  {
    "code": 200,
    "message": "success",
    "data": {
      "id": 123
    },
    "details": {
        "message": "发布成功"
    }
  }
  ```
- **401 Unauthorized**: JWT无效或缺失。
- **400 Bad Request**: 如果缺少必要参数。

---

## 2. 获取评论详情

获取单条评论的完整信息，包括其所有嵌套的子评论和当前用户的点赞状态。

- **Endpoint**: `GET /wxapp/comment/detail`
- **Tags**: `wxapp-comment`
- **Summary**: 获取单条评论详情
- **Permissions**: `Authenticated User` (需要JWT)

### 查询参数 (Query)

| 参数 | 类型 | 是否必须 | 描述 |
| --- | --- | --- | --- |
| `comment_id` | `integer` | 是 | 要查询的评论ID。 |

### 响应 (200 OK)

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 123,
    "content": "这是一条评论。",
    "nickname": "用户昵称",
    "avatar": "...",
    "bio": "用户简介",
    "like_count": 10,
    "reply_count": 2,
    "create_time": "...",
    "liked": true,
    "children": [
      {
        "id": 124,
        "content": "这是对评论的回复。",
        "nickname": "回复者",
        "avatar": "...",
        "liked": false,
        "children": []
      }
    ]
  }
}
```

---

## 3. 获取评论的回复列表 (分页)

分页获取指定评论下的直接回复。

- **Endpoint**: `GET /wxapp/comment/replies`
- **Tags**: `wxapp-comment`
- **Summary**: 获取单条评论的回复列表
- **Permissions**: `Optional Auth` (公开可访问，提供JWT可获取点赞状态)

### 查询参数 (Query)

| 参数 | 类型 | 是否必须 | 默认值 | 描述 |
| --- | --- | --- | --- | --- |
| `comment_id` | `integer` | 是 | | 父评论的ID。 |
| `page` | `integer` | 否 | 1 | 页码。 |
| `page_size` | `integer` | 否 | 5 | 每页数量。 |

### 响应 (200 OK)

响应中的 `is_liked` 字段仅在用户通过JWT认证后才会准确返回。

```json
{
  "code": 200,
  "message": "success",
  "data": [
    {
      "id": 124,
      "content": "回复内容...",
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
  }
}
```

---

## 4. 获取资源下的评论列表 (分页)

分页获取某个资源（如帖子）下的顶级评论。

- **Endpoint**: `GET /wxapp/comment/list`
- **Tags**: `wxapp-comment`
- **Summary**: 获取评论列表
- **Permissions**: `Optional Auth` (公开可访问，提供JWT可获取点赞状态)

### 查询参数 (Query)

| 参数 | 类型 | 是否必须 | 默认值 | 描述 |
| --- | --- | --- | --- | --- |
| `resource_id` | `integer` | 是 | | 资源ID (例如帖子ID)。 |
| `resource_type` | `string` | 否 | `post` | 资源类型。 |
| `page` | `integer` | 否 | 1 | 页码。 |
| `page_size` | `integer` | 否 | 10 | 每页数量。 |

### 响应 (200 OK)

```json
{
    "code": 200,
    "message": "success",
    "data": [
        {
            "id": 1,
            "resource_id": 2,
            "resource_type": "post",
            "parent_id": null,
            "user_id": 1,
            "nickname": "南开小超人",
            "avatar": "...",
            "content": "这是一条对帖子的测试评论。",
            "image": null,
            "like_count": 0,
            "reply_count": 0,
            "create_time": "2025-07-13T03:32:42",
            "bio": "这是我的新简介！",
            "is_liked": false,
            "children": []
        }
    ],
    "pagination": {
        "total": 1,
        "page": 1,
        "page_size": 10,
        "total_pages": 1,
        "has_more": false
    }
}
```

---

## 5. 更新评论

- **Endpoint**: `POST /wxapp/comment/update`
- **Tags**: `wxapp-comment`
- **Summary**: 更新评论
- **Permissions**: `Comment Author` (需要JWT)

### 请求体 (Body)

| 参数 | 类型 | 是否必须 | 描述 |
| --- | --- | --- | --- |
| `id` | `integer` | 是 | 要更新的评论ID。 |
| `content` | `string` | 是 | 新的评论内容。 |

### 响应

- **200 OK**:
  ```json
  {
    "code": 200,
    "message": "success",
    "details": { "message": "更新成功" }
  }
  ```

---

## 6. 删除评论

- **Endpoint**: `POST /wxapp/comment/delete`
- **Tags**: `wxapp-comment`
- **Summary**: 删除评论
- **Permissions**: `Comment Author` (需要JWT)

### 请求体 (Body)

| 参数 | 类型 | 是否必须 | 描述 |
| --- | --- | --- | --- |
| `id` | `integer` | 是 | 要删除的评论ID。 |

### 响应

- **200 OK**:
  ```json
  {
    "code": 200,
    "message": "success",
    "details": { "message": "删除成功" }
  }
  ```

---

## 7. 获取用户的评论列表

- **Endpoint**: `GET /wxapp/comment/user`
- **Tags**: `wxapp-comment`
- **Summary**: 获取指定用户的评论列表
- **Permissions**: `Optional Auth`

### 查询参数 (Query)

| 参数 | 类型 | 是否必须 | 描述 |
| --- | --- | --- | --- |
| `user_id` | `integer` | 是 | 目标用户的ID。 |
| `page` | `integer` | 否 | 页码, 默认为1。 |
| `page_size` | `integer` | 否 | 每页数量, 默认为10。 |

### 响应

响应结构与 `GET /list` 类似。

---

## 8. 批量获取评论状态

- **Endpoint**: `GET /wxapp/comment/status`
- **Tags**: `wxapp-comment`
- **Summary**: 批量获取评论的点赞状态
- **Permissions**: `Authenticated User` (需要JWT)

### 查询参数 (Query)

| 参数 | 类型 | 是否必须 | 描述 |
| --- | --- | --- | --- |
| `comment_id` | `string` | 是 | 评论ID列表，以逗号分隔，例如 `1,2,3`。 |

### 响应

```json
{
    "code": 200,
    "message": "success",
    "data": {
        "1": true,
        "2": false,
        "3": true
    }
}
```
