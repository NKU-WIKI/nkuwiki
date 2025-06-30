# 微信小程序：用户反馈接口

本文档详细说明了与微信小程序中用户反馈功能相关的所有API接口。

## 1. 提交反馈

- **Endpoint**: `POST /wxapp/feedback/`
- **Permissions**: `Authenticated User`
- **Tags**: `wxapp-feedback`
- **Summary**: 用户提交一条新的反馈。

### 请求体 (Body)

```json
{
    "openid": "oLx8G7ADjzh23EzAJavndryh76rE",
    "title": "关于搜索功能的建议",
    "content": "小程序的搜索功能有时候会卡顿，希望可以优化一下。",
    "category": "suggestion",
    "contact": "test@nku.edu.cn",
    "image": ["url1.jpg", "url2.jpg"]
}
```

### 响应 (200 OK)

```json
{
    "code": 200,
    "message": "反馈成功提交",
    "data": {
        "feedback_id": 1
    },
    "details": null,
    "timestamp": "2025-06-21T17:20:50.251903",
    "pagination": null
}
```

---

## 2. 获取反馈列表

- **Endpoint**: `GET /wxapp/feedback/list`
- **Permissions**: `Authenticated User`
- **Tags**: `wxapp-feedback`
- **Summary**: 获取反馈列表，支持按分类和状态筛选。

### 查询参数 (Query)

| 参数 | 类型 | 是否必须 | 默认值 | 描述 |
| --- | --- | --- | --- | --- |
| `page` | `integer` | 否 | 1 | 页码。 |
| `page_size` | `integer`| 否 | 10 | 每页数量。 |
| `status` | `string` | 否 | `null`| 按状态筛选 (pending, processing, resolved, etc.) |
| `category`| `string` | 否 | `null`| 按分类筛选 (bug, suggestion, other) |

### 响应 (200 OK)

```json
{
    "code": 200,
    "message": "success",
    "data": [
        {
            "id": 1,
            "title": "关于搜索功能的建议",
            "content": "小程序的搜索功能有时候会卡顿，希望可以优化一下。",
            "category": "suggestion",
            "status": "pending",
            "create_time": "2025-06-21T09:20:50",
            "user_nickname": "南开小透明",
            "user_avatar": null
        }
    ],
    "details": null,
    "timestamp": "2025-06-21T17:21:41.003066",
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

## 3. 获取反馈详情

- **Endpoint**: `GET /wxapp/feedback/detail`
- **Permissions**: `Authenticated User`
- **Tags**: `wxapp-feedback`
- **Summary**: 获取单条反馈的详细信息，包括处理历史。

### 查询参数 (Query)

| 参数 | 类型 | 是否必须 | 描述 |
| --- | --- | --- | --- |
| `feedback_id` | `integer` | 是 | 要查询的反馈ID。 |

### 响应 (200 OK)

```json
{
    "code": 200,
    "message": "success",
    "data": {
        "id": 1,
        "openid": "oLx8G7ADjzh23EzAJavndryh76rE",
        "title": "关于搜索功能的建议",
        "content": "小程序的搜索功能有时候会卡顿，希望可以优化一下。",
        "category": "suggestion",
        "contact": "test@nku.edu.cn",
        "image": "[\"url1.jpg\", \"url2.jpg\"]",
        "device_info": null,
        "status": "resolved",
        "admin_reply": "感谢您的反馈，我们已经收到并开始排查问题。",
        "admin_id": "admin_02",
        "create_time": "2025-06-21T09:24:08",
        "update_time": "2025-06-21T09:24:08",
        "user_nickname": "南开小透明",
        "user_avatar": null,
        "history": [
            {
                "id": 1,
                "feedback_id": 1,
                "operator": "admin_02",
                "action_type": "status_change",
                "details": "{\"new_status\": \"resolved\"}",
                "create_time": "2025-06-21T09:24:08"
            }
        ]
    },
    "details": null,
    "timestamp": "2025-06-21T17:24:18.328774",
    "pagination": null
}
```

---

## 4. 更新反馈状态

- **Endpoint**: `PUT /wxapp/feedback/{feedback_id}/status`
- **Permissions**: `Admin`
- **Tags**: `wxapp-feedback`
- **Summary**: 更新指定反馈的状态。

### 请求体 (Body)

```json
{
    "status": "processing",
    "admin_id": "admin_01"
}
```

### 响应 (200 OK)

```json
{
    "code": 200,
    "message": "状态更新成功",
    "data": null,
    "details": null,
    "timestamp": "2025-06-21T17:23:14.910602",
    "pagination": null
}
```

---

## 5. 回复反馈

- **Endpoint**: `POST /wxapp/feedback/{feedback_id}/reply`
- **Permissions**: `Admin`
- **Tags**: `wxapp-feedback`
- **Summary**: 回复指定反馈，并自动将状态更新为 `replied`。

### 请求体 (Body)

```json
{
    "reply_content": "感谢您的反馈，我们已经收到并开始排查问题。",
    "admin_id": "admin_01"
}
```

### 响应 (200 OK)

```json
{
    "code": 200,
    "message": "回复成功",
    "data": null,
    "details": null,
    "timestamp": "2025-06-21T17:23:23.934871",
    "pagination": null
}
```

---

## 6. 删除反馈

- **Endpoint**: `POST /wxapp/feedback/delete`
- **Permissions**: `Admin`
- **Tags**: `wxapp-feedback`
- **Summary**: 删除一条反馈及其处理历史。

### 请求体 (Body)

```json
{
    "feedback_id": 1,
    "admin_id": "admin_01"
}
```

### 响应 (200 OK)

```json
{
    "code": 200,
    "message": "反馈删除成功",
    "data": null,
    "details": null,
    "timestamp": "2025-06-21T17:24:28.823945",
    "pagination": null
}
``` 