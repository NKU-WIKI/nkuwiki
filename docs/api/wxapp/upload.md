# 微信小程序 - 文件上传接口文档

本文档详细说明了微信小程序端用于上传文件的API端点。

## 上传单个图片

此接口用于上传单个图片文件，例如用户头像、帖子配图等。服务器会对图片进行压缩处理，并返回一个可公开访问的URL。

- **URL**: `/wxapp/upload/image`
- **Method**: `POST`
- **认证**: **需要** (Bearer Token)

---

### 请求格式

请求体必须为 `multipart/form-data` 格式。

**表单字段**:

| 字段名 | 类型   | 必须 | 描述                             |
| ------ | ------ | ---- | -------------------------------- |
| `file` | `File` | 是   | 要上传的图片文件。               |

**请求头 (Headers)**:

| Key             | Value           | 描述                                     |
| --------------- | --------------- | ---------------------------------------- |
| `Content-Type`  | `multipart/form-data` | 必须为此类型。                           |
| `Authorization` | `Bearer {token}`  | 将登录后获取的JWT Token放在这里。 |

---

### 响应

#### 成功响应 (200 OK)

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "url": "https://your-domain.com/static/202310/a1b2c3d4-e5f6-7890-1234-567890abcdef.jpg"
  },
  "details": "图片上传成功",
  "timestamp": "2023-10-27T10:00:00.000Z",
  "pagination": null
}
```

- **`data.url`**: 上传成功后图片的完整访问地址。前端应保存此URL，并在需要时（如创建帖子）将其提交给其他业务接口。

---

#### 失败响应

##### 1. 未授权 (401 Unauthorized)

如果请求头中没有提供有效JWT，或者JWT已过期。

```json
{
    "detail": "无法验证凭据"
}
```

##### 2. 文件类型不支持 (400 Bad Request)

如果上传的文件不是允许的图片格式（如 `jpeg`, `png`, `gif`）。

```json
{
  "code": 400,
  "message": "Bad Request",
  "data": null,
  "details": "不支持的文件类型，请上传jpeg, png或gif格式的图片。",
  "timestamp": "2023-10-27T10:05:00.000Z",
  "pagination": null
}
```

##### 3. 图片处理失败 (500 Internal Server Error)

如果服务器在处理或保存图片过程中发生内部错误。

```json
{
  "code": 500,
  "message": "Internal Server Error",
  "data": null,
  "details": "图片处理失败，请稍后重试。",
  "timestamp": "2023-10-27T10:06:00.000Z",
  "pagination": null
}
``` 