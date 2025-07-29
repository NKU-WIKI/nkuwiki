## 环境

华为云4核8G 无GPU ubuntu24.04
/opt/vevns/base/bin/python（3.12）

# 数据库操作规范 (基于 aiomysql)


表结构在etl/load/mysql_tables/下，修改表需要同步修改相应的sql文件


## 1. 数据库连接池 (`db_pool_manager.py`)

项目采用基于 `aiomysql` 的异步数据库连接池，为所有数据库操作提供高效、非阻塞的连接管理。

### 核心特性
- **异步连接池**: 使用 `aiomysql.create_pool` 创建，在应用启动时初始化，在应用关闭时销毁。
- **上下文管理**: 通过异步上下文管理器 `get_db_connection` 提供连接，确保连接的自动获取和释放。

### 获取连接

所有数据库操作都应通过 `get_db_connection` 异步上下文管理器获取连接。

```python
# etl/load/db_pool_manager.py
import aiomysql
from contextlib import asynccontextmanager

# 全局连接池实例
db_pool: aiomysql.Pool = None

# (初始化和关闭逻辑...)

@asynccontextmanager
async def get_db_connection():
    """
    从连接池获取一个数据库连接的异步上下文管理器。
    """
    if not db_pool:
        raise ConnectionError("数据库连接池不可用。")

    conn = None
    try:
        conn = await db_pool.acquire()
        yield conn
    finally:
        if conn:
            await db_pool.release(conn)

# 使用示例
async def some_db_operation():
    try:
        async with get_db_connection() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute("SELECT * FROM some_table LIMIT 1")
                result = await cursor.fetchone()
                print(result)
    except Exception as e:
        logger.error(f"数据库操作失败: {e}")
```

## 2. 核心数据库异步操作 (`db_core.py`)

数据库核心操作层 (`db_core.py`) 完全基于 `aiomysql` 实现，所有函数均为异步方法，防止阻塞主应用的 `asyncio` 事件循环。

### 常用异步函数

- `execute_custom_query(query, params, fetch)`: 执行任意自定义SQL。
- `insert_record(table_name, data)`: 插入单条记录。
- `batch_insert(table_name, records, batch_size)`: 高效的批量插入。
- `update_record(table_name, conditions, data)`: 根据条件更新记录。
- `query_records(table_name, conditions, fields, order_by, limit, offset)`: 功能强大的查询函数，返回数据和总数。
- `get_by_id(table_name, record_id)`: 通过主键ID获取单条记录。
- `count_records(table_name, conditions)`: 根据条件统计记录数。
- `get_all_tables()`: 获取所有表名。

### 使用示例

所有 `db_core` 函数都必须使用 `await` 调用。

```python
import asyncio
from etl.load import db_core
from etl.load.db_pool_manager import init_db_pool, close_db_pool

async def main():
    # 在应用启动时初始化连接池
    await init_db_pool()

    try:
        # 示例1: 插入一条记录
        new_user_data = {"nickname": "async_user", "openid": f"test_openid_{asyncio.runners.random.randint(1000, 9999)}"}
        # 假设 wxapp_users 表存在
        user_id = await db_core.insert_record("wxapp_users", new_user_data)
        print(f"插入用户成功，ID: {user_id}")

        # 示例2: 查询记录
        query_conditions = {"nickname": "async_user"}
        result = await db_core.query_records(
            table_name="wxapp_users",
            conditions=query_conditions,
            fields=["openid", "nickname", "create_time"],
            limit=1
        )
        if result['data']:
            print("查询结果:", result['data'][0])
            print("总记录数:", result['total'])

        # 示例3: 批量插入
        new_posts = [
            {"openid": new_user_data["openid"], "title": "帖子A", "content": "内容A"},
            {"openid": new_user_data["openid"], "title": "帖子B", "content": "内容B"},
        ]
        # 假设 wxapp_posts 表存在
        inserted_count = await db_core.batch_insert("wxapp_posts", new_posts)
        print(f"批量插入 {inserted_count} 条帖子成功")

        # 示例4: 执行自定义SQL
        custom_sql = "SELECT COUNT(*) as count FROM wxapp_posts WHERE openid = %s"
        count_result = await db_core.execute_custom_query(custom_sql, [new_user_data["openid"]], fetch='one')
        print("帖子总数:", count_result['count'])

    finally:
        # 在应用关闭时关闭连接池
        await close_db_pool()

if __name__ == "__main__":
    # 确保在运行环境中已有相关表结构
    # 例如 wxapp_users, wxapp_posts
    asyncio.run(main())
```

## 3. 表结构管理 (`table_manager.py`)

表结构的管理由 `TableManager` 负责，其设计同样是**异步**的，并支持通过命令行进行操作。它依赖 `db_core` 执行所有数据库修改。

