# 微信小程序：用户反馈接口

本文档详细说明了与微信小程序中用户反馈功能相关的所有API接口。所有接口都遵循了项目的标准认证和响应格式。

## 1. 创建用户反馈

- **Endpoint**: `POST /api/wxapp/feedback/create`
- **Permissions**: `可选认证 (Optional Authentication)`
- **Tags**: `wxapp-feedback`
- **Summary**: 用户提交一条新的反馈。如果用户已登录，会自动关联其`user_id`。

### 请求头 (Headers)

| 参数 | 类型 | 是否必须 | 描述 |
| --- | --- | --- | --- |
| `Authorization` | `string` | 否 | `Bearer <JWT>`。如果提供了有效的Token，反馈将与该用户关联。 |

### 请求体 (Body)

| 参数 | 类型 | 是否必须 | 描述 |
| --- | --- | --- | --- |
| `content` | `string` | 是 | 反馈的正文内容。 |
| `title` | `string` | 否 | 反馈标题。 |
| `category` | `string` | 否 | 反馈分类 (e.g., `suggestion`, `bug`)。 |
| `contact` | `string` | 否 | 用户的联系方式 (邮箱、电话等)。 |
| `image` | `array` | 否 | 图片URL列表, e.g., `["url1", "url2"]`。 |
| `device_info`| `object` | 否 | 提交反馈时用户的设备信息。 |

### 成功响应 (200 OK)

```json
{
    "code": 200,
    "message": "反馈提交成功！",
    "data": {
        "id": 42
    },
    "details": null,
    "timestamp": "2025-07-13T12:30:00.123456",
    "pagination": null
}
```

---

## 2. 获取我的反馈列表

- **Endpoint**: `GET /api/wxapp/feedback/my/list`
- **Permissions**: `需要认证 (Authentication Required)`
- **Tags**: `wxapp-feedback`
- **Summary**: 获取当前登录用户的反馈提交历史。

### 请求头 (Headers)

| 参数 | 类型 | 是否必须 | 描述 |
| --- | --- | --- | --- |
| `Authorization` | `string` | 是 | `Bearer <JWT>`。必须提供有效的Token。 |

### 查询参数 (Query)

| 参数 | 类型 | 是否必须 | 默认值 | 描述 |
| --- | --- | --- | --- | --- |
| `page` | `integer` | 否 | 1 | 页码。 |
| `page_size` | `integer`| 否 | 10 | 每页数量。 |

### 成功响应 (200 OK)

```json
{
    "code": 200,
    "message": "success",
    "data": [
        {
            "id": 42,
            "user_id": 101,
            "title": "新功能建议",
            "content": "希望可以增加一个夜间模式。",
            "category": "suggestion",
            "contact": "user@example.com",
            "image": ["http://example.com/img1.png"],
            "device_info": {
                "model": "iPhone 15 Pro",
                "system": "iOS 18.0"
            },
            "status": "pending",
            "admin_reply": null,
            "admin_id": null,
            "create_time": "2025-07-13T12:30:00",
            "update_time": "2025-07-13T12:30:00"
        }
    ],
    "details": null,
    "timestamp": "2025-07-13T12:31:00.567890",
    "pagination": {
        "total": 1,
        "page": 1,
        "page_size": 10,
        "total_pages": 1,
        "has_more": false
    }
}
``` 