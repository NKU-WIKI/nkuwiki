# 微信小程序：敏感词管理接口

本文档详细说明了与微信小程序中敏感词库管理功能相关的所有API接口。

## 1. 获取整个敏感词库

- **Endpoint**: `GET /wxapp/banwords/library`
- **Permissions**: `Admin`
- **Tags**: `wxapp-banwords`
- **Summary**: 获取所有敏感词分类及其词汇。

### 响应 (200 OK)

```json
{
    "code": 200,
    "message": "获取敏感词库成功",
    "data": {
        "library": {
            "politics": {
                "defaultRisk": 1,
                "words": ["敏感词A", "敏感词B"],
                "patterns": []
            },
            "advertisement": {
                "defaultRisk": 3,
                "words": ["代开发票", "办证"],
                "patterns": []
            }
        }
    },
    "details": null,
    "timestamp": "2025-06-21T17:25:25.369004",
    "pagination": null
}
```

---

## 2. 获取敏感词分类列表

- **Endpoint**: `GET /wxapp/banwords/categories`
- **Permissions**: `Admin`
- **Tags**: `wxapp-banwords`
- **Summary**: 只获取所有敏感词的分类名称。

### 响应 (200 OK)

```json
{
    "code": 200,
    "message": "获取敏感词分类成功",
    "data": {
        "categories": [
            "politics",
            "advertisement",
            "spam"
        ]
    },
    "details": null,
    "timestamp": "2025-06-21T17:28:54.432578",
    "pagination": null
}
```

---

## 3. 添加敏感词

- **Endpoint**: `POST /wxapp/banwords/library`
- **Permissions**: `Admin`
- **Tags**: `wxapp-banwords`
- **Summary**: 向指定分类添加一个或多个新的敏感词。

### 请求体 (Body)

| 参数 | 类型 | 是否必须 | 描述 |
| :--- | :--- | :--- | :--- |
| `category` | `string` | 是 | 敏感词所属的分类名称。 |
| `words` | `List[string]` | 是 | 要添加的敏感词列表。 |
| `risk` | `integer` | 否 | 风险等级，默认为3。 |

**示例:**
```json
{
    "category": "advertisement",
    "words": ["优惠券"],
    "risk": 3
}
```

### 响应 (200 OK)

```json
{
    "code": 200,
    "message": "成功添加1个敏感词",
    "data": {
        "added_count": 1
    },
    "details": null,
    "timestamp": "2025-06-21T17:30:59.345601",
    "pagination": null
}
```

---

## 4. 删除敏感词

- **Endpoint**: `POST /wxapp/banwords/delete-word`
- **Permissions**: `Admin`
- **Tags**: `wxapp-banwords`
- **Summary**: 从指定分类中删除一个敏感词。

### 请求体 (Body)

| 参数 | 类型 | 是否必须 | 描述 |
| :--- | :--- | :--- | :--- |
| `category` | `string` | 是 | 敏感词所属的分类名称。 |
| `word` | `string` | 是 | 要删除的敏感词。 |

**示例:**
```json
{
    "category": "advertisement",
    "word": "优惠券"
}
```

### 响应 (200 OK)

```json
{
    "code": 200,
    "message": "成功删除敏感词: 优惠券",
    "data": {},
    "details": null,
    "timestamp": "2025-06-21T17:31:09.494495",
    "pagination": null
}
```

---

## 5. 更新整个分类的敏感词

- **Endpoint**: `POST /wxapp/banwords/update-category/{category}`
- **Permissions**: `Admin`
- **Tags**: `wxapp-banwords`
- **Summary**: 使用新的词汇列表完全替换指定分类下的所有敏感词。

### 路径参数 (Path)

| 参数 | 类型 | 描述 |
| :--- | :--- | :--- |
| `category` | `string` | 要更新的分类名称。 |

### 请求体 (Body)

| 参数 | 类型 | 是否必须 | 描述 |
| :--- | :--- | :--- | :--- |
| `words` | `List[string]` | 是 | 新的敏感词列表。 |

**示例:**
```json
{
    "words": [
        "测试词1",
        "测试词2"
    ]
}
```

### 响应 (200 OK)

```json
{
    "code": 200,
    "message": "成功更新分类 advertisement 的敏感词",
    "data": {
        "word_count": 2
    },
    "details": null,
    "timestamp": "2025-06-21T17:31:20.061053",
    "pagination": null
}
``` 