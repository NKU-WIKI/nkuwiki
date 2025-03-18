# 爬虫模块开发指南

## 模块概述

crawler 模块负责从各种数据源抓取数据，是 ETL 流程中的"Extract"环节。该模块提供了多种爬虫实现，用于从不同平台和网站获取结构化和非结构化数据。

## 文件结构

- `__init__.py` - 模块入口，导入模块专用的配置依赖

- `base_crawler.py` - 基础爬虫类，定义了通用的爬虫接口和功能

- `module_example.py` - 示例爬虫

- `wechat.py` - 微信公众号文章爬虫

- `sina_finance.py` - 新浪财经数据爬虫

- `market.py` - 校园集市数据爬虫

- `init_script.js` - 浏览器反检测脚本

- `webpage_spider/` - 通用网页爬虫工具

## 开发新爬虫

1. **继承基类**: 所有新爬虫应继承 `BaseCrawler` 类:

```python
from __init__ import *
from  base_crawler import BaseCrawler
class MyCrawler(BaseCrawler):
    # 实现必要的方法
    pass

```text

1. **需要实现的方法**:
   - `__init__(self, **kwargs)`: 初始化爬虫配置
     - `self.platform` 平台
     - `self.base_url` 基础链接
     - `self.content_type` 内容类型
   - `scrape(self, **kwargs)`: 主爬取方法，爬取元数据
   - `download(self, oringal_url)`: 下载url的内容
   - `login_for_cookies(self)`: 需要登录的平台必须实现

2. **使用示例**:

```python

# 初始化爬虫

wechat = Wechat(authors = "club_official_accounts", debug=False, headless=True, use_proxy=True)  # 抓取文章元信息
wechat.scrape(max_article_num=5, total_max_article_num=1e10)   # max_article_num最大抓取数量

# 下载文章内容

wechat.download(debug=True, headless=True, use_proxy=True)

```text

## 注意事项

1. **速率限制**: 生产环境（大规模爬取）请设置`debug=false`，调试模式没有反爬机制很容易被封。

2. **错误处理**: 妥善处理网络错误、解析错误等异常情况。

3. **数据保存**: 爬取的原始数据应保存在 `data/raw/` 目录下，推荐以json格式存储，参考以下命名规范：

```json
{
  "platform": "[必填]wechat/website/market/rednote/tiktok/etc.",
  "original_url": "[必填]带签名认证的原始链接",
  "title": "[必填]UTF-8编码",
  "author": "[必填]公众号/发布者名称",
  "publish_time": "[必填]发布时间（根据内容决定YYYY-mm-dd格式，或是YYYY-mm-dd HH:mm:ss格式)",
  "scrape_time": "[必填]]抓取时间（根据内容决定YYYY-mm-dd格式，或是YYYY-mm-dd HH:mm:ss格式)",
  "content_type": "[选填]article/notice/event",
  "expire_time": "[选填]失效时间戳",
  "abstract": "[选填]AI生成的300字摘要",
  "keywords": "[选填]实体词抽取结果",
  "{other_field}": "[选填]其他字段"
}

```text

## 调试与测试

单独运行爬虫模块进行测试:

```bash
python wechat.py #直接运行
python -m etl.crawler.your_crawler # 或者模块式运行

```text

使用内置的日志记录功能记录关键信息:

```python
self.logger.info("爬取进度: {}/{}".format(current, total))

```text

## 参考

- 查看 `base_crawler.py` 作为开发参考

- 参考现有爬虫实现 (如 `wechat.py`, `sina_finance.py`) 了解最佳实践
