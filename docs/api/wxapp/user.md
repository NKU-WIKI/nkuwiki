# 微信小程序：用户接口

本文档详细说明了与微信小程序中用户功能相关的所有API接口。

## 1. 获取用户公开信息

**接口**: `GET /wxapp/user/profile`

**功能描述**: 获取指定用户的公开信息，包括昵称、头像、简介和各项统计数据。此接口可匿名访问。如果请求时提供了有效的JWT，响应中会额外包含当前用户与目标用户的关注关系。

**认证**: 可选。

**请求参数 (Query)**:

| 参数 | 类型 | 是否必须 | 描述 |
| --- | --- | --- | --- |
| `user_id` | `integer` | 是 | 要查询的目标用户的ID。 |

**成功响应示例**:
返回的`data`对象不包含`openid`, `phone`等敏感信息。

```json
{
    "code": 200,
    "message": "success",
    "data": {
        "id": 1,
        "openid": "oLx8G7ADjzh23EzAJavndryh76rE",
        "nickname": "南开小透明",
        "avatar": "...",
        "bio": "你好，nkuwiki！",
        "post_count": 7,
        "follower_count": 1,
        "following_count": 0,
        "create_time": "2025-06-09T13:24:10",
        "is_following": false 
    }
}
```
- `is_following`: `boolean` 类型。仅在提供了有效JWT时出现，表示当前登录用户是否关注了目标用户。

---

## 2. 获取当前登录用户的完整信息

**接口**: `GET /wxapp/user/my/profile`

**功能描述**: 获取当前登录用户的完整个人信息，用于"我的"页面或个人资料编辑页。此接口直接返回通过JWT依赖注入的用户对象，性能最佳。

**认证**: 必需。

**成功响应示例**:

```json
{
    "code": 200,
    "message": "success",
    "data": {
        "id": 1,
        "openid": "oLx8G7ADjzh23EzAJavndryh76rE",
        "nickname": "南开小透明",
        "avatar": "...",
        "bio": "你好，nkuwiki！",
        "wechatId": "my_wechat",
        "qqId": "12345",
        "phone": "13800138000",
        "post_count": 7,
        "follower_count": 1,
        "following_count": 0,
        "create_time": "2025-06-09T13:24:10",
        "role": "user"
    }
}
```

---

## 3. 更新用户信息

**接口**：`POST /wxapp/user/update`

**功能描述**：更新当前登录用户的个人信息。只传递需要更新的字段即可。

**认证**: 必需。

**请求体**:

| 参数 | 类型 | 是否必须 | 描述 |
| --- | --- | --- | --- |
| `nickname` | `string` | 否 | 新的用户昵称。 |
| `avatar` | `string` | 否 | 新的头像URL。 |
| `gender` | `integer` | 否 | 性别：0-未知, 1-男, 2-女。 |
| `bio` | `string` | 否 | 新的个人简介。 |
| `...` | `...` | 否 | 其他 wxapp_user 表中允许更新的字段。 |

**成功响应示例**:
响应体为更新后完整的用户对象。
```json
{
    "code": 200,
    "message": "success",
    "data": {
        "id": 1,
        "openid": "optX864KZIbWQz1GNszGD2fS-d5g",
        "nickname": "南开测试先锋",
        "avatar": "",
        "bio": "正在测试API文档的Agent"
    },
    "details": {
      "message": "用户信息更新成功"
    }
}
```

---

## 4. 获取指定用户的粉丝列表

**接口**：`GET /wxapp/user/followers`

**功能描述**：获取指定用户的粉丝列表。

**请求参数 (Query)**:

| 参数 | 类型 | 是否必须 | 描述 |
| --- | --- | --- | --- |
| `user_id` | `integer` | 是 | 要查询的用户的ID。 |
| `page` | `integer` | 否 | 页码, 默认为1。 |
| `page_size` | `integer`| 否 | 每页数量, 默认为10。 |

**成功响应示例**:
`data` 字段是一个包含用户对象的数组。

```json
{
    "code": 200,
    "message": "success",
    "data": [
        {
            "id": 2,
            "openid": "test_user_005",
            "nickname": "我是粉丝",
            "avatar": "...",
            "bio": "..."
        }
    ],
    "pagination": { "total": 1, "page": 1, ... }
}
```
---

## 5. 获取指定用户的关注列表

**接口**：`GET /wxapp/user/following`

**功能描述**：获取指定用户关注的用户列表。

**请求参数 (Query)**:

| 参数 | 类型 | 是否必须 | 描述 |
| --- | --- | --- | --- |
| `user_id` | `integer` | 是 | 要查询的用户的ID。 |
| `page` | `integer` | 否 | 页码, 默认为1。 |
| `page_size` | `integer`| 否 | 每页数量, 默认为10。 |

**成功响应示例**:
`data` 字段是一个包含用户对象的数组。
```json
{
    "code": 200,
    "message": "success",
    "data": [
        {
            "id": 3,
            "openid": "test_user_006",
            "nickname": "我关注的人",
            "avatar": "...",
            "bio": "..."
        }
    ],
    "pagination": { "total": 1, "page": 1, ... }
}
```
---

## 6. 获取我的粉丝列表

**接口**：`GET /wxapp/user/me/followers`

**功能描述**：获取**当前登录用户**的粉丝列表。

**认证**: 必需。

**请求参数 (Query)**:

| 参数 | 类型 | 是否必须 | 描述 |
| --- | --- | --- | --- |
| `page` | `integer` | 否 | 页码, 默认为1。 |
| `page_size` | `integer`| 否 | 每页数量, 默认为10。 |

**成功响应示例**:
响应结构与`GET /wxapp/user/followers`接口完全相同。

---

## 7. 获取我的关注列表

**接口**：`GET /wxapp/user/me/following`

**功能描述**：获取**当前登录用户**关注的用户列表。

**认证**: 必需。

**请求参数 (Query)**:

| 参数 | 类型 | 是否必须 | 描述 |
| --- | --- | --- | --- |
| `page` | `integer` | 否 | 页码, 默认为1。 |
| `page_size` | `integer`| 否 | 每页数量, 默认为10。 |

**成功响应示例**:
响应结构与`GET /wxapp/user/following`接口完全相同。

---

## 8. 获取用户的收藏列表

**接口**：`GET /wxapp/user/favorite`

**功能描述**：获取当前登录用户收藏的所有内容（目前支持帖子）。

**认证**: 必需。

**请求参数 (Query)**:

| 参数 | 类型 | 是否必须 | 描述 |
| --- | --- | --- | --- |
| `page` | `integer` | 否 | 页码, 默认为1。 |
| `page_size` | `integer`| 否 | 每页数量, 默认为10。 |

**成功响应示例**:
`data` 字段是一个包含收藏对象的数组，每个对象都有 `type` 字段以区分类型。

```json
{
    "code": 200,
    "message": "success",
    "data": [
        {
            "type": "post",
            "id": 12,
            "title": "我收藏的帖子标题",
            "content": "帖子内容预览...",
            "image": "...",
            "create_time": "...",
            "author_nickname": "帖子作者",
            "author_avatar": "..."
        }
    ],
    "pagination": { "total": 1, "page": 1, ... }
}
```

---

## 9. 获取用户的点赞列表

**接口**: `GET /wxapp/user/like`

**功能描述**: 获取当前登录用户点赞过的所有内容（目前支持帖子和评论）。

**认证**: 必需。

**请求参数 (Query)**:

| 参数 | 类型 | 是否必须 | 描述 |
| --- | --- | --- | --- |
| `page` | `integer` | 否 | 页码, 默认为1。 |
| `page_size` | `integer`| 否 | 每页数量, 默认为10。 |

**成功响应示例**:

`data` 字段是一个包含点赞对象的数组，每个对象都有 `type` 字段以区分类型。

```json
{
    "code": 200,
    "message": "success",
    "data": [
        {
            "type": "post",
            "post_info": { ... }
        },
        {
            "type": "comment",
            "comment_info": { ... }
        }
    ],
    "pagination": { "total": 2, "page": 1, ... }
}
```
---

## 10. 获取用户的评论列表

**接口**: `GET /wxapp/user/comment`

**功能描述**: 获取当前登录用户发表过的所有评论。

**认证**: 必需。

**请求参数 (Query)**:

| 参数 | 类型 | 是否必须 | 描述 |
| --- | --- | --- | --- |
| `page` | `integer` | 否 | 页码, 默认为1。 |
| `page_size` | `integer`| 否 | 每页数量, 默认为10。 |

**成功响应示例**:

`data` 字段是一个包含评论对象的数组。

```json
{
    "code": 200,
    "message": "success",
    "data": [
        {
            "id": 101,
            "post_id": 1,
            "content": "这是一个测试评论",
            "create_time": "2024-06-21T18:00:00",
            "like_count": 5
        }
    ],
    "pagination": { "total": 1, "page": 1, ... }
}
```
---

## 11. 获取用户列表 (管理员)

**接口**: `GET /wxapp/user/list`

**功能描述**: 获取用户列表，支持分页和按昵称搜索。

**认证**: 必需 (管理员)。

**请求参数 (Query)**:

| 参数 | 类型 | 是否必须 | 描述 |
| --- | --- | --- | --- |
| `page` | `integer` | 否 | 页码, 默认为1。 |
| `page_size` | `integer`| 否 | 每页数量, 默认为10。 |
| `nickname` | `string` | 否 | 按用户昵称进行模糊搜索。 |
| `sort_by` | `string` | 否 | 排序方式，可选值: `latest`, `popular`。 |

**成功响应示例**:

```json
{
    "code": 200,
    "message": "success",
    "data": [
        {
            "id": 1,
            "nickname": "南开测试先锋",
            "avatar": "...",
            "role": "admin",
            "create_time": "..."
        }
    ],
    "pagination": { "total": 1, "page": 1, ... }
}
```
---

## 12. 获取用户关系状态

**接口**: `GET /wxapp/user/status`

**功能描述**: 获取当前登录用户与目标用户的关系状态，例如是否关注。

**认证**: 必需。

**请求参数 (Query)**:

| 参数 | 类型 | 是否必须 | 描述 |
| --- | --- | --- | --- |
| `target_user_id` | `integer` | 是 | 目标用户的ID。 |

**成功响应示例**:

```json
{
    "code": 200,
    "message": "success",
    "data": {
        "is_following": true,
        "is_followed_by": false
    }
}
```

---

## 12. 同步用户信息 (已废弃)

**接口**：`POST /wxapp/user/sync`

**功能描述**：此接口仅为兼容旧版客户端而保留，**已废弃**。新的登录和用户信息同步逻辑已统一到 `POST /api/wxapp/auth/login` 接口中。调用此接口将返回错误。

**响应 (410 Gone)**:

```json
{
    "code": 410,
    "message": "此接口已废弃",
    "details": {
        "message": "请使用POST /api/wxapp/auth/login接口进行登录和同步"
    }
}
``` 