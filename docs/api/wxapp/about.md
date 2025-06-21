### GET /api/wxapp/about

**功能描述**：获取应用的"关于"信息，如版本号、描述、联系方式等。

**请求参数**：无

**成功响应示例**:

```json
{
    "code": 200,
    "message": "success",
    "data": {
        "app_name": "nkuwiki",
        "version": "0.0.9",
        "description": "nkuwiki是南开大学校园知识共享平台，致力于构建南开知识共同体，践行开源·共治·普惠三位一体价值体系。",
        "company": "沈阳最优解教育科技有限公司",
        "email": "support@nkuwiki.com",
        "github": "https://github.com/NKU-WIKI/nkuwiki",
        "website": "https://nkuwiki.com",
        "copyright": "©2025 nkuwiki团队"
    },
    "details": null,
    "timestamp": "2025-06-21T17:04:02.335117",
    "pagination": null
}
``` 