### 核心特性
- **SQL文件驱动**：表结构定义在 `etl/load/mysql_tables/` 目录下的各个 `.sql` 文件中，文件名即表名（如 `wxapp_users.sql`）。
- **异步操作**：所有管理功能（创建、删除、查询信息）都是 `async` 方法。
- **命令行支持**：可作为脚本运行，方便地进行数据库初始化和维护。

### 使用示例

```python
import asyncio
from etl.load.table_manager import TableManager
from etl.load.db_pool_manager import init_db_pool, close_db_pool

async def manage_tables():
    await init_db_pool()
    manager = TableManager()

    try:
        # 获取所有可用的表定义
        available_tables = manager.get_available_table_definitions()
        print("可用的表定义:", available_tables)

        # 检查 'wxapp_users' 表是否存在
        exists = await manager.table_exists('wxapp_users')
        print(f"'wxapp_users' 表是否存在: {exists}")

        # 获取表信息
        if exists:
            info = await manager.get_table_info('wxapp_users')
            if info:
                print(f"'wxapp_users' 表信息: {info.get('record_count', 0)} 条记录")

        # 重新创建所有表（危险操作！）
        # await manager.recreate_tables(force=True)
        # print("所有表已重建")
    finally:
        await close_db_pool()


if __name__ == "__main__":
    asyncio.run(manage_tables())
```
---
description: 
globs: 
alwaysApply: true
---
# API 开发核心规范

## 1. 接口设计与命名

### 1.1 请求方法
- **GET**: 用于幂等操作（如获取数据）。所有参数必须通过**查询字符串** (`?key=value`) 传递。**禁止**在GET请求中使用路径参数或请求体。
- **POST**: 用于非幂等操作（如创建或更新数据）。所有参数必须通过**请求体**（JSON格式）传递。**禁止**在POST请求中使用查询参数或路径参数。

### 1.2 路由命名
- 所有接口路径使用**小写字母**。
- 单词之间使用**短横线 `-`** 分隔，**禁止**使用下划线 `_`。
- 示例: `/api/wxapp/notification/mark-read-batch`

### 1.3 字段命名
- **统一单数形式**: 集合类型的字段名应使用单数形式，例如 `image` (图片列表), `tag` (标签列表)。
- **计数字段规范**:
  - `like_count`, `favorite_count`, `post_count`, `follower_count`, `following_count`, `comment_count`, `view_count`
- **严格遵循**: 所有API接口的请求和响应都必须使用规范的字段名。

## 2. 标准响应格式

所有API端点都 **必须** 返回 `api.models.common.Response` 类的实例，例如 `Response.success()` 或 `Response.paged()`。这确保了API响应结构的一致性。

### 2.1 基础响应结构
```json
{
  "code": 200,
  "message": "success",
  "data": {},
  "details": null,
  "timestamp": "2023-01-01 12:00:00"
}
```

### 2.2 分页响应结构
对于返回列表数据的接口，必须包含 `pagination` 字段。
```json
{
  "code": 200,
  "message": "success",
  "data": [...],
  "pagination": {
    "total": 100,
    "page": 1,
    "page_size": 10,
    "total_pages": 10,
    "has_more": true
  }
}
```
- **分页查询参数**: 客户端请求时应使用 `page` 和 `page_size`。

### 2.3 禁止的操作
- **不使用 `response_model`**: 接口定义中 **禁止** 使用 `response_model` 参数。文档由FastAPI根据返回类型注解自动生成。
- **直接传递字典**: 服务层（如 `db_core`）获取的原始 `dict` 或 `list[dict]` 数据应直接传递给 `Response` 对象，**禁止** 将这些字典在接口层实例化为Pydantic模型再传递。

### 示例：正确的返回方式
```python
# 正确 ✅: 直接返回 Response 对象，并将原始字典作为数据传递
from api.models.common import Response, PaginationInfo
from etl.load import db_core

@router.get("/insights")
async def get_insights(page: int = 1, page_size: int = 10):
    result = await db_core.query_records("insights", limit=page_size, offset=(page - 1) * page_size)
    insights_data = result.get('data', [])
    total = result.get('total', 0)
    
    pagination = PaginationInfo(
        total=total, page=page, page_size=page_size,
        total_pages=(total + page_size - 1) // page_size if page_size > 0 else 0,
        has_more=page * page_size < total
    )
    
    return Response.paged(data=insights_data, pagination=pagination)
```

### 为什么执行此规则？
1.  **性能**: 避免了将数据库查询结果反序列化为字典后，再序列化为Pydantic模型对象所带来的不必要性能开销。
2.  **一致性**: 确保所有API响应都遵循统一的结构（code, message, data, pagination等）。
3.  **解耦**: 保持API逻辑与数据模型定义的解耦。Pydantic模型仅用于定义数据结构，而不应干预运行时行为。

