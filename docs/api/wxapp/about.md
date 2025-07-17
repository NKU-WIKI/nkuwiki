# 微信小程序：关于信息接口

本文档详细说明了获取小程序“关于”信息的API接口。

## 1. 获取关于信息

- **Endpoint**: `GET /api/wxapp/about`
- **Permissions**: `Public`
- **Tags**: `wxapp-about`
- **Summary**: 获取应用的“关于”信息，如版本号、描述、联系方式等。该信息通常在服务器的配置文件中静态定义。

### 请求参数 (Query)

该接口无查询参数。

### 成功响应 (200 OK)

```json
{
    "code": 200,
    "message": "success",
    "data": {
        "app_name": "nkuwiki",
        "version": "1.0.0",
        "description": "nkuwiki是南开大学校园知识共享平台，致力于构建南开知识共同体。",
        "company": "南开大学",
        "email": "support@nkuwiki.com",
        "github": "https://github.com/NKU-WIKI/nkuwiki",
        "website": "https://nkuwiki.com",
        "copyright": "©2025 nkuwiki团队"
    },
    "details": null,
    "timestamp": "2025-07-13T12:40:00.123456",
    "pagination": null
}
```

### 失败响应 (404 Not Found)

如果服务器未配置相关信息，将返回错误。

```json
{
    "code": 404,
    "message": "关于信息未配置",
    "data": null,
    "details": null,
    "timestamp": "2025-07-13T12:41:00.567890",
    "pagination": null
}
``` 