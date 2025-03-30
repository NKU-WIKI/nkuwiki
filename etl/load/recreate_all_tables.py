#!/usr/bin/env python3
"""
重新创建所有表脚本
删除并重新创建所有数据库表
"""
import os
import sys
import glob
import argparse
from pathlib import Path

# 添加项目根目录到Python路径
root_dir = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(root_dir))

from etl.load import db_core
from core.utils.logger import register_logger

# 创建脚本专用日志记录器
logger = register_logger('etl.load.recreate_tables')

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='删除并重新创建所有数据库表')
    parser.add_argument('--force', action='store_true', help='强制执行，不提示确认')
    parser.add_argument('--tables', nargs='+', help='指定要重建的表名(不包含.sql后缀)，默认全部表')
    parser.add_argument('--verbose', '-v', action='store_true', help='显示详细日志')
    return parser.parse_args()

def get_table_name_from_file(file_path):
    """从SQL文件名提取表名"""
    return Path(file_path).stem

def read_sql_file(file_path):
    """读取SQL文件内容"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        logger.error(f"读取SQL文件{file_path}失败: {str(e)}")
        return None

def execute_sql(sql_content, table_name):
    """执行SQL语句"""
    try:
        result = db_core.execute_custom_query(sql_content, fetch=False)
        return True
    except Exception as e:
        logger.error(f"执行SQL语句创建表{table_name}失败: {str(e)}")
        return False

def drop_table(table_name):
    """删除表"""
    try:
        drop_sql = f"DROP TABLE IF EXISTS {table_name}"
        db_core.execute_custom_query(drop_sql, fetch=False)
        logger.debug(f"表{table_name}已删除或不存在")
        return True
    except Exception as e:
        logger.error(f"删除表{table_name}失败: {str(e)}")
        return False

def recreate_tables(specific_tables=None, force=False):
    """重新创建所有表"""
    # 获取所有SQL文件
    sql_dir = Path(__file__).parent / "mysql_tables"
    logger.debug(f"SQL目录: {sql_dir}")
    
    if specific_tables:
        # 如果指定了特定表，构建完整文件路径列表
        sql_files = [str(sql_dir / f"{table}.sql") for table in specific_tables
                    if os.path.exists(sql_dir / f"{table}.sql")]
        logger.debug(f"指定的表: {specific_tables}")
        logger.debug(f"找到的SQL文件: {sql_files}")
        if not sql_files:
            logger.warning("未找到指定的表SQL文件")
            return False
    else:
        # 获取所有SQL文件
        sql_files = glob.glob(str(sql_dir / "*.sql"))
        logger.debug(f"找到的SQL文件: {sql_files}")
    
    if not sql_files:
        logger.warning("未找到SQL文件")
        return False
    
    # 显示将要操作的表
    tables = [get_table_name_from_file(f) for f in sql_files]
    logger.info(f"将重新创建以下{len(tables)}个表: {', '.join(tables)}")
    
    if not force:
        confirm = input("此操作将删除并重新创建上述表，所有数据将丢失！确定继续吗？(y/n): ")
        if confirm.lower() != 'y':
            logger.info("操作已取消")
            return False
    
    success_count = 0
    failed_tables = []
    
    # 删除并重新创建每个表
    for sql_file in sql_files:
        table_name = get_table_name_from_file(sql_file)
        logger.info(f"正在处理表 {table_name}")
        
        # 删除表
        logger.debug(f"正在删除表 {table_name}")
        if not drop_table(table_name):
            failed_tables.append(table_name)
            continue
        
        # 读取SQL文件内容
        logger.debug(f"正在读取SQL文件 {sql_file}")
        sql_content = read_sql_file(sql_file)
        if not sql_content:
            failed_tables.append(table_name)
            continue
        
        # 执行创建表SQL
        logger.debug(f"正在执行创建表SQL: {sql_file}")
        logger.debug(f"SQL内容: {sql_content[:100]}...")
        if execute_sql(sql_content, table_name):
            logger.info(f"表 {table_name} 重新创建成功")
            success_count += 1
        else:
            failed_tables.append(table_name)
    
    # 输出结果统计
    result = f"操作完成: 成功 {success_count}/{len(sql_files)} 个表"
    if failed_tables:
        result += f", 失败表: {', '.join(failed_tables)}"
    
    logger.info(result)
    return success_count == len(sql_files)

def main():
    """主函数"""
    args = parse_args()
    
    # 设置日志级别
    if args.verbose:
        # 使用全局 loguru 级别，我们不能直接修改已绑定的 logger 级别
        from loguru import logger as global_logger
        import sys
        
        # 移除默认处理器，添加一个DEBUG级别的处理器
        global_logger.remove()
        global_logger.add(sys.stderr, level="DEBUG", format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>")
        print("已设置为详细日志模式")
    
    logger.info("开始重新创建所有表")
    
    try:
        # 检查数据库连接
        try:
            with db_core.get_connection():
                logger.debug("数据库连接测试成功")
        except Exception as e:
            logger.error(f"无法连接到数据库: {str(e)}")
            return 1
        
        # 执行表重建
        success = recreate_tables(args.tables, args.force)
        return 0 if success else 1
        
    except KeyboardInterrupt:
        logger.info("操作被用户中断")
        return 1
    except Exception as e:
        logger.error(f"发生未预期的错误: {str(e)}")
        import traceback
        logger.debug(traceback.format_exc())
        return 1

if __name__ == "__main__":
    sys.exit(main()) 