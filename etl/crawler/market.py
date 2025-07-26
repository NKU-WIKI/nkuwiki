import hashlib
import hmac
import json
import random
import time
import urllib.parse
from typing import List, Dict, Any, Optional
import requests
import sys
import os
import pytz
from collections import Counter
from pathlib import Path
from datetime import datetime

# 添加项目路径
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from etl.crawler import crawler_logger, RAW_PATH, default_timezone
from etl.utils.file import clean_filename

config = {
    "market_token": "azl6TDJyZG1nWlcxbG9PYmxIbktmWnFsckxXV3pwZk9sMkp3a2NtZGY5T0V6YXFYeFgycnM4YXJmdHlGWXQ2dGpLTEsySmltaVphWG5YeVR1SW1MdDREYm5hK3pqYWVZdU5DbGxvV2dxNldJanNEUGdjMkYxNGhsaVpMR2lZdXdsS3F5ck1sK2dkUzlwNlhQaDNqT2pJNk1xNStEczFpV2VWZHFwUT09"
}


class Market:
    """校园市场爬虫类，具备下载保存功能"""
    
    def __init__(self, debug: bool = False, tag: str = "nku"):
        self.debug = debug
        self.platform = "market"
        self.content_type = "post"
        self.tag = tag
        self.base_url = "https://c.zanao.com"
        self.api_urls = {
            "list": "https://api.x.zanao.com/thread/v2/list",
            "comment": "https://c.zanao.com/sc-api/comment/post",
            "search": "https://c.zanao.com/thread/v2/search",
            "hot": "https://c.zanao.com/thread/hot"
        }
        self.university = "nankai"
        self.secret_key = "1b6d2514354bc407afdd935f45521a8c"
        self.headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Connection': 'keep-alive',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
            'sec-ch-ua': '"Chromium";v="116", "Not)A;Brand";v="24", "Google Chrome";v="116"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"'
        }
        
        # 初始化基类功能
        self.logger = crawler_logger.bind(platform=self.platform)
        self.counter = Counter()  # 初始化计数器
        self.tz = pytz.timezone(default_timezone)  # 设置时区
        
        # 设置基本目录（与基类保持一致）
        self.base_dir = RAW_PATH / Path(self.platform) 
        self.data_dir = self.base_dir / Path(self.tag)
        self.data_dir.mkdir(exist_ok=True, parents=True)  # 创建目录，如果目录不存在
        
        # 文件管理
        self.lock_file = 'lock.txt'
        self.counter_file = 'counter.txt'
        self.update_file = 'update.txt'
        self.scraped_original_urls_file = 'scraped_original_urls.json'
        
        # 打开更新文件
        try:
            self.update_f = open(self.base_dir / self.update_file, 'a+', encoding='utf-8')
        except Exception as e:
            self.logger.error(f"无法打开更新文件: {e}")
            self.update_f = None
        
        self.last_headers = None

    def _generate_m(self, length: int = 20) -> str:
        """生成指定长度的随机数字字符串"""
        return ''.join(str(random.randint(0, 9)) for _ in range(length))

    def _generate_td(self) -> int:
        """生成当前时间戳（秒）"""
        return int(time.time())

    def _hmac_md5(self, key: str, message: str) -> str:
        """HMAC-MD5哈希"""
        return hmac.new(key.encode(), message.encode(), hashlib.md5).hexdigest()

    def _generate_ah(self, m: str, td: int) -> str:
        """生成签名，对齐JavaScript中的签名生成逻辑"""
        raw_str = f"{self.university}_{m}_{td}_{self.secret_key}"
        return self._custom_md5(raw_str)

    def _custom_md5(self, input_str: str) -> str:
        """实现与JavaScript完全一致的MD5算法"""
        return hashlib.md5(input_str.encode('utf-8')).hexdigest()

    def _generate_headers(self, time_offset: int) -> Dict[str, str]:
        """生成请求头"""
        m = self._generate_m(20)
        td = self._generate_td() - time_offset * 60
        ah = self._generate_ah(m, td)

        headers = self.headers.copy()
        headers.update({
            "X-Sc-Nd": m,
            "X-Sc-Od": config["market_token"],
            "X-Sc-Ah": ah,
            "X-Sc-Td": str(td),
            "X-Sc-Alias": self.university,
        })
        return headers

    def get_scraped_original_urls(self) -> List[str]:
        """获取已抓取的原始URL列表（基类方法）"""
        urls_file = self.base_dir / self.scraped_original_urls_file
        
        if not urls_file.exists():
            return []
        try:
            with open(urls_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"读取已抓取URL列表出错: {e}")
            return []

    def update_scraped_articles(self, scraped_original_urls: List[str], articles: List[Dict[str, Any]]) -> None:
        """保存已抓取文章（基类方法）"""
        for article in articles:    
            if article['original_url'] not in scraped_original_urls:
                year_month = article.get('publish_time', datetime.now().strftime("%Y-%m-%d"))[0:7].replace('-', '')
                save_dir = self.data_dir / year_month
                save_dir.mkdir(exist_ok=True, parents=True)
                clean_title = clean_filename(article.get('title', ''))
                
                # 创建文章专属目录
                article_dir = save_dir / clean_title
                article_dir.mkdir(exist_ok=True, parents=True)
                
                # 在文章目录下保存JSON文件
                save_path = article_dir / clean_title
                
                meta = {
                    "id": self._custom_md5(article.get('original_url', '')),
                    "platform": self.platform,
                    "source": self.tag,
                    "original_url": article.get('original_url', ''),
                    "title": article.get('title', ''),
                    "author": article.get('author', ''),
                    "publish_time": article.get('publish_time', ''),
                    "scrape_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "content": article.get('content', ''),
                    "content_type": self.content_type
                }
                try:
                    with open(save_path.with_suffix('.json'), 'w', encoding='utf-8', errors='ignore') as f:
                        json.dump(meta, f, ensure_ascii=False, indent=2)
                    self.counter['download'] += 1
                    self.logger.info(f"保存文章: {clean_title}")
                except PermissionError:
                    self.logger.error(f"无法写入文件 {save_path}，权限被拒绝")
                    # 尝试使用临时文件名
                    temp_path = save_path.with_name(f"temp_{save_path.name}")
                    with open(temp_path.with_suffix('.json'), 'w', encoding='utf-8', errors='ignore') as f:
                        json.dump(meta, f, ensure_ascii=False, indent=2)
                    self.counter['download'] += 1
                except Exception as e:
                    self.logger.error(f"保存文章失败: {e}")
                    self.counter['error'] += 1
                scraped_original_urls.append(article['original_url'])
                self.counter['scrape'] += 1
            else:
                self.counter['noneed'] += 1
        
        # 更新已抓取URL列表
        total_f = self.base_dir / self.scraped_original_urls_file
        try:
            total_f.write_text(json.dumps(scraped_original_urls, ensure_ascii=False, indent=0))
        except Exception as e:
            self.logger.error(f"更新已抓取URL列表失败: {e}")

    def save_counter(self, start_time: float) -> None:
        """保存计数器（基类方法）"""
        path = self.base_dir / self.counter_file
        try:
            # 使用临时文件
            temp_path = path.with_name(f"temp_{path.name}")
            with temp_path.open('w', encoding='utf-8') as h:
                visit = self.counter.get('visit', 0)
                scrape = self.counter.get('scrape', 0)
                download = self.counter.get('download', 0)
                error = self.counter.get('error', 0)
                noneed = self.counter.get('noneed', 0)
                time_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                used_time = int(time.time() - start_time)
                self.logger.info(f'#summary# {used_time}s, visit: {visit}, scrape: {scrape}, download: {download}, error: {error}, noneed: {noneed}')
                h.write(f'{time_str},{used_time},{visit},{scrape},{download},{error},{noneed}\n')
            # 成功后重命名
            if temp_path.exists():
                temp_path.replace(path)
        except PermissionError:
            self.logger.error(f"无法访问文件 {path}，权限被拒绝")
        except Exception as e:
            self.logger.error(f"保存计数器失败: {str(e)}")

    def close(self) -> None:
        """关闭资源"""
        try:
            if hasattr(self, 'update_f') and self.update_f:
                self.update_f.close()
                self.update_f = None
            self.logger.info("资源已正确关闭")
        except Exception as e:
            self.logger.error(f"关闭资源时发生错误: {e}")

    async def get_latest_list(self, time_offset: int) -> List[Dict[str, Any]]:
        """获取最新帖子列表（为了与JS版本保持一致，保留async但实际使用同步请求）"""
        try:
            headers = self._generate_headers(time_offset)
            self.last_headers = headers
            
            self.logger.debug(f'正在请求API: {self.api_urls["list"]}')
            
            params = {
                "from_time": str(self._generate_td() - time_offset * 60),
                "hot": "1"
            }
            
            self.logger.debug(f'请求参数: {params}')
            self.logger.debug(f'关键请求头: X-Sc-Nd={headers.get("X-Sc-Nd")}, X-Sc-Ah={headers.get("X-Sc-Ah")}, X-Sc-Td={headers.get("X-Sc-Td")}')

            response = requests.post(
                self.api_urls["list"],
                headers=headers,
                params=params
            )

            self.counter['visit'] += 1
            self.logger.debug(f'收到响应: status={response.status_code}')
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    self.logger.debug(f'响应JSON结构: {data.keys() if isinstance(data, dict) else "非字典类型"}')
                    
                    if isinstance(data, dict):
                        # 处理errno/errmsg/data结构的响应
                        if 'errno' in data and data.get('errno') == 0:
                            # 成功响应，data字段包含实际数据
                            if 'data' in data and isinstance(data['data'], dict):
                                response_data = data['data']
                                
                                # 检查是否有list字段
                                if 'list' in response_data and isinstance(response_data['list'], list):
                                    post_list = response_data['list']
                                    self.logger.info(f'获取到 {len(post_list)} 个帖子')
                                    
                                    if len(post_list) > 0:
                                        return [self._parse_item(item) for item in post_list]
                                    else:
                                        return []
                                else:
                                    self.logger.warning(f'data字段缺少list: {list(response_data.keys()) if isinstance(response_data, dict) else "非字典类型"}')
                                    return []
                        else:
                            self.logger.error(f'API响应错误: errno={data.get("errno")}, errmsg={data.get("errmsg")}')
                            self.counter['error'] += 1
                            return []
                            
                    return []
                except json.JSONDecodeError as e:
                    self.logger.error(f'JSON解析失败: {e}')
                    self.logger.debug(f'响应文本前500字符: {response.text[:500]}')
                    self.counter['error'] += 1
                    return []
            else:
                self.logger.error(f'HTTP状态码错误: {response.status_code}')
                self.logger.debug(f'响应文本: {response.text[:500]}')
                self.counter['error'] += 1
                return []
                    
        except Exception as error:
            self.logger.error(f'API请求异常: {error}')
            self.counter["error"] += 1
            return []

    def _parse_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """解析单个帖子项"""
        parsed = {
            "title": item.get("title", ""),
            "content": item.get("content", ""),
            "author": item.get("nickname", ""),
            "publish_time": item.get("localtime", ""),
            "original_url": f'{self.base_url}/view/info/{item.get("thread_id")}?cid={self.university}',
            "content_type": self.content_type,
            "platform": self.platform
        }
        
        return parsed

    async def crawl_and_download(self, minutes: int = 60) -> Dict[str, Any]:
        """爬取并下载数据"""
        start_time = time.time()
        self.logger.info(f"开始爬取校园市场数据，时间范围: {minutes}分钟")
        
        try:
            # 获取已抓取的URL列表
            scraped_urls = self.get_scraped_original_urls()
            self.logger.info(f"已抓取URL数量: {len(scraped_urls)}")
            
            # 收集帖子
            all_posts = []
            for i in range(0, minutes + 1, 10):
                posts = await self.get_latest_list(i)
                all_posts.extend(posts)
                
                if not self.debug:
                    time.sleep(random.uniform(1, 3))  # 随机延迟
            
            # 去重
            unique_posts = []
            seen_urls = set()
            for post in all_posts:
                if post['original_url'] not in seen_urls:
                    unique_posts.append(post)
                    seen_urls.add(post['original_url'])
            
            self.logger.info(f"去重后帖子数量: {len(unique_posts)}")
            
            # 保存文章
            self.update_scraped_articles(scraped_urls, unique_posts)
            
            # 保存计数器
            self.save_counter(start_time)
            
            return {
                "success": True,
                "total_posts": len(unique_posts),
                "new_posts": self.counter.get('scrape', 0),
                "errors": self.counter.get('error', 0),
                "time_used": int(time.time() - start_time)
            }
            
        except Exception as e:
            self.logger.error(f"爬取过程异常: {e}")
            self.counter['error'] += 1
            self.save_counter(start_time)
            return {
                "success": False,
                "error": str(e),
                "time_used": int(time.time() - start_time)
            }
        finally:
            self.close()


# 保持原有的handler函数以兼容JS版本调用
async def handler(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """处理函数，与JavaScript版本保持一致"""
    try:
        market = Market()
        
        posts = []
        minutes = input_data.get("minutes", 60)
        
        for i in range(0, minutes + 1, 10):
            var_posts = await market.get_latest_list(i)
            posts.extend(var_posts)
        
        # 去重
        unique_posts = []
        seen_urls = set()
        for post in posts:
            if post['original_url'] not in seen_urls:
                unique_posts.append(post)
                seen_urls.add(post['original_url'])
        
        return {
            "posts": unique_posts,
            "unique_count": len(unique_posts),
            "total_count": len(posts)
        }
    except Exception as e:
        return {
            "error": str(e),
            "posts": []
        }


async def main():
    """主函数，演示下载功能"""
    print("开始测试market爬虫下载功能...")
    
    # 创建爬虫实例
    market = Market(debug=True)
    
    # 执行爬取和下载
    result = await market.crawl_and_download(minutes=60)
    
    print(f"爬取结果: {result}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
