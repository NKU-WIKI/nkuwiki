import mysql.connector
import json
import glob
import logging
import os
from pathlib import Path
from typing import Dict, Any
from dotenv import load_dotenv
import re

# 加载.env文件
env_path = Path(__file__).parent / '.env'
if env_path.exists():
    load_dotenv(dotenv_path=env_path, override=True)
else:
    logging.warning("未找到.env配置文件，将使用环境变量")

def load_config() -> Dict[str, Any]:
    """加载带有连接池的数据库配置"""
    return {
        "host": os.environ.get("DB_HOST", "localhost"),
        "port": int(os.environ.get("DB_PORT", 5432)),
        "user": os.environ.get("DB_USER", "nkuwiki"),
        "password": os.environ.get("DB_PASSWORD"),
        "database": os.environ.get("DB_NAME", "structured")
    }

def create_table(conn) -> None:
    """创建支持中文的数据库表结构"""
    with conn.cursor() as cursor:
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS wechat_articles (
            id INT AUTO_INCREMENT PRIMARY KEY,
            run_time        DATETIME,
            publish_time    DATE,
            title           VARCHAR(512) CHARACTER SET utf8mb4,
            nickname        VARCHAR(255) CHARACTER SET utf8mb4,
            original_url    VARCHAR(512),
            content_type    VARCHAR(50),
            file_path       VARCHAR(512),
            download_status VARCHAR(50),
            UNIQUE KEY (original_url)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        conn.commit()

def process_file(file_path: str) -> Dict:
    """处理单个JSON文件并返回清洗后的数据"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 验证必要字段存在
        required_fields = ['run_time', 'publish_time', 'title', 'nickname', 
                          'original_url', 'content_type', 'file_path', 'download_status']
        for field in required_fields:
            if field not in data:
                raise ValueError(f"缺少必要字段: {field}")

        # 数据清洗
        return {
            "run_time": data["run_time"].replace(" ", "T"),
            "publish_time": data["publish_time"],
            "title": str(data.get("title", "")).strip(),
            "nickname": str(data.get("nickname", "")).strip(),
            "original_url": data["original_url"],
            "content_type": data["content_type"],
            "file_path": data["file_path"],
            "download_status": data["download_status"]
        }
    except json.JSONDecodeError as e:
        logging.error(f"文件 {file_path} 不是有效的JSON: {str(e)}")
        raise

def export_wechat_to_postgres():
    """将微信JSON数据导入PostgreSQL数据库"""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    config = load_config()
    
    try:
        # 测试连接
        test_conn = mysql.connector.connect(**config)
        test_conn.close()
        
        with mysql.connector.connect(**config) as conn:
            conn.autocommit = False
            create_table(conn)
            
            # 匹配月份目录格式为YYYYMM
            json_files = glob.glob("/data/raw/wechat/20[0-9][0-9][0-9][0-9]/*.json")
            
            # 验证文件路径格式
            valid_files = [
                f for f in json_files 
                if re.match(r"/data/raw/wechat/\d{6}/.+\.json$", f)
            ]
            invalid_files = set(json_files) - set(valid_files)
            
            logging.info(f"发现 {len(valid_files)} 个有效文件（共扫描到 {len(json_files)} 个文件）")
            if invalid_files:
                logging.warning(f"发现 {len(invalid_files)} 个无效路径文件，样例：{list(invalid_files)[:3]}")
            
            total = len(valid_files)
            logging.info(f"开始处理 {total} 个文件")

            batch_size = 100
            data_batch = []
            
            with conn.cursor() as cursor:
                for i, file_path in enumerate(valid_files, 1):
                    try:
                        data = process_file(file_path)
                        data_batch.append((
                            data["run_time"],
                            data["publish_time"],
                            data["title"],
                            data["nickname"],
                            data["original_url"],
                            data["content_type"],
                            data["file_path"],
                            data["download_status"]
                        ))

                        if i % batch_size == 0:
                            cursor.executemany("""
                                INSERT INTO wechat_articles 
                                (run_time, publish_time, title, nickname, 
                                 original_url, content_type, file_path, download_status)
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                                ON DUPLICATE KEY UPDATE original_url=VALUES(original_url)
                            """, data_batch)
                            conn.commit()
                            data_batch = []
                            logging.info(f"已提交 {i}/{total} ({i/total:.1%})")

                    except Exception as e:
                        logging.error(f"文件 {file_path} 处理失败: {str(e)}\n{json.dumps(data, ensure_ascii=False)}")
                        continue

                # 提交剩余数据
                if data_batch:
                    cursor.executemany("""
                        INSERT INTO wechat_articles 
                        (run_time, publish_time, title, nickname, 
                         original_url, content_type, file_path, download_status)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE original_url=VALUES(original_url)
                    """, data_batch)
                    conn.commit()

            logging.info("数据导入完成")

    except Exception as e:
        logging.error(f"数据库连接失败: {str(e)}")
        raise

if __name__ == "__main__":
    export_wechat_to_postgres()
