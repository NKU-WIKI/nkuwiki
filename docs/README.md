# 南开Wiki RAG接口文档

## 文档导航

南开Wiki检索增强生成(RAG)接口文档集合，用于开发者了解和使用RAG服务。

### 核心文档

- [RAG API接口文档](./rag_api.md) - 详细的API接口说明，包含参数、响应格式和示例
- [RAG接口使用指南](./rag_usage_guide.md) - 开发者使用指南，包含最佳实践和示例代码
- [RAG接口测试报告](./rag_test_report.md) - 测试结果和性能报告

## 快速开始

对于希望快速集成RAG接口的开发者，建议先阅读[RAG接口使用指南](./rag_usage_guide.md)，了解基本概念和使用方式。

需要详细API参数和响应格式的开发者，可以参考[RAG API接口文档](./rag_api.md)。

## 测试环境

我们提供了一个简化的测试环境：

```
http://localhost:8888/rag
```

该测试环境实现了与正式环境相同的API接口，但使用了模拟数据，非常适合前端开发和接口集成测试。

## 多实例动态负载均衡连接池

nkuwiki现已支持多实例环境下的动态负载均衡连接池，特点如下：

1. **实例自动协调**：通过Redis实现多实例间连接池资源的协调分配
2. **基于负载因子动态分配**：根据实例CPU使用率和连接使用情况动态分配连接池大小
3. **自适应调整**：定期检测系统负载变化，自动调整连接池大小
4. **失败自动降级**：在连接池达到极限时自动创建独立连接作为应急措施
5. **实时监控**：提供实时监控API查看各实例连接池状态

### 连接池监控接口

- `GET /api/admin/system/db-pool` - 获取数据库连接池状态
- `POST /api/admin/system/db-pool/resize?size={size}` - 手动调整连接池大小

### 使用示例

```python
# 使用上下文管理器安全地获取和释放连接
from etl.load.db_pool_manager import get_db_connection

def execute_db_operation():
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM some_table")
            return cursor.fetchall()
```

### 配置要求

使用多实例动态连接池需要以下配置：

1. Redis服务器（用于实例间协调）
2. MySQL数据库服务器支持连接池
3. 安装psutil和redis库（已添加到requirements.txt）

配置项在config.json中：

```json
{
  "redis": {
    "host": "localhost",
    "port": 6379,
    "db": 0,
    "password": null
  }
}
```

## 贡献与反馈

如发现文档错误或有改进建议，请通过以下方式反馈：

1. 提交Issue到项目仓库
2. 发送邮件至维护团队
3. 在小程序内提交反馈

## 版本历史

**v1.0.0** (2025-03-24)
- 初始版本
- 支持基本RAG功能
- 提供三种输出格式：markdown、text、html
