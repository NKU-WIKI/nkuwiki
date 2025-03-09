"""
示例爬虫模块，展示如何实现一个通用爬虫
"""
from __init__ import *
from base_crawler import BaseCrawler

class ExampleCrawler(BaseCrawler):
    """示例爬虫类
    
    Attributes:
        target_sites: 配置名称，包含要爬取的网站列表
        debug: 调试模式开关
        headless: 是否使用无头浏览器模式
        use_proxy: 是否使用代理
    """
    
    def __init__(self, target_sites: str = "example_sites", tag: str = "example", debug: bool = False, headless: bool = False, use_proxy: bool = False) -> None:
        self.platform = "example"
        self.tag = tag
        self.content_type = "article"
        self.base_url = "https://example.com/"
        super().__init__(debug, headless, use_proxy)
        
        # 获取目标网站列表
        sites = os.environ.get(target_sites.upper(), "")
        if not sites:
            self.logger.error(f"Config etl.crawler.sites.{target_sites} is not set")
            raise ValueError(f"目标网站配置 {target_sites} 未设置")
        self.target_sites = sites.split(",")
        self.logger.info(f"开始爬取网站: {self.target_sites}")
        self.cookie_init_url = "https://example.com/"  # 初始化cookies的URL

    async def login_for_cookies(self) -> dict[str, str]:
        """获取网站cookies
        
        Returns:
            包含cookies的字典
            
        Raises:
            Exception: 获取cookies异常
        """
        try:
            await self.page.goto(self.base_url)
            await self.random_sleep()
            
            self.logger.info('获取cookies...')
            cookies = {cookie['name']: cookie['value'] for cookie in await self.context.cookies()}
            self.logger.success('成功获取cookies')
            return cookies
            
        except Exception as e:
            self.logger.error(f"获取cookies失败: {str(e)}")
            raise

    async def scrape_content_from_sites(self, scraped_urls: set, max_item_num: int, 
                                total_max_item_num: int) -> list[dict]:
        """从多个网站抓取内容
        
        Args:
            scraped_urls: 已经抓取过的URL集合
            max_item_num: 每个网站最大抓取数量
            total_max_item_num: 总共最大抓取数量
            
        Returns:
            包含抓取内容的列表
        """
        total_items = []
        total_count = 0
        
        for site in self.target_sites:
            if total_count >= total_max_item_num:
                break
                
            self.logger.info(f"开始抓取网站: {site}")
            try:
                # 模拟访问网站
                await self.page.goto(f"{self.base_url}{site}")
                await self.random_sleep()
                
                # 模拟获取内容列表
                items = []
                for i in range(min(max_item_num, total_max_item_num - total_count)):
                    item = {
                        "title": f"{site} 内容 {i+1}",
                        "url": f"{self.base_url}{site}/item/{i+1}",
                        "original_url": f"{self.base_url}{site}/item/{i+1}",
                        "author": site,
                        "publish_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "platform": self.platform
                    }
                    
                    if item["original_url"] not in scraped_urls:
                        items.append(item)
                        self.logger.info(f"抓取到新内容: {item['title']}")
                    else:
                        self.logger.debug(f"跳过已抓取内容: {item['original_url']}")
                
                total_items.extend(items)
                total_count += len(items)
                
            except Exception as e:
                self.logger.error(f"抓取网站 {site} 失败: {str(e)}")
                
        self.logger.info(f'共抓取 {len(total_items)} 个内容，来自 {self.target_sites}')
        return total_items

    async def scrape(self, max_item_num: int = 5, total_max_item_num: int = 20) -> None:
        """抓取网站内容
        
        Args:
            max_item_num: 每个网站最大抓取数量
            total_max_item_num: 总共最大抓取数量
        """
        try:
            # 获取已经抓取的链接
            scraped_urls = self.get_scraped_original_urls()
            
            # 检查cookies是否存在，不存在则获取
            cookie_ts, cookies = self.read_cookies(timeout=24*3600)  
            if cookies is None:
                cookies = await self.login_for_cookies()  
                self.save_cookies(cookies)  
            else:
                await self.init_cookies(cookies, go_base_url=True)
                
            start_time = time.time()
            
            if not self.debug:
                lock_path = self.base_dir / self.lock_file
                lock_path.write_text(str(int(start_time)))  # 写入锁文件
                
                scraped_urls = self.get_scraped_original_urls()
                items = await self.scrape_content_from_sites(scraped_urls, max_item_num, total_max_item_num)
                self.update_scraped_articles([item['original_url'] for item in items], items)
                
                lock_path.unlink()  # 删除锁文件
            else:
                items = await self.scrape_content_from_sites(scraped_urls, max_item_num, total_max_item_num)
                self.update_scraped_articles([item['original_url'] for item in items], items)
            
            self.save_counter(start_time)
            self.update_f.close()
            
        except Exception as e:
            self.logger.error(f"抓取出错: {e}")

    async def download_item(self, item: dict) -> None:
        """下载单个内容
        
        Args:
            item: 内容信息字典（需包含original_url）
        """
        try:
            self.counter['total'] = self.counter.get('total', 0) + 1
            title = item['title']
            
            self.logger.info(f"开始下载内容: {title}")
            
            # 模拟访问内容页面
            await self.page.goto(item['original_url'])
            await self.random_sleep()
            
            # 模拟提取内容
            content = f"# {title}\n\n这是{title}的内容\n\n发布时间: {item['publish_time']}"
            
            # 保存内容
            save_path = self.save_article(item, content)
            
            self.logger.success(f"成功下载内容: {title}, 保存路径: {save_path}")
            self.counter['success'] = self.counter.get('success', 0) + 1
            
        except Exception as e:
            self.counter['error'] = self.counter.get('error', 0) + 1
            self.logger.exception(f'下载内容失败: {e}, URL: {item["original_url"]}')

    async def download(self):
        """下载所有已抓取但未下载的内容"""
        data_dir = Path(self.base_dir)
        start_time = time.time()

        for json_path in data_dir.glob('**/*.json'):
            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    item_data = json.load(f)

                if not isinstance(item_data, dict):
                    continue

                # 检查是否有HTML文件需要删除
                html_files = list(json_path.parent.glob('*.html'))
                if html_files:
                    for html_file in html_files:
                        html_file.unlink()
                        self.logger.debug(f"删除HTML文件: {html_file}")
                
                # 检查是否缺少MD文件或内容为空
                md_files = list(json_path.parent.glob('*.md'))
                content = item_data.get('content', '')
                
                if not md_files or not content:
                    await self.download_item(item_data)
                    self.counter['processed'] = self.counter.get('processed', 0) + 1
                    if self.counter['processed'] % 10 == 0:
                        self.logger.info(f"已处理 {self.counter['processed']} 个内容")
                    await self.random_sleep()
                    
            except Exception as e:
                self.counter['error'] = self.counter.get('error', 0) + 1
                
        self.save_counter(start_time)
        self.logger.info(f"下载完成，共处理 {self.counter.get('processed', 0)} 个内容, " +
                         f"错误 {self.counter.get('error', 0)} 个")


if __name__ == "__main__":
    import asyncio

    async def main():
        """异步主函数"""
        # 爬取模式 - 使用debug=False进行生产环境爬取
        crawler = ExampleCrawler(debug=True)
        await crawler.scrape(max_item_num=3, total_max_item_num=10)
        
        # 下载模式 - 下载已爬取但未保存内容的文章
        # crawler = ExampleCrawler(debug=True)
        # await crawler.download()

    # 运行主函数
    asyncio.run(main()) 