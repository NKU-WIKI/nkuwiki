from __init__ import *

class BaseCrawler():
    """通用爬虫基类，封装常用爬取方法和反反爬策略
    
    Attributes:
        debug: 调试模式开关
        headless: 无头模式开关
        use_proxy: 是否使用代理
        platform: 平台名称
        tag: 标签名称
    """
    def __init__(self, debug: bool = False, headless: bool = False, use_proxy: bool = False, tag: str = "") -> None:
        self.debug = debug
        self.headless = headless
        self.use_proxy = use_proxy
        self.logger = crawler_logger.bind(platform=self.platform)
        self.proxy_pool = self.load_proxies()
        self.current_proxy = None
        # 设置基本目录
        self.base_dir = RAW_PATH / Path(self.platform) 
        self.data_dir = self.base_dir / Path(self.tag)
        self.data_dir.mkdir(exist_ok=True, parents=True)  # 创建目录，如果目录不存在
        self.counter = Counter()  # 初始化计数器
        self.lock_file = 'lock.txt'  # 锁文件，用于防止重复运行
        self.counter_file = 'counter.txt'  # 计数器文件，用于记录运行统计
        self.update_file = 'update.txt'  # 更新文件，用于记录更新信息
        self.update_f = open(self.base_dir / self.update_file, 'a+', encoding='utf-8')  # 打开更新文件
        self.scraped_original_urls_file = 'scraped_original_urls.json'  # 已抓取链接文件
        self.cookies_file = 'cookies.txt'  # cookies文件，用于保存登录信息
        self.tz = pytz.timezone(DEFAULT_TIMEZONE)  # 设置时区
         # 将在async_init方法中初始化
        self._playwright_context = None 
        self.playwright = None
        self.browser = None
        self.page = None
        self.headers = {
            'Accept': random.choice([
                'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
            ]),
            'User-Agent': random.choice(DEFAULT_USER_AGENTS),
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
            'sec-ch-ua': '"Chromium";v="116", "Not)A;Brand";v="24", "Google Chrome";v="116"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
        }
        random.seed(int(time.time()))

    async def async_init(self):
        """异步初始化playwright和浏览器"""
        self._playwright_context = await async_playwright().start()
        self.playwright = self._playwright_context
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            args=[
               "--disable-blink-features=AutomationControlled",
                "--disable-infobars",  # 禁用Chrome提示栏
                "--no-sandbox",
                "--disable-gpu",
                "--disable-dev-shm-usage",
                "--ignore-certificate-errors",  # 忽略证书错误
                "--disable-web-security",  # 禁用同源策略
                f"--window-size={random.randint(1200, 1400)},{random.randint(800, 1000)}",  # 随机窗口尺寸
            ],
            executable_path="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" if sys.platform == "darwin" else None,
            ignore_default_args=["--enable-automation"]  # 禁用自动化提示
        )
        if self.use_proxy and self.proxy_pool:
            await self.rotate_proxy()
        self.context = await self.browser.new_context(
            user_agent=self.headers['User-Agent'],
            locale=DEFAULT_LOCALE,
            timezone_id=DEFAULT_TIMEZONE,
            color_scheme='light', 
            device_scale_factor=random.choice([1, 1.25, 1.5]),
            is_mobile=False,
            has_touch=False,
            permissions=[],
            extra_http_headers= self.headers
        )
        self.page = await self.context.new_page()
        await self.inject_anti_detection_script()
        
    def __del__(self):
        """析构时安全释放资源，避免直接关闭异步资源"""
        try:
            if hasattr(self, 'update_f') and self.update_f:
                try:
                    self.update_f.close()
                except:
                    pass
                    
            # 注意：不要在这里关闭异步资源，这可能导致I/O operation on closed pipe错误
            # 应通过显式调用close()方法关闭异步资源
        except:
            pass

    def load_proxies(self) -> List[str]:
        """加载代理列表
        
        Returns:
            代理列表
        """
        # 可以从环境变量或配置文件加载
        proxy_str = os.environ.get("PROXY_POOL", "")
        if not proxy_str and self.use_proxy:
            # 如果使用代理但未配置，添加一个默认的本地代理
            return ["http://127.0.0.1:7897"]
        return proxy_str.split(",") if proxy_str else []

    async def random_sleep(self) -> None:
        """增强版随机行为模拟"""
        if self.debug: 
            return
        
        # 模拟人类滚动模式
        scroll_steps = [
            (random.randint(100, 300), 500),
            (random.randint(400, 600), 800),
            (random.randint(700, 900), 1000)
        ]
        for pos, delay in scroll_steps:
            await self.page.evaluate(f"window.scrollTo(0, {pos})")
            await asyncio.sleep(delay / 1000.0)
        
        # 模拟鼠标移动轨迹
        await self.page.mouse.move(
            random.randint(0, 500), 
            random.randint(0, 300),
            steps=random.randint(5, 10)
        )
        
        # 随机输入行为（焦点在body时）
        await self.page.keyboard.press('PageDown')
        await asyncio.sleep(random.uniform(0.5, 1.5))

    def read_cookies(self, timeout: int = 6*3600):
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
        """保存cookies到文件

        Args:
            cookies: 要保存的cookies
        """
        with open(self.base_dir / self.cookies_file, 'w') as f:
            json.dump(cookies, f, indent=4)

    async def inject_anti_detection_script(self) -> None:
        """向页面注入反自动化检测脚本"""
        try:
            # 获取脚本所在目录的绝对路径
            script_dir = Path(__file__).resolve().parent
            init_script_path = script_dir / 'init_script.js'
            
            # 读取初始化脚本
            with open(init_script_path, 'r', encoding='utf-8') as f:
                init_script = f.read()
                
            # 注入脚本
            await self.page.add_init_script(init_script)
        except Exception as e:
            self.logger.warning(f"注入反检测脚本失败: {e},使用内联备用脚本")
            # 使用内联备用脚本
            await self.page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => false,
            });
            // 劫持 iframe
            const oldFrame = HTMLIFrameElement.prototype.contentWindow.get;
            Object.defineProperty(HTMLIFrameElement.prototype, 'contentWindow', {
                get: function () {
                    const frame = oldFrame.call(this);
                    try {
                        frame.Object.defineProperty(frame.navigator, 'webdriver', {
                            get: () => false,
                        });
                    } catch (e) { }
                    return frame;
                }
            });
            """)

    async def init_cookies(self, cookies: Dict[str, str], go_base_url: bool = True) -> None:
        """
        初始化cookies，go_base_url为是否打开基础URL，默认False，即打开cookie_init_url
        """
        try:
            await self.inject_anti_detection_script()
            await self.page.goto(self.cookie_init_url)
            self.counter['visit'] += 1
            await self.random_sleep()
            # 分批添加cookies并随机等待
            batch_size = 3  # 每批添加的cookie数量
            cookie_list = []
            for name, value in cookies.items():
                cookie_list.append({'name': name, 'value': value, 'url': self.cookie_init_url})
                if len(cookie_list) >= batch_size:
                    await self.context.add_cookies(cookie_list)
                    cookie_list = []
                    await self.random_sleep()  # 每批之间随机等待
            # 添加剩余的cookies
            if cookie_list:
                await self.context.add_cookies(cookie_list)
                await self.random_sleep()
            if go_base_url:
                await self.page.goto(self.base_url)
                self.counter['visit'] += 1
                await self.random_sleep()
        except Exception as e:
            self.counter['error'] += 1  # 错误计数器加1
            self.logger.error(e)  # 记录错误日志

    def update_scraped_articles(self, scraped_original_urls: List[str], articles: List[Dict[str, Any]]) -> None:
        """
        保存已抓取文章，articles为新增抓取文章
        """

        total_f = self.base_dir / self.scraped_original_urls_file
        for article in articles:    
            if(article['original_url'] not in scraped_original_urls):
                year_month = article.get('publish_time', datetime.now().strftime("%Y-%m%d"))[0:7].replace('-', '')
                save_dir = self.data_dir / year_month
                save_dir.mkdir(exist_ok=True, parents=True)
                clean_title = clean_filename(article.get('title', ''))
                
                # 创建文章专属目录
                article_dir = save_dir / clean_title
                article_dir.mkdir(exist_ok=True, parents=True)
                
                # 在文章目录下保存JSON文件
                save_path = article_dir / clean_title
                
                meta = {
                    "platform": self.platform,
                    "original_url": article.get('original_url', ''),
                    "title": article.get('title', ''),
                    "author": article.get('author', ''),
                    "publish_time": article.get('publish_time', ''),
                    "scrape_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "content_type": self.content_type
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
                scraped_original_urls.append(article['original_url'])
        total_f = self.base_dir / self.scraped_original_urls_file
        total_f.write_text(json.dumps(scraped_original_urls, ensure_ascii=False, indent=0))

    def get_scraped_original_urls(self) -> List[str]:
        """获取已抓取的原始URL列表
        
        Args:
        Returns:
            URL列表
        """
        urls_file = self.base_dir / self.scraped_original_urls_file
        if not urls_file.exists():
            return []
        try:
            with open(urls_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"读取已抓取URL列表出错: {e}")
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

    async def close(self) -> None:
        """关闭浏览器和playwright，避免I/O operation on closed pipe错误"""
        try:
            # 关闭page
            if hasattr(self, 'page') and self.page:
                try:
                    await self.page.close()
                except Exception as e:
                    self.logger.error(f"关闭页面出错: {e}")
                self.page = None
                
            # 关闭context
            if hasattr(self, 'context') and self.context:
                try:
                    await self.context.close()
                except Exception as e:
                    self.logger.error(f"关闭context出错: {e}")
                self.context = None

            # 关闭browser
            if hasattr(self, 'browser') and self.browser:
                try:
                    await self.browser.close()
                except Exception as e:
                    self.logger.error(f"关闭浏览器出错: {e}")
                self.browser = None

            # 关闭playwright
            if hasattr(self, 'playwright') and self.playwright:
                try:
                    await self.playwright.stop()
                except Exception as e:
                    self.logger.error(f"关闭playwright出错: {e}")
                self.playwright = None
                
            # 关闭文件句柄
            if hasattr(self, 'update_f') and self.update_f:
                try:
                    self.update_f.close()
                except Exception as e:
                    self.logger.error(f"关闭文件出错: {e}")
                self.update_f = None
                
            self.logger.info("所有资源已正确关闭")
        except Exception as e:
            self.logger.error(f"关闭资源时发生错误: {e}")

    async def rotate_proxy(self) -> None:
        """轮换代理"""
        if not self.proxy_pool:
            self.logger.warning("无可用代理池")
            return
            
        # 获取健康的代理
        healthy_proxies = self.get_healthy_proxies()
        if not healthy_proxies:
            self.logger.warning("无健康代理可用，使用随机代理")
            healthy_proxies = self.proxy_pool
            
        # 随机选择一个代理
        self.current_proxy = random.choice(healthy_proxies)
        
        # 如果浏览器已初始化，创建新的上下文
        if self.browser:
            # 创建上下文
            self.context = await self.browser.new_context(
                proxy={
                    "server": self.current_proxy,
                    "bypass": "127.0.0.1,localhost"
                },
                user_agent=self.headers['User-Agent'],
                locale=DEFAULT_LOCALE,
                timezone_id=DEFAULT_TIMEZONE
            )
            
            # 创建新页面
            if hasattr(self, 'page') and self.page:
                await self.page.close()
            self.page = await self.context.new_page()
            
            # 设置超时
            self.page.set_default_timeout(30000)  # 30秒超时

    def check_proxy_health(self, proxy: str) -> bool:
        """检查代理健康状态
        
        Args:
            proxy: 代理地址
            
        Returns:
            代理是否可用
        """
        try:
            # 测试连接百度
            test_url = "http://www.baidu.com"
            proxies = {"http": proxy, "https": proxy}
            response = requests.get(test_url, proxies=proxies, timeout=5)
            return response.status_code == 200
        except Exception:
            return False

    def get_healthy_proxies(self) -> List[str]:
        """获取健康的代理列表
        
        Returns:
            健康的代理列表
        """
        if not self.proxy_pool:
            return []
            
        healthy_proxies = []
        for proxy in self.proxy_pool:
            if self.check_proxy_health(proxy):
                healthy_proxies.append(proxy)
                
        return healthy_proxies

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
        
