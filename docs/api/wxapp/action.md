# 微信小程序：通用互动接口

本文档详细说明了微信小程序中用于处理点赞、收藏、关注等通用互动行为的API接口。

## 1. 通用切换操作 (Toggle Action)

此接口用于执行所有状态切换类的操作，例如：点赞/取消点赞、收藏/取消收藏、关注/取消关注。

- **Endpoint**: `POST /api/wxapp/action/toggle`
- **Tags**: `wxapp-action`
- **Summary**: 通用点赞/收藏/关注操作

### 请求体 (Body)

| 参数 | 类型 | 是否必须 | 可选值 | 描述 |
| --- | --- | --- | --- | --- |
| `target_id` | `integer` or `string` | 是 | | 互动目标的ID。如果 `target_type` 是 `user`，则为用户的 `openid` (string)；否则为 `id` (integer)。 |
| `target_type` | `string` | 是 | `post`, `comment`, `user` | 互动目标的类型。 |
| `action_type` | `string` | 是 | `like`, `favorite`, `follow` | 互动的类型。 |
| `openid` | `string` | 是 | | 执行此操作的用户的OpenID。 |

### 行为逻辑

1.  **检查记录**: 服务器会检查 `wxapp_action` 表中是否存在匹配 `(openid, action_type, target_id, target_type)` 的记录。
2.  **切换状态**:
    -   如果**不存在**记录，则创建一条新记录，表示行为被激活 (例如，用户点了赞)。
    -   如果**存在**记录，则删除该记录，表示行为被取消 (例如，用户取消了点赞)。
3.  **更新计数**:
    -   操作成功后，会自动更新相关表的计数字段。例如，对 `post` 进行 `like` 操作会增/减 `wxapp_post` 表的 `like_count` 字段。

### 响应

- **200 OK**:
  ```json
  {
    "code": 200,
    "message": "success",
    "data": {
      "is_active": true
    },
    "details": null,
    "timestamp": "..."
  }
  ```
  - `is_active`: `true` 表示操作后行为是激活状态 (已点赞/已收藏/已关注)，`false` 表示是未激活状态。

- **404 Not Found**: 如果 `target_id` 对应的资源不存在。
- **400 Bad Request**: 如果缺少必要参数或参数值不合法 (如 `target_type` 不支持)。

## 互动接口

本模块包含用户之间的互动操作，如评论、点赞、收藏、关注等。

### 1. 创建评论

**接口**：`POST /api/wxapp/action/comment`

**功能描述**：在一个资源（如帖子或知识）下创建新的评论或回复。

**请求体**:

| 参数 | 类型 | 是否必须 | 描述 |
| --- | --- | --- | --- |
| `resource_id` | `integer` | 是 | 评论所属资源的ID，例如帖子ID。 |
| `resource_type` | `string` | 是 | 资源类型，合法值为 `post` 或 `knowledge`。 |
| `content` | `string` | 是 | 评论的具体内容。 |
| `openid` | `string` | 是 | 发表评论的用户的OpenID。 |
| `parent_id` | `integer` | 否 | 如果是回复某条评论，则为父评论的ID。 |
| `image` | `array` | 否 | 评论中包含的图片URL列表。 |

**成功响应示例**:

```json
{
    "code": 200,
    "message": "success",
    "data": {
        "id": 1,
        "resource_id": 1,
        "resource_type": "post",
        "parent_id": null,
        "openid": "oLx8G7ADjzh23EzAJavndryh76rE",
        "nickname": null,
        "avatar": null,
        "content": "这是一个测试评论",
        "image": "[]",
        "like_count": 0,
        "reply_count": 0,
        "status": 1,
        "is_deleted": 0,
        "create_time": "2025-06-21T06:11:20",
        "update_time": "2025-06-21T06:11:20"
    },
    "details": null,
    "timestamp": "2025-06-21T14:11:20.957533",
    "pagination": null
}
```

**错误响应示例**:

*   **参数缺失**:
    ```json
    {
        "code": 400,
        "message": "缺少必要参数: resource_id"
    }
    ```
*   **资源未找到**:
    ```json
    {
        "code": 404,
        "message": "资源(post) not found"
    }
    ```

### 2. 点赞/取消点赞评论

**接口**：`POST /api/wxapp/action/comment/like`

