#!/usr/bin/env python
"""
MySQL查询测试脚本
用于测试与MySQL数据库的连接和查询功能
"""
import sys
from pathlib import Path
import json
import time

# 直接输出消息，不依赖于logger
print("开始执行MySQL测试脚本...")
print(f"当前Python版本: {sys.version}")
print(f"当前工作目录: {Path.cwd().absolute()}")

# 调试导入路径
sys.path.append(str(Path(__file__).resolve().parent))
print(f"sys.path: {sys.path}")

# 检查关键文件是否存在
etl_init = Path("etl/__init__.py")
load_init = Path("etl/load/__init__.py")
py_mysql = Path("etl/load/py_mysql.py")

print(f"etl/__init__.py 存在: {etl_init.exists()}")
print(f"etl/load/__init__.py 存在: {load_init.exists()}")
print(f"etl/load/py_mysql.py 存在: {py_mysql.exists()}")

# 使用基本的日志输出
def log(message, level="INFO"):
    print(f"[{level}] {message}")

# 尝试导入配置模块
try:
    from config import Config
    config = Config()
    log("配置模块加载成功")
    
    # 打印MySQL配置
    db_host = config.get('etl.data.mysql.host', 'N/A')
    db_port = config.get('etl.data.mysql.port', 'N/A')
    db_user = config.get('etl.data.mysql.user', 'N/A')
    db_name = config.get('etl.data.mysql.name', 'N/A')
    
    log(f"MySQL配置: host={db_host}, port={db_port}, user={db_user}, db={db_name}")
except Exception as e:
    log(f"配置模块加载失败: {e}", "ERROR")
    
# 尝试导入数据库模块
try:
    log("尝试导入etl模块...")
    from etl import *
    log("etl模块导入成功")
    
    log("尝试导入etl.load模块...")
    from etl.load import get_conn
    log("etl.load模块导入成功")
    
    log("尝试导入数据库函数...")
    from etl.load.py_mysql import (
        query_records, count_records, execute_custom_query, get_nkuwiki_tables
    )
    log("数据库函数导入成功")
except Exception as e:
    log(f"模块导入失败: {e}", "ERROR")
    import traceback
    traceback.print_exc()
    sys.exit(1)

def test_connection():
    """测试数据库连接"""
    log("测试数据库连接...")
    try:
        with get_conn() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                if result and result[0] == 1:
                    log("数据库连接成功!")
                    return True
                else:
                    log("数据库连接失败: 无法验证连接", "ERROR")
                    return False
    except Exception as e:
        log(f"数据库连接失败: {str(e)}", "ERROR")
        import traceback
        traceback.print_exc()
        return False

def test_get_tables():
    """测试获取表列表"""
    log("测试获取表列表...")
    try:
        tables = get_nkuwiki_tables()
        if tables:
            log(f"获取到 {len(tables)} 个表: {', '.join(tables[:5])}...")
            if len(tables) > 5:
                log(f"更多表: {len(tables) - 5} 个...")
            return tables
        else:
            log("数据库中没有找到表", "WARNING")
            return []
    except Exception as e:
        log(f"获取表列表失败: {str(e)}", "ERROR")
        import traceback
        traceback.print_exc()
        return []

def test_table_structure(table_name):
    """测试获取表结构"""
    log(f"测试获取表 {table_name} 的结构...")
    try:
        structure = execute_custom_query(f"DESCRIBE {table_name}")
        if structure:
            log(f"表 {table_name} 结构:")
            for field in structure:
                log(f"  {field['Field']} ({field['Type']})"
                   f" {'NOT NULL' if field['Null'] == 'NO' else ''}"
                   f" {'PRIMARY KEY' if field['Key'] == 'PRI' else ''}")
            return structure
        else:
            log(f"表 {table_name} 不存在或为空", "WARNING")
            return []
    except Exception as e:
        log(f"获取表结构失败: {str(e)}", "ERROR")
        return []

