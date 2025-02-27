# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy

#     id = db.Column(db.Integer, primary_key=True, unique=True, nullable=False)
#      = db.Column(db.Text, index=True)
#     type = db.Column(db.Text)
#     data_create_time = db.Column(db.DateTime, default=datetime.now())  # 设置默认值为当前时间
#     push_time = db.Column(db.Text)  # 发布时间
#     source = db.Column(db.Text)  # 来源
#     url = db.Column(db.Text)
#     content = db.Column(db.Text)  # 文章内容
#     file_url = db.Column(db.Text,default='')  # 如果以PDF发的通知，存储PDF链接。

# 定义实体类
class ContentItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    # 标题
    title = scrapy.Field()
    # 发布时间
    push_time = scrapy.Field()
    # 类别，例如通知公告
    # type = scrapy.Field()
    # 来源，例如文学院
    source = scrapy.Field()
    # 链接地址
    url = scrapy.Field()
    # 文章内容
    content = scrapy.Field()
    # pdf链接（若有）
    file_url = scrapy.Field()
    def print_self(self):
        from pprint import pp
        pp(dict(self))
