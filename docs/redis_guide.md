# Redis配置与使用指南

Redis在nkuwiki项目中主要用于数据库连接池管理、缓存和会话存储。

## 配置方法

### 基础配置

配置文件位置：`config.json` 中的 `etl.data.redis` 节点

```json
{
  "etl": {
    "data": {
      "redis": {
        "host": "localhost",
        "port": 6379,
        "db": 0,
        "password": "Nkuwiki_Redis_2025!"
      }
    }
  }
}
```

### 服务器配置

生产环境配置文件：`/etc/redis/redis.conf`

关键配置项：
```
maxmemory 4gb
maxmemory-policy allkeys-lru
appendonly yes
bind 127.0.0.1
requirepass 强密码
```

## 使用说明

### 数据库连接池管理

`etl/load/db_pool_manager.py` 使用Redis协调多实例环境下的连接池大小。
当Redis不可用时自动降级为本地模式。

### 测试连接

```bash
python tools/test_redis.py
```

### 管理接口

- 连接池状态：`GET /api/admin/system/db-pool`
- 调整连接池：`POST /api/admin/system/db-pool/resize?size=16`

## 常见问题

1. **连接失败**：检查服务状态、配置和防火墙
2. **认证失败**：检查密码配置
3. **性能问题**：调整连接池大小和内存策略

相关日志：
- 服务器日志：`/var/log/redis/redis-server.log`
- 应用日志：`logs/etl.log`

## 安全建议

1. 不在公网暴露Redis端口
2. 使用强密码
3. 限制内存使用
4. 定期备份数据

## 参考资料

- [Redis官方文档](https://redis.io/documentation)
- [Redis安全最佳实践](https://redis.io/topics/security) 