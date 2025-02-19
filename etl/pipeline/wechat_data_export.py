import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent)) 

import mysql.connector
import json
import glob
from pathlib import Path
from typing import Dict
from config import Config
Config().load_config()
from loguru import logger
import re

logger.add("logs/data_export.log", rotation="1 day", retention="3 months", level="INFO")

def get_conn(use_database=True):
    config = {
        "host": Config().get("db_host"),
        "port": Config().get("db_port"),
        "user": Config().get("db_user"),
        "password": Config().get("db_password"),
        "charset": 'utf8mb4',
        "unix_socket": '/var/run/mysqld/mysqld.sock'
    }
    if use_database:
        config["database"] = Config().get("db_name")
    return mysql.connector.connect(**config)

def init_database():
    """分步初始化数据库"""
    try:
        # 第一步：连接无数据库状态
        with get_conn(use_database=False) as conn:
            with conn.cursor() as cur:
                # 创建数据库（如果不存在）
                cur.execute(f"CREATE DATABASE IF NOT EXISTS {Config().get('db_name')} CHARACTER SET utf8mb4")
                logger.info(f"已创建/验证数据库: {Config().get('db_name')}")
    except Exception as e:
        logger.exception(f"数据库初始化失败")
        raise
        
    try:
        # 第二步：连接目标数据库执行表结构
        with get_conn() as conn:
            with conn.cursor() as cur:
                sql_dir = Path(__file__).parent.parent / "tables"
                for sql_file in sorted(sql_dir.glob('*.sql')):
                    # 提取表名
                    sql_content = sql_file.read_text(encoding='utf-8')
                    table_name = re.search(r"CREATE TABLE (?:IF NOT EXISTS )?(\w+)", sql_content).group(1)
                    logger.info(f"正在创建表: {table_name}")
                    
                    # 执行SQL
                    for result in cur.execute(sql_content, multi=True):
                        if result.with_rows:
                            logger.debug(f"执行结果: {result.fetchall()}")
                conn.commit()
        logger.info(f"数据库表结构初始化完成，共建立 {len(list(sql_dir.glob('*.sql')))} 张表")
    except Exception as e:
        logger.exception(f"数据库表结构初始化失败")
        raise

def process_file(file_path: str) -> Dict:
    """处理单个JSON文件并返回清洗后的数据"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 修改必要字段验证
        required_fields = ['run_time', 'publish_time', 'title', 'nickname', 'original_url']
        for field in required_fields:
            if field not in data:
                raise ValueError(f"缺少必要字段: {field}")

        # 数据清洗
        return {
            "run_time": data["run_time"].replace(" ", "T"),
            "publish_time": data["publish_time"],
            "title": str(data.get("title", "")).strip(),
            "nickname": str(data.get("nickname", "")).strip(),
            "original_url": data["original_url"]
        }
    except json.JSONDecodeError as e:
        logger.error(f"文件 {file_path} 不是有效的JSON: {str(e)}")
        raise

def export_wechat_to_mysql(n):
    """将微信JSON数据导入MySQL数据库"""
    
    # 初始化数据库
    init_database()

    # 读取所有匹配的元数据文件
    metadata_dir = Path(Config().get("data_path")) / "processed"
    metadata_files = list(metadata_dir.glob("wechat_metadata*.json"))
    
    if not metadata_files:
        logger.error("未找到元数据文件：wechat_metadata*.json")
        return

    # 合并多个元数据文件
    metadata = []
    for file in metadata_files:
        try:
            with open(file, 'r', encoding='utf-8') as f:
                metadata.extend(json.load(f))
                logger.info(f"已加载元数据文件：{file.name}（{len(metadata)}条记录）")
        except Exception as e:
            logger.error(f"加载元数据文件失败 {file}: {str(e)}")
            continue

    total_items = len(metadata)
    process_data = metadata[:n]

    with get_conn() as conn:
        conn.autocommit = False
        
        logger.info(f"开始处理 {len(process_data)}/{total_items} 条数据（配置限制 import_limit={n}）")

        batch_size = 100
        data_batch = []
        
        with conn.cursor() as cursor:
            for i, data in enumerate(process_data, 1):
                try:
                    # 直接使用元数据中的字段
                    for field in ['run_time', 'publish_time', 'title', 'nickname', 'original_url']:
                        if field not in data:
                            raise ValueError(f"元数据缺少字段: {field}")

                    data_batch.append((
                        data["run_time"].replace(" ", "T"),
                        data["publish_time"],
                        str(data.get("title", "")).strip(),
                        str(data.get("nickname", "")).strip(),
                        data["original_url"]
                    ))

                    if i % batch_size == 0 or i == len(process_data):
                        cursor.executemany("""
                            INSERT INTO wechat_articles 
                            (run_time, publish_time, title, nickname, original_url)
                            VALUES (%s, %s, %s, %s, %s)
                            ON DUPLICATE KEY UPDATE 
                                title=VALUES(title),
                                publish_time=VALUES(publish_time),
                                nickname=VALUES(nickname)
                        """, data_batch)
                        conn.commit()
                        data_batch = []
                        logger.info(f"已提交 {i}/{len(process_data)} ({i/len(process_data):.1%})")

                except Exception as e:
                    logger.error(f"数据记录处理失败: {str(e)}\n{json.dumps(data, ensure_ascii=False)}")
                    continue

        logger.info("数据导入完成")

def query_table(table_name: str, limit: int = 1000) -> list:
    """查询指定表内容"""
    try:
        with get_conn() as conn:
            with conn.cursor(dictionary=True) as cursor:
                cursor.execute(f"SELECT * FROM {table_name} LIMIT %s", (limit,))
                result = cursor.fetchall()
                logger.info(f"查询表 {table_name} 成功，获取 {len(result)} 条记录")
                return result
    except Exception as e:
        logger.error(f"查询表 {table_name} 失败: {str(e)}")
        return []

if __name__ == "__main__":
    # export_wechat_to_mysql(n = 10)
    print(query_table('wechat_articles', 5))  # 测试查询功能
