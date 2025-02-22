import base64
import hmac
import hashlib
import time  # 已在代码中使用但需要确认是否导入
import random  # 已在代码中使用但需要确认是否导入
from typing import Optional  # 可选，用于类型提示
import json

from __init__ import *
from base_crawler import BaseCrawler

Config().load_config()


class Market(BaseCrawler):
    """Zanao市场数据爬虫"""
    
    def __init__(self, debug=False, headless=False):
        self.platform = "market"
        self.content_type = "post"
        self.base_url = "https://c.zanao.com"
        super().__init__(self.platform, debug, headless)
        self.api_urls = {
            "list": "https://api.x.zanao.com/thread/v2/list",
            "comment": "https://c.zanao.com/sc-api/comment/post",
            "search": "https://c.zanao.com/thread/v2/search",
            "hot": "https://c.zanao.com/thread/hot"
        }
        self.university = "nankai"
        self.secret_key = "1b6d2514354bc407afdd935f45521a8c"  # 来自JS的固定密钥

    def _generate_m(self, length=20):
        """生成随机数m"""
        try:
            return ''.join(str(random.randint(0, 9)) for _ in range(length))
        except Exception as e:
            self.logger.error(f"生成随机数m失败: {str(e)}")
            self.logger.debug(f"生成长度参数: {length}")
            raise

    def _generate_td(self):
        """生成时间戳"""
        return int(time.time())

    def _hmac_md5(self, key, message):
        return hashlib.md5(message.encode()).hexdigest()

    def _generate_ah(self, m, td):
        raw_str = f"{self.university}_{m}_{td}_{self.secret_key}"
        return self._hmac_md5(self.secret_key, raw_str)

    def _generate_headers(self):
        """完整请求头生成"""
        try:
            m = self._generate_m(20)
            if not m.isdigit() or len(m) != 20:
                raise ValueError(f"Invalid m generated: {m}")
        except Exception as e:
            self.logger.error(f"生成请求头时发生错误: {str(e)}")
            m = '0' * 20
        td = self._generate_td()
        self.headers.update({
            "X-Sc-Nd": m,
            "X-Sc-Od": Config().get("market_token"),
            "X-Sc-Ah": self._generate_ah(m, td),
            "X-Sc-Td": str(td),
            'X-Sc-Alias': self.university,
        })
        return self.headers

    def get_hot_list(self):
        """获取热门列表"""
        try:
            headers = self._generate_headers()
            
            response = self.page.request.post(
                self.api_urls["list"],
                headers=headers,
                params={"from_time": str(int(time.time())), "hot": "1"}
            )
            # 
            if response.status == 200:
                data = response.json()
                # 增加数据结构校验
                if isinstance(data, dict):
                    data_dict = data.get("data", {})
                    if isinstance(data_dict, dict):
                        items = data_dict.get("list", [])
                        # 过滤非字典类型的项
                        return [self._parse_item(item) for item in items if isinstance(item, dict)]
                self.logger.error("API返回数据结构异常: %s", data)
                return []
            return []
        except Exception as e:
            self.logger.error(f"获取热门列表失败: {str(e)}，响应数据: {response.text if response else '无响应'}")
            self.counter['error'] += 1
            return []

    def _parse_item(self, item):
        """解析数据项"""
        return {
            "id": item.get("thread_id"),
            "title": item.get("title"),
            "content": item.get("content"),
            "finish_status": item.get("finish_status"),
            "nickname": item.get("nickname"),
            "publish_time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
            "original_url": f"{self.base_url}/thread/{item.get('thread_id')}"
        }

    def post_comment(self, thread_id, content):
        """发表评论"""
        try:
            self.random_sleep()
            response = self.page.request.post(
                self.api_urls["comment"],
                headers=self._generate_headers(),
                data={
                    "id": str(thread_id),
                    "content": content,
                    "reply_comment_id": "0",
                    "root_comment_id": "0",
                    "cert_show": "0",
                    "isIOS": "false"
                },
                cookies=self._load_cookies()
            )
            return response.status == 200
        except Exception as e:
            self.logger.error(f"评论失败: {str(e)}")
            self.counter['error'] += 1
            return False

    def search_posts(self, keyword):
        """搜索帖子"""
        try:
            response = self.page.request.post(
                self.api_urls["search"],
                headers=self._generate_headers(),
                data={
                    "keyword": keyword,
                    "page": 1,
                    "page_size": 10
                }
            )
            
            if response.status == 200:
                data = response.json()
                return [self._parse_item(item) for item in data.get("data", {}).get("list", [])]
            return []
        except Exception as e:
            self.logger.error(f"搜索失败: {str(e)}")
            self.counter['error'] += 1
            return []

    def run(self, keywords=[]):
        """执行完整爬取流程"""
        start_time = time.time()
        try:
            # 检查登录状态
            if not self._load_cookies():
                raise Exception("需要先执行登录操作")
            
            # 获取并保存热门列表
            hot_list = self.get_hot_list()
            self.update_scraped_articles(self.get_scraped_original_urls(), hot_list)
            
            # 执行关键词搜索
            search_results = []
            for kw in keywords:
                self.random_sleep()
                search_results.extend(self.search_posts(kw))
            
            # 保存搜索结果
            self.update_scraped_articles(self.get_scraped_original_urls(), search_results)
            
            return True
        finally:
            self.save_counter(start_time)
            self.close()

if __name__ == "__main__":
    market = Market(debug=True, headless=False)
    hot_list = market.get_hot_list()
    print(hot_list)
     
