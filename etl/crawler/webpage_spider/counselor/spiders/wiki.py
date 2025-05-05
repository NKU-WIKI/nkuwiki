# -*- coding: utf-8 -*-
import scrapy
from scrapy.selector import Selector
from items import ContentItem
from parse_different_college import parse_function,url_maps
import sqlite3
import re
import os
from datetime import date
def check_url_end(url):
    pattern = r'\d+\.(html|shtml|chtml|htm)$|/post/\d+$|/article/\d+$'
    return bool(re.search(pattern, url))

def check_content(url):
    if 'https://career.nankai.edu.cn/company/index/id' in url:
        return True
    if url in [
        'https://career.nankai.edu.cn/download/index/type/2.html',
        'https://career.nankai.edu.cn/download/index/type/1.html',
    ]: # 伪装为文章的列表链接。
        return True
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



class WiKiSpider(scrapy.Spider):
    name = 'wikipieda_spider'
    allowed_domains = ['nankai.edu.cn']
    start_urls = list(url_maps.values())
    custom_settings = {
        'ITEM_PIPELINES': {'counselor.pipelines.WikiPipeline': 800},
        'LOG_FILE': f'./log/{date.today().strftime("%Y-%m-%d")}.txt'

    }
    # 将查询结果存储到一个集合中
    url_set = set()

    path1 = 'nk_2_update.db'
    script_dir = os.path.dirname(os.path.abspath(__file__))
    path1 = os.path.join(os.path.dirname(script_dir),path1)
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
        if response.status not in range(200, 300):
            self.logger.error(f'访问{response.url}返回状态码{response.status},响应的内容为{response.content.decode()}')
            return
        sel = Selector(response)
        this_url = response.url
        parsed_url = urlparse(this_url)
        base = f"{parsed_url.scheme}://{parsed_url.netloc}"
        self.logger.info(f'本次访问URL:{this_url}')
        print('当前队列长度：',len(self.crawler.engine.slot.scheduler))
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
        if response.status not in range(200, 300):
            self.logger.error(f'访问{response.url}返回状态码{response.status},响应的内容为{response.content.decode()}')
            return
        this_url = response.url
        parsed_url = urlparse(this_url)
        self.logger.info(f'本次访问URL:{this_url},进入到了文章解析函数。')
        base = parsed_url.netloc
        college = ''
        print('当前队列长度：', len(self.crawler.engine.slot.scheduler))
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