def test_query_records(table_name, limit=5):
    """测试查询记录"""
    log(f"测试查询表 {table_name} 的记录 (限制 {limit} 条)...")
    try:
        records = query_records(
            table_name=table_name,
            conditions=None,
            order_by=None,
            limit=limit,
            offset=0
        )
        if records:
            log(f"从表 {table_name} 查询到 {len(records)} 条记录:")
            for i, record in enumerate(records, 1):
                # 检查record是否为字典
                if isinstance(record, dict):
                    # 最多显示前3个字段
                    field_sample = {k: v for k, v in list(record.items())[:3]}
                    log(f"  记录 {i}: {json.dumps(field_sample, ensure_ascii=False)}")
                    if len(record) > 3:
                        log(f"    ... 更多字段: {len(record) - 3} 个")
                else:
                    log(f"  记录 {i}: {record} (注意: 不是字典类型，而是 {type(record)})")
            return records
        else:
            log(f"表 {table_name} 中没有记录", "WARNING")
            return []
    except Exception as e:
        log(f"查询记录失败: {str(e)}", "ERROR")
        import traceback
        traceback.print_exc()
        return []

def test_count_records(table_name):
    """测试统计记录数量"""
    log(f"测试统计表 {table_name} 的记录数量...")
    try:
        count = count_records(table_name)
        log(f"表 {table_name} 中有 {count} 条记录")
        return count
    except Exception as e:
        log(f"统计记录数量失败: {str(e)}", "ERROR")
        return -1

def test_custom_query(query):
    """测试自定义查询"""
    log(f"测试自定义查询: {query}")
    try:
        result = execute_custom_query(query)
        if result:
            log(f"查询返回 {len(result)} 条结果:")
            for i, row in enumerate(result[:5], 1):
                log(f"  结果 {i}: {json.dumps(row, ensure_ascii=False)}")
            if len(result) > 5:
                log(f"  ... 更多结果: {len(result) - 5} 条")
            return result
        else:
            log("查询没有返回结果", "WARNING")
            return []
    except Exception as e:
        log(f"自定义查询失败: {str(e)}", "ERROR")
        return []

def main():
    """主测试函数"""
    log("开始MySQL数据库查询测试...")
    
    # 测试数据库连接
    if not test_connection():
        log("数据库连接测试失败，终止后续测试", "ERROR")
        return False
    
    # 获取所有表
    tables = test_get_tables()
    if not tables:
        log("未找到表，跳过表相关测试", "WARNING")
        return False
    
    # 为测试选择第一个表
    test_table = tables[2]
    log(f"选择表 {test_table} 进行后续测试")
    
    # 测试获取表结构
    test_table_structure(test_table)
    
    # 测试统计记录数量
    count = test_count_records(test_table)
    
    # 测试查询记录
    if count > 0:
        test_query_records(test_table)
    
    # 测试自定义查询
    test_custom_query(f"SELECT * FROM {test_table} LIMIT 3")
    
    # 高级查询测试 (如果表中有列)
    structure = execute_custom_query(f"DESCRIBE {test_table}")
    if structure and len(structure) > 0:
        first_column = structure[0]['Field']
        log(f"使用第一列 {first_column} 进行高级查询测试")
        test_custom_query(f"SELECT COUNT(*), {first_column} FROM {test_table} GROUP BY {first_column} LIMIT 5")
    
    log("MySQL数据库查询测试完成")
    return True

if __name__ == "__main__":
    try:
        log("=== MySQL API 测试开始 ===")
        start_time = time.time()
        success = main()
        elapsed = time.time() - start_time
        log(f"测试{'成功' if success else '失败'}完成，耗时: {elapsed:.2f} 秒")
        log("=== MySQL API 测试结束 ===")
    except KeyboardInterrupt:
        log("测试被用户中断", "WARNING")
    except Exception as e:
        log(f"测试过程中发生未处理异常: {str(e)}", "ERROR")
        import traceback
        traceback.print_exc()