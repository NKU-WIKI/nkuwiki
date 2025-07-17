# 数据加载模块开发指南

## 模块概述

`etl/load` 模块负责将转换后的数据加载到目标存储系统中，是 ETL 流程中的"Load"环节。支持 MySQL 数据库的数据写入，包含表结构定义、数据导入、表重建、数据库连接池等工具。

## 目录结构

- `__init__.py` - 模块入口，导出常用方法
- `db_core.py` - 数据库核心操作方法（异步/同步查询、插入、更新等）
- `db_pool_manager.py` - 数据库连接池管理
- `const.py` - 常量定义
- `import_data.py` - 通用数据导入脚本，支持多平台 JSON 数据批量导入
- `dump_tables.py` - 数据库表结构导出工具
- `recreate_all_tables.py` - 一键重建所有表
- `recreate_wxapp_tables.py` - 重建小程序相关表
- `mysql_tables/` - MySQL 表结构定义（.sql 文件）

## 常用脚本说明

### 1. 通用数据导入（import_data.py）

支持 wechat、website、market、wxapp 等多平台 JSON 数据批量导入 MySQL。

**用法示例：**
```bash
# 基本用法
python -m etl.load.import_data --platform wechat --tag nku --data-dir /data/raw/wechat

# 导入前重建表
python -m etl.load.import_data --platform website --tag nku --data-dir /data/raw/website --pattern "*.json" --rebuild-table

# 显示详细日志
python -m etl.load.import_data --platform market --verbose
```

**参数说明：**
- `--platform`：必填，平台类型（wechat、website、market、wxapp）
- `--tag`：数据标签，默认 nku
- `--data-dir`：数据目录路径
- `--pattern`：文件匹配模式，默认 *.json
- `--rebuild-table`：导入前重建表
- `--batch-size`：批量插入大小，默认 100
- `--verbose`：显示详细日志

**支持 JSON 格式：**
- 直接记录列表
- 包含 data 字段的对象

### 2. 表结构管理

- `recreate_all_tables.py`：重建所有表（慎用，数据会清空）
- `recreate_wxapp_tables.py`：重建小程序相关表
- `mysql_tables/`：所有表结构 SQL 定义，建新表或加字段需在此目录下操作

### 3. 数据库操作

- `db_core.py`：提供异步/同步的数据库操作方法，供业务代码直接调用
- `db_pool_manager.py`：数据库连接池管理，提升并发性能

### 4. 其他工具

- `dump_tables.py`：导出数据库表结构

## 日志与调试

- 日志请使用 core/utils/logger.py 的 register_logger 方法注册，debug 级别为主，重要信息用 info。
- 脚本支持详细日志输出，便于调试。

## 注意事项

- 大批量数据建议使用批处理
- 生产环境请使用连接池
- 建新表或加字段请在 mysql_tables 目录下操作，遵循命名规范
- 只允许加字段，不允许改字段类型

## 参考

- 具体数据库操作方法见 `db_core.py`
- 数据导入最佳实践见 `import_data.py`
- 表结构定义见 `mysql_tables/`