**功能描述**：对指定ID的评论进行点赞。如果用户已点赞，则会取消点赞。这是一个切换（toggle）操作。

**请求体**:

| 参数 | 类型 | 是否必须 | 描述 |
| --- | --- | --- | --- |
| `comment_id` | `integer` | 是 | 被点赞的评论的ID。 |
| `openid` | `string` | 是 | 执行点赞操作的用户的OpenID。 |

**成功响应示例 (点赞)**:

```json
{
    "code": 200,
    "message": "success",
    "data": {
        "success": true,
        "status": "liked",
        "is_liked": true,
        "like_count": 1
    },
    "details": {
        "message": "Like succeeded"
    },
    "timestamp": "2025-06-21T14:19:46.883925",
    "pagination": null
}
```

**成功响应示例 (取消点赞)**:

```json
{
    "code": 200,
    "message": "success",
    "data": {
        "success": true,
        "status": "unliked",
        "is_unliked": false,
        "like_count": 0
    },
    "details": {
        "message": "Like cancelled"
    },
    "timestamp": "2025-06-21T14:20:00.000000",
    "pagination": null
}
```

### 3. 点赞/取消点赞帖子

**接口**：`POST /api/wxapp/post/like`

**功能描述**：对指定ID的帖子进行点赞。如果用户已点赞，则会取消点赞。这是一个切换（toggle）操作。

**请求体**:

| 参数 | 类型 | 是否必须 | 描述 |
| --- | --- | --- | --- |
| `post_id` | `integer` | 是 | 被点赞的帖子的ID。 |
| `openid` | `string` | 是 | 执行点赞操作的用户的OpenID。 |

**成功响应示例 (点赞)**:

```json
{
    "code": 200,
    "message": "success",
    "data": {
        "success": true,
        "status": "liked",
        "is_liked": true,
        "like_count": 12 
    },
    "details": {
        "message": "Like succeeded"
    },
    "timestamp": "2025-06-21T14:30:00.000000",
    "pagination": null
}
```

### 4. 收藏/取消收藏帖子

**接口**：`POST /api/wxapp/post/favorite`

**功能描述**：对指定ID的帖子进行收藏。如果用户已收藏，则会取消收藏。这是一个切换（toggle）操作。

**请求体**:

| 参数 | 类型 | 是否必须 | 描述 |
| --- | --- | --- | --- |
| `post_id` | `integer` | 是 | 被收藏的帖子的ID。 |
| `openid` | `string` | 是 | 执行收藏操作的用户的OpenID。 |

**成功响应示例 (收藏)**:

```json
{
    "code": 200,
    "message": "success",
    "data": {
        "success": true,
        "status": "favorited",
        "is_favorited": true,
        "favorite_count": 5
    },
    "details": {
        "message": "Favorite succeeded"
    },
    "timestamp": "2025-06-21T14:35:00.000000",
    "pagination": null
}
```

### 1.4 获取操作状态

**接口**: `GET /api/wxapp/action/status`
**描述**: 批量获取用户对多个目标（帖子/评论）的操作状态（如是否点赞、收藏）
**查询参数**:

| 参数名 | 类型 | 是否必填 | 描述 |
| --- | --- | --- | --- |
| `openid` | `string` | 是 | 用户的 openid |
| `target_ids` | `string` | 是 | 目标ID列表，用逗号分隔，如 "1,2,3" |
| `target_type` | `string` | 是 | 目标类型，`post` 或 `comment` |
| `action_type` | `string` | 是 | 操作类型，`like` 或 `favorite` |

