#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
为website_nku和wechat_nku表添加is_official字段并更新值
根据const.py中的official_author列表来判断是否为官方信息
优化版：解决原脚本卡住问题
"""
import sys
import os
import asyncio
import time
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

async def add_is_official_field(table_name):
    """为指定表添加is_official字段"""
    try:
        if not await check_column_exists(table_name, 'is_official'):
            # 直接执行SQL而不返回结果（设置fetch=False）
            sql = f"""
            ALTER TABLE {table_name}
            ADD COLUMN `is_official` tinyint(1) NULL DEFAULT '0' COMMENT '是否为官方信息'
            """
            
            print(f"添加字段SQL: {sql}")
            result = await async_execute_custom_query(sql, fetch=False)
            print(f"向{table_name}表添加is_official字段: {result}")
            
            # 等待一段时间确保字段添加完成
            for i in range(10):
                if await check_column_exists(table_name, 'is_official'):
                    print(f"{table_name}表已成功添加is_official字段")
                    return True
                print(f"等待字段添加完成 {i+1}/10...")
                await asyncio.sleep(1)
                
            if not await check_column_exists(table_name, 'is_official'):
                print(f"警告: 在10次检查后，{table_name}表仍未检测到is_official字段")
                return False
        else:
            print(f"{table_name}表已存在is_official字段")
        return True
    except Exception as e:
        print(f"添加{table_name}表is_official字段失败: {str(e)}")
        return False

async def update_is_official(table_name):
    """更新指定表中的is_official字段"""
    try:
        # 检查字段是否存在
        if not await check_column_exists(table_name, 'is_official'):
            print(f"{table_name}表中不存在is_official字段，请先添加字段")
            return -1
            
        # 查询所有记录
        total_count_sql = f"SELECT COUNT(*) as total FROM {table_name}"
        total_result = await async_execute_custom_query(total_count_sql)
        total_count = total_result[0]['total'] if total_result else 0
        print(f"{table_name}表共有 {total_count} 条记录")
        
        # 重置is_official字段
        reset_sql = f"UPDATE {table_name} SET is_official = 0"
        reset_result = await async_execute_custom_query(reset_sql, fetch=False)
        print(f"重置{table_name}表is_official字段，影响 {reset_result} 行")
        
        # 输出official_author列表信息
        print(f"official_author列表长度: {len(official_author)}")
        print(f"official_author列表前10个元素: {official_author[:10]}")
        
        # 查询有多少author在official_author列表中
        sample_sql = f"SELECT DISTINCT author FROM {table_name} LIMIT 20"
        sample_authors = await async_execute_custom_query(sample_sql)
        print(f"{table_name}表中的author样本: {[a['author'] for a in sample_authors]}")
        
        # 批量更新is_official字段
        # 小批量处理，避免长时间事务
        batch_size = 20
        total_updated = 0
        
        for i in range(0, len(official_author), batch_size):
            batch = official_author[i:i+batch_size]
            if not batch:
                continue
            
            placeholders = ', '.join(['%s'] * len(batch))
            update_sql = f"""
            UPDATE {table_name} 
            SET is_official = 1 
            WHERE author IN ({placeholders})
            """
            update_result = await async_execute_custom_query(update_sql, batch, fetch=False)
            total_updated += update_result
            print(f"批次 {i//batch_size+1}/{(len(official_author)-1)//batch_size+1}: 更新 {update_result} 条记录")
            
            # 每个批次之间暂停一下，避免长时间锁表
            await asyncio.sleep(0.5)
        
        print(f"更新{table_name}表is_official字段，设置 {total_updated} 条记录为官方信息")
        
        # 查询更新后状态
        status_sql = f"SELECT is_official, COUNT(*) as count FROM {table_name} GROUP BY is_official"
        status_result = await async_execute_custom_query(status_sql)
        for row in status_result:
            print(f"{table_name}表is_official={row['is_official']}的记录有 {row['count']} 条")
        
        return total_updated
    except Exception as e:
        print(f"更新{table_name}表is_official字段失败: {str(e)}")
        return -1

async def async_main():
    """异步主函数"""
    print("开始修复website_nku和wechat_nku表的is_official字段")
    
    # 调试信息
    print(f"Python版本: {sys.version}")
    print(f"当前工作目录: {os.getcwd()}")
    print(f"sys.path: {sys.path}")
    
    # 第一步：添加website_nku字段
    print("\n===== 处理website_nku表 =====")
    success_web = await add_is_official_field('website_nku')
    if not success_web:
        print("添加website_nku表字段失败，脚本终止")
        return -1
    
    # 第二步：更新website_nku字段值
    web_count = await update_is_official('website_nku')
    if web_count < 0:
        print("更新website_nku表is_official字段失败")
    else:
        print(f"成功更新website_nku表is_official字段，共 {web_count} 条记录被标记为官方信息")
    
    # 第三步：添加wechat_nku字段
    print("\n===== 处理wechat_nku表 =====")
    success_wechat = await add_is_official_field('wechat_nku')
    if not success_wechat:
        print("添加wechat_nku表字段失败，脚本终止")
        return -1
    
    # 第四步：更新wechat_nku字段值
    wechat_count = await update_is_official('wechat_nku')
    if wechat_count < 0:
        print("更新wechat_nku表is_official字段失败")
    else:
        print(f"成功更新wechat_nku表is_official字段，共 {wechat_count} 条记录被标记为官方信息")
    
    total_updated = web_count + wechat_count if web_count >= 0 and wechat_count >= 0 else -1
    if total_updated >= 0:
        print(f"脚本执行完成：成功更新is_official字段，共 {total_updated} 条记录被标记为官方信息")
    else:
        print("脚本执行完成：更新is_official字段失败")
    
    return total_updated

def main():
    """入口函数"""
    start_time = time.time()
    result = asyncio.run(async_main())
    end_time = time.time()
    print(f"总耗时: {end_time - start_time:.2f}秒")
    return result

if __name__ == "__main__":
    main() 