# 索引器字段映射统一规范

本文档定义了所有索引器统一使用的字段映射规范，参考了 etl/embedding/ingestion.py 中的实现模式。

## 数据库表字段 -> 索引元数据字段

所有索引器（BM25、Qdrant、Elasticsearch）都使用以下统一的字段映射：

### website_nku 表字段映射

| 数据库字段 | 索引元数据字段 | 类型 | 说明 |
|------------|----------------|------|------|
| `id` | `id` | int | 记录唯一标识符 |
| `original_url` | `url` | string | 页面URL地址 |
| `title` | `title` | string | 页面标题 |
| `content` | `content` | text | 页面内容（仅用于索引，不存储在元数据中） |
| `publish_time` | `publish_time` | datetime | 发布时间 |
| `platform` | `source` | string | 数据来源平台 |
| `pagerank_score` | `pagerank_score` | float | PageRank权威性分数 |

### SQL查询模板

```sql
SELECT id, original_url, title, content, publish_time, platform, pagerank_score
FROM website_nku
WHERE content IS NOT NULL AND content != ''
ORDER BY id
```

### 元数据结构（参考 ingestion.py:load_data_from_mysql）

```python
metadata = {
    'source_id': record.get('id'),                              # 数据库记录ID
    'id': record.get('id'),                                     # 兼容性保留
    'url': record.get('original_url', ''),                     # 页面URL
    'title': record.get('title', ''),                          # 页面标题
    'author': record.get('author', ''),                        # 作者信息
    'original_url': record.get('original_url', ''),            # 原始URL（原字段名）
    'publish_time': str(record.get('publish_time', '')),       # 发布时间（转为字符串）
    'source': record.get('platform', ''),                      # 数据来源平台
    'platform': record.get('platform', ''),                   # 平台名称（原字段名）
    'pagerank_score': float(record.get('pagerank_score', 0.0)) # PageRank分数
}
```

## 其他表的字段映射

### market_nku 表
- `original_url` -> `url`
- `platform` -> `source`
- `author` -> `author`
- `category` -> `category`

### wechat_nku 表
- `original_url` -> `url`
- `platform` -> `source`
- `author` -> `author`
- `like_count` -> `like_count`

## 注意事项

1. **一致性**: 所有索引器必须使用相同的字段映射
2. **向后兼容**: 元数据字段名应保持稳定，避免频繁更改
3. **类型转换**: `pagerank_score` 必须转换为 float 类型
4. **空值处理**: 所有字符串字段提供默认空字符串，避免 None 值 