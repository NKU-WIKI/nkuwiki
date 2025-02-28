# -*- coding: utf-8 -*-
import scrapy
from mysql.connector import ClientFlag
from scrapy.selector import Selector
from items import ContentItem
from parse_different_college import parse_function,url_maps
import sqlite3
import re
import os
import mysql.connector
from datetime import date
def check_url_end(url):
    pattern = r'\d+\.(html|shtml|chtml|htm)$|/post/\d+$|/article/\d+$'
    return bool(re.search(pattern, url))

def check_content(url):
    if '/list' in url:
        return False
    l = ['page.htm','news/news-detail','/info/','mp.weixin.qq.com']
    for i in l:
        if i in url:
            return True
    if check_url_end(url):
        return True
    return False
from urllib.parse import urlparse

def is_valid_url(url):
    try:
        parsed_url = urlparse(url)
        # 检查是否包含协议（scheme）和网络位置（netloc）
        return all([parsed_url.scheme in ['http', 'https'], parsed_url.netloc])
    except ValueError:
        return False

def get_conn(use_database=True) -> mysql.connector.MySQLConnection:
    """获取MySQL数据库连接

    Args:
        use_database: 是否连接指定数据库，默认为True

    Returns:
        MySQLConnection: 数据库连接对象
    """
    from ..db_config import Config
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

class WiKiSpider(scrapy.Spider):
    name = 'wikipieda_spider'
    allowed_domains = ['nankai.edu.cn']
    start_urls = list(url_maps.values())
    custom_settings = {
        'ITEM_PIPELINES': {'counselor.pipelines.WikiPipeline': 800},
        'LOG_FILE': f'./log/{date.today().strftime("%Y-%m-%d")}.txt'

    }



    conn = get_conn()
    cursor = conn.cursor()
    # 查询所有 url 字段的值
    cursor.execute("SELECT original_url FROM web_articles")
    rows = cursor.fetchall()
    # 将查询结果存储到一个集合中
    url_set = set(row[0] for row in rows)
    # 关闭数据库连接
    cursor.close()
    conn.close()



    path1 = 'nk_2_update.db'
    if 'counselor' not in os.getcwd():
        path1 = './counselor/'+path1
    conn = sqlite3.connect(path1, check_same_thread=False)
    cursor = conn.cursor()
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
    conn.commit()
    # 查询所有 url 字段的值
    cursor.execute("SELECT url FROM entries")
    rows = cursor.fetchall()
    # 将查询结果存储到一个集合中
    url_set.update(set(row[0] for row in rows))
    # 关闭数据库连接
    cursor.close()
    conn.close()

    def check_if_in_sqlite(self,url):
        # 检查URL是否已经存在
        if url in self.url_set:
            return True
        else:
            return False

    # scrapy默认启动的用于处理start_urls的方法
    def parse(self, response):
        # 获得一个新请求
        this_url = response.url
        # 说明该请求时一个分类
        yield scrapy.Request(this_url, callback=self.parse_category)

    def parse_category(self, response):
        '''
        处理分类页面的请求
        :param response:
        :return:
        '''
        sel = Selector(response)
        this_url = response.url
        parsed_url = urlparse(this_url)
        base = f"{parsed_url.scheme}://{parsed_url.netloc}"
        self.logger.info(f'本次访问URL:{this_url}')
        # print('当前队列长度：',len(self.crawler.engine.slot.scheduler))
        # 完成两件事：找新的页面，记录新的页面
        a_tags = sel.xpath('//a')
        urls = [tag.xpath('@href').get() for tag in a_tags]
        url2 = []
        for url in urls:
            flag = True
            if url == '#':
                continue
            if not isinstance(url, str):
                continue
            if url is None:
                continue
            if 'javascript:' in url:
                flag = False
            elif 'void(0)' in url:
                flag = False
            elif 'JavaScript:;' in url:
                flag = False
            elif '_' in url:  # 非法字符
                flag = False
            elif '<span' in url:
                flag = False
            elif '@' in url:
                flag = False
            elif '*' in url:
                flag = False
            elif '.docx' in url:
                flag = False
            elif '.doc' in url:
                flag = False
            elif '.pdf' in url:
                flag = False
            elif '.xlsx' in url:
                flag = False
            elif '.xls' in url:
                flag = False
            elif 'page.psp' in url:
                flag = False


            if not flag:
                continue
            if 'http' not in url:
                url = base + url.replace('..', '')
            url2.append(url)
        url2 = [i.replace(' ','') for i in url2]
        # 处理完分类页面后，将所有可能的内容请求链接直接提交处理队列处理
        for url in url2:
            if is_valid_url(url):
                if self.check_if_in_sqlite(url):
                    continue
                if check_content(url):
                    yield scrapy.Request(url, callback=self.parse_content)
                else:
                    yield scrapy.Request(url, callback=self.parse_category)

    def parse_content(self, response):
        '''
        处理文章页面请求
        :param response:
        :return:
        '''

        this_url = response.url
        parsed_url = urlparse(this_url)
        self.logger.info(f'本次访问URL:{this_url},进入到了文章解析函数。')
        base = parsed_url.netloc
        college = ''
        # print('当前队列长度：', len(self.crawler.engine.slot.scheduler))
        for key, value in url_maps.items():
            if base in value:
                college = key
        if college == '':
            self.logger.info(f'未能解析出学院名字，url={this_url}')
        try:
            title, push_time, content, img = parse_function(response.text, this_url)
        except Exception as e:
            self.logger.error(f"出错在学院{college},{e},url={this_url}")
            return ContentItem()
        if title is None:
            title = response.xpath("//title/text()").get()
            if title is None:
                title = ''
        counselor_item = ContentItem()
        counselor_item['title'] = title
        counselor_item['push_time'] = push_time
        counselor_item['content'] = content
        counselor_item['file_url'] = img
        counselor_item['source'] = college
        counselor_item['url'] = this_url

        return counselor_item