## 3. 数据库交互

- **使用核心模块**: 所有数据库操作都 **必须** 通过 `etl.load.db_core` 中的异步函数进行。
- **禁止原生SQL**: **严禁** 在API路由中直接编写和执行原生的SQL查询字符串。

```python
import etl.load.db_core as db_core

result = await db_core.query_records(
    table_name="users",
    conditions={"status": "active"},
    limit=10
)
```
---
description: 
globs: 
alwaysApply: true
---
# 字段名规范

## 核心原则

**API接口字段名必须与数据库表字段名保持严格一致**

## 字段名映射规范

### 1. 数据库表字段到API响应字段的映射

API接口返回的字段名应该直接使用数据库表中的字段名，不进行任何转换。

#### 标准字段（所有表共有）
- `id` - 主键ID
- `create_time` - 创建时间  
- `update_time` - 更新时间
- `title` - 标题
- `content` - 内容
- `author` - 作者（website_nku/wechat_nku表）
- `original_url` - 原始链接
- `platform` - 平台标识
- `publish_time` - 发布时间

#### 特定表字段
**website_nku表专有字段：**
- `scrape_time` - 爬取时间
- `view_count` - 浏览数
- `pagerank_score` - PageRank分数
- `is_official` - 是否为官方信息

**wechat_nku表专有字段：**
- `scrape_time` - 爬取时间
- `view_count` - 阅读数
- `like_count` - 点赞数
- `is_official` - 是否为官方信息

**market_nku表专有字段：**
- `category` - 分类
- `image` - 图片列表
- `status` - 状态
- `view_count` - 浏览数
- `like_count` - 点赞数
- `comment_count` - 评论数

**wxapp_post表专有字段：**
- `openid` - 用户openid
- `nickname` - 用户昵称（作为author的来源）
- `avatar` - 用户头像
- `phone` - 手机号
- `wechatId` - 微信号
- `qqId` - QQ号
- `bio` - 用户简介
- `category_id` - 分类ID
- `image` - 图片列表
- `tag` - 标签列表
- `location` - 位置信息
- `allow_comment` - 是否允许评论
- `is_public` - 是否公开
- `view_count` - 浏览数
- `like_count` - 点赞数
- `comment_count` - 评论数
- `favorite_count` - 收藏数
- `status` - 帖子状态
- `is_deleted` - 是否删除

### 2. 字段转换规则

#### 时间字段处理
- 数据库中的 `datetime` 类型字段在API中统一转换为 `string` 格式
- 格式：`str(datetime_value)` 或 ISO 8601 格式

#### JSON字段处理
- 数据库中的 `json` 类型字段（如 `tag`, `image`, `location`）在API中保持为对象或字符串
- 空值时返回空字符串 `""`

#### 特殊字段映射
- `wxapp_post.nickname` → API中的 `author` 字段
- `wxapp_post.id` → 构造 `original_url` 为 `wxapp://post/{id}`

### 3. 禁止的字段名转换

❌ **严禁进行以下转换：**
- `url` ↔ `original_url`（必须使用 `original_url`）
- `source` ↔ `platform`（必须使用 `platform`）
- 下划线命名 ↔ 驼峰命名的转换
- 数据库字段名的任何形式的"美化"或"简化"

### 4. API响应标准格式

每个接口的响应数据项必须包含以下核心字段：

```json
{
  "create_time": "2025-01-15T10:30:00",
  "update_time": "2025-01-15T10:30:00", 
  "author": "作者名称",
  "platform": "平台标识",
  "original_url": "原文链接",
  "tag": "标签信息",
  "title": "标题",
  "content": "内容",
  "relevance": 0.85
}
```

### 5. 验证规则

在开发API接口时：
1. 检查返回字段名是否与对应数据库表字段名完全一致
2. 确保没有进行任何字段名转换
3. 保留数据库表中存在的所有有用字段（如 `is_official`, `view_count` 等）
4. 对于不同表的相同概念字段（如author），优先使用数据库中的实际字段名

### 6. 特殊情况处理

#### 多表查询时的字段冲突
- 不同表有相同字段名时，保持原字段名不变
- 通过 `platform` 字段区分数据来源

#### 计算字段
- `relevance` - 相关度分数（计算得出，非数据库字段）
- `is_truncated` - 内容是否被截断（API处理标识）

## 执行要求

1. **新建接口**：严格按照此规范设计字段名
2. **修改现有接口**：逐步调整为符合此规范
3. **代码审查**：字段名一致性作为必检项
4. **文档更新**：API文档必须反映真实的数据库字段名
