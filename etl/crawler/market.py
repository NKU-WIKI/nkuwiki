import os
import re
import time
import random
import hashlib
import hmac
import asyncio
from datetime import datetime
from pathlib import Path
from etl.crawler import crawler_logger, MARKET_TOKEN
from etl.crawler.base_crawler import BaseCrawler


class Market(BaseCrawler):
    """Zanao集市数据爬虫"""
    
    def __init__(self, tag: str = "nku", debug=False, headless=False):
        self.platform = "market"
        self.tag = tag
        self.content_type = "post"
        self.base_url = "https://c.zanao.com"
        self.logger = crawler_logger
        super().__init__(debug, headless)

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
        """生成当前时间戳"""
        return int(time.time())

    def _hmac_md5(self, key, message):
        """HMAC-MD5加密"""
        return hashlib.md5(message.encode()).hexdigest()

    def _generate_ah(self, m, td):
        """生成签名"""
        raw_str = f"{self.university}_{m}_{td}_{self.secret_key}"
        return self._hmac_md5(self.secret_key, raw_str)

    def _generate_headers(self, timestamp):
        """生成请求头"""
        try:
            m = self._generate_m(20)
            if not m.isdigit() or len(m) != 20:
                raise ValueError(f"Invalid m generated: {m}")
        except Exception as e:
            self.logger.error(f"生成请求头时发生错误: {str(e)}")
            m = '0' * 20

        self.headers.update({
            "X-Sc-Nd": m,
            "X-Sc-Od": MARKET_TOKEN,
            "X-Sc-Ah": self._generate_ah(m, timestamp),
            "X-Sc-Td": str(timestamp),
            'X-Sc-Alias': self.university,
        })
        # print(self.headers)
        return self.headers

    async def _get_latest_list_async(self, timestamp):
        """异步获取最新列表"""
        try:
            response = await self.page.request.post(
                self.api_urls["list"],
                headers=self._generate_headers(timestamp),
                params={"from_time": str(timestamp), "hot": "1"}
            )
            
            if response.status == 200:
                data = await response.json()
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
            # 修复异常处理中response可能未定义的问题
            response_text = "无响应"
            if 'response' in locals() and response:
                try:
                    response_text = await response.text()
                except:
                    response_text = "无法获取响应内容"
            self.logger.error(f"获取最新列表失败: {str(e)}，响应数据: {response_text}")
            self.counter['error'] += 1
            return []
            
    async def _get_hot_list_async(self, headers):
        """异步获取热门列表"""
        try:
            response = await self.page.request.post(
                self.api_urls["hot"],
                headers=headers,
                params={"from_time": str(int(time.time())), "hot": "2"}
            )
            
            if response.status == 200:
                data = await response.json()
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
            # 修复异常处理中response可能未定义的问题
            response_text = "无响应"
            if 'response' in locals() and response:
                try:
                    response_text = await response.text()
                except:
                    response_text = "无法获取响应内容"
            self.logger.error(f"获取热门列表失败: {str(e)}，响应数据: {response_text}")
            self.counter['error'] += 1
            return []

    def _parse_item(self, item):
        """解析数据项"""
        return {
            "title": item.get("title"),
            "content": item.get("content"),
            "author": item.get("nickname"),
            "publish_time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
            "original_url": f"{self.base_url}/view/info/{item.get('thread_id')}?cid={self.university}",
            "scrape_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "content_type": self.content_type,
            "platform": self.platform
        }
            
    async def _post_comment_async(self, headers, thread_id, content):
        """异步发表评论"""
        try:
            # 在异步方法中调用异步random_sleep
            await self.random_sleep()
            
            response = await self.page.request.post(
                self.api_urls["comment"],
                headers=headers,
                data={
                    "id": str(thread_id),
                    "content": content,
                    "reply_comment_id": "0",
                    "root_comment_id": "0",
                    "cert_show": "0",
                    "isIOS": "false"
                }
            )
            return response.status == 200
        except Exception as e:
            # 修复异常处理中response可能未定义的问题
            response_text = "无响应"
            if 'response' in locals() and response:
                try:
                    response_text = await response.text()
                except:
                    response_text = "无法获取响应内容"
            self.logger.error(f"评论失败: {str(e)}，响应数据: {response_text}")
            self.counter['error'] += 1
            return False
            
    async def _search_posts_async(self, headers, keyword):
        """异步搜索帖子"""
        try:
            response = await self.page.request.post(
                self.api_urls["search"],
                headers=headers,
                data={
                    "keyword": keyword,
                    "page": 1,
                    "page_size": 10
                }
            )
            
            if response.status == 200:
                data = await response.json()
                return [self._parse_item(item) for item in data.get("data", {}).get("list", [])]
            return []
        except Exception as e:
            # 修复异常处理中response可能未定义的问题
            response_text = "无响应"
            if 'response' in locals() and response:
                try:
                    response_text = await response.text()
                except:
                    response_text = "无法获取响应内容"
            self.logger.error(f"搜索失败: {str(e)}，响应数据: {response_text}")
            self.counter['error'] += 1
            return []

    async def _run_async_impl(self, keywords=[]):
        """异步执行完整爬取流程"""
        start_time = time.time()
        try:
            # 检查登录状态
            if not self._load_cookies():
                raise Exception("需要先执行登录操作")
            
            # 获取并保存热门列表
            headers = self._generate_headers()
            hot_list = await self._get_hot_list_async(headers)
            self.update_scraped_articles(self.get_scraped_original_urls(), hot_list)
            
            # 执行关键词搜索
            search_results = []
            for kw in keywords:
                await self.random_sleep()
                
                # 直接使用异步搜索方法
                search_headers = self._generate_headers()
                search_headers.update({
                    "Referer": "https://servicewechat.com/wx3921ddb0258ff14f/57/page-frame.html"    
                })
                results = await self._search_posts_async(search_headers, kw)
                search_results.extend(results)
                
            # 合并结果并去重
            all_results = list(hot_list)
            all_results.extend(search_results)
            
            # 返回结果
            self.logger.info(f"本次爬取共{len(all_results)}条内容，耗时{time.time()-start_time:.2f}秒")
            return all_results
        except Exception as e:
            self.logger.error(f"爬取失败: {str(e)}")
            self.counter['error'] += 1
            return []

    async def _start_periodic_crawl_async(self, interval=60 * 15, max_runs=None):
        """异步执行定时爬取任务"""
        run_count = 0
        
        # 创建锁文件
        lock_file = self.base_dir / self.lock_file
        if lock_file.exists():
            self.logger.warning(f"检测到锁文件{lock_file}，可能已有爬虫在运行")
            return
            
        with open(lock_file, 'w') as f:
            f.write(str(os.getpid()))
            
        try:
            while max_runs is None or run_count < max_runs:
                start_time = time.time()
                try:
                    self.logger.info(f"开始第{run_count+1}次定时爬取")
                    await self._run_async_impl()
                    
                    # 保存爬取统计
                    self.save_counter(start_time)
                except Exception as e:
                    self.logger.error(f"定时任务执行失败: {str(e)}")
                    self.counter['error'] += 1
                
                # 更新计数器并等待
                run_count += 1
                
                # 如果还需要继续运行，则等待
                if max_runs is None or run_count < max_runs:
                    await asyncio.sleep(interval)
        finally:
            # 删除锁文件
            if lock_file.exists():
                lock_file.unlink()

    def _run_async(self, coroutine):
        """运行异步任务的同步包装器
        
        注意：此方法只能在非异步环境中调用，不能在已有事件循环的环境中调用
        """
        # 检查是否已经存在事件循环
        try:
            asyncio.get_running_loop()
            # 如果没有抛出异常，表示已经存在一个事件循环
            self.logger.error("检测到已有事件循环运行，不能创建嵌套事件循环")
            raise RuntimeError("Cannot run the event loop while another loop is running")
        except RuntimeError:
            # 正常情况下应该抛出异常，表示当前没有事件循环
            pass
            
        # 创建新的事件循环
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(coroutine)
        finally:
            loop.close()

if __name__ == "__main__":
    # 使用异步主函数
    async def main():
        market = None
        try:
            market = Market(debug=True, headless=True)
            
            # 初始化
            await market.async_init()
            
            # 获取30分钟前的帖子 - 注意:在异步环境中直接使用异步方法
            latest_list = await market._get_latest_list_async(market._generate_td()-60*0)
            
            for item in latest_list:
                print(item['original_url'])
                
            # 可以取消注释以测试其他功能
            # headers = market._generate_headers()
            # hot_list = await market._get_hot_list_async(headers)
            # for item in hot_list:
            #     print(item['title'])
            
            # headers = market._generate_headers()
            # headers.update({"Referer": "https://servicewechat.com/wx3921ddb0258ff14f/57/page-frame.html"})
            # search_results = await market._search_posts_async(headers, "考研")
            # for item in search_results:
            #     print(item['title'])
                
        except Exception as e:
            import traceback
            print(f"错误: {str(e)}")
            traceback.print_exc()
        finally:
            # 确保关闭browser和playwright
            if market and market.page:
                await market.close()
    
    # 运行异步主函数
    asyncio.run(main())
     
