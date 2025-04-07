#!/usr/bin/env python3
"""
通用数据导入脚本
将数据从JSON文件导入到MySQL数据库表中
"""
import os
import sys
import json
import glob
import argparse
import datetime
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# 添加项目根目录到Python路径
root_dir = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(root_dir))

from etl.load import db_core
from etl.load.recreate_all_tables import recreate_tables
from core.utils.logger import register_logger
from etl import config

# 创建脚本专用日志记录器
logger = register_logger('etl.load.import_data')

# 添加进度条函数
def progress_bar(iteration, total, prefix='', suffix='', decimals=1, length=50, fill='█', print_end='\r'):
    """
    显示进度条
    
    Args:
        iteration: 当前迭代索引
        total: 总迭代次数
        prefix: 前缀字符串
        suffix: 后缀字符串
        decimals: 百分比小数位数
        length: 进度条长度
        fill: 进度条填充字符
        print_end: 结束字符
    """
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filled_length = int(length * iteration // total)
    bar = fill * filled_length + '-' * (length - filled_length)
    print(f'\r{prefix} |{bar}| {percent}% {suffix}', end=print_end, flush=True)
    
    # 完成时打印新行
    if iteration == total:
        print()

# 添加custom_query执行函数（如果db_core中不存在）
def execute_custom_query(sql, params=None, fetch=True):
    """执行自定义SQL查询"""
    if hasattr(db_core, 'execute_custom_query'):
        return db_core.execute_custom_query(sql, params, fetch)
    else:
        return db_core.execute_query(sql, params, fetch)

# 使用上面定义的函数替换db_core中的函数
if not hasattr(db_core, 'execute_custom_query'):
    db_core.execute_custom_query = execute_custom_query

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='将数据从JSON文件导入到MySQL数据库')
    parser.add_argument('--platform', required=True, choices=['wechat', 'website', 'market', 'wxapp'], 
                        help='数据平台类型')
    parser.add_argument('--tag', default='nku', help='数据标签，默认为nku')
    parser.add_argument('--data-dir', help='数据目录路径，默认使用配置中的路径')
    parser.add_argument('--pattern', default='*.json', help='JSON文件匹配模式，默认为*.json')
    parser.add_argument('--rebuild-table', action='store_true', help='导入前重建表')
    parser.add_argument('--batch-size', type=int, default=100, help='批量插入大小，默认100')
    parser.add_argument('--verbose', '-v', action='store_true', help='显示详细日志')
    return parser.parse_args()

def get_data_dir(platform: str, user_dir: Optional[str] = None) -> str:
    """获取数据目录路径"""
    if user_dir:
        return user_dir
    
    # 从配置中获取基础数据路径
    base_path = config.get('etl.data.raw.path', '/raw')
    
    # 构建平台特定的路径
    platform_paths = {
        'wechat': os.path.join(base_path, 'wechat'),
        'website': os.path.join(base_path, 'website'),
        'market': os.path.join(base_path, 'market'),
        'wxapp': os.path.join(base_path, 'wxapp'),
    }
    
    return platform_paths.get(platform, os.path.join(base_path, platform))

def get_table_name(platform: str, tag: str) -> str:
    """获取表名"""
    return f"{platform}_{tag}"

def create_table_if_needed(table_name: str):
    """检查表是否存在，不存在则创建"""
    try:
        sql = f"SHOW TABLES LIKE '{table_name}'"
        result = db_core.execute_query(sql)
        
        if not result:
            # 表不存在，找到对应的SQL文件并执行
            sql_file = os.path.join(
                Path(__file__).parent, 
                "mysql_tables", 
                f"{table_name}.sql"
            )
            
            if os.path.exists(sql_file):
                with open(sql_file, 'r', encoding='utf-8') as f:
                    sql_content = f.read()
                    execute_custom_query(sql_content, fetch=False)
                    logger.info(f"已创建表 {table_name}")
            else:
                logger.error(f"找不到表 {table_name} 的SQL定义文件")
                return False
        return True
    except Exception as e:
        logger.error(f"创建表出错: {str(e)}")
        return False

