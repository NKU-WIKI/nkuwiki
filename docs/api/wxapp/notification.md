# 微信小程序：通知接口

本文档详细说明了与微信小程序中用户通知功能相关的所有API接口。所有接口都需要用户通过JWT进行认证。

## 1. 获取通知列表

- **Endpoint**: `GET /wxapp/notification/list`
- **Tags**: `wxapp-notification`
- **Summary**: 获取当前用户的通知列表，按时间倒序排列。
- **Permissions**: `Authenticated User`

### 查询参数

| 参数 | 类型 | 是否必须 | 默认值 | 描述 |
| --- | --- | --- | --- | --- |
| `page` | `integer` | 否 | 1 | 页码。 |
| `page_size` | `integer`| 否 | 10 | 每页数量。 |

### 响应 (200 OK)

```json
{
    "code": 200,
    "message": "success",
    "data": [
        {
            "id": 1,
            "title": "有人关注了你",
            "content": "用户 '南开小透明' 刚刚关注了你。",
            "type": "follow",
            "is_read": false,
            "target_id": "user_id_of_sender",
            "target_type": "user",
            "create_time": "2025-07-13T10:00:00",
            "sender_nickname": "南开小透明",
            "sender_avatar": "https://path/to/avatar.png"
        },
        {
            "id": 2,
            "title": "系统通知",
            "content": "欢迎使用NKU-WIKI！",
            "type": "system",
            "is_read": true,
            "target_id": null,
            "target_type": "system",
            "create_time": "2025-07-12T18:00:00",
            "sender_nickname": "系统通知",
            "sender_avatar": null
        }
    ],
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

## 2. 获取未读通知数量

- **Endpoint**: `GET /wxapp/notification/unread-count`
- **Tags**: `wxapp-notification`
- **Summary**: 获取用户未读通知的总数。
- **Permissions**: `Authenticated User`

### 响应 (200 OK)

```json
{
    "code": 200,
    "message": "success",
    "data": {
        "unread_count": 5
    }
}
```

---

## 3. 标记通知为已读

- **Endpoint**: `POST /wxapp/notification/read`
- **Tags**: `wxapp-notification`
- **Summary**: 将一个或多个通知标记为已读。
- **Permissions**: `Authenticated User`

### 请求体

| 参数 | 类型 | 是否必须 | 描述 |
| --- | --- | --- | --- |
| `notification_ids` | `array[integer]` | 是 | 要标记为已读的通知ID列表。 |

**示例:**
```json
{
    "notification_ids": [1, 2, 3]
}
```

### 响应 (200 OK)

```json
{
    "code": 200,
    "message": "操作成功"
}
```
---

## 4. 全部标记为已读

- **Endpoint**: `POST /wxapp/notification/read-all`
- **Tags**: `wxapp-notification`
- **Summary**: 将当前用户的所有未读通知标记为已读。
- **Permissions**: `Authenticated User`

### 请求体

无

### 响应 (200 OK)

```json
{
    "code": 200,
    "message": "所有未读通知已标记为已读"
}
```
---

## 5. 删除通知

- **Endpoint**: `POST /wxapp/notification/delete`
- **Tags**: `wxapp-notification`
- **Summary**: 逻辑删除单条通知。
- **Permissions**: `Authenticated User`

### 请求体

| 参数 | 类型 | 是否必须 | 描述 |
| --- | --- | --- | --- |
| `notification_id` | `integer` | 是 | 要删除的通知ID。 |


**示例:**
```json
{
    "notification_id": 1
}
```

### 响应 (200 OK)

```json
{
    "code": 200,
    "message": "删除成功"
}
```

---

## 6. 获取通知摘要

- **Endpoint**: `GET /wxapp/notification/summary`
- **Tags**: `wxapp-notification`
- **Summary**: 获取未读通知的摘要信息，按类型分类。
- **Permissions**: `Authenticated User`

### 响应 (200 OK)

```json
{
    "code": 200,
    "message": "success",
    "data": {
        "total_unread": 8,
        "unread_by_type": {
            "like": 5,
            "comment": 2,
            "follow": 1
        }
    }
}
``` 