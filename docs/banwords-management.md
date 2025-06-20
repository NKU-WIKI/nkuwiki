# 敏感词管理系统

## 概述

NKUWiki项目的敏感词管理系统已从前端静态文件迁移到后端动态管理，实现了更灵活和安全的敏感词控制。

## 文件结构

```
nkuwiki/
├── banwords.json              # 敏感词库文件（被gitignore忽略）
├── banwords-template.json     # 敏感词库模板文件
├── scripts/
│   └── migrate_banwords.py    # 数据迁移脚本
├── api/routes/wxapp/
│   └── banwords.py           # 敏感词管理API
└── services/app/utils/
    ├── banwordManager.js     # 前端敏感词管理器
    ├── textCensor.js         # 文本审核工具
    └── banwords.js           # 原始JS文件（已弃用）
```

## 敏感词库格式

### JSON文件结构

```json
{
  "description": "敏感词库配置文件",
  "version": "1.0.0",
  "lastUpdate": "2024-01-01 12:00:00",
  "library": {
    "political": {
      "defaultRisk": 5,
      "description": "政治敏感词",
      "words": ["词1", "词2", ...],
      "patterns": []
    },
    "violent": {
      "defaultRisk": 4,
      "description": "暴力相关敏感词",
      "words": [...],
      "patterns": []
    }
  }
}
```

### 分类说明

| 分类 | 风险等级 | 描述 |
|------|----------|------|
| political | 5 | 政治敏感词 |
| violent | 4 | 暴力相关敏感词 |
| pornographic | 5 | 色情低俗敏感词 |
| gambling | 4 | 赌博相关敏感词 |
| illegal | 4 | 违法犯罪敏感词 |
| abuse | 3 | 辱骂攻击敏感词 |
| advertisement | 2 | 广告垃圾信息 |
| spam | 2 | 垃圾信息 |
| religion | 3 | 宗教相关敏感词 |
| ethnic | 4 | 民族地区敏感词 |

## API接口

### 获取敏感词库

```http
GET /api/wxapp/banwords
```

**响应示例：**
```json
{
  "status": "success",
  "data": {
    "library": {
      "political": {
        "defaultRisk": 5,
        "words": [...],
        "patterns": []
      }
    }
  },
  "message": "获取敏感词库成功"
}
```

### 获取分类列表

```http
GET /api/wxapp/banwords/categories
```

### 添加敏感词

```http
POST /api/wxapp/banwords
Content-Type: application/json

{
  "category": "political",
  "words": ["新词1", "新词2"],
  "risk": 5
}
```

### 删除敏感词

```http
DELETE /api/wxapp/banwords/{category}/{word}
```

### 更新分类词汇

```http
PUT /api/wxapp/banwords/{category}
Content-Type: application/json

["词1", "词2", "词3"]
```

## 前端使用

### 初始化和检测

```javascript
const textCensor = require('./utils/textCensor');

// 检测敏感词（自动从后端获取词库）
const result = await textCensor.check('测试文本');
console.log(result.risk); // true/false
console.log(result.matches); // 匹配的敏感词
console.log(result.reason); // 风险原因

// 过滤敏感词
const filteredText = await textCensor.filter('测试文本');
```

### 敏感词库管理

```javascript
const banwordManager = require('./utils/banwordManager');

// 获取分类列表
const categories = await banwordManager.getCategories();

// 获取特定分类的词汇
const words = await banwordManager.getCategoryWords('political');

// 强制更新词库
await banwordManager.forceUpdate();

// 清除缓存
banwordManager.clearCache();
```

## 缓存机制

- **缓存时间**: 30分钟
- **自动更新**: 缓存过期时自动从后端获取
- **错误处理**: 网络失败时使用默认词库
- **并发控制**: 避免同时多次请求后端

## 部署和维护

### 初始化敏感词库

`banwords.json` 文件包含了所有的敏感词数据，后端服务依赖此文件来加载词库。

如果项目根目录下不存在 `banwords.json` 文件，你需要手动创建它。你可以创建一个空的词库文件，内容如下:

```json
{
  "description": "敏感词库配置文件",
  "version": "1.0.0",
  "lastUpdate": "2024-01-01 12:00:00",
  "library": {}
}
```

随后，你可以通过API或直接编辑此文件来添加敏感词。

### 安全注意事项

1.  **敏感词库文件** (`banwords.json`) 已被 `.gitignore` 忽略，以防敏感内容泄露。
2.  **不要将敏感词库提交到版本控制系统**。
3. **定期备份敏感词库文件**
4. **生产环境请使用更严格的访问控制**

### 更新词库

1. **通过API更新**（推荐）:
   - 使用前端管理界面
   - 调用REST API接口

2. **直接编辑文件**:
   - 编辑 `banwords.json` 文件
   - 重启后端服务以生效

### 监控和日志

- 检查后端日志中的敏感词相关错误
- 监控API调用频率和性能
- 定期审查敏感词匹配统计

## 故障排除

### 常见问题

1. **前端获取不到敏感词**
   - 检查 `banwords.json` 文件是否存在
   - 检查文件格式是否正确
   - 查看后端日志错误信息

2. **敏感词检测不生效**
   - 确认前端已正确初始化 textCensor
   - 检查缓存是否过期
   - 验证API响应数据格式

3. **更新敏感词不生效**
   - 清除前端缓存
   - 检查API保存是否成功
   - 确认JSON文件权限

### 调试模式

1. **启用调试日志**:
```javascript
// 前端
const logger = require('./utils/logger');
logger.setLevel('debug');
```

2. **检查缓存状态**:
```javascript
console.log('缓存过期:', banwordManager.isCacheExpired());
console.log('最后更新:', banwordManager.lastUpdateTime);
```

## 升级和迁移

当需要升级敏感词系统时：

1. 备份当前敏感词库
2. 更新代码和API
3. 运行数据迁移脚本
4. 测试功能是否正常
5. 部署到生产环境

## 性能优化

1. **前端缓存**: 减少不必要的API调用
2. **增量更新**: 仅传输变更的敏感词
3. **压缩传输**: API响应使用gzip压缩
4. **异步处理**: 避免阻塞用户界面

## 扩展功能

未来可以考虑的扩展：

1. **敏感词白名单**: 允许特定词汇通过
2. **用户级别控制**: 不同用户不同敏感词策略
3. **机器学习检测**: 基于AI的敏感内容识别
4. **统计分析**: 敏感词命中率统计
5. **审核工作流**: 人工审核机制 