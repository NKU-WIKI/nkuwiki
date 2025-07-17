### 请求体 (Body)

| 参数 | 类型 | 是否必须 | 可选值 | 描述 |
| --- | --- | --- | --- | --- |
| `target_id` | `integer` | 是 | | 互动目标的ID，**始终**为整数类型的主键ID。 |
| `target_type` | `string` | 是 | `post`, `comment`, `user` | 互动目标的类型。 |
| `action_type` | `string` | 是 | `like`, `favorite`, `follow` | 互动的类型。 |

### 行为逻辑

1.  **检查记录**: 服务器会根据 `token` 解析出的 `user_id`，检查 `wxapp_action` 表中是否存在匹配 `(user_id, action_type, target_id, target_type)` 的记录。
2.  **切换状态**:
    -   如果**不存在**记录，则创建一条新记录，表示行为被激活 (例如，用户点了赞)。 