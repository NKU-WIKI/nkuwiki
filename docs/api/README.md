# NKUWiki API 文档

本文档提供了 NKUWiki 后端 API 的结构说明和使用指南。

## 1. 文档结构

API 文档按照功能模块进行组织，存放在不同的子目录中：

-   `agent/`: 与多智能体系统相关的接口。
-   `knowledge/`: 知识库、检索、洞察等核心功能的接口。
-   `wxapp/`: 主要服务于微信小程序的特定接口，如用户、帖子等。

每个子目录下的文档详细描述了该模块的具体端点（Endpoint）、参数和响应格式。**在进行开发前，请务必仔细阅读相关模块下的具体 API 文档。**

## 2. 数据库表结构

所有数据库表的结构定义（`CREATE TABLE` 语句）都存放在项目 `etl/load/mysql_tables/` 目录下。每个 `.sql` 文件对应一张数据表。

在开发和理解 API 时，可以参考此目录下的文件来了解数据表的详细字段和结构。

## 3. API 请求规范

请求地址：https://nkuwiki.com

### 3.1 请求前缀

所有对后端服务的 API 请求都必须以 `/api/` 作为路径前缀。

**示例:**
```
GET /api/knowledge/search?query=南开大学
```

### 3.2 版本区分（正式版 vs. 体验版）

后端服务同时部署了 `main` (正式版) 和 `dev` (体验版) 两个分支。客户端可以通过在 HTTP 请求头中添加 `X-Branch` 字段来指定访问哪个版本。

-   `X-Branch: main`: 请求将被路由到正式版服务。
-   `X-Branch: dev`: 请求将被路由到体验版（开发版）服务。
-   **不提供 `X-Branch` 请求头**: 默认情况下，请求会访问 `main` 正式版服务。

这种机制使得前端可以在不修改请求路径的情况下，方便地在不同环境之间进行切换和测试。

**请求示例 (使用 cURL):**

```bash
# 请求正式版服务 (或不加 X-Branch 头)
curl -H "X-Branch: main" https://www.nkuwiki.com/api/some-endpoint

# 请求体验版服务
curl -H "X-Branch: dev" https://www.nkuwiki.com/api/some-endpoint
```

### 3.3 请求方法

-   **GET**: 用于幂等的数据获取操作。
    -   **所有参数**必须通过**查询字符串** (`?key=value`) 传递。
    -   **禁止**在 GET 请求中使用请求体 (`Request Body`)。

-   **POST**: 用于非幂等的数据创建或更新操作。
    -   **所有参数**必须通过**请求体**以 JSON 格式传递。
    -   **禁止**在 POST 请求的 URL 中附加查询参数。

## 4. API 响应结构

所有 API 接口都遵循统一的响应格式，以确保一致性和可预测性。

### 4.1 标准响应

用于非列表数据的请求，如获取单个资源或执行操作。

```json
{
  "code": 200,
  "message": "success",
  "data": {},
  "details": null,
  "timestamp": "2024-07-29T12:00:00.000Z"
}
```
-   `code`: HTTP 状态码，`200` 表示成功。
-   `message`: 响应消息，通常为 `success` 或错误信息。
-   `data`: 核心响应数据，可以是对象或 null。
-   `details`: 详细的错误信息，成功时为 `null`。
-   `timestamp`: 服务器响应时间戳。

### 4.2 分页响应

用于返回列表数据的请求，在标准响应的基础上增加了 `pagination` 字段。

```json
{
  "code": 200,
  "message": "success",
  "data": [
    { "id": 1, "title": "..." },
    { "id": 2, "title": "..." }
  ],
  "pagination": {
    "total": 100,
    "page": 1,
    "page_size": 10,
    "total_pages": 10,
    "has_more": true
  },
  "timestamp": "2024-07-29T12:00:00.000Z"
}
```
-   `pagination.total`: 总记录数。
-   `pagination.page`: 当前页码。
-   `pagination.page_size`: 每页记录数。
-   `pagination.total_pages`: 总页数。
-   `pagination.has_more`: 是否还有下一页。

## 5. 端到端请求示例

下面是一个完整的请求示例，演示如何获取知识库文章列表的第一页，每页包含5条数据。

**请求 (cURL):**
```bash
curl -X GET "https://www.nkuwiki.com/api/knowledge/posts?page=1&page_size=5"
```

**响应 (成功获取列表):**
```json
{
  "code": 200,
  "message": "success",
  "data": [
    {
      "id": 101,
      "title": "关于申请2024年本科生创新科研项目的通知",
      "author": "教务处",
      "platform": "website_nku",
      "publish_time": "2024-07-28T10:00:00"
    },
    {
      "id": 102,
      "title": "南开大学2024年暑期社会实践活动启动",
      "author": "校团委",
      "platform": "wechat_nku",
      "publish_time": "2024-07-27T18:30:00"
    }
  ],
  "pagination": {
    "total": 50,
    "page": 1,
    "page_size": 2,
    "total_pages": 25,
    "has_more": true
  },
  "timestamp": "2024-07-29T14:30:00.123Z"
}
```
*（注：为简洁起见，`data` 数组中仅展示2条记录，且字段已简化。）* 