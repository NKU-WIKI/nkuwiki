#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
使用Python直接执行SQL脚本修复数据库索引
"""
import os
import sys
import logging
from typing import List, Dict, Any

# 添加项目根目录到路径
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, "../.."))
sys.path.insert(0, project_root)

from etl.load.db_core import execute_custom_query
from core.utils.logger import register_logger

# 设置日志格式
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = register_logger("fix.mysql.indexes")

# 定义需要修复的表和索引
TABLES_TO_FIX = {
    "wxapp_post": {"content_field": "content", "title_field": "title"},
    "website_nku": {"content_field": "content", "title_field": "title"},
    "wechat_nku": {"content_field": "content", "title_field": "title"},
    "wxapp_comment": {"content_field": "content"},
    "market_nku": {"content_field": "content", "title_field": "title"}
}

def check_table_exists(table_name: str) -> bool:
    """检查表是否存在"""
    try:
        logger.debug(f"检查表 {table_name} 是否存在")
        sql = "SHOW TABLES LIKE %s"
        result = execute_custom_query(sql, [table_name])
        exists = len(result) > 0
        logger.debug(f"表 {table_name} {'存在' if exists else '不存在'}")
        return exists
    except Exception as e:
        logger.error(f"检查表失败 {table_name}: {str(e)}")
        return False

def drop_fulltext_index(table_name: str) -> bool:
    """删除表上已有的FULLTEXT索引"""
    try:
        logger.debug(f"检查表 {table_name} 是否存在FULLTEXT索引")
        sql = f"SHOW INDEX FROM {table_name} WHERE Key_name = 'ft_content'"
        result = execute_custom_query(sql)
        
        if result:
            logger.debug(f"删除表 {table_name} 上的ft_content索引")
            sql = f"ALTER TABLE {table_name} DROP INDEX ft_content"
            execute_custom_query(sql, fetch=False)
            logger.debug(f"成功删除表 {table_name} 上的ft_content索引")
            return True
        else:
            logger.debug(f"表 {table_name} 上不存在ft_content索引")
            return False
    except Exception as e:
        logger.error(f"删除索引失败 {table_name}: {str(e)}")
        return False

def create_fulltext_index(table_name: str, content_field: str, title_field: str = None) -> bool:
    """创建FULLTEXT索引"""
    try:
        fields = [content_field]
        if title_field:
            fields.append(title_field)
            
        fields_str = ", ".join(fields)
        logger.debug(f"为表 {table_name} 创建FULLTEXT索引: {fields_str}")
        
        sql = f"ALTER TABLE {table_name} ADD FULLTEXT INDEX ft_content ({fields_str}) WITH PARSER ngram"
        execute_custom_query(sql, fetch=False)
        logger.debug(f"成功为表 {table_name} 创建FULLTEXT索引")
        return True
    except Exception as e:
        logger.error(f"创建索引失败 {table_name}: {str(e)}")
        return False

def check_index_exists(table_name: str) -> List[Dict[str, Any]]:
    """检查表上的索引"""
    try:
        logger.debug(f"检查表 {table_name} 上的索引")
        sql = f"SHOW INDEX FROM {table_name} WHERE Index_type = 'FULLTEXT'"
        result = execute_custom_query(sql)
        
        if result:
            indexed_columns = [idx["Column_name"] for idx in result]
            logger.debug(f"表 {table_name} 上的FULLTEXT索引列: {indexed_columns}")
        else:
            logger.debug(f"表 {table_name} 上不存在FULLTEXT索引")
            
        return result
    except Exception as e:
        logger.error(f"检查索引失败 {table_name}: {str(e)}")
        return []

def fix_table_index(table_name: str, content_field: str, title_field: str = None) -> bool:
    """修复表的索引"""
    if not check_table_exists(table_name):
        logger.error(f"表 {table_name} 不存在，无法修复索引")
        return False
    
    # 删除已有的索引
    drop_fulltext_index(table_name)
    
    # 创建新索引
    success = create_fulltext_index(table_name, content_field, title_field)
    
    # 验证索引
    if success:
        indexes = check_index_exists(table_name)
        if not indexes:
            logger.error(f"表 {table_name} 索引创建失败，未找到FULLTEXT索引")
            return False
            
        # 检查索引列
        indexed_columns = [idx["Column_name"] for idx in indexes]
        if content_field not in indexed_columns:
            logger.error(f"表 {table_name} 索引创建失败，{content_field} 字段未被索引")
            return False
            
        if title_field and title_field not in indexed_columns:
            logger.error(f"表 {table_name} 索引创建失败，{title_field} 字段未被索引")
            return False
            
        logger.info(f"表 {table_name} 索引创建成功")
        return True
    else:
        logger.error(f"表 {table_name} 索引创建失败")
        return False

def check_ngram_plugin() -> bool:
    """检查ngram插件是否可用"""
    try:
        logger.debug("检查ngram插件状态")
        sql = "SELECT 1 FROM INFORMATION_SCHEMA.PLUGINS WHERE PLUGIN_NAME='ngram' AND PLUGIN_STATUS='ACTIVE'"
        result = execute_custom_query(sql)
        
        if result:
            logger.info("MySQL ngram插件已启用")
            return True
        else:
            logger.warning("MySQL ngram插件未启用")
            return False
    except Exception as e:
        logger.error(f"检查ngram插件失败: {str(e)}")
        return False

def main() -> bool:
    """主函数，执行所有索引修复"""
    logger.info("开始修复数据库索引")
    
    # 检查ngram插件
    if not check_ngram_plugin():
        logger.warning("ngram插件未启用，可能导致索引创建失败")
    
    # 修复所有表索引
    results = {}
    for table_name, fields in TABLES_TO_FIX.items():
        content_field = fields["content_field"]
        title_field = fields.get("title_field")
        logger.info(f"开始修复表 {table_name} 的索引")
        results[table_name] = fix_table_index(table_name, content_field, title_field)
    
    # 统计结果
    success_count = sum(1 for result in results.values() if result)
    total_count = len(results)
    
    logger.info(f"索引修复完成, 成功: {success_count}/{total_count} ({success_count/total_count*100:.2f}%)")
    
    for table_name, success in results.items():
        status = "✅ 成功" if success else "❌ 失败"
        logger.info(f"{status}: {table_name}")
    
    return success_count == total_count

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 