**响应**:

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "1": true,
    "2": false,
    "3": true
  },
  "details": null,
  "pagination": null,
  "timestamp": "2023-01-01 12:00:00"
}
```

## 二、评论接口

### 2.1 获取单条评论详情

**接口**：`GET /api/wxapp/comment/detail`  
**描述**：获取单条评论的完整信息，包括其所有层级的子评论（回复）。  
**查询参数**：

| 参数名     | 类型   | 是否必填 | 描述                               |
| ---------- | ------ | -------- | ---------------------------------- |
| `comment_id` | `string` | 是       | 要查询的评论的ID。               |
| `openid`     | `string` | 是       | 当前用户的 `openid`，用于判断点赞状态。 |

**成功响应**：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 2,
    "resource_id": 1,
    "resource_type": "post",
    "parent_id": null,
    "openid": "oLx8G7ADjzh23EzAJavndryh76rE",
    "content": "这是一条自动生成的父评论，用于测试。",
    "image": null,
    "like_count": 0,
    "reply_count": 0,
    "status": 1,
    "is_deleted": 0,
    "create_time": "2025-06-21T07:47:04",
    "update_time": "2025-06-21T07:47:04",
    "liked": false,
    "nickname": "南开小透明",
    "avatar": null,
    "bio": "你好，nkuwiki！",
    "children": [
      {
        "id": 3,
        "resource_id": 1,
        "resource_type": "post",
        "parent_id": 2,
        "openid": "oLx8G7ADjzh23EzAJavndryh76rE",
        "content": "这是对父评论的第一条回复。",
        "image": null,
        "like_count": 0,
        "reply_count": 0,
        "status": 1,
        "is_deleted": 0,
        "create_time": "2025-06-21T07:47:04",
        "update_time": "2025-06-21T07:47:04",
        "nickname": "南开小透明",
        "avatar": null,
        "bio": "你好，nkuwiki！",
        "is_liked": false,
        "parent_comment_count": 0,
        "children": [
          {
            "id": 5,
            "resource_id": 1,
            "resource_type": "post",
            "parent_id": 3,
            "openid": "oLx8G7ADjzh23EzAJavndryh76rE",
            "content": "这是一条孙子辈的评论，回复第一条子评论。",
            "image": null,
            "like_count": 0,
            "reply_count": 0,
            "status": 1,
            "is_deleted": 0,
            "create_time": "2025-06-21T07:47:04",
            "update_time": "2025-06-21T07:47:04",
            "nickname": "南开小透明",
            "avatar": null,
            "bio": "你好，nkuwiki！",
            "is_liked": false,
            "parent_comment_count": 0
          }
        ]
      },
      {
        "id": 4,
        "resource_id": 1,
        "resource_type": "post",
        "parent_id": 2,
        "openid": "oLx8G7ADjzh23EzAJavndryh76rE",
        "content": "这是第二条回复。",
        "image": null,
        "like_count": 0,
        "reply_count": 0,
        "status": 1,
        "is_deleted": 0,
        "create_time": "2025-06-21T07:47:04",
        "update_time": "2025-06-21T07:47:04",
        "nickname": "南开小透明",
        "avatar": null,
        "bio": "你好，nkuwiki！",
        "is_liked": false,
        "parent_comment_count": 1
      }
    ]
  },
  "details": null,
  "pagination": null,
  "timestamp": "2025-06-21T15:48:59.563235"
}
```

**错误响应**：

- `400 Bad Request`：如果 `comment_id` 或 `openid` 缺失或格式不正确。
- `404 Not Found`：如果提供的 `comment_id` 不存在。
- `500 Internal Server Error`：如果服务器内部发生错误。 

### 2.2 获取评论的回复列表

**接口**：`GET /api/wxapp/comment/replies`  
**描述**：分页获取单条评论的直接回复列表。  
**查询参数**：

| 参数名 | 类型 | 是否必填 | 描述 |
| --- | --- | --- | --- |
| `comment_id` | `string` | 是 | 要查询的父评论的ID。 |
| `page` | `integer`| 否 | 页码，从1开始，默认为1。 |
| `page_size` | `integer`| 否 | 每页数量，默认为5。 |
| `openid` | `string` | 否 | 当前用户的 `openid`，用于判断点赞状态。 |

**成功响应**：

```json
{
   "code": 200,
   "data": [
      {
         "id": 3,
         "content": "这是对父评论的第一条回复。",
         "create_time": "2025-06-21T07:47:04",
         "update_time": "2025-06-21T07:47:04",
         "is_deleted": 0,
         "like_count": 0,
         "nickname": "南开小透明",
         "openid": "oLx8G7ADjzh23EzAJavndryh76rE",
         "parent_id": 2,
         "reply_count": 0,
         "resource_id": 1,
         "resource_type": "post",
         "status": 1,
         "avatar": null,
         "bio": "你好，nkuwiki！",
         "is_liked": false
      }
   ],
   "details": null,
   "message": "success",
   "pagination": {
      "has_more": true,
      "page": 1,
      "page_size": 1,
      "total": 2,
      "total_pages": 2
   },
   "timestamp": "2025-06-21T15:52:37.646832"
}
``` 