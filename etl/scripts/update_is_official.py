#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
为website_nku和wechat_nku表添加is_official字段并更新值
根据const.py中的official_author列表来判断是否为官方信息
"""
import sys
import os
import asyncio
from pathlib import Path

# 添加项目根目录到sys.path
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent
sys.path.insert(0, str(project_root))

from etl.load.db_core import async_execute_custom_query
from etl.load.const import official_author

async def check_column_exists(table_name, column_name):
    """检查表中是否存在指定列"""
    try:
        sql = f"SHOW COLUMNS FROM {table_name} LIKE '{column_name}'"
        result = await async_execute_custom_query(sql)
        return len(result) > 0
    except Exception as e:
        print(f"检查列是否存在失败: {str(e)}")
        return False

async def add_is_official_field_to_tables():
    """为表添加is_official字段"""
    try:
        # 为website_nku表添加字段
        if not await check_column_exists('website_nku', 'is_official'):
            website_sql = """
            ALTER TABLE website_nku
            ADD COLUMN `is_official` tinyint(1) NULL DEFAULT '0' COMMENT '是否为官方信息'
            """
            website_result = await async_execute_custom_query(website_sql, fetch=False)
            print(f"向website_nku表添加is_official字段: {website_result}")
        else:
            print("website_nku表已存在is_official字段")
        
        # 为wechat_nku表添加字段
        if not await check_column_exists('wechat_nku', 'is_official'):
            wechat_sql = """
            ALTER TABLE wechat_nku
            ADD COLUMN `is_official` tinyint(1) NULL DEFAULT '0' COMMENT '是否为官方信息'
            """
            wechat_result = await async_execute_custom_query(wechat_sql, fetch=False)
            print(f"向wechat_nku表添加is_official字段: {wechat_result}")
        else:
            print("wechat_nku表已存在is_official字段")
        
        return True
    except Exception as e:
        print(f"添加is_official字段失败: {str(e)}")
        return False

async def update_website_nku_is_official():
    """更新website_nku表中的is_official字段"""
    try:
        # 检查字段是否存在
        if not await check_column_exists('website_nku', 'is_official'):
            print("website_nku表中不存在is_official字段，请先添加字段")
            return -1
            
        # 查询所有记录
        total_count_sql = "SELECT COUNT(*) as total FROM website_nku"
        total_result = await async_execute_custom_query(total_count_sql)
        total_count = total_result[0]['total'] if total_result else 0
        print(f"website_nku表共有 {total_count} 条记录")
        
        # 重置is_official字段
        reset_sql = "UPDATE website_nku SET is_official = 0"
        reset_result = await async_execute_custom_query(reset_sql, fetch=False)
        print(f"重置website_nku表is_official字段，影响 {reset_result} 行")
        
        # 输出official_author列表前10个元素，用于调试
        print(f"official_author列表前10个元素: {official_author[:10] if len(official_author) > 0 else []}")
        print(f"official_author列表长度: {len(official_author)}")
        
        # 查询有多少author在official_author列表中
        sample_sql = "SELECT DISTINCT author FROM website_nku LIMIT 20"
        sample_authors = await async_execute_custom_query(sample_sql)
        print(f"website_nku表中的author样本: {[a['author'] for a in sample_authors]}")
        
        # 批量更新is_official字段
        # 由于author数量可能很多，我们分批处理
        batch_size = 100
        total_updated = 0
        
        for i in range(0, len(official_author), batch_size):
            batch = official_author[i:i+batch_size]
            if not batch:
                continue
            
            placeholders = ', '.join(['%s'] * len(batch))
            update_sql = f"""
            UPDATE website_nku 
            SET is_official = 1 
            WHERE author IN ({placeholders})
            """
            update_result = await async_execute_custom_query(update_sql, batch, fetch=False)
            total_updated += update_result
            print(f"批次 {i//batch_size+1}: 更新 {update_result} 条记录")
        
        print(f"更新website_nku表is_official字段，设置 {total_updated} 条记录为官方信息")
        
        # 查询更新后状态
        status_sql = "SELECT is_official, COUNT(*) as count FROM website_nku GROUP BY is_official"
        status_result = await async_execute_custom_query(status_sql)
        for row in status_result:
            print(f"website_nku表is_official={row['is_official']}的记录有 {row['count']} 条")
        
        return total_updated
    except Exception as e:
        print(f"更新website_nku表is_official字段失败: {str(e)}")
        return -1

async def update_wechat_nku_is_official():
    """更新wechat_nku表中的is_official字段"""
    try:
        # 检查字段是否存在
        if not await check_column_exists('wechat_nku', 'is_official'):
            print("wechat_nku表中不存在is_official字段，请先添加字段")
            return -1
            
        # 查询所有记录
        total_count_sql = "SELECT COUNT(*) as total FROM wechat_nku"
        total_result = await async_execute_custom_query(total_count_sql)
        total_count = total_result[0]['total'] if total_result else 0
        print(f"wechat_nku表共有 {total_count} 条记录")
        
        # 重置is_official字段
        reset_sql = "UPDATE wechat_nku SET is_official = 0"
        reset_result = await async_execute_custom_query(reset_sql, fetch=False)
        print(f"重置wechat_nku表is_official字段，影响 {reset_result} 行")
        
        # 查询有多少author在official_author列表中
        sample_sql = "SELECT DISTINCT author FROM wechat_nku LIMIT 20"
        sample_authors = await async_execute_custom_query(sample_sql)
        print(f"wechat_nku表中的author样本: {[a['author'] for a in sample_authors]}")

        # 批量更新is_official字段
        # 由于author数量可能很多，我们分批处理
        batch_size = 100
        total_updated = 0
        
        for i in range(0, len(official_author), batch_size):
            batch = official_author[i:i+batch_size]
            if not batch:
                continue
            
            placeholders = ', '.join(['%s'] * len(batch))
            update_sql = f"""
            UPDATE wechat_nku 
            SET is_official = 1 
            WHERE author IN ({placeholders})
            """
            update_result = await async_execute_custom_query(update_sql, batch, fetch=False)
            total_updated += update_result
            print(f"批次 {i//batch_size+1}: 更新 {update_result} 条记录")
        
        print(f"更新wechat_nku表is_official字段，设置 {total_updated} 条记录为官方信息")
        
        # 查询更新后状态
        status_sql = "SELECT is_official, COUNT(*) as count FROM wechat_nku GROUP BY is_official"
        status_result = await async_execute_custom_query(status_sql)
        for row in status_result:
            print(f"wechat_nku表is_official={row['is_official']}的记录有 {row['count']} 条")
        
        return total_updated
    except Exception as e:
        print(f"更新wechat_nku表is_official字段失败: {str(e)}")
        return -1

async def async_main():
    """异步主函数"""
    print("开始为website_nku和wechat_nku表添加并更新is_official字段")
    
    # 调试信息
    print(f"Python版本: {sys.version}")
    print(f"当前工作目录: {os.getcwd()}")
    print(f"sys.path: {sys.path}")
    
    # 第一步：添加字段
    if not await add_is_official_field_to_tables():
        print("添加字段失败，脚本终止")
        return -1
    
    # 第二步：更新字段值
    web_count = await update_website_nku_is_official()
    wechat_count = await update_wechat_nku_is_official()
    
    total_updated = web_count + wechat_count if web_count >= 0 and wechat_count >= 0 else -1
    if total_updated >= 0:
        print(f"成功更新is_official字段，共 {total_updated} 条记录被标记为官方信息")
    else:
        print("更新is_official字段失败")
    
    return total_updated

def main():
    """入口函数"""
    return asyncio.run(async_main())

if __name__ == "__main__":
    main() 