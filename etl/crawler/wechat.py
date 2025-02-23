from __init__ import *
from base_crawler import BaseCrawler

Config().load_config()

class Wechat(BaseCrawler):
    """微信公众号文章爬虫
    
    Attributes:
        authors: 配置名称，包含要爬取的公众号昵称列表
        debug: 调试模式开关
        headless: 是否使用无头浏览器模式
    """
    def __init__(self, authors: str = "university_official_account", debug: bool = False, headless: bool = False) -> None:
        # 确保在初始化时重新读取环境变量
        self.platform = "wechat"
        self.content_type = "article"
        self.base_url = "https://mp.weixin.qq.com/"  # 基础URL
        super().__init__(platform=self.platform, debug=debug, headless=headless)
        self.page = self.context.new_page()
        self.cookie_init_url = "https://mp.weixin.qq.com/"  # 初始化cookies的URL
        # 从配置中获取昵称并过滤空值
        self.authors = [
            name.strip() 
            for name in Config().get(authors, '').split(',') 
            if name.strip()
        ]
        if not self.authors:
            self.logger.error(f"Config {authors} is not set or is empty")
        
        self.logger.info(f"authors: {self.authors}")

    def login_for_cookies(self) -> dict[str, str]:
        """登录微信公众号平台获取cookies
        
        Returns:
            包含登录cookies的字典
            
        Raises:
            TimeoutError: 登录超时（5分钟未扫码）
            Exception: 其他登录异常
        """
        try:
            # 注入脚本
            self.inject_anti_detection_script()
            self.page.goto(self.base_url)
            self.random_sleep()
            max_wait = 300  # 最大等待5分钟
            
            # 立即检查是否已登录（二维码元素不存在）
            if not self.page.query_selector('img[class="login__type__container__scan__qrcode"]'):
                self.logger.info('检测到已登录状态')
                self.random_sleep()
                return {cookie['name']: cookie['value'] for cookie in self.context.cookies()}

            while max_wait > 0:
                self.logger.info('请扫描二维码登录...')
                # 持续监测二维码元素是否存在
                if not self.page.query_selector('img[class="login__type__container__scan__qrcode"]'):
                    time.sleep(5)  # 给登录后页面加载留出时间
                    self.logger.info('登录成功')
                    return {cookie['name']: cookie['value'] for cookie in self.context.cookies()}
                time.sleep(5)
                max_wait -= 5
                
            if max_wait <= 0:
                raise TimeoutError("登录超时")
        except Exception as e:
            # 增加失败后清理
            self.context.clear_cookies()
            self.context.clear_cache()
            raise e

    def scrape_articles_from_authors(self, scraped_original_urls: set, max_article_num: int, 
                                     total_max_article_num: int) -> list[dict]:
        """从指定公众号列表抓取文章元数据
        
        Args:
            scraped_original_urls: 已抓取链接集合（用于去重）
            max_article_num: 单个公众号最大抓取数量
            total_max_article_num: 总最大抓取数量
            
        Returns:
            包含文章信息的字典列表，格式:
            [{
                'author': 公众号名称,
                'publish_time': 发布时间,
                'title': 文章标题,
                'original_url': 文章链接
            }]
        """
        total_articles = []
        
        # 设置较短的默认超时时间
        self.page.set_default_timeout(6000)  # 设置为6秒
        
        try:
            self.random_sleep()
            new_content_button = self.page.wait_for_selector('div[class="new-creation__menu-item"]', 
                state='attached', 
                timeout=3000
            )
        except Exception as e:
            self.page.screenshot(path='viewport.png', full_page=True)
            self.counter['error'] += 1
            self.logger.error(f'get articles from {self.authors} error, {type(e)}: {e}')
            return total_articles

        # 增加操作重试机制
        max_retries = 3
        for attempt in range(max_retries):
            try:
                new_content_button.click()
                break
            except Exception as e:
                if attempt == max_retries - 1:
                    self.logger.error(f"点击失败，已重试 {max_retries} 次，跳过")
                    return total_articles
                self.logger.warning(f"点击失败，重试 {attempt+1}/{max_retries}")
                self.page.reload()
        try:
            self.context.wait_for_event('page')
            new_page = self.context.pages[-1]
            self.page = new_page
            self.logger.info('go to new content page')
            self.random_sleep()
            self.page.wait_for_selector('li[id="js_editor_insertlink"] > span').click()
        except Exception as e:
            self.page.screenshot(path='viewport.png', full_page=True)
            self.counter['error'] += 1
            self.logger.error(f'get articles error, {type(e)}: {e}')
            return total_articles
        for author in self.authors:
            self.random_sleep()
            try:
                self.page.wait_for_selector('p[class="inner_link_account_msg"] > div > button', 
                    timeout=3000,
                    state='visible'
                ).click()
            except Exception as e:
                self.logger.error(f'Failed to find account button: {e}')
            self.random_sleep()
            try:
                search_account_field = self.page.wait_for_selector(
                    'input[placeholder="输入文章来源的账号名称或微信号，回车进行搜索"]',
                    timeout=3000
                )
                search_account_field.fill(author)
            except Exception as e:
                self.logger.error(f'Failed to find search field,{str(e)}')
                break
            self.random_sleep()
            try:
                self.page.wait_for_selector(
                    'button[class="weui-desktop-icon-btn weui-desktop-search__btn"]',
                    timeout=3000
                ).click()
            except Exception as e:
                self.logger.error(f'Failed to find search button: {e}')
                break
            self.random_sleep()
            # 等待账号选择器出现
            try:
                account_selector = self.page.wait_for_selector(
                    '//li[@class="inner_link_account_item"]/div[1]',
                    timeout=3000
                )
                account_selector.click()

            except Exception as e:
                self.logger.error(f'failed to click account, {author} seems does not exist')
                continue
            self.random_sleep()
            # 获取页码信息
            try:
                max_page_label = self.page.wait_for_selector(
                    'span[class="weui-desktop-pagination__num__wrp"] > label:nth-of-type(2)',
                    timeout=3000
                )
                max_page_num = int(max_page_label.inner_text())
            except Exception as e:
                self.logger.warning(f'Failed to get max page number: {e}, set default max page number to 1')
                max_page_num = 1
            page = 1
            articles = []
            while len(articles) < max_article_num and page <= max_page_num:
                try:
                    self.random_sleep()
                    article_titles_elements = self.page.query_selector_all('div[class="inner_link_article_title"] > span:nth-of-type(2)')
                    article_publish_times_elements = self.page.query_selector_all('div[class="inner_link_article_date"] > span:nth-of-type(1)')
                    article_original_urls_elements = self.page.query_selector_all('div[class="inner_link_article_date"] > span:nth-of-type(2) > a[href]')
                    cnt = 0
                    for i in range(len(article_titles_elements)):
                        article_title = str(article_titles_elements[i].inner_text())
                        article_publish_time = str(article_publish_times_elements[i].inner_text())
                        article_original_url = str(article_original_urls_elements[i].get_attribute('href'))
                        if(article_original_url not in scraped_original_urls):
                            articles.append({
                                'author': author,
                                'publish_time': article_publish_time,
                                'title': article_title,
                                'original_url': article_original_url
                            })
                            cnt += 1
                    page += 1
                    self.logger.debug(f'scraped {cnt} articles from {author}')
                    try: 
                        # 通过文本内容定位"下一页"按钮
                        next_page_button = self.page.get_by_text("下一页")
                        next_page_button.click()
                    except Exception as e:
                        self.counter['error'] += 1
                        self.logger.warning(f'Page: {page}, Next Button error, {type(e)}: {e}, author: {author}')
                        break
                except Exception as e:
                    self.counter['error'] += 1
                    self.logger.error(f'Page: {page}, Get article links error, {type(e)}: {e}, author: {author}')
                    break  # 如果处理页面出错，跳出当前账号的处理

            self.update_scraped_articles(scraped_original_urls, articles)
            self.logger.info(f'save {len(articles)} articles from {author}')
            total_articles.extend(articles)
            if len(total_articles) >= total_max_article_num:
                break

        self.logger.info(f'save total {len(total_articles)} articles from {self.authors}')
        return total_articles

    def download_article(self, article: dict, add_scraped_records: list) -> None:
        """下载单篇文章内容并保存元数据
        
        Args:
            article: 文章信息字典（需包含link/title/date等字段）
            add_scraped_records: 用于记录已成功下载的链接列表
        """
        # 下载文章
        file_url = ''
        try:
            # 创建新页面下载文章
            article_page = self.context.new_page()
            article_page.goto(article['original_url'])
            self.counter['visit'] += 1
            self.random_sleep()
            
            try:
                # 下载文章内容
                file_name = article['title']
                metadata = {}  # 初始化元数据
                metadata['run_time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # 记录运行时间
                metadata['publish_time'] = article['date']  # 记录发布时间
                metadata['title'] = article['title']  # 记录标题
                metadata['author'] = article['author']  # 记录作者
                metadata['original_url'] = article['original_url']  # 记录原始链接
                metadata['content_type'] = self.content_type  # 记录内容类型
                year_month = article['date'][0:7].replace('-', '')  # 获取年月
                # metadata['file_path'] = f'{year_month}/{file_name}.html'  # 记录文件路径
                dir_path = self.base_dir / year_month  # 获取目录路径
                self.headers['Referer'] = article['original_url']  # 设置Referer头  
                resp = requests.get(article['original_url'], headers=self.headers, cookies=None)  # 发送HTTP请求下载文件
                file_len = len(resp.content)  # 获取文件长度
                dir_path.mkdir(parents=True, exist_ok=True)  # 创建目录
                data_path = dir_path / f'{file_name}.html'  # 获取文件路径
                meta_path = dir_path / f'{file_name}.json'  # 获取元数据文件路径
                self.counter['scrape'] += 1  # 抓取计数器加1
                if resp.status_code == 200 and file_len > 1000:  # 如果请求成功且文件长度大于1000字节
                    current_time_ms = int(time.time() * 1000)  # 获取当前时间戳
                    self.update_f.write(f"{metadata['file_path']}\t{current_time_ms}\n")  # 写入更新文件
                    self.logger.info(f"Success download: {metadata['file_path']}, article_original_url: {article['original_url']}, file_url: {file_url}")  # 记录日志
                    add_scraped_records.append(article['original_url'])  # 添加到已抓取链接列表
                    self.counter['download'] += 1  # 下载计数器加1
                    metadata['download_status'] = 'success'
                else:
                    self.counter['error'] += 1  # 错误计数器加1
                    self.logger.error(f'request html error, code: {resp.status_code}, len: {file_len}, url: {file_url}')  # 记录错误日志
                    metadata['download_status'] = 'failed'
                meta_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2))  # 写入元数据
                data_path.write_bytes(resp.content)  # 写入文件内容
            finally:
                # 确保关闭页面
                article_page.close()
        except Exception as e:
            self.counter['error'] += 1
            self.logger.error(f'get article_original_url error, {type(e)}: {e}, url: {article["original_url"]}')

    def scrape(self, max_article_num: int = 5, total_max_article_num: int = 20) -> None:
        """执行完整爬取流程
        
        Args:
            max_article_num: 单个公众号最大抓取数量（默认5）
            total_max_article_num: 总最大抓取数量（默认20）
            
        Note:
            生产环境需设置debug=False避免反爬检测
        """
        cookie_ts, cookies = self.read_cookies(timeout=2.5*24*3600)  # 读取cookies
        if cookies is None:
            cookies = self.login_for_cookies()  # 登录并获取cookies 
            self.save_cookies(cookies)  # 保存cookies
        else:
            self.init_cookies(cookies, go_base_url=True)  # 初始化cookies
        start_time = time.time()
        if self.debug == False:
            lock_path = self.base_dir / self.lock_file
            # if lock_path.exists():
            #     last_run_ts = lock_path.read_text()
            #     self.logger.error(f'last run not end, last_run_ts: {last_run_ts}')  # 记录错误日志
            #     return
            lock_path.write_text(str(int(start_time)))  # 写入锁文件
            scraped_original_urls = self.get_scraped_original_urls()  # 获取已抓取链接
            self.scrape_articles_from_authors(scraped_original_urls, max_article_num, total_max_article_num)  
            lock_path.unlink()  # 删除锁文件
        else:
            scraped_original_urls = self.get_scraped_original_urls()  # 获取已抓取链接
            self.scrape_articles_from_authors(scraped_original_urls, max_article_num, total_max_article_num)  
    
        self.save_counter(start_time)  
        self.update_f.close()  
            
    def download(self):
        # TODO: 添加下载实现
        pass

# 生产环境下设置debug=False！！！一定不要设置为True，debug模式没有反爬机制，很容易被封号！！！ max_article_num = 你想抓取的数量
# 调试可以设置debug=True，max_article_num <= 5
# 抓取公众号文章元信息需要cookies（高危操作），下载文章内容不需要cookies，两者分开处理
if __name__ == "__main__":
    wechat = Wechat(authors = "club_official_account", debug=False, headless=False)  # 初始化
    wechat.scrape(max_article_num=5, total_max_article_num=1e10)   # max_article_num最大抓取数量