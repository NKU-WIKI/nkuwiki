#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import json
import mysql.connector
from datetime import datetime


def get_conn():
    """获取MySQL数据库连接"""
    try:
        conn = mysql.connector.connect(
            host='127.0.0.1',
            port=3306,
            user='nkuwiki',
            password='Nkuwiki0!',
            database='nkuwiki',
            use_pure=True
        )
        return conn
    except Exception as e:
        print(f"数据库连接失败: {e}")
        sys.exit(1)


def query_table(table_name, limit=1):
    """查询表内容"""
    try:
        conn = get_conn()
        cursor = conn.cursor(dictionary=True)
        
        query = f"SELECT * FROM {table_name} LIMIT %s"
        cursor.execute(query, (limit,))
        
        result = cursor.fetchall()
        
        # 处理datetime对象便于JSON序列化
        processed_result = []
        for row in result:
            processed_row = {}
            for key, value in row.items():
                if isinstance(value, datetime):
                    processed_row[key] = value.isoformat()
                else:
                    processed_row[key] = value
            processed_result.append(processed_row)
        
        cursor.close()
        conn.close()
        
        return processed_result
    except Exception as e:
        print(f"查询失败: {e}")
        return []


def execute_custom_query(query, params=None):
    """执行自定义SQL查询"""
    try:
        conn = get_conn()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute(query, params or ())
        
        result = cursor.fetchall()
        
        # 处理datetime对象便于JSON序列化
        processed_result = []
        for row in result:
            processed_row = {}
            for key, value in row.items():
                if isinstance(value, datetime):
                    processed_row[key] = value.isoformat()
                else:
                    processed_row[key] = value
            processed_result.append(processed_row)
        
        cursor.close()
        conn.close()
        
        return processed_result
    except Exception as e:
        print(f"查询失败: {e}")
        return []


def main():
    """直接从数据库查询数据并打印结果"""
    print("\n===== 直接从数据库查询数据 =====")
    
    # 查询一条记录
    print("\n1. 使用query_table函数查询:")
    result = query_table("wechat_nku", 1)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    # 使用execute_custom_query
    print("\n2. 使用execute_custom_query函数查询:")
    result = execute_custom_query("SELECT * FROM wechat_nku LIMIT 1")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    # 检查行数
    print("\n3. 检查表中的行数:")
    result = execute_custom_query("SELECT COUNT(*) as total FROM wechat_nku")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    # 检查是否有真实数据
    print("\n4. 查询完整的一行数据:")
    result = execute_custom_query("SELECT * FROM wechat_nku WHERE id = 1")
    if result:
        # 打印每个字段名和值
        row = result[0]
        print("\n字段名和值:")
        for key, value in row.items():
            print(f"{key}: {value}")
    else:
        print("未找到数据")
    
    # 检查数据分布
    print("\n5. 检查是否有内容不为'content'的记录:")
    result = execute_custom_query("SELECT * FROM wechat_nku WHERE content != 'content' LIMIT 5")
    print(f"找到 {len(result)} 条记录")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main() 