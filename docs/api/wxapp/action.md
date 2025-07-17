# 微信小程序：通用互动接口

本文档详细说明了微信小程序中用于处理点赞、收藏、关注等通用互动行为的API接口。

## 1. 通用切换操作 (Toggle Action)

此接口是处理所有状态切换类操作的核心，例如：点赞/取消点赞、收藏/取消收藏、关注/取消关注。

- **Endpoint**: `POST /wxapp/action/toggle`
- **认证**: 需要认证。请在请求头中携带有效的 JWT: `Authorization: Bearer <token>`。

### 请求体 (Body)

| 参数 | 类型 | 是否必须 | 可选值 | 描述 |
| --- | --- | --- | --- | --- |
| `target_id` | `integer` or `string` | 是 | | 互动目标的ID。如果 `target_type` 是 `user`，则为用户的 `openid` (string)；否则为 `id` (integer)。 |
| `target_type` | `string` | 是 | `post`, `comment`, `user` | 互动目标的类型。 |
| `action_type` | `string` | 是 | `like`, `favorite`, `follow` | 互动的类型。 |

### 行为逻辑

1.  **检查记录**: 服务器会根据 `token` 解析出的 `openid`，检查 `wxapp_action` 表中是否存在匹配 `(openid, action_type, target_id, target_type)` 的记录。
2.  **切换状态**:
    -   如果**不存在**记录，则创建一条新记录，表示行为被激活 (例如，用户点了赞)。
    -   如果**存在**记录，则删除该记录，表示行为被取消 (例如，用户取消了点赞)。
3.  **更新计数**:
    -   操作成功后，会自动更新相关表的计数字段。例如，对 `post` 进行 `like` 操作会增/减 `wxapp_post` 表的 `like_count` 字段。

### 响应

- **200 OK**:
  ```json
  {
    "code": 200,
    "message": "success",
    "data": {
      "is_active": true
    },
    "details": null,
    "timestamp": "..."
  }
  ```
  - `is_active`: `true` 表示操作后行为是激活状态 (已点赞/已收藏/已关注)，`false` 表示是未激活状态。

- **404 Not Found**: 如果 `target_id` 对应的资源不存在。
- **400 Bad Request**: 如果缺少必要参数或参数值不合法 (如 `target_type` 不支持)。

*注意：为节省篇幅，`/wxapp/post/like`、`/wxapp/post/favorite`、`/wxapp/action/comment/like` 等具体的点赞/收藏接口已废弃，请统一使用通用的 `/wxapp/action/toggle` 接口。* 