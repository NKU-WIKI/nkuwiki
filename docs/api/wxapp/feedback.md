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
| `category` | `string` | 否 | 反馈分类 (e.g., `bug`（错误）、`experience`（体验问题）、`suggestion`（产品建议）、`other`（其他）)。 |
| `contact` | `string` | 否 | 用户的联系方式 (邮箱、电话等)。 |
| `image` | `array` | 否 | 图片URL列表, e.g., `["url1", "url2"]`。 |
| `device_info`| `object` | 否 | 提交反馈时用户的设备信息。 |
| `version` | `string` | 否 | 应用版本号。 |

### 请求示例

#### 基本反馈（匿名用户）
```json
{
    "content": "这是一个测试反馈，用于验证接口功能",
    "title": "测试反馈标题",
    "category": "bug",
    "contact": "test@example.com",
    "version": "1.0.0"
}
```

#### 包含图片和设备信息的反馈
```json
{
    "content": "发现了一个界面显示问题，附上截图",
    "title": "界面显示异常",
    "category": "bug",
    "contact": "user@nku.edu.cn",
    "version": "1.2.3",
    "image": [
        "https://example.com/screenshot1.jpg",
        "https://example.com/screenshot2.jpg"
    ],
    "device_info": {
        "platform": "iOS",
        "version": "16.0",
        "model": "iPhone 14",
        "brand": "Apple",
        "screen_width": 390,
        "screen_height": 844
    }
}
```

#### 登录用户反馈（需要认证token）
```json
{
    "content": "建议增加夜间模式功能",
    "title": "功能建议",
    "category": "suggestion",
    "version": "1.2.3"
}
```

### 成功响应 (200 OK)

```json
{
    "code": 200,
    "message": "反馈提交成功！",
    "data": {
        "id": 4
    },
    "details": null,
    "timestamp": "2025-07-29T17:33:36.838601",
    "pagination": null
}
```

### 错误响应 (400 Bad Request)

当缺少必要参数时：

```json
{
    "code": 400,
    "message": "缺少必要参数: content",
    "data": null,
    "details": null,
    "timestamp": "2025-07-29T17:33:36.867679",
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
            "id": 12,
            "user_id": 1,
            "title": "功能建议",
            "content": "建议增加夜间模式功能",
            "category": "suggestion",
            "contact": null,
            "image": null,
            "device_info": null,
            "version": "1.2.3",
            "status": "pending",
            "admin_reply": null,
            "admin_id": null,
            "create_time": "2025-07-29T09:48:12",
            "update_time": "2025-07-29T09:48:12"
        },
        {
            "id": 9,
            "user_id": 1,
            "title": "功能建议",
            "content": "建议增加夜间模式功能",
            "category": "suggestion",
            "contact": null,
            "image": null,
            "device_info": null,
            "version": "1.2.3",
            "status": "pending",
            "admin_reply": null,
            "admin_id": null,
            "create_time": "2025-07-29T09:47:11",
            "update_time": "2025-07-29T09:47:11"
        },
        {
            "id": 6,
            "user_id": 1,
            "title": "功能建议",
            "content": "建议增加夜间模式功能",
            "category": "suggestion",
            "contact": null,
            "image": null,
            "device_info": null,
            "version": "1.2.3",
            "status": "pending",
            "admin_reply": null,
            "admin_id": null,
            "create_time": "2025-07-29T09:33:36",
            "update_time": "2025-07-29T09:33:36"
        }
    ],
    "details": null,
    "timestamp": "2025-07-29T17:49:38.573861",
    "pagination": {
        "total": 3,
        "page": 1,
        "page_size": 10,
        "total_pages": 1,
        "has_more": false
    }
}
```

### 错误响应

#### 401 Unauthorized - 未提供认证token

```json
{
    "detail": "Not authenticated"
}
```

#### 401 Unauthorized - 无效的认证token

```json
{
    "detail": "无法验证凭据"
}
```