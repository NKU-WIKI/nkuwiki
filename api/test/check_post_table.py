#!/usr/bin/env python3
"""
检查wxapp_post表中的数据
"""
import sys
import os
import json

# 添加项目根目录到sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from etl.load.db_core import execute_query
from core.utils.logger import register_logger

logger = register_logger('api.test.check_db')

def check_post_table():
    """检查帖子表"""
    try:
        # 1. 检查表是否存在
        tables_sql = "SHOW TABLES LIKE 'wxapp_post'"
        tables = execute_query(tables_sql)
        if not tables:
            print("wxapp_post表不存在")
            return
            
        print("wxapp_post表存在")
        
        # 2. 检查表结构
        structure_sql = "DESCRIBE wxapp_post"
        fields = execute_query(structure_sql)
        print(f"wxapp_post表有 {len(fields)} 个字段:")
        for field in fields:
            print(f"- {field['Field']} ({field['Type']})")
        
        # 3. 检查数据量
        count_sql = "SELECT COUNT(*) as total FROM wxapp_post"
        count_result = execute_query(count_sql)
        total_posts = count_result[0]['total'] if count_result else 0
        print(f"wxapp_post表中有 {total_posts} 条记录")
        
        # 4. 查看最新记录
        if total_posts > 0:
            recent_sql = "SELECT * FROM wxapp_post ORDER BY create_time DESC LIMIT 5"
            recent_posts = execute_query(recent_sql)
            print("\n最新的5条帖子:")
            for post in recent_posts:
                print(f"ID: {post['id']}, 标题: {post['title']}, 创建时间: {post['create_time']}")
        else:
            print("\n尝试插入一条测试记录...")
            try:
                insert_sql = """
                INSERT INTO wxapp_post 
                (openid, nickname, avatar, title, content, category_id)
                VALUES (%s, %s, %s, %s, %s, %s)
                """
                params = [
                    "test_db_user",
                    "数据库测试用户",
                    "https://example.com/avatar.png",
                    "数据库直接插入的测试帖子",
                    "这是一条通过直接操作数据库插入的测试帖子内容。",
                    1
                ]
                execute_query(insert_sql, params, fetch=False)
                print("插入成功")
                
                verify_sql = "SELECT * FROM wxapp_post WHERE openid = 'test_db_user' LIMIT 1"
                inserted = execute_query(verify_sql)
                if inserted:
                    print(f"成功查询到插入的记录: ID={inserted[0]['id']}, 标题={inserted[0]['title']}")
                else:
                    print("无法查询到插入的记录")
            except Exception as e:
                print(f"插入测试记录失败: {str(e)}")
            
    except Exception as e:
        import traceback
        logger.error(f"检查帖子表时出错: {str(e)}")
        logger.error(traceback.format_exc())
        print(f"检查帖子表时出错: {str(e)}")

if __name__ == "__main__":
    print("开始检查wxapp_post表...")
    check_post_table()
    print("检查完成") 