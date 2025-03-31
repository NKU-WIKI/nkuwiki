#!/usr/bin/env python3
"""
检查数据库中存在的表
"""
import sys
import os
import json

# 添加项目根目录到sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from etl.load.db_core import execute_query
from core.utils.logger import register_logger

logger = register_logger('api.test.check_db')

def check_db_tables():
    """检查数据库中的表"""
    try:
        # 1. 获取所有表
        tables_sql = "SHOW TABLES"
        tables = execute_query(tables_sql)
        
        if tables:
            # 表名在不同系统中可能位于不同的键下，尝试提取
            table_name_key = list(tables[0].keys())[0] if tables[0] else 'Tables_in_nkuwiki'
            table_names = [table[table_name_key] for table in tables]
            
            print(f"数据库中共有 {len(table_names)} 个表:")
            for table in table_names:
                print(f"- {table}")
            
            logger.debug(f"数据库表: {table_names}")
        else:
            print("数据库中没有表")
        
        # 2. 检查是否存在wxapp_开头的表
        wxapp_tables = [table for table in table_names if table.startswith('wxapp_')] if tables else []
        if wxapp_tables:
            print(f"\n找到 {len(wxapp_tables)} 个wxapp_开头的表:")
            for table in wxapp_tables:
                print(f"- {table}")
        else:
            print("\n没有找到wxapp_开头的表")
            
        # 3. 检查是否需要初始化数据库
        print("\n检查数据库初始化状态...")
        # 加载SQL表结构文件列表
        sql_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "etl", "load", "mysql_tables")
        sql_files = [f for f in os.listdir(sql_dir) if f.endswith('.sql')]
        
        print(f"找到 {len(sql_files)} 个SQL表结构文件:")
        for sql_file in sql_files:
            print(f"- {sql_file}")
            
        # 检查是否有实现初始化数据库的功能
        print("\n尝试查找数据库初始化函数...")
        if not wxapp_tables and sql_files:
            print("数据库中没有wxapp_表，可能需要初始化数据库")
            
    except Exception as e:
        import traceback
        logger.error(f"检查数据库表时出错: {str(e)}")
        logger.error(traceback.format_exc())
        print(f"检查数据库表时出错: {str(e)}")

if __name__ == "__main__":
    print("开始检查数据库表...")
    check_db_tables()
    print("检查完成") 