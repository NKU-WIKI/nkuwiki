#!/usr/bin/env python3
"""
检查帖子表中的数据
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
        # 1. 检查表结构
        structure_sql = "DESCRIBE wxapp_post"
        table_structure = execute_query(structure_sql)
        logger.debug(f"帖子表结构: {json.dumps(table_structure, default=str)}")
        
        # 2. 检查数据总量
        count_sql = "SELECT COUNT(*) as total FROM wxapp_post"
        count_result = execute_query(count_sql)
        total_posts = count_result[0]['total'] if count_result else 0
        logger.debug(f"帖子总数: {total_posts}")
        
        # 3. 获取最新的帖子
        if total_posts > 0:
            recent_sql = "SELECT * FROM wxapp_post ORDER BY create_time DESC LIMIT 5"
            recent_posts = execute_query(recent_sql)
            logger.debug(f"最新的5条帖子: {json.dumps(recent_posts, default=str)}")
            
            # 打印给用户
            print(f"帖子表中共有 {total_posts} 条记录")
            print("\n最新的帖子:")
            for post in recent_posts:
                print(f"ID: {post['id']}, 标题: {post['title']}, 创建时间: {post['create_time']}")
        else:
            print("帖子表中没有数据")
            
            # 4. 尝试插入一条测试数据
            print("\n尝试插入一条测试数据...")
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
            insert_result = execute_query(insert_sql, params, fetch=False)
            print(f"插入结果: {insert_result}")
            
            # 5. 再次检查数据
            verify_sql = "SELECT * FROM wxapp_post WHERE openid = 'test_db_user' ORDER BY create_time DESC LIMIT 1"
            verify_result = execute_query(verify_sql)
            if verify_result:
                print(f"成功插入测试帖子，ID: {verify_result[0]['id']}")
            else:
                print("测试帖子插入失败")
        
        # 6. 检查帖子字段
        check_post_fields()
        
    except Exception as e:
        import traceback
        logger.error(f"检查帖子表时出错: {str(e)}")
        logger.error(traceback.format_exc())
        print(f"检查帖子表时出错: {str(e)}")

def check_post_fields():
    """检查帖子表字段和约束"""
    try:
        # 1. 检查字段名称
        field_sql = "SHOW COLUMNS FROM wxapp_post"
        fields = execute_query(field_sql)
        field_names = [field['Field'] for field in fields]
        logger.debug(f"帖子表字段: {field_names}")
        
        # 2. 检查表索引
        index_sql = "SHOW INDEX FROM wxapp_post"
        indexes = execute_query(index_sql)
        logger.debug(f"帖子表索引: {json.dumps(indexes, default=str)}")
        
        # 3. 检查外键约束
        constraint_sql = """
        SELECT TABLE_NAME, COLUMN_NAME, CONSTRAINT_NAME, REFERENCED_TABLE_NAME, REFERENCED_COLUMN_NAME
        FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
        WHERE REFERENCED_TABLE_NAME IS NOT NULL AND TABLE_NAME = 'wxapp_post'
        """
        constraints = execute_query(constraint_sql)
        logger.debug(f"帖子表外键约束: {json.dumps(constraints, default=str)}")
        
        # 4. 检查有字段没有的记录 (关键字段检查)
        null_check_sql = """
        SELECT id, title, content, create_time 
        FROM wxapp_post 
        WHERE title IS NULL OR content IS NULL OR openid IS NULL
        LIMIT 5
        """
        null_records = execute_query(null_check_sql)
        if null_records:
            logger.warning(f"存在关键字段为空的记录: {json.dumps(null_records, default=str)}")
            print("\n警告: 存在关键字段为空的记录:")
            for record in null_records:
                print(f"ID: {record['id']}, 创建时间: {record['create_time']}")
    
    except Exception as e:
        logger.error(f"检查帖子表字段时出错: {str(e)}")
        print(f"检查帖子表字段时出错: {str(e)}")

if __name__ == "__main__":
    print("开始检查帖子表数据...")
    check_post_table()
    print("检查完成") 