def read_json_file(file_path: str) -> List[Dict[str, Any]]:
    """读取JSON文件"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
            # 1. 支持直接的列表
            if isinstance(data, list):
                return data
                
            # 2. 支持带有data键的字典
            elif isinstance(data, dict):
                # 2.1 标准data字段
                if 'data' in data and isinstance(data['data'], list):
                    return data['data']
                    
                # 2.2 单条记录的情况，将其包装为列表
                elif any(key in data for key in ['title', 'content', 'author', 'original_url']):
                    return [data]
                    
                # 2.3 嵌套的数据结构，尝试从中提取有效字段
                else:
                    # 尝试从字典中找到可能的数据列表
                    for key, value in data.items():
                        if isinstance(value, list) and len(value) > 0 and isinstance(value[0], dict):
                            return value
                            
                    # 如果字典中有嵌套字典，检查是否是单个记录
                    record = {}
                    for key, value in data.items():
                        if isinstance(value, dict) and any(k in value for k in ['title', 'content', 'author']):
                            record.update(value)
                            
                    if record:
                        return [record]
            
            # 没有找到有效的数据结构
            return []
    except Exception as e:
        # 简化错误日志，使用debug级别
        logger.debug(f"读取JSON文件 {file_path} 失败: {str(e)}")
        return []

def preprocess_record(record: Dict[str, Any], platform: str) -> Dict[str, Any]:
    """预处理记录，确保字段匹配表结构"""
    # 复制一份以避免修改原始数据
    processed = record.copy()
    
    # 确保基本字段存在
    if 'title' not in processed:
        processed['title'] = ''
    if 'content' not in processed:
        processed['content'] = ''
    if 'author' not in processed:
        processed['author'] = '未知作者'
    if 'original_url' not in processed:
        processed['original_url'] = ''
    
    # 设置平台字段
    processed['platform'] = platform
    
    # 处理日期字段
    for field in ['publish_time', 'scrape_time']:
        if field in processed and processed[field]:
            # 如果是字符串，尝试转换为datetime
            if isinstance(processed[field], str):
                try:
                    # 尝试多种日期格式
                    formats = [
                        '%Y-%m-%d %H:%M:%S',
                        '%Y-%m-%d %H:%M',
                        '%Y-%m-%dT%H:%M:%S',
                        '%Y-%m-%dT%H:%M:%S.%f',
                        '%Y-%m-%d'
                    ]
                    
                    for fmt in formats:
                        try:
                            processed[field] = datetime.datetime.strptime(
                                processed[field], fmt
                            )
                            break
                        except ValueError:
                            continue
                        
                except Exception as e:
                    logger.warning(f"日期转换失败 {field}: {processed[field]}, {str(e)}")
                    processed[field] = None
    
    return processed

def insert_batch(table_name: str, records: List[Dict[str, Any]]) -> int:
    """批量插入记录"""
    if not records:
        return 0
    
    try:
        # 先获取表的结构，确定有哪些字段
        with db_core.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(f"SHOW COLUMNS FROM `{table_name}`")
                table_columns = [col['Field'] for col in cursor.fetchall()]
        
        # 过滤掉不在表中的字段
        filtered_records = []
        for record in records:
            filtered_record = {}
            for key, value in record.items():
                if key in table_columns:
                    filtered_record[key] = value
            filtered_records.append(filtered_record)
        
        if not filtered_records:
            return 0
        
        # 获取字段列表（从第一条记录）
        fields = list(filtered_records[0].keys())
        
        # 构建INSERT语句
        placeholders = ', '.join(['%s'] * len(fields))
        columns = ', '.join([f'`{field}`' for field in fields])
        
        sql = f"INSERT IGNORE INTO `{table_name}` ({columns}) VALUES ({placeholders})"
        
        # 准备数据
        values = []
        for record in filtered_records:
            row = [record.get(field) for field in fields]
            values.append(row)
        
        # 执行批量插入
        with db_core.get_connection() as conn:
            with conn.cursor() as cursor:
                affected_rows = cursor.executemany(sql, values)
                return affected_rows
    except Exception as e:
        logger.error(f"批量插入失败: {str(e)}")
        return 0

def import_data(platform: str, tag: str, data_dir: str, file_pattern: str, batch_size: int) -> Tuple[int, int]:
    """
    导入数据
    
    Args:
        platform: 平台类型
        tag: 数据标签
        data_dir: 数据目录
        file_pattern: 文件匹配模式
        batch_size: 批处理大小
        
    Returns:
        tuple: (导入文件数, 导入记录数)
    """
    table_name = get_table_name(platform, tag)
    
    # 确保表存在
    if not create_table_if_needed(table_name):
        logger.error(f"无法确保表 {table_name} 存在，导入中止")
        return 0, 0
    
    # 查找所有匹配的JSON文件（支持递归搜索）
    json_files = []
    for root, _, files in os.walk(data_dir):
        for file in files:
            if file.endswith('.json'):
                json_files.append(os.path.join(root, file))
    
    if not json_files:
        logger.warning(f"在 {data_dir} 中没有找到JSON文件")
        return 0, 0
    
    logger.info(f"找到 {len(json_files)} 个JSON文件")
    
    # 导入统计
    total_files = len(json_files)
    processed_files = 0
    total_records = 0
    current_batch = []
    start_time = time.time()
    error_count = 0
    
    # 初始化进度条
    progress_bar(0, total_files, prefix=f'导入数据到 {table_name}:', suffix='完成')
    
    # 导入每个文件
    for file_path in json_files:
        try:
            records = read_json_file(file_path)
            if not records:
                error_count += 1
                continue
            
            # 处理每条记录
            for record in records:
                processed_record = preprocess_record(record, platform)
                current_batch.append(processed_record)
                
                # 达到批处理大小，执行插入
                if len(current_batch) >= batch_size:
                    inserted = insert_batch(table_name, current_batch)
                    total_records += inserted
                    current_batch = []
            
            processed_files += 1
            
            # 更新进度条
            if processed_files % max(1, total_files // 100) == 0 or processed_files == total_files:
                elapsed = time.time() - start_time
                records_per_second = int(total_records / elapsed) if elapsed > 0 else 0
                suffix = f'完成 | {total_records} 记录 | {records_per_second} 记录/秒'
                progress_bar(processed_files, total_files, prefix=f'导入数据到 {table_name}:', suffix=suffix)
                
        except Exception as e:
            error_count += 1
            logger.error(f"处理文件 {file_path} 失败: {str(e)}")
    
    # 处理剩余的记录
    if current_batch:
        inserted = insert_batch(table_name, current_batch)
        total_records += inserted
    
    # 完成进度条
    elapsed_time = time.time() - start_time
    records_per_second = int(total_records / elapsed_time) if elapsed_time > 0 else 0
    final_suffix = f'完成 | {total_records} 记录 | {elapsed_time:.1f}秒 | {records_per_second} 记录/秒'
    progress_bar(total_files, total_files, prefix=f'导入数据到 {table_name}:', suffix=final_suffix)
    
    # 总结信息
    if error_count > 0:
        logger.warning(f"导入过程中有 {error_count} 个文件处理出错")
    
    logger.info(f"导入完成: 处理了 {processed_files}/{total_files} 个文件，成功导入 {total_records} 条记录到表 {table_name}")
    return processed_files, total_records

def main():
    """主函数"""
    args = parse_args()
    
    # 设置日志级别
    if args.verbose:
        from loguru import logger as global_logger
        import sys
        
        # 移除默认处理器，添加一个DEBUG级别的处理器
        global_logger.remove()
        global_logger.add(sys.stderr, level="DEBUG", format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>")
        logger.debug("已设置为详细日志模式")
    
    platform = args.platform
    tag = args.tag
    data_dir = args.data_dir or get_data_dir(platform)
    
    logger.info(f"开始导入 {platform}_{tag} 数据...")
    logger.info(f"数据目录: {data_dir}")
    
    try:
        # 检查数据目录
        if not os.path.exists(data_dir):
            logger.error(f"数据目录 {data_dir} 不存在")
            return 1
        
        # 检查数据库连接
        try:
            with db_core.get_connection():
                logger.debug("数据库连接测试成功")
        except Exception as e:
            logger.error(f"无法连接到数据库: {str(e)}")
            return 1
        
        # 如果需要，重建表
        if args.rebuild_table:
            logger.info(f"重建表 {platform}_{tag}")
            recreate_tables([f"{platform}_{tag}"], force=True)
        
        # 导入数据
        files_count, records_count = import_data(
            platform, 
            tag, 
            data_dir, 
            args.pattern, 
            args.batch_size
        )
        
        if records_count > 0:
            logger.info(f"成功从 {files_count} 个文件导入 {records_count} 条记录到 {platform}_{tag}")
            return 0
        else:
            logger.warning(f"未能导入任何记录到 {platform}_{tag}")
            return 1
        
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