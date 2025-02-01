#!/usr/bin/env python3
"""
微信元数据导入工具（支持断点续传和错误重试）
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import logging
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, TypedDict
import time

import psycopg2
from psycopg2.extras import execute_batch
from tqdm import tqdm
from tenacity import (
    retry,
    stop_after_attempt,
    wait_fixed,
    retry_if_exception_type
)
from dotenv import load_dotenv

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("import.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ImporterConfig:
    """配置容器类"""
    def __init__(self):
        self.batch_size = 200
        self.max_retries = 3
        self.resume = False
        self.dry_run = False

class WechatArticle(TypedDict):
    original_url: str
    title: str
    publish_time: datetime
    nickname: str
    content_type: str
    file_path: str
    download_status: str

class WechatImporter:
    def __init__(self, db_config: Dict[str, str], config: ImporterConfig):
        self.db_config = db_config
        self.config = config
        self.processed_files = set()
        self.stats = {
            'total': 0,
            'success': 0,
            'failed': 0,
            'skipped': 0
        }
        
        # 加载进度记录
        if self.config.resume and os.path.exists('processed.txt'):
            with open('processed.txt', 'r') as f:
                self.processed_files = set(f.read().splitlines())

        self.schema = os.getenv('DB_SCHEMA', 'nkuwiki')
        self.table_name = os.getenv('DB_TABLE', 'wechat_articles')

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_fixed(1),
        retry=retry_if_exception_type(psycopg2.OperationalError)
    )
    def _get_connection(self):
        """获取数据库连接（带重试）"""
        logger.debug(f"连接参数: {self.db_config}")
        return psycopg2.connect(**self.db_config)

    def _parse_meta(self, meta_path: Path) -> Tuple[dict, str]:
        try:
            if not meta_path.exists():
                return None, f"文件不存在: {meta_path}"
            
            with meta_path.open('r', encoding='utf-8') as f:
                meta = json.load(f)
                
            # 处理不同时间格式
            publish_time_str = meta.get("publish_time") or meta.get("run_time", "")
            try:
                # 尝试带时间的格式
                publish_time = datetime.strptime(publish_time_str, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                try:
                    # 尝试仅日期格式
                    publish_time = datetime.strptime(publish_time_str, "%Y-%m-%d")
                except ValueError as e:
                    return None, f"时间格式错误: {publish_time_str}"
                
            return {
                "original_url": meta["original_url"],
                "title": meta["title"],
                "publish_time": publish_time,
                "nickname": meta.get("nickname", ""),
                "content_type": meta.get("content_type", ""),
                "file_path": meta.get("file_path", ""),
                "download_status": meta.get("download_status", "")
            }, ""
        except Exception as e:
            return None, f"解析失败: {str(e)}"

    def _process_batch(self, cur, batch: List[dict]):
        query = """
            INSERT INTO nkuwiki.wechat_articles (
                original_url, title, publish_time,
                nickname, content_type, file_path, download_status
            ) VALUES (
                %(original_url)s, %(title)s, %(publish_time)s,
                %(nickname)s, %(content_type)s, %(file_path)s, %(download_status)s
            ) ON CONFLICT (original_url) DO NOTHING
        """
        execute_batch(cur, query, batch)

    def _initialize_database(self, cur):
        """确保表结构正确"""
        try:
            cur.execute("""
                DROP TABLE IF EXISTS nkuwiki.wechat_articles CASCADE;
                CREATE TABLE nkuwiki.wechat_articles (
                    article_id BIGSERIAL PRIMARY KEY,
                    original_url TEXT NOT NULL UNIQUE,
                    title VARCHAR(255) NOT NULL,
                    publish_time TIMESTAMPTZ NOT NULL,
                    nickname VARCHAR(255),
                    content_type VARCHAR(50),
                    file_path TEXT,
                    download_status VARCHAR(20)
                );
                CREATE INDEX idx_publish_time ON nkuwiki.wechat_articles (publish_time);
            """)
            cur.connection.commit()
        except Exception as e:
            logger.error(f"数据库初始化失败: {str(e)}")
            raise

    def run_import(self, data_dir: str):
        """执行导入流程"""
        conn = None
        try:
            conn = self._get_connection()
            if not conn:
                raise RuntimeError("无法建立数据库连接")
            
            # 创建新的游标用于数据处理
            with conn.cursor() as cur:
                self._initialize_database(cur)
                conn.commit()
                
                # 修改文件匹配逻辑，适配Linux路径
                meta_files = list(Path(data_dir).rglob("*.json")) + list(Path(data_dir).rglob("*.JSON"))
                
                logger.info(f"找到 {len(meta_files)} 个元数据文件")
                batch = []
                
                with tqdm(total=len(meta_files), desc="处理进度") as pbar:
                    for meta_path in meta_files:
                        logger.debug(f"正在处理: {meta_path}")
                        self.stats['total'] += 1
                        str_path = str(meta_path)
                        
                        # 修改跳过条件，添加调试日志
                        if self.config.resume and str_path in self.processed_files:
                            logger.debug(f"跳过已处理文件: {str_path}")
                            self.stats['skipped'] += 1
                            pbar.update(1)
                            continue
                            
                        # 解析数据
                        data, err = self._parse_meta(meta_path)
                        if not data:
                            self.stats['failed'] += 1
                            logger.error(f"{meta_path}: {err}")
                            continue
                            
                        # 收集批次
                        batch.append(data)
                        if len(batch) >= self.config.batch_size:
                            if not self.config.dry_run:
                                self._process_batch(cur, batch)
                                conn.commit()
                            batch = []
                            
                        # 记录进度
                        self.processed_files.add(str_path)
                        pbar.update(1)
                        
                    # 处理剩余数据
                    if batch and not self.config.dry_run:
                        self._process_batch(cur, batch)
                        conn.commit()
                    
            # 游标在此处自动关闭
        except Exception as e:
            logger.error(f"致命错误: {str(e)}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()
            # 保存进度
            with open('processed.txt', 'w') as f:
                f.write('\n'.join(self.processed_files))
            # 打印统计
            logger.info(f"""
                导入完成:
                总文件数: {self.stats['total']}
                成功: {self.stats['success']}
                失败: {self.stats['failed']}
                跳过: {self.stats['skipped']}
            """)

def parse_args():
    parser = argparse.ArgumentParser(description='微信元数据导入工具')
    parser.add_argument('data_dir', help='数据目录路径')
    # 添加互斥参数组
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--resume', action='store_true', help='断点续传模式')
    group.add_argument('--no-resume', dest='resume', action='store_false', 
                      help='禁用断点续传（默认）')
    parser.set_defaults(resume=False)  # 设置默认值
    
    parser.add_argument('--dry-run', action='store_true',
                       help='试运行模式（不实际写入数据库）')
    parser.add_argument('--log-level', default='INFO',
                       choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                       help='日志级别（默认INFO）')
    return parser.parse_args()

def main():
    load_dotenv()
    args = parse_args()
    
    config = ImporterConfig()
    config.resume = args.resume  # 自动处理--resume/--no-resume
    config.dry_run = args.dry_run
    logging.getLogger().setLevel(args.log_level)
    
    db_config = {
        "host": os.getenv('DB_HOST', 'localhost'),
        "port": os.getenv('DB_PORT', '5432'),
        "dbname": os.getenv('DB_NAME', 'nkuwiki_db'),
        "user": os.getenv('DB_USER', 'nkuwiki_user'),  # ← 关键修改
        "password": os.getenv('DB_PASSWORD', '123456'),
        "connect_timeout": int(os.getenv('DB_CONNECT_TIMEOUT', 30)),
        "sslmode": "disable"  # 添加SSL模式
    }
    
    importer = WechatImporter(db_config, config)
    importer.run_import(args.data_dir or "/data/wechat/202501/")

if __name__ == "__main__":
    main()