"""web数据导出到MySQL的流程模块

包含功能：
- 数据库初始化
- 批量数据导入
"""
import datetime
import os
import sqlite3
import sys  # noqa: F401
from pathlib import Path  # noqa: F401

sys.path.append(str(Path(__file__).parent.parent.parent))

import mysql.connector
import json  # noqa: F401
from db_config import Config
from mysql.connector.constants import ClientFlag
from dotenv import load_dotenv,set_key

load_dotenv()


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


def init_database(logger):
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






def export_web_to_mysql(logger):
    """将网页保存的临时sqlite数据导入MySQL数据库

    Args:
        n: 最大导入数量限制

    流程：
    1. 初始化数据库
    2. 加载元数据文件
    3. 批量插入数据（支持断点续传）
    4. 使用upsert方式更新重复记录
    """

    # 初始化数据库
    init_database(logger)
    offset = int(os.getenv('offset'))

    conn = sqlite3.connect(os.path.join('./counselor','nk_2_update.db'))
    cursor = conn.cursor()
    cursor.execute("SELECT title,content,url,push_time_date,source FROM entries ORDER BY push_time_date DESC OFFSET ?",(offset,))
    # 获取列名并转换结果
    results2 = []
    length = len(cursor.fetchall())
    if length == 0:
        logger.info(f'【上传mysql】{datetime.datetime.now().strftime("%Y-%m-%d")}无数据。')
        return
    flag = False
    for title, content, url, push_time_date, source in cursor.fetchall():
        results2.append({
            'title': title,
            'author':source,
            'original_url': url,
            'publish_time': push_time_date,
            'scrape_time': datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            'platform':str(source)+'网站',
        })
        if push_time_date == '':
            flag = True
            logger.info(f'【上传mysql】title:{title},url:{url},author:{source}，push_time_date为空。')
        if title == '':
            flag = True
            logger.info(f'【上传mysql】title:{title},url:{url},author:{source}，title为空。')

    conn.close()
    if flag:
        logger.info(f'【上传mysql】检测到数据不完整，本次上传取消。')
        return
    logger.info(f'【上传mysql】数据完整，准备上传。')
    offset += length
    set_key('.env', 'offset', str(offset))




    with get_conn() as conn:
        conn.autocommit = False

        batch_size = 100
        data_batch = []

        with conn.cursor() as cursor:
            for i, data in enumerate(results2, 1):
                try:
                    # 修改后：添加content_type字段
                    data_batch.append((
                        data["publish_time"],
                        str(data.get("title", "")).strip(),
                        str(data.get("author", "")).strip(),
                        data["original_url"],
                        data["platform"]
                    ))

                    if i % batch_size == 0 or i == len(results2):
                        cursor.executemany("""
                            INSERT INTO web_articles 
                            (publish_time, title, author, original_url, platform)
                            VALUES (%s, %s, %s, %s, %s, %s)
                            ON DUPLICATE KEY UPDATE 
                                title=VALUES(title),
                                publish_time=VALUES(publish_time),
                                author=VALUES(author),
                                platform=VALUES(platform)
                        """, data_batch)
                        conn.commit()
                        data_batch = []

                except Exception as e:
                    logger.error(f"数据记录处理失败: {str(e)}\n{json.dumps(data, ensure_ascii=False)}")
                    continue

        logger.info("数据导入完成")








if __name__ == "__main__":
    # delete_table("wechat_articles")
    init_database()
    export_web_to_mysql(n=10)
    # print(query_table('wechat_articles', 5))  # 测试查询功能

    # create_table("market_posts")