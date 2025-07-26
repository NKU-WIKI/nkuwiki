# 获取洞察列表

分页获取结构化的洞察信息。

- **Endpoint**: `GET /knowledge/insight`
- **Tags**: `Knowledge`
- **认证**: `Public`
- **说明**: 返回结果默认按日期 (`insight_date`) 倒序排列。

## 请求参数

| 参数名 | 位置 | 类型 | 是否必需 | 默认值 | 描述 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `date` | `query` | `string` | 否 | 当天日期 | 要查询的日期，格式为 `YYYY-MM-DD`。若要获取所有日期的洞察，请传入 `all`。 |
| `category` | `query` | `string` | 否 | `null` | 按分类筛选，例如：`官方`, `社区`, `集市`。 |
| `page` | `query` | `integer` | 否 | `1` | 页码。 |
| `page_size`| `query` | `integer` | 否 | `10` | 每页数量。 |

## 请求示例

```bash
# 获取指定日期的洞察
curl -X GET "http://127.0.0.1:8000/api/knowledge/insight?date=2024-06-20"

# 获取'社区'分类的所有洞察
curl -X GET "http://127.0.0.1:8000/api/knowledge/insight?date=all&category=社区"
```

## 响应示例

### 成功

```json
{
  "code": 200,
  "message": "成功",
  "data": [
    {
      "id": 77,
      "title": "官方发布新的校园活动日历",
      "content": "内容详情A\n",
      "tags": "[\"活动\", \"官方\"]",
      "category": "官方",
      "insight_date": "2024-06-20T00:00:00",
      "source_node_ids": "[1, 2, 3]",
      "relevance_score": 0.0,
      "create_time": "2025-06-21T09:35:10",
      "update_time": "2025-06-21T09:35:10"
    }
  ],
  "details": null,
  "timestamp": "2025-06-21T17:45:54.460637",
  "pagination": {
    "total": 1,
    "page": 1,
    "page_size": 10,
    "total_pages": 1,
    "has_more": false
  }
}
```

### 失败（日期格式错误）

```json
{
    "code": 400,
    "message": "Bad request",
    "details": "日期格式无效，请使用 YYYY-MM-DD 格式，或传入 'all'。",
    "timestamp": "..."
}
``` 