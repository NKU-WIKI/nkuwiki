# 认证接口 (Authentication)

本模块负责处理用户的身份认证，如登录和令牌管理。

### 1. 微信小程序登录

**接口**：`POST /wxapp/auth/login`

**功能描述**：
此接口是微信小程序用户登录的唯一入口。它接收小程序通过 `wx.login()` 获取的临时登录凭证 `code`，并将其发送到后端。后端会使用此 `code` 向微信服务器换取用户的 `openid`，并以此为凭据，在系统内查找或创建用户记录，然后生成一个包含用户唯一标识 `user_id` 且具有时效性的 `JWT (JSON Web Token)` 作为用户的登录令牌返回给前端。

前端在获取到 `token` 后，应将其保存在本地（如 `Taro.storage`），并在后续所有需要认证的请求的 `Authorization` 请求头中携带它，格式为 `Bearer <token>`。

**请求体**:

| 参数 | 类型 | 是否必须 | 描述 |
| --- | --- | --- | --- |
| `code` | `string` | 是 | 小程序端通过 `wx.login()` 获取的临时登录凭证。 |
| `userInfo` | `object` | 否 | 包含用户信息的对象（如 `nickname`, `avatar`）。仅在用户首次登录（即后端数据库无该用户记录）时用于填充初始资料。 |

**成功响应示例 (登录/注册成功)**:

```json
{
    "code": 200,
    "message": "success",
    "data": {
        "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOjEsInVzZXJfaWQiOjEsImV4cCI6MTcxODk4NTc0OX0.abcdefg123456",
        "token_type": "bearer",
        "user_info": {
            "id": 1,
            "nickname": "微信用户",
            "avatar": "https://path/to/default/avatar.png",
            "gender": 0,
            "country": "China",
            "province": "Tianjin",
            "city": "Tianjin",
            "language": "zh_CN",
            "role": "user",
            "create_time": "2024-06-21 17:00:00",
            "last_login_time": "2024-06-21 17:00:00"
        }
    },
    "details": null,
    "timestamp": "2024-06-21 17:00:00",
    "pagination": null
}
```

**失败响应示例 (无效Code)**:

```json
{
    "code": 400,
    "message": "Bad Request",
    "data": null,
    "details": "微信登录凭证无效: invalid code, rid: 687325de-...",
    "timestamp": "2024-06-21 17:01:00",
    "pagination": null
}
```

**失败响应示例 (微信服务器错误)**:

```
```