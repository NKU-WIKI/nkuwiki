# 微信小程序：通知接口

本文档详细说明了与微信小程序中用户通知功能相关的所有API接口。

## 1. 获取通知列表

- **Endpoint**: `GET /wxapp/notification/list`
- **Tags**: `wxapp-notification`
- **Summary**: 获取通知列表，并将未读通知标记为已读。
- **Permissions**: `Authenticated User`

### 查询参数 (Query)

| 参数 | 类型 | 是否必须 | 默认值 | 描述 |
| --- | --- | --- | --- | --- |
| `openid` | `string` | 是 | `null` | 要查询通知的用户的OpenID。 |
| `page` | `integer` | 否 | 1 | 页码。 |
| `page_size` | `integer`| 否 | 10 | 每页数量。 |

### 响应 (200 OK)

```json
{
    "code": 200,
    "message": "success",
    "data": [
        {
            "id": 6,
            "openid": "oLx8G7ADjzh23EzAJavndryh76rE",
            "title": null,
            "content": "关注了你",
            "type": "follow",
            "is_read": 1,
            "sender": "{\"avatar\": \"avatar_url_3\", \"openid\": \"test_user_003\", \"nickname\": \"测试用户3\"}",
            "target_id": "test_user_003",
            "target_type": "user",
            "extra_data": null,
            "create_time": "2025-06-21T09:05:02",
            "update_time": "2025-06-21T09:05:02",
            "status": 1
        }
    ],
    "details": null,
    "timestamp": "2025-06-21T17:05:49.306481",
    "pagination": {
        "total": 3,
        "page": 1,
        "page_size": 10,
        "total_pages": 1,
        "has_more": false
    }
}
```
> **注意**: 调用此接口会把返回列表中的未读通知自动标记为已读。

---

## 2. 获取通知详情

- **Endpoint**: `GET /wxapp/notification/detail`
- **Tags**: `wxapp-notification`
- **Summary**: 获取单条通知详情，并将其标记为已读。
- **Permissions**: `Authenticated User`

### 查询参数 (Query)

| 参数 | 类型 | 是否必须 | 描述 |
| --- | --- | --- | --- |
| `notification_id` | `integer` | 是 | 要查询的通知ID。 |
| `openid` | `string` | 是 | 当前用户的OpenID，用于权限验证。 |

### 响应 (200 OK)

```json
{
    "code": 200,
    "message": "success",
    "data": {
        "id": 4,
        "openid": "oLx8G7ADjzh23EzAJavndryh76rE",
        "title": null,
        "content": "赞了你的帖子",
        "type": "like",
        "is_read": 1,
        "sender": "{\"avatar\": \"avatar_url_1\", \"openid\": \"test_user_001\", \"nickname\": \"测试用户1\"}",
        "target_id": 1,
        "target_type": "post",
        "extra_data": null,
        "create_time": "2025-06-21T09:05:02",
        "update_time": "2025-06-21T09:05:08",
        "status": 1
    },
    "details": null,
    "timestamp": "2025-06-21T17:05:57.073199",
    "pagination": null
}
```

---

## 3. 获取未读通知数量

- **Endpoint**: `GET /wxapp/notification/count`
- **Tags**: `wxapp-notification`
- **Summary**: 获取用户未读通知的总数。
- **Permissions**: `Authenticated User`

### 查询参数 (Query)

| 参数 | 类型 | 是否必须 | 描述 |
| --- | --- | --- | --- |
| `openid` | `string` | 是 | 要查询的用户的OpenID。 |

### 响应 (200 OK)

```json
{
    "code": 200,
    "message": "success",
    "data": {
        "unread_count": 0
    },
    "details": null,
    "timestamp": "2025-06-21T17:06:07.034283",
    "pagination": null
}
```

---

## 4. 批量标记通知为已读

- **Endpoint**: `POST /wxapp/notification/read`
- **Tags**: `wxapp-notification`
- **Summary**: 将一个或多个通知标记为已读。
- **Permissions**: `Authenticated User`

### 请求体 (Body)

```json
{
    "notification_ids": [4, 5],
    "openid": "oLx8G7ADjzh23EzAJavndryh76rE"
}
```

### 响应 (200 OK)

```json
{
    "code": 200,
    "message": "操作成功",
    "data": null,
    "details": null,
    "timestamp": "2025-06-21T17:06:21.238797",
    "pagination": null
}
```

---

## 5. 删除通知

- **Endpoint**: `POST /wxapp/notification/delete`
- **Tags**: `wxapp-notification`
- **Summary**: 删除单条通知。
- **Permissions**: `Authenticated User`

### 请求体 (Body)

```json
{
    "notification_id": 1,
    "openid": "oLx8G7ADjzh23EzAJavndryh76rE"
}
```

### 响应 (200 OK)

```json
{
    "code": 200,
    "message": "删除成功",
    "data": null,
    "details": null,
    "timestamp": "2025-06-21T17:10:31.491047",
    "pagination": null
}
```

---

## 6. 获取通知摘要

- **Endpoint**: `GET /wxapp/notification/summary`
- **Tags**: `wxapp-notification`
- **Summary**: 获取未读通知的摘要信息。
- **Permissions**: `Authenticated User`

### 查询参数 (Query)

| 参数 | 类型 | 是否必须 | 描述 |
| --- | --- | --- | --- |
| `openid` | `string` | 是 | 要查询的用户的OpenID。 |

### 响应 (200 OK)

```json
{
    "code": 200,
    "message": "success",
    "data": {
        "total_unread": 0,
        "unread_by_type": {
            "like": 0,
            "comment": 0,
            "follow": 0,
            "system": 0
        }
    },
    "details": null,
    "timestamp": "2025-06-21T17:08:08.414391",
    "pagination": null
}
``` 