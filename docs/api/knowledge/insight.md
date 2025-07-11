# 获取指定日期的洞察

获取特定日期的所有洞察报告。

- **Endpoint**: `GET /knowledge/insight`
- **Permissions**: `Public`
- **方法**: `GET`
- **速率限制**: `100/minute`

## 请求参数

| 参数名     | 位置    | 类型     | 是否必需 | 描述                               |
| :--------- | :------ | :------- | :------- | :--------------------------------- |
| `date`     | `query` | `string` | 是       | 要查询的日期，格式为 `YYYY-MM-DD`。 |
| `page`     | `query` | `integer`| 否       | 页码，默认为 `1`。                 |
| `page_size`| `query` | `integer`| 否       | 每页数量，默认为 `10`。            |

## 请求示例

```bash
curl -X GET "http://127.0.0.1:8000/api/knowledge/insight?date=2024-06-20"
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
      "insight_date": "2024-06-20",
      "source_node_ids": "[1, \n2, 3]",
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
    "detail": [
        {
            "type": "date_from_datetime_parsing",
            "loc": [
                "query",
                "date"
            ],
            "msg": "Input should be a valid date or datetime, input is invalid",
            "input": "6.20",
            "ctx": {
                "error": "invalid character in year"
            },
            "url": "https://errors.pydantic.dev/2.5/v/date_from_datetime_parsing"
        }
    ]
}
``` 