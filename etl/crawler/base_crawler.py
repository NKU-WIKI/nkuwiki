from __init__ import *

Config().load_config()

class BaseCrawler():
    """通用爬虫基类，封装常用爬取方法和反反爬策略
    
    Attributes:
        debug: 调试模式开关
        headless: 无头模式开关
        platform: 平台名称
    """
    def __init__(self, platform: str, debug: bool = False, headless: bool = False) -> None:       
        self.debug = debug
        self.headless = headless
        log_day_str = '{time:%Y-%m-%d}'
        # 使用Path对象处理路径，避免跨平台问题
        base_path = Path(__file__).resolve().parent.parent
        self.base_data_dir = base_path / 'data' / 'raw'
        self.base_log_dir = base_path / 'logs'
        
        # 确保目录存在并有正确权限
        self.base_data_dir.mkdir(parents=True, exist_ok=True)
        self.base_log_dir.mkdir(parents=True, exist_ok=True)
        self.process_name = platform
        self.platform = platform
        logger.add(f'{self.base_log_dir}/{self.process_name}.{log_day_str}.log', rotation="1 day", retention='3 months', level="INFO")# 配置日志记录器
        self.logger = logger
        self.base_dir = Path(self.base_data_dir) / self.platform
        self.base_dir.mkdir(exist_ok=True, parents=True)  # 创建目录，如果目录不存在
        self.counter = Counter()  # 初始化计数器
        self.lock_file = 'lock.txt'  # 锁文件，用于防止重复运行
        self.counter_file = 'counter.txt'  # 计数器文件，用于记录运行统计
        self.update_file = 'update.txt'  # 更新文件，用于记录更新信息
        self.update_f = open(self.base_dir / self.update_file, 'a+', encoding='utf-8')  # 打开更新文件
        self.scraped_urls_file = 'scraped_urls.json'  # 已抓取链接文件
        self.cookies_file = 'cookies.txt'  # cookies文件，用于保存登录信息
        self.tz = pytz.timezone('Asia/Shanghai')  # 设置时区
        self.playwright = sync_playwright().start()  # 初始化Playwright
        self.browser = self.playwright.chromium.launch(headless=self.headless)
        self.context = self.browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36',
            locale='zh-CN',
            timezone_id='Asia/Shanghai',
            color_scheme='dark',
            # 禁用自动化特征
            bypass_csp=True,
            java_script_enabled=True,
            service_workers='block',
            permissions=[]  # 禁用所有权限请求
        )
        self.proxy_pool = Config().get("PROXY_POOL", "http://127.0.0.1:7897").split(',')
        self.current_proxy = None
        # 初始化代理
        self.rotate_proxy()
        self.min_sleep_microsec = 3000  # 最小休眠时间
        self.max_sleep_microsec = 8000  # 最大休眠时间
        self.max_retry = 5  # 最大重试次数
        self.login_url = self.base_url  # 登录URL
        # 修改请求头增加随机性
        self.headers = {
            'Accept': random.choice([
                'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
            ]),
            'User-Agent': random.choice([
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15'
            ]),
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
            'sec-ch-ua-platform': '"macOS"',
        }
        # 增加代理健康检查
        def check_proxy_health(proxy):
            try:
                test_url = "http://www.gstatic.com/generate_204"
                response = requests.get(test_url, proxies={"http": proxy, "https": proxy}, timeout=10)
                return response.status_code == 204
            except:
                return False

        # 在初始化时选择可用代理
        healthy_proxies = [p for p in self.proxy_pool if check_proxy_health(p)]
        if healthy_proxies:
            self.current_proxy = random.choice(healthy_proxies)

    def __del__(self):
        """析构时关闭浏览器"""
        try:
            if hasattr(self, 'browser'):
                self.browser.close()
            if hasattr(self, 'playwright'):
                self.playwright.stop()
        except Exception as e:
            self.logger.error(f"Browser quit error: {e}")
    """
    通用函数
    """
    def random_sleep(self) -> None:
        """执行随机延迟，模拟人类操作"""
        if(self.debug): 
            pass
        else:
            # 随机滚动页面
            self.page.evaluate(f"window.scrollTo(0, {random.randint(100, 500)})")
            # 随机休眠一段时间
            time.sleep(random.uniform(self.min_sleep_microsec, self.max_sleep_microsec)/1000.0)

    def read_cookies(self, timeout: int = 6*3600) -> tuple[int, Optional[Dict[str, str]]]:
        """
        从文件中读取cookies，timeout为cookies有效期，默认6小时
        """
        f = self.base_dir / self.cookies_file
        if f.exists():
            cookies = {}
            lines = f.read_text().split('\n')
            cookie_ts = int(lines[0])
            now_ts = int(time.time())
            if now_ts - cookie_ts <= timeout:
                for i in range(1, len(lines)):
                    line = lines[i]
                    if ": " in line:
                        k, v = line.split(": ")
                        cookies[k] = v
                if len(cookies) >= 5:
                    return cookie_ts, cookies
        return 0, None
    
    def save_cookies(self, cookies: Dict[str, str]) -> None:
        """
        保存cookies到文件
        """
        f = self.base_dir / self.cookies_file
        now_ts = int(time.time())
        lines = f'{now_ts}\n'
        for k, v in cookies.items():
            lines += f'{k}: {v}\n'
        f.write_text(lines) 

    def inject_anti_detection_script(self) -> None:
        """注入反检测JavaScript代码"""
        try:
            # 读取初始化脚本
            init_script_path = Path(__file__).resolve().parent / 'init_script.js'
            with open(init_script_path, 'r', encoding='utf-8') as f:
                init_script = f.read()
            # 注入脚本
            self.page.add_init_script(init_script)
        except Exception as e:
            self.logger.error(f"Failed to inject anti-detection script: {e}")

    def init_cookies(self, cookies: Dict[str, str], go_base_url: bool = True) -> None:
        """
        初始化cookies，go_base_url为是否打开基础URL，默认False，即打开cookie_init_url
        """
        try:
            self.inject_anti_detection_script()
            self.page.goto(self.cookie_init_url)
            self.counter['visit'] += 1
            self.page.evaluate(f"window.scrollTo(0, {random.randint(100, 500)})")
            self.random_sleep()
            # 分批添加cookies并随机等待
            batch_size = 3  # 每批添加的cookie数量
            cookie_list = []
            for name, value in cookies.items():
                cookie_list.append({'name': name, 'value': value, 'url': self.cookie_init_url})
                if len(cookie_list) >= batch_size:
                    self.context.add_cookies(cookie_list)
                    cookie_list = []
                    self.random_sleep()  # 每批之间随机等待
            # 添加剩余的cookies
            if cookie_list:
                self.context.add_cookies(cookie_list)
                self.random_sleep()
            self.random_sleep()
            if go_base_url:
                self.page.goto(self.base_url)
                self.counter['visit'] += 1
                self.random_sleep()
                self.logger.info('go to base url')
        except Exception as e:
            self.counter['error'] += 1  # 错误计数器加1
            self.logger.error(e)  # 记录错误日志

    def update_scraped_articles(self, scraped_links: List[str], articles: List[Dict[str, Any]]) -> None:
        """
        保存已抓取文章，articles为新增抓取文章
        """
        def clean_filename(filename):
            """清理文件名，使其符合Windows和Linux文件系统规范"""
            # 1. 替换或删除特殊字符
            # Windows/Linux都不允许的字符: / \ : * ? " < > |
            # 空格和点号虽然允许，但可能造成问题，也替换掉
            invalid_chars = r'[<>:"/\\|?*\s.]+'
            clean_name = re.sub(invalid_chars, '_', filename)
            
            # 2. 删除首尾的点和空格（Windows不允许）
            clean_name = clean_name.strip('. ')
            
            # 3. 确保文件名不为空或仅包含特殊字符
            if not clean_name or clean_name.isspace():
                clean_name = 'untitled'
                
            # 4. 限制文件名长度（考虑中文字符）
            # Windows最长255字节，Linux一般255字符
            # 保守起见，取较小值，并留出后缀名空间
            while len(clean_name.encode('utf-8')) > 200:
                clean_name = clean_name[:-1]
            
            return clean_name

        total_f = self.base_dir / self.scraped_urls_file
        for article in articles:    
            if(article['original_url'] not in scraped_links):
                year_month = article['publish_time'][0:7].replace('-', '')
                save_dir = self.base_dir / year_month
                save_dir.mkdir(exist_ok=True, parents=True)
                clean_title = clean_filename(article['title'])
                save_path = save_dir / clean_title
                meta = {
                    "platform": self.platform,
                    "original_url": article['original_url'],
                    "title": article['title'],
                    "author": article['author'],
                    "publish_time": article['publish_time'],
                    "scrape_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "content_type": self.content_type
                    # "read_count": article.get('read_count', 0),
                    # "like_count": article.get('like_count', 0),
                }
                try:
                    with open(save_path.with_suffix('.json'), 'w', encoding='utf-8', errors='ignore') as f:
                        json.dump(meta, f, ensure_ascii=False, indent=2)
                except PermissionError:
                    self.logger.error(f"无法写入文件 {save_path}，权限被拒绝")
                    # 尝试使用临时文件名
                    temp_path = save_path.with_name(f"temp_{save_path.name}")
                    with open(temp_path.with_suffix('.json'), 'w', encoding='utf-8', errors='ignore') as f:
                        json.dump(meta, f, ensure_ascii=False, indent=2)
                scraped_links.append(article['original_url'])
        total_f = self.base_dir / self.scraped_urls_file
        total_f.write_text(json.dumps(scraped_links, ensure_ascii=False, indent=0))

    def get_scraped_original_urls(self) -> List[str]:
        """
        获取已抓取链接
        """
        total_f = self.base_dir / self.scraped_urls_file
        if total_f.exists():
            content = total_f.read_text()
            if len(content) > 0:  
                try:
                    return json.loads(content)  # 返回已抓取链接
                except:
                    pass
        return []

    def save_counter(self, start_time: float) -> None:
        """
        保存计数器，start_time为开始时间
        """
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
                self.logger.info(f'#summary# {used_time}s, visit: {visit}, scrape: {scrape}, download: {download}, error: {error}, noneed: {noneed}')  # 记录日志
                h.write(f'{time_str},{used_time},{visit},{scrape},{download},{error},{noneed}\n')  # 写入计数器文件
            # 成功后重命名
            if temp_path.exists():
                temp_path.replace(path)
        except PermissionError:
            self.logger.error(f"无法访问文件 {path}，权限被拒绝")
        except Exception as e:
            self.logger.error(f"保存计数器失败: {str(e)}")

    # def remove_disclosures(self, pdf_path: Path, match: str) -> None:
    #     """
    #     使用 pdfplumber 检查文本，使用 PyPDF2 修改并保存 PDF，match为匹配文本
    #     """
    #     try:
    #         # 提取文本以找到 match 起始页
    #         start_deleting_from = None
    #         with pdfplumber.open(pdf_path) as pdf:
    #             for i, page in enumerate(pdf.pages):
    #                 text = page.extract_text()
    #                 if match in text:
    #                     start_deleting_from = i
    #                     break

    #         # 如果找到 match，删除相应页面
    #         if start_deleting_from is not None:
    #             reader = PdfReader(pdf_path)
    #             writer = PdfWriter()
    #             for i in range(start_deleting_from):
    #                 writer.add_page(reader.pages[i])

    #             with open(pdf_path, "wb") as f:
    #                 writer.write(f)
    #     except Exception as e:
    #         self.counter['error'] += 1  # 错误计数器加1
    #         self.logger.error(f"An error occurred while cleaning {pdf_path}: {e}")  # 记录错误日志

    def close(self) -> None:
        """显式关闭浏览器"""
        try:
            self.browser.close()
            self.logger.info("Browser closed successfully")
        except Exception as e:
            self.logger.error(f"Browser close failed: {e}")

    def rotate_proxy(self) -> None:
        """从代理池中随机选择可用代理"""
        if self.proxy_pool:
            self.current_proxy = random.choice(self.proxy_pool)
            self.logger.info(f"使用代理: {self.current_proxy}")
            
            # 创建带有代理的新上下文
            self.context = self.browser.new_context(
                proxy={"server": self.current_proxy},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36',
                locale='zh-CN',
                timezone_id='Asia/Shanghai',
                color_scheme='dark',
                # 禁用自动化特征
                bypass_csp=True,
                java_script_enabled=True,
                service_workers='block',
                permissions=[]  # 禁用所有权限请求
            )
    def check_proxy_health(self, proxy: str) -> bool:
        """检查代理是否可用"""
        try:
            test_url = "http://www.gstatic.com/generate_204"
            response = requests.get(
                test_url,
                proxies={"http": proxy, "https": proxy},
                timeout=10
            )
            return response.status_code == 204
        except Exception as e:
            self.logger.warning(f"代理 {proxy} 不可用: {str(e)}")
            return False

    def get_healthy_proxies(self) -> List[str]:
        """获取可用代理列表"""
        return [p for p in self.proxy_pool if self.check_proxy_health(p)]

    def safe_write_file(self, path: Path, content: str) -> bool:
        """安全地写入文件，处理权限和锁问题"""
        try:
            # 创建临时文件
            temp_path = path.with_name(f"temp_{path.name}")
            with open(temp_path, 'w', encoding='utf-8') as f:
                f.write(content)
            # 如果成功写入临时文件，则替换原文件
            temp_path.replace(path)
            return True
        except Exception as e:
            self.logger.error(f"写入文件 {path} 失败: {str(e)}")
            return False