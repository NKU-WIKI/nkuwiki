"""微信数据导出到MySQL的ETL流程模块

包含功能：
- 数据库初始化
- JSON数据清洗处理
- 批量数据导入
- 数据查询验证
"""

import re
from loguru import logger
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent)) 

import mysql.connector
import json
from pathlib import Path
from typing import Dict
from config import Config
from mysql.connector.constants import ClientFlag
Config().load_config()


logger.add("logs/data_export.log", rotation="1 day", retention="3 months", level="INFO")

def get_conn(use_database=True) -> mysql.connector.MySQLConnection:
    """获取MySQL数据库连接
    
    Args:
        use_database: 是否连接指定数据库，默认为True
        
    Returns:
        MySQLConnection: 数据库连接对象
    """
    config = {
        "host": Config().get("db_host"),
        "port": Config().get("db_port"),
        "user": Config().get("db_user"),
        "password": Config().get("db_password"),
        "charset": 'utf8mb4',
        "unix_socket": '/var/run/mysqld/mysqld.sock',
        "client_flags": [ClientFlag.MULTI_STATEMENTS]  # 使用新的标志名称
    }
    # 如果是远程连接服务器数据库host改成服务器ip，
    # config["host"] = {服务器ip}
    # 或者在config.json中修改
    if use_database:
        config["database"] = Config().get("db_name")
    return mysql.connector.connect(**config)

def init_database():
    """分步初始化数据库
    
    步骤：
    1. 创建数据库（如果不存在）
    2. 执行所有SQL文件创建表结构
    
    Raises:
        Exception: 任一阶段失败时抛出异常
    """
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

def create_table(table_name: str):
    """根据表名执行对应的SQL文件创建表结构
    
    Args:
        table_name: 要创建的表名称（对应.sql文件名）
        
    Raises:
        FileNotFoundError: 当SQL文件不存在时抛出
        ValueError: 表名不合法时抛出
    """
    try:
        # 验证表名合法性（防止路径遍历）
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', table_name):
            raise ValueError(f"非法表名: {table_name}")
            
        sql_dir = Path(__file__).parent.parent / "tables"
        sql_file = sql_dir / f"{table_name}.sql"
        
        if not sql_file.exists():
            raise FileNotFoundError(f"SQL文件不存在: {sql_file}")

        with get_conn() as conn:
            with conn.cursor() as cur:
                # 读取并执行SQL文件
                sql_content = sql_file.read_text(encoding='utf-8')
                for statement in sql_content.split(';'):
                    statement = statement.strip()
                    if statement:
                        try:
                            cur.execute(statement)
                        except mysql.connector.Error as err:
                            logger.error(f"执行SQL失败: {err}\n{statement}")
                            conn.rollback()
                            raise
                conn.commit()
                logger.info(f"表 {table_name} 创建成功，使用SQL文件: {sql_file.name}")

    except (FileNotFoundError, ValueError) as e:
        logger.error(str(e))
        raise
    except mysql.connector.Error as err:
        logger.error(f"数据库错误: {err}")
        raise
    except Exception as e:
        logger.exception("表结构创建失败")
        raise

def process_file(file_path: str) -> Dict:
    """处理单个JSON文件并返回清洗后的数据
    
    Args:
        file_path: JSON文件路径
        
    Returns:
        dict: 清洗后的结构化数据
        
    Raises:
        ValueError: 缺少必要字段时抛出
        JSONDecodeError: JSON解析失败时抛出
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 修改必要字段验证
        required_fields = ['scrape_time', 'publish_time', 'title', 'author', 'original_url']
        for field in required_fields:
            if field not in data:
                raise ValueError(f"缺少必要字段: {field}")

        # 数据清洗
        return {
            "scrape_time": data["scrape_time"].replace(" ", "T"),
            "publish_time": data["publish_time"],
            "title": str(data.get("title", "")).strip(),
            "author": str(data.get("author", "")).strip(),
            "original_url": data["original_url"]
        }
    except json.JSONDecodeError as e:
        logger.error(f"文件 {file_path} 不是有效的JSON: {str(e)}")
        raise

def export_wechat_to_mysql(n: int):
    """将微信JSON数据导入MySQL数据库
    
    Args:
        n: 最大导入数量限制
        
    流程：
    1. 初始化数据库
    2. 加载元数据文件
    3. 批量插入数据（支持断点续传）
    4. 使用upsert方式更新重复记录
    """
    
    # 初始化数据库
    init_database()

    # 读取所有匹配的元数据文件
    metadata_dir = Path(Config().get("data_path")) / "processed"
    
    # 修改后：使用正则表达式匹配带日期的元数据文件
    metadata_files = [
        f for f in metadata_dir.glob("*.json") 
        if re.match(r"^wechat_metadata_\d{8}\.json$", f.name)
    ]
    
    if not metadata_files:
        logger.error("未找到符合格式的元数据文件，文件名应为：wechat_metadata_YYYYMMDD.json")
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
                    # 修改后：添加content_type字段
                    data_batch.append((
                        data["publish_time"],
                        str(data.get("title", "")).strip(),
                        str(data.get("author", "")).strip(),
                        data["original_url"],
                        data["platform"],
                        data.get("content_type")  # 新增content_type字段
                    ))

                    if i % batch_size == 0 or i == len(process_data):
                        cursor.executemany("""
                            INSERT INTO wechat_articles 
                            (publish_time, title, author, original_url, platform, content_type)
                            VALUES (%s, %s, %s, %s, %s, %s)
                            ON DUPLICATE KEY UPDATE 
                                title=VALUES(title),
                                publish_time=VALUES(publish_time),
                                author=VALUES(author),
                                platform=VALUES(platform),
                                content_type=VALUES(content_type)  # 新增更新字段
                        """, data_batch)
                        conn.commit()
                        data_batch = []
                        logger.info(f"已提交 {i}/{len(process_data)} ({i/len(process_data):.1%})")

                except Exception as e:
                    logger.error(f"数据记录处理失败: {str(e)}\n{json.dumps(data, ensure_ascii=False)}")
                    continue

        logger.info("数据导入完成")

def query_table(table_name: str, limit: int = 1000) -> list:
    """查询指定表内容
    
    Args:
        table_name: 要查询的表名
        limit: 返回结果最大条数，默认1000
        
    Returns:
        list: 查询结果列表，元素为字典形式的记录
    """
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

def delete_table(table_name: str) -> bool:
    """删除指定数据库表
    
    Args:
        table_name: 要删除的表名
        
    Returns:
        bool: 删除是否成功
        
    Raises:
        mysql.connector.Error: 数据库操作失败时抛出
    """
    try:
        # 验证表名格式（防止SQL注入）
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', table_name):
            raise ValueError(f"非法表名: {table_name}")
            
        with get_conn() as conn:
            with conn.cursor() as cursor:
                # 使用字符串格式化（需先验证表名）
                cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
                conn.commit()
                logger.warning(f"成功删除表: {table_name}")
                return True
    except mysql.connector.Error as e:
        logger.error(f"删除表 {table_name} 失败: {str(e)}")
        raise
    except ValueError as e:
        logger.error(f"表名验证失败: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"发生未知错误: {str(e)}")
        return False

if __name__ == "__main__":
    # delete_table("wechat_articles")
    init_database()
    export_wechat_to_mysql(n = 10)
    # print(query_table('wechat_articles', 5))  # 测试查询功能
    
    # create_table("market_posts")