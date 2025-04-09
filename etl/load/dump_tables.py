#!/usr/bin/env python3
"""
导出所有表结构的脚本
"""
import sys
sys.path.append('.')
from etl.load.db_core import execute_query

def main():
    """主函数"""
    tables = execute_query('SHOW TABLES')
    print('数据库表结构信息：')
    print('=' * 80)

    for table_row in tables:
        table_name = list(table_row.values())[0]
        print(f'\n表名: {table_name}')
        print('-' * 80)
        
        # 获取表结构
        fields = execute_query(f'DESCRIBE {table_name}')
        
        # 打印字段信息
        print(f'{"字段名":<20}{"类型":<20}{"允许为空":<12}{"键":<10}{"默认值":<20}')
        print(f'{"-"*20:<20}{"-"*20:<20}{"-"*12:<12}{"-"*10:<10}{"-"*20:<20}')
        
        for field in fields:
            field_name = field.get('Field', '')
            field_type = field.get('Type', '')
            nullable = field.get('Null', '')
            key = field.get('Key', '')
            default = str(field.get('Default', ''))
            
            print(f'{field_name:<20}{field_type:<20}{nullable:<12}{key:<10}{default:<20}')
        
        print('-' * 80)

if __name__ == "__main__":
    main() 