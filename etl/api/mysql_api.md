# MySQL API 接口文档

## 基本信息

- 基础路径: `mysql/`
- API 描述: 南开百科知识平台的 MySQL 数据访问接口
- 版本: 1.0.0

## 接口列表

### 1. 获取数据库表列表

- **接口**: `GET /tables`
- **描述**: 获取数据库中所有表的列表
- **响应模型**: `TablesResponse`
- **返回示例**:
  ```json
  {
    "tables": ["表1", "表2", "表3"]
  }
  ```

### 2. 获取表结构

- **接口**: `GET /table/{table_name}/structure`
- **描述**: 获取指定表的字段结构信息
- **参数**: 
  - `table_name` (path): 要查询的表名
- **响应模型**: `TableStructureResponse`
- **返回示例**:
  ```json
  {
    "fields": [
      {"field": "id", "type": "int", "null": "NO", "key": "PRI", "default": null, "extra": "auto_increment"},
      {"field": "name", "type": "varchar(100)", "null": "YES", "key": "", "default": null, "extra": ""}
    ]
  }
  ```

### 3. 查询数据

- **接口**: `POST /query`
- **描述**: 根据条件查询表数据
- **请求体**: `QueryRequest`
  ```json
  {
    "table_name": "要查询的表名",
    "conditions": {"字段名": "值"},
    "order_by": "排序字段",
    "limit": 100,
    "offset": 0
  }
  ```
- **参数说明**:
  - `table_name` (必填): 要查询的表名
  - `conditions` (可选): 查询条件，键值对形式
  - `order_by` (可选): 排序字段
  - `limit` (可选): 返回记录数量限制，默认100
  - `offset` (可选): 分页偏移量，默认0
- **响应模型**: `List[Dict[str, Any]]`
- **返回示例**:
  ```json
  [
    {"id": 1, "name": "示例1"},
    {"id": 2, "name": "示例2"}
  ]
  ```

### 4. 统计记录数量

- **接口**: `POST /count`
- **描述**: 统计符合条件的记录数量
- **请求体**: `CountRequest`
  ```json
  {
    "table_name": "要统计的表名",
    "conditions": {"字段名": "值"}
  }
  ```
- **参数说明**:
  - `table_name` (必填): 要统计的表名
  - `conditions` (可选): 统计条件，键值对形式
- **响应模型**: `CountResponse`
- **返回示例**:
  ```json
  {
    "count": 42
  }
  ```

### 5. 自定义SQL查询

- **接口**: `POST /custom_query`
- **描述**: 执行自定义SQL查询语句（仅支持SELECT操作）
- **请求体**: `CustomQueryRequest`
  ```json
  {
    "query": "SELECT * FROM users WHERE age > ?",
    "params": [18],
    "fetch": true
  }
  ```
- **参数说明**:
  - `query` (必填): 自定义SQL查询语句
  - `params` (可选): 查询参数列表，用于替换SQL中的占位符
  - `fetch` (可选): 是否获取查询结果，默认为true
- **安全限制**: 仅支持SELECT查询，不允许执行INSERT、UPDATE、DELETE、DROP、ALTER、TRUNCATE等操作
- **返回示例**:
  ```json
  {
    "result": [
      {"id": 1, "name": "用户1", "age": 25},
      {"id": 2, "name": "用户2", "age": 30}
    ]
  }
  ```

## 错误处理

所有接口在出现错误时将返回以下格式的错误信息：

- **400错误**: 客户端请求参数错误
  ```json
  {
    "detail": "错误详情信息"
  }
  ```

- **500错误**: 服务器内部错误
  ```json
  {
    "detail": "错误详情信息"
  }
  ```

## 注意事项

1. 所有查询接口均会进行SQL注入防护
2. 自定义查询仅支持SELECT操作，不支持数据修改操作
3. 默认查询结果限制为100条记录，可通过limit参数调整
