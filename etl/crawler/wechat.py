from __init__ import *
from base_crawler import BaseCrawler

# 微信公众号
class Wechat(BaseCrawler):
    def __init__(self):
        self.name = "wechat"
        self.base_url = "https://mp.weixin.qq.com/"  # 基础URL
        self.cookie_init_url = "https://mp.weixin.qq.com/"  # 初始化cookies的URL
        # self.username = os.getenv("WECHAT_USERNAME")  # 从环境变量读取
        # self.password = os.getenv("WECHAT_PASSWORD")  # 从环境变量读取
        self.nicknames = [
           '我们在听'
        ]
        super().__init__(self.name, debug=False, headless=True)
    def login_for_cookies(self):
        """
        登录并获取cookies
        """
        try:
            self.page.goto(self.login_url)  # 打开登录页面
            self.counter['visit'] += 1  # 访问计数器加1
            self.random_sleep()  # 随机休眠
            time.sleep(15) # 微信限制，只能人工扫码登陆
            return {cookie['name']: cookie['value'] for cookie in self.context.cookies()}  # 返回cookies
        except Exception as e:
            self.counter['error'] += 1  # 错误计数器加1
            if(self.debug):
                self.page.screenshot(path='./login.png')  # 调试模式下截图
            self.logger.error(f'get cookies error, {type(e)}: {e}, url: {self.login_url}')  # 记录错误日志
  
    def get_articles_from_nickname(self, scraped_records, nickname, max_article_num):
        """
        从公众号名称获取文章链接
        """
        articles = []
        self.page.goto(self.base_url)
        try:
            new_content_button = self.page.wait_for_selector('div[class="new-creation__menu-item"]')
        except Exception as e:
            self.page.screenshot(path='viewport.png', full_page=True)
            self.counter['error'] += 1  # 错误计数器加1
            self.logger.error(f'get articles from nickname error, {type(e)}: {e}, nickname: {nickname}')  # 记录错误日志
        new_content_button.click()

        self.context.wait_for_event('page')  # 等待新页面事件
        new_page = self.context.pages[-1]  # 获取最新打开的页面
        self.page = new_page  # 切换到新页面

        self.random_sleep()  # 随机休眠（debug模式无效）
        try:
            self.page.wait_for_selector('li[id="js_editor_insertlink"] > span').click()
        except Exception as e:
            self.page.screenshot(path='viewport.png', full_page=True)
            self.counter['error'] += 1  # 错误计数器加1
            self.logger.error(f'get articles from nickname error, {type(e)}: {e}, nickname: {nickname}')  # 记录错误日志
        self.random_sleep()  # 随机休眠（debug模式无效）
        self.page.wait_for_selector('p[class="inner_link_account_msg"] > div > button').click()
        self.random_sleep()  # 随机休眠（debug模式无效）
        search_account_field = self.page.wait_for_selector('input[placeholder="输入文章来源的账号名称或微信号，回车进行搜索"]')
        search_account_field.fill(nickname)
        self.page.wait_for_selector('button[class="weui-desktop-icon-btn weui-desktop-search__btn"]').click()
        self.random_sleep()  # 随机休眠（debug模式无效）
        self.page.wait_for_selector('//li[@class="inner_link_account_item"]/div[1]').click()
        self.random_sleep()  # 随机休眠（debug模式无效）
        max_page_num = int(self.page.wait_for_selector('span[class="weui-desktop-pagination__num__wrp"] > label:nth-of-type(2)').inner_text())
        page = 1
        while len(articles) < max_article_num and page <= max_page_num:
            try:
                self.random_sleep()  # 随机休眠（debug模式无效）
                article_titles_elements = self.page.query_selector_all('div[class="inner_link_article_title"] > span:nth-of-type(2)')
                article_dates_elements = self.page.query_selector_all('div[class="inner_link_article_date"] > span:nth-of-type(1)')
                article_links_elements = self.page.query_selector_all('div[class="inner_link_article_date"] > span:nth-of-type(2) > a[href]')
                for i in range(len(article_titles_elements)):
                    article_title = str(article_titles_elements[i].inner_text())
                    article_date = str(article_dates_elements[i].inner_text())
                    article_link = str(article_links_elements[i].get_attribute('href'))
                    self.random_sleep()  # 随机休眠（debug模式无效）
                    if(article_link not in scraped_records):
                        articles.append({
                            'nickname': nickname,
                            'date': article_date,
                            'title': article_title,
                            'link': article_link
                        })
                page += 1
                try: 
                    next_page_button = self.page.wait_for_selector('span[class="weui-desktop-pagination__nav"] > a[href]')
                    next_page_button.click()
                except Exception as e:
                    self.counter['error'] += 1  # 错误计数器加1
                    self.logger.error(f'Page: {page}, Next Button error, {type(e)}: {e}, nickname: {nickname}')  # 记录错误日志
                    break                                           
            except Exception as e:
                self.counter['error'] += 1  # 错误计数器加1
                self.logger.error(f'Page: {page}, Get article links error, {type(e)}: {e}, nickname: {nickname}')  # 记录错误日志
                break
        return articles

    def get_articles(self, scraped_records, max_article_num):
        # 获取所有文章链接
        articles = []
        for nickname in self.nicknames:
            articles.extend(self.get_articles_from_nickname(scraped_records, nickname, max_article_num))  # 获取每个公众号的文章
        # articles = list({article['link']: article for article in articles}.values())  # 去重
        self.logger.info(f'Get Total {len(articles)} articles')  # 记录日志
        return articles

    def scrape_article(self, article, add_scraped_records, cookies):
        # 抓取文章
        file_url = ''
        try:
            self.page.goto(article['link'])  # 打开文章链接
            self.counter['visit'] += 1  # 访问计数器加1
            self.random_sleep()  # 随机休眠
        except Exception as e:
            self.counter['error'] += 1  # 错误计数器加1
            self.logger.error(f'get article_link error, {type(e)}: {e}, url: {article["link"]}')  # 记录错误日志
        try:
            file_name = article['title'] # 获取文件名
            metadata = {}  # 初始化元数据
            metadata['run_time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # 记录运行时间
            metadata['publish_time'] = article['date']  # 记录发布时间
            metadata['title'] = article['title']  # 记录标题
            metadata['nickname'] = article['nickname']  # 记录作者
            metadata['original_url'] = article['link']  # 记录原始链接
            metadata['content_type'] = self.content_type  # 记录内容类型
            year_month = article['date'][0:7].replace('-', '')  # 获取年月
            metadata['file_path'] = f'{year_month}/{file_name}.html'  # 记录文件路径
            dir_path = self.base_dir / year_month  # 获取目录路径
            self.headers['Referer'] = article['link']  # 设置Referer头  
            resp = requests.get(article['link'], headers=self.headers, cookies=None)  # 发送HTTP请求下载文件
            file_len = len(resp.content)  # 获取文件长度
            dir_path.mkdir(parents=True, exist_ok=True)  # 创建目录
            data_path = dir_path / f'{file_name}.html'  # 获取文件路径
            meta_path = dir_path / f'{file_name}.json'  # 获取元数据文件路径
            self.counter['scrape'] += 1  # 抓取计数器加1
            if resp.status_code == 200 and file_len > 1000:  # 如果请求成功且文件长度大于1000字节
                current_time_ms = int(time.time() * 1000)  # 获取当前时间戳
                self.update_f.write(f"{metadata['file_path']}\t{current_time_ms}\n")  # 写入更新文件
                self.logger.info(f"Success download: {metadata['file_path']}, article_link: {article['link']}, file_url: {file_url}")  # 记录日志
                add_scraped_records.append(article['link'])  # 添加到已抓取链接列表
                self.counter['download'] += 1  # 下载计数器加1
                metadata['download_status'] = 'success'
            else:
                self.counter['error'] += 1  # 错误计数器加1
                self.logger.error(f'request html error, code: {resp.status_code}, len: {file_len}, url: {file_url}')  # 记录错误日志
                metadata['download_status'] = 'failed'
            meta_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2))  # 写入元数据
            data_path.write_bytes(resp.content)  # 写入文件内容

        except Exception as e:
            self.counter['error'] += 1  # 错误计数器加1
            self.logger.error(f'scrape file_url error, {type(e)}: {e}, url: {file_url}')  # 记录错误日志

    def run(self, max_article_num):
        cookie_ts, cookies = self.read_cookies(timeout=2.5*24*3600)  # 读取cookies
        if cookies is None:
            cookies = self.login_for_cookies()  # 登录并获取cookies
            self.save_cookies(cookies)  # 保存cookies
        else:
            self.init_cookies(cookies, go_base_url=False)  # 初始化cookies
        self.save_cookies(cookies)
        if self.debug == False:
            start_time = time.time()
            lock_path = self.base_dir / self.lock_file
            if lock_path.exists():
                last_run_ts = lock_path.read_text()
                logger.error(f'last run not end, last_run_ts: {last_run_ts}')  # 记录错误日志
                return
            lock_path.write_text(str(int(start_time)))  # 写入锁文件
            scraped_records = self.get_scraped_records()  # 获取已抓取链接
            article_links = self.get_links(scraped_records, max_article_num)  # 获取文章链接
            add_scraped_records = []
            for article_link in article_links:
                self.scrape_article(article_link, add_scraped_records, cookies)  # 下载文件
            self.save_scraped_records(add_scraped_records)  # 保存已抓取链接
            self.save_counter(start_time)  # 保存计数器
            lock_path.unlink()  # 删除锁文件
            self.update_f.close()  # 关闭更新文件
        else:
            start_time = time.time()
            scraped_records = self.get_scraped_records()  # 获取已抓取链接
            self.page.goto(self.login_url)
            articles = self.get_articles(scraped_records, max_article_num)  # 获取文章链接
            add_scraped_records = []
            for article in articles:
                self.scrape_article(article, add_scraped_records, cookies)  # 下载文件
            self.save_scraped_records(add_scraped_records)  # 保存已抓取链接
            self.save_counter(start_time)  # 保存计数器
            self.update_f.close()  # 关闭更新文件
            
# 0 */4 * * * cd /home/crawler/work/scrape_pipeline/ && /opt/anaconda3/envs/ai/bin/python wechat/wechat.py >> logs/wechat.log 2>&1
# 运行方法
# （第一次运行需要安装虚拟环境依赖，已经安装好，这步可以跳过） cd /home/nkuwiki/nkuwiki/ && pip install -e . &&  playwright install && /opt/venvs/crawler/bin/python etl/crawler/wechat.py 
# 运行 cd /home/nkuwiki/nkuwiki/ && /opt/venvs/crawler/bin/python etl/crawler/wechat.py 
# 生产环境下设置debug=False！！！一定不要设置为True，debug模式没有反爬机制，爬太多会被封号！！！ max_article_num = 你想抓取的数量
# 调试可以设置debug=True，max_article_num < 5
if __name__ == "__main__":
    load_dotenv()  # 加载.env文件
    wechat = Wechat()  # 初始化
    wechat.run(max_article_num=5)   # max_article_num最大抓取数量