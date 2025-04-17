from scrapy.exceptions import IgnoreRequest
from parse_different_college import forgot_netlocs, url_maps_urls
import re
from urllib.parse import urlparse
from filter_url import filter_url

def check_url_end(url):
    pattern = r'\d+\.html$'
    return bool(re.search(pattern, url))


def check_content(url):
    l = ['page.htm', 'news/news-detail', '/info/']
    for i in l:
        if i in url:
            return True
    if check_url_end(url):
        return True
    return False


def check_url_allowed(url):
    for u in url_maps_urls:
        if u in url:
            return True
    return False


class URLFilterMiddleware:

    @classmethod
    def from_crawler(cls, crawler):
        # 初始化中间件
        return cls()

    def process_request(self, request, spider):
        """
        在请求被发送之前，对URL进行筛选
        """
        url = request.url
        parsed_url = urlparse(url)
        netloc = parsed_url.netloc
        if url == '#':
            raise IgnoreRequest(f"URL {request.url} 被筛选出去。")
        if not isinstance(url, str):
            raise IgnoreRequest(f"URL {request.url} 被筛选出去。")
        if 'javascript:' in url:
            raise IgnoreRequest(f"URL {request.url} 被筛选出去。")
        elif 'void(0)' in url:
            raise IgnoreRequest(f"URL {request.url} 被筛选出去。")
        elif 'JavaScript:;' in url:
            raise IgnoreRequest(f"URL {request.url} 被筛选出去。")
        elif '_' in url:  # 非法字符
            raise IgnoreRequest(f"URL {request.url} 被筛选出去。")
        elif '<span' in url:
            raise IgnoreRequest(f"URL {request.url} 被筛选出去。")
        elif '@' in url:
            raise IgnoreRequest(f"URL {request.url} 被筛选出去。")
        elif '.docx' in url:
            raise IgnoreRequest(f"URL {request.url} 被筛选出去。")
        elif '.doc' in url:
            raise IgnoreRequest(f"URL {request.url} 被筛选出去。")
        elif '.pdf' in url:
            raise IgnoreRequest(f"URL {request.url} 被筛选出去。")
        elif '.xlsx' in url:
            raise IgnoreRequest(f"URL {request.url} 被筛选出去。")
        elif '.xls' in url:
            raise IgnoreRequest(f"URL {request.url} 被筛选出去。")
        elif 'page.psp' in url:
            raise IgnoreRequest(f"URL {request.url} 被筛选出去。")
        elif url in filter_url:
            raise IgnoreRequest(f"URL {request.url} 被筛选出去。")
        elif netloc in forgot_netlocs:
            raise IgnoreRequest(f"URL {request.url} 被筛选出去。")

        if check_url_allowed(url):
            return None
        if 'mp.weixin.qq.com' in url:
            return None
        elif 'nankai.edu.cn' in url:
            return None
        elif 'iam.nankai.edu.cn' in url:
            raise IgnoreRequest(f"URL {request.url} 被筛选出去。")
        elif 'cyber-backend.nankai.edu.cn' in url:
            raise IgnoreRequest(f"URL {request.url} 被筛选出去。")
        elif 'cim-profile.nankai.edu.cn' in url:
            raise IgnoreRequest(f"URL {request.url} 被筛选出去。")
        else:
            spider.logger.info(f'待筛选URL：{url}')
            raise IgnoreRequest(f"URL {request.url} 被筛选出去。")

    def process_response(self, request, response, spider):
        """
        在响应返回之后，对响应内容进行处理（可选）
        """
        # 示例：过滤掉状态码为404的响应
        if response.status != 200:
            spider.logger.info(f"响应为 {response.status}，URL: {request.url}")
            raise IgnoreRequest(f"Response with status {response.status} is filtered out")
        return response
