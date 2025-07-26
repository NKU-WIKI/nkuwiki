# 微信小程序：违禁词管理接口

本文档详细说明了用于管理违禁词库的API接口。接口分为两部分：可供所有人访问的公共读取接口，以及需要管理员权限才能使用的写入/修改接口。

## 1. 公共接口 (Public API)

### 1.1 获取整个违禁词库

- **Endpoint**: `GET /api/wxapp/banwords/library`
- **Permissions**: `Public`
- **Tags**: `wxapp-banwords`
- **Summary**: 获取所有违禁词分类及其包含的词汇。

#### 成功响应 (200 OK)

```json
{
    "code": 200,
    "message": "success",
    "data": {
        "library": {
            "政治类": {
                "id": 1,
                "default_risk": 5,
                "words": ["词A", "词B"]
            },
            "广告类": {
                "id": 2,
                "default_risk": 3,
                "words": ["词C", "词D", "词E"]
            }
        }
    },
    "details": null,
    "timestamp": "2025-07-13T13:00:00.123456",
    "pagination": null
}
```

### 1.2 获取所有分类

- **Endpoint**: `GET /api/wxapp/banwords/categories`
- **Permissions**: `Public`
- **Tags**: `wxapp-banwords`
- **Summary**: 获取所有违禁词的分类列表。

#### 成功响应 (200 OK)

```json
{
    "code": 200,
    "message": "success",
    "data": [
        {
            "id": 1,
            "name": "政治类"
        },
        {
            "id": 2,
            "name": "广告类"
        }
    ],
    "details": null,
    "timestamp": "2025-07-13T13:01:00.567890",
    "pagination": null
}
```

---

## 2. 管理员接口 (Admin API)

**所有管理员接口都需要在请求头中提供管理员用户的 `Bearer Token`。**

### 2.1 创建新分类

- **Endpoint**: `POST /api/wxapp/banwords/category`
- **Permissions**: `Admin Required`
- **Tags**: `wxapp-banwords`
- **Summary**: 创建一个新的违禁词分类。

#### 请求体 (Body)

| 参数 | 类型 | 是否必须 | 描述 |
| --- | --- | --- | --- |
| `name` | `string` | 是 | 新的分类名称。必须是唯一的。 |
| `default_risk` | `integer`| 否 | 该分类的默认风险等级，默认为3。 |

#### 成功响应 (200 OK)

```json
{
    "code": 200,
    "message": "分类创建成功",
    "data": {
        "id": 3
    },
    "details": null,
    "timestamp": "2025-07-13T13:02:00.123456",
    "pagination": null
}
```

### 2.2 批量添加违禁词

- **Endpoint**: `POST /api/wxapp/banwords/words`
- **Permissions**: `Admin Required`
- **Tags**: `wxapp-banwords`
- **Summary**: 向一个分类中批量添加多个违禁词。重复的词将被忽略。

#### 请求体 (Body)

| 参数 | 类型 | 是否必须 | 描述 |
| --- | --- | --- | --- |
| `category_id` | `integer` | 是 | 要添加到的分类ID。 |
| `words` | `array` | 是 | 包含多个违禁词字符串的列表。 |

#### 成功响应 (200 OK)

```json
{
    "code": 200,
    "message": "批量添加完成",
    "data": {
        "added_count": 5
    },
    "details": null,
    "timestamp": "2025-07-13T13:03:00.567890",
    "pagination": null
}
```

### 2.3 删除违禁词

- **Endpoint**: `DELETE /api/wxapp/banwords/word`
- **Permissions**: `Admin Required`
- **Tags**: `wxapp-banwords`
- **Summary**: 从一个分类中删除一个指定的违禁词。

#### 请求体 (Body)

| 参数 | 类型 | 是否必须 | 描述 |
| --- | --- | --- | --- |
| `category_id` | `integer` | 是 | 违禁词所在的分类ID。 |
| `word` | `string` | 是 | 要删除的违禁词。 |

#### 成功响应 (200 OK)

```json
{
    "code": 200,
    "message": "删除成功",
    "data": null,
    "details": null,
    "timestamp": "2025-07-13T13:04:00.123456",
    "pagination": null
}
``` 