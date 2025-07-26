# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
import re
import os
import sqlite3
import threading
import hashlib
from pathlib import Path
from datetime import datetime
from .items import ContentItem, LinkItem


def extract_date(text):
    # 定义正则表达式匹配日期
    pattern = r'\d{4}[-/]\d{1,2}[-/]\d{1,2}'

    # 搜索匹配的日期字符串
    match = re.search(pattern, text)

    if match:
        # 提取匹配的日期字符串
        date_str = match.group(0)

        # 将日期字符串转换为 datetime.date
        # 尝试不同的日期格式
        for fmt in ("%Y/%m/%d", "%Y-%m-%d"):
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue

        # 如果无法匹配任何日期格式，返回 None
        return None
    else:
        return None

def get_date_from_url(url:str):
    date_match = re.search(r"(\d{4}/\d{2}/\d{2})", url)

    if date_match:
        # 提取日期字符串并转换为 datetime.date 格式
        date_str = date_match.group(1).replace("/", "-")  # 将斜杠替换为短横线
        date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
        return date_obj
    else:
        return None

class WikiPipeline(object):

    def __init__(self):
        # 数据库路径
        counselor_dir = Path(__file__).parent
        self.db_path = counselor_dir / 'nk_database.db'
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.lock = threading.Lock()

        # 快照存储路径
        # /data/raw/website/snapshots/
        self.snapshots_path = counselor_dir.parent.parent.parent / 'data' / 'raw' / 'website' / 'snapshots'
        self.snapshots_path.mkdir(parents=True, exist_ok=True)

    def add_entry(self, title, push_time, url, content, file_url, source):
        with self.lock:
            if title is None:
                title = ''
            if push_time is None:
                push_time = ''
            if content is None:
                content = ''
            if file_url is None:
                file_url = ''
            
            # 检查URL是否已经存在
            self.cursor.execute('SELECT COUNT(*) FROM entries WHERE url = ?', (url,))
            count = self.cursor.fetchone()[0]
            if count > 0:
                return  # 如果URL已存在，不插入新记录
            push_time_date = None
            if push_time != '':
                push_time_date = extract_date(push_time_date)
            else:
                push_time_date = get_date_from_url(url)
            self.cursor.execute('''
                INSERT INTO entries (title, push_time, url, content, file_url, source, push_time_date)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (title, push_time, url, content, file_url, source,push_time_date))
            self.conn.commit()

    def open_spider(self, spider):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                push_time TEXT NOT NULL,
                url TEXT NOT NULL,
                content TEXT NOT NULL,
                file_url TEXT,
                source TEXT NOT NULL,
                push_time_date DATE NULL
            )
        ''')
        self.conn.commit()


    def close_spider(self, spider):
        self.conn.close()

    def process_item(self, item, spider):
        obj = dict(item)
        # spider.logger.info(f"obj={str(obj)}")
        if obj == {}:
            spider.logger.warning('未能解析出任何东西')
            return
        if obj['url'] is None:
            spider.logger.warning('url未赋值。')
            return
        url = obj['url']
        if obj['title'] is None:
            spider.logger.warning(f'标题未赋值。url={url}')
        if obj['push_time'] is None:
            spider.logger.warning(f'push_time未赋值。url={url}')
        # if obj['type'] is None:
        #     spider.logger.warning('type未赋值。')
        if obj['source'] is None:
            spider.logger.warning(f'source未赋值。url={url}')

        # 保存网页快照
        if 'html_content' in obj and obj['html_content']:
            if not obj.get('file_url'): # 只为网页创建快照，不为文档创建
                try:
                    # 使用URL的SHA256哈希作为文件名
                    url_hash = hashlib.sha256(url.encode('utf-8')).hexdigest()
                    snapshot_file = self.snapshots_path / f"{url_hash}.html"
                    with open(snapshot_file, 'wb') as f:
                        f.write(obj['html_content'])
                    spider.logger.info(f"网页快照已保存: {snapshot_file}")
                except Exception as e:
                    spider.logger.error(f"保存网页快照失败: {e}")
            # 从item中移除，避免存入数据库
            del obj['html_content']

        if obj['content'] =='' and obj['file_url'] is None:
            # spider.logger.error(f'content和file_url未赋值。url={url}')
            return
        try:
            self.add_entry(obj['title'],obj['push_time'],url,obj['content'],obj['file_url'],obj['source'])
        except Exception as e:
            spider.logger.error(f"Failed to write item to file: {e}")
        return item


class LinkGraphPipeline(object):
    def __init__(self):
        path1 = 'nk_database.db'
        script_dir = os.path.abspath(__file__)
        path1 = os.path.join(os.path.dirname(script_dir), path1)
        self.conn = sqlite3.connect(path1, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.lock = threading.Lock()

    def open_spider(self, spider):
        with self.lock:
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS link_graph (
                    source_url TEXT NOT NULL,
                    target_url TEXT NOT NULL,
                    PRIMARY KEY (source_url, target_url)
                )
            ''')
            self.conn.commit()

    def close_spider(self, spider):
        self.conn.close()

    def process_item(self, item, spider):
        if not isinstance(item, LinkItem):
            return item  # 如果不是LinkItem，则传递给下一个pipeline

        with self.lock:
            try:
                self.cursor.execute('''
                    INSERT OR IGNORE INTO link_graph (source_url, target_url)
                    VALUES (?, ?)
                ''', (item['source_url'], item['target_url']))
                self.conn.commit()
            except Exception as e:
                spider.logger.error(f"Failed to write link to database: {e}")
        return item