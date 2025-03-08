from __init__ import *
from base_crawler import BaseCrawler

class Wechat(BaseCrawler):
    """微信公众号爬虫
    
    Attributes:
        authors: 配置名称，包含要爬取的公众号昵称列表
        debug: 调试模式开关
        headless: 是否使用无头浏览器模式
        use_proxy: 是否使用代理
    """
    def __init__(self, authors: str = "company_accounts", debug: bool = False, headless: bool = False, use_proxy: bool = False) -> None:
        self.platform = "company"
        self.content_type = "article"
        self.base_url = "https://mp.weixin.qq.com/"
        super().__init__(self.platform, debug, headless, use_proxy)
        
        # 获取公众号列表
        accounts = os.environ.get(authors.upper(), "")
        if not accounts:
            self.logger.error(f"Config etl.crawler.accounts.{authors} is not set")
            raise
        self.authors = accounts.split(",")
        self.logger.info(f"start to scrape articles from authors: {self.authors}")
        self.cookie_init_url = "https://mp.weixin.qq.com/"  # 初始化cookies的URL

    async def login_for_cookies(self) -> dict[str, str]:
        """登录微信公众号平台获取cookies
        
        Returns:
            包含登录cookies的字典
            
        Raises:
            TimeoutError: 登录超时（5分钟未扫码）
            Exception: 其他登录异常
        """
        try:
            await self.page.goto(self.base_url)
            await self.random_sleep()
            max_wait = 300  # 最大等待5分钟
            
            # 立即检查是否已登录（二维码元素不存在）
            if not await self.page.query_selector('img[class="login__type__container__scan__qrcode"]'):
                self.logger.info('检测到已登录状态')
                await self.random_sleep()
                return {cookie['name']: cookie['value'] for cookie in self.context.cookies()}

            while max_wait > 0:
                self.logger.info('请扫描二维码登录...')
                # 持续监测二维码元素是否存在
                if not await self.page.query_selector('img[class="login__type__container__scan__qrcode"]'):
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

    async def scrape_articles_from_authors(self, scraped_original_urls: set, max_article_num: int, 
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
        try:
            await self.random_sleep()
            new_content_button = await self.page.wait_for_selector('div[class="new-creation__menu-item"]', 
                state='attached', 
                timeout=3000
            )
            await new_content_button.click()
            await self.context.wait_for_event('page')
            self.page = self.context.pages[-1]
            await self.random_sleep()
            element = await self.page.wait_for_selector('li[id="js_editor_insertlink"] > span')
            await element.click()
        except Exception as e:
            await self.page.screenshot(path='viewport.png', full_page=True)
            self.counter['error'] += 1
            self.logger.error(f'get articles from {self.authors} error, {type(e)}: {e}')
            return total_articles
        fg = False
        for author in self.authors:
            if(author == "海信集团招聘"):
                fg = True
            if(fg == False):
                continue
            await self.random_sleep()
            try:
                button = await self.page.wait_for_selector('p[class="inner_link_account_msg"] > div > button', 
                    timeout=3000,
                    state='visible'
                )
                await button.click()
            except Exception as e:
                self.logger.error(f'Failed to find account button: {e}')
                continue
            await self.random_sleep()
            try:
                search_account_field = await self.page.wait_for_selector(
                    'input[placeholder="输入文章来源的账号名称或微信号，回车进行搜索"]',
                    timeout=3000
                )
                await search_account_field.fill(author)
            except Exception as e:
                self.logger.error(f'Failed to find search field,{str(e)}')
                break
            await self.random_sleep()
            try:
                search_button = await self.page.wait_for_selector(
                    'button[class="weui-desktop-icon-btn weui-desktop-search__btn"]',
                    timeout=3000
                )
                await search_button.click()
            except Exception as e:
                self.logger.error(f'Failed to find search button: {e}')
                break
            await self.random_sleep()
            # 等待账号选择器出现
            try:
                account_selector = await self.page.wait_for_selector(
                    '//li[@class="inner_link_account_item"]/div[1]',
                    timeout=3000
                )
                await account_selector.click()

            except Exception as e:
                self.logger.error(f'failed to click account, {author} seems does not exist')
                continue
            await self.random_sleep()
            # 获取页码信息
            try:
                max_page_label = await self.page.wait_for_selector(
                    'span[class="weui-desktop-pagination__num__wrp"] > label:nth-of-type(2)',
                    timeout=3000
                )
                max_page_num = int(await max_page_label.inner_text())
            except Exception as e:
                self.logger.warning(f'Failed to get max page number: {e}, set default max page number to 1')
                max_page_num = 1
            page = 1
            articles = []
            while len(articles) < max_article_num and page <= max_page_num:
                try:
                    await asyncio.sleep(1.0) 
                    await self.random_sleep()
                    article_titles_elements = await self.page.query_selector_all('div[class="inner_link_article_title"] > span:nth-of-type(2)')
                    article_publish_times_elements = await self.page.query_selector_all('div[class="inner_link_article_date"] > span:nth-of-type(1)')
                    article_original_urls_elements = await self.page.query_selector_all('div[class="inner_link_article_date"] > span:nth-of-type(2) > a[href]')
                    cnt = 0
                    for i in range(len(article_titles_elements)):
                        article_title = str(await article_titles_elements[i].inner_text())
                        article_publish_time = str(await article_publish_times_elements[i].inner_text())
                        article_original_url = str(await article_original_urls_elements[i].get_attribute('href'))
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
                    # 修改时间过滤逻辑
                    # 如果找到2025年之前的文章，就停止爬取更多页面
                    # 假设文章按时间倒序排列，最新的先显示
                    if articles and articles[-1]['publish_time'] < "2025-01-01":
                        self.logger.info(f'Found articles before 2025, stopping pagination for {author}')
                        break
                    try: 
                        # 通过文本内容定位"下一页"按钮
                        next_page_button = self.page.get_by_text("下一页")
                        await next_page_button.click()
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

    async def scrape(self, max_article_num: int = 5, total_max_article_num: int = 20) -> None:
        """抓取微信公众号文章

        Args:
            max_article_num: 每个公众号最大抓取数量
            total_max_article_num: 总共最大抓取数量
        """
        try:
            # 先获取已经抓取的链接
            scraped_original_urls = self.get_scraped_original_urls()
            # 检查cookies是否存在，不存在则登录获取
            cookie_ts, cookies = self.read_cookies(timeout=2.5*24*3600)  
            if cookies is None:
                cookies = await self.login_for_cookies()  
                self.save_cookies(cookies)  
            else:
                await self.init_cookies(cookies, go_base_url=True)  
            start_time = time.time()
            if self.debug == False:
                lock_path = self.base_dir / self.lock_file
                # if lock_path.exists():
                #     last_run_ts = lock_path.read_text()
                #     self.logger.error(f'last run not end, last_run_ts: {last_run_ts}')  # 记录错误日志
                #     return
                lock_path.write_text(str(int(start_time)))  # 写入锁文件
                scraped_original_urls = self.get_scraped_original_urls()  # 获取已抓取链接
                articles = await self.scrape_articles_from_authors(scraped_original_urls, max_article_num, total_max_article_num)
                self.update_scraped_articles([article['original_url'] for article in articles], articles)
                lock_path.unlink()  # 删除锁文件
            else:
                articles = await self.scrape_articles_from_authors(scraped_original_urls, max_article_num, total_max_article_num)
                self.update_scraped_articles([article['original_url'] for article in articles], articles)
        
            self.save_counter(start_time)  
            self.update_f.close()  
            
        except Exception as e:
            self.logger.error(f"抓取出错: {e}")

    async def download_article(self, article: dict) -> None:
        """下载单篇文章内容
        Args:
            article: 文章信息字典（需包含original_url）
        """
        try:
            article_page = await self.context.new_page()
            await article_page.goto(article['original_url'])
            self.counter['visit'] += 1
            await self.random_sleep()

            year_month = article.get('publish_time', datetime.now().strftime("%Y-%m%d"))[0:7].replace('-', '')
            title = clean_filename(article.get('title', 'untitled'))

            save_dir = self.base_dir  / year_month / title
            # 修复异步调用
            html_content = await article_page.content()
            # 确保目录存在
            Path(save_dir).mkdir(parents=True, exist_ok=True)
            html_path = save_dir / f"{title}.html"
            with open(html_path, 'w', encoding='utf-8', errors='ignore') as f:
                f.write(html_content)

            if 'original_url' in article:
                from etl.transform.wechatmp2md import wechatmp2md
                success = wechatmp2md(article['original_url'], str(save_dir))
                if success:
                    generated_dirs = [d for d in Path(save_dir).iterdir() if d.is_dir() and d.name != 'imgs']
                    if generated_dirs:
                        generated_dir = generated_dirs[0]
                        md_with_imgs_dir = save_dir / "md_with_imgs"
                        generated_dir.rename(md_with_imgs_dir)

                        generated_md_files = list(Path(md_with_imgs_dir).glob("*.md"))
                        if generated_md_files:
                            md_file = save_dir / f"{title}.md"
                            shutil.copy2(generated_md_files[0], md_file)

                            with open(md_file, 'r', encoding='utf-8', errors='ignore') as f:
                                content = f.read()
                            content = re.sub(r'!\[.*?\]\(.*?\)', '', content)
                            content = re.sub(r'\n\s*\n', '\n', content)
                            with open(md_file, 'w', encoding='utf-8') as f:
                                f.write(content.strip())
                            from etl.transform.abstract import generate_abstract
                            abstract = generate_abstract(md_file)
                            if abstract:
                                article['content'] = abstract
                                # 将摘要保存为abstract.md文件
                                with open(save_dir / "abstract.md", 'w', encoding='utf-8') as f:
                                    f.write(abstract)
                                with open(save_dir / f"{title}.json", 'w', encoding='utf-8') as f:
                                    json.dump(article, f, ensure_ascii=False, indent=4)
                                self.logger.debug(f"生成摘要成功并保存为abstract.md: {title}")
                                # 添加日志输出原始URL和摘要内容
                                preview_abstract = abstract[:100] + "..." if len(abstract) > 100 else abstract
                                self.logger.info(f"原始URL: {article['original_url']}\n摘要内容预览: {preview_abstract}")
                            else:
                                self.logger.error(f"生成摘要失败: {title}")
                                self.counter['error'] += 1
                    else:
                        self.logger.error(f"转换失败，未生成新的文件夹: {title}")
                        self.counter['error'] += 1
                else:
                    self.logger.error(f"Markdown转换命令执行失败: {title}")
                    self.counter['error'] += 1

            self.logger.info(f'已下载文章: {title}, md长度: {len(content.strip())}, 摘要长度: {len(abstract)}')

        except Exception as e:
            self.counter['error'] += 1
            self.logger.exception(f'下载文章内容失败: {e}, URL: {article["original_url"]}')
        finally:
            try:
                # 修复异步调用
                await article_page.close()
            except:
                pass

    async def download(self):
        data_dir = self.base_dir
        start_time = time.time()
        
        # 定义招聘相关关键词，扩大范围以模糊匹配所有招聘信息
        recruitment_keywords = [
            # 基础招聘术语
            '招聘', '职位', '岗位', '应聘', '求职', '校招', '社招', '实习', '人才', '简历', 
            # 招聘类型
            '校园招聘', '企业招聘', '全球招聘', '秋季招聘', '春季招聘', '暑期招聘', '专场招聘',
            # 需求表述
            '人才需求', '用人需求', '招人', '招募', '诚招', '急招', '热招', '高薪招', '直招',
            # 机会表述
            '就业机会', '工作机会', '职业机会', '发展机会', '就业机会', '就业信息',
            # 正式或委婉表述
            '招贤纳士', '诚聘', '虚位以待', '求贤若渴', '纳贤', '聘用', '聘请',
            # 英文关键词
            'job', 'career', 'hire', 'recruit', 'employment', 'position', 'opportunity',
            # 招聘活动
            '招聘会', '宣讲会', '双选会', '招聘活动', '线上招聘', '现场招聘',
            # 招聘流程相关
            '面试', 'offer', '入职', '简历投递', '笔试', '面试官', '笔试题', '招聘流程',
            # 福利待遇相关
            '薪资', '待遇', '福利', '五险一金', '年终奖', '奖金', '补贴', '津贴',
            # 求职者相关
            '毕业生', '应届生', '毕业', '学历', '研究生', '本科', '硕士', '博士',
            # 行业特定术语
            '猎头', 'HR', '人力资源', '用人单位', '招工',
            # 模糊相关词
            '加入', '加盟', '加入我们', '团队扩招', '扩招', '寻找', '寻'
        ]
        
        # 过滤出202501及之后的文件夹
        target_folders = []
        for folder in Path(data_dir).iterdir():
            if folder.is_dir() and folder.name.isdigit() and len(folder.name) == 6:
                # 判断文件夹名是否为数字格式的年月(YYYYMM)且大于等于202501
                if folder.name >= "202501":
                    target_folders.append(folder.name)
        
        self.logger.info(f"找到符合条件的文件夹: {target_folders}")
        self.logger.info(f"使用的招聘关键词数量: {len(recruitment_keywords)}")
        
        # 只处理这些文件夹内的JSON文件
        for folder_name in target_folders:
            folder_path = data_dir  / folder_name
            for json_path in Path(folder_path).glob('**/*.json'):
                try:
                    with open(json_path, 'r', encoding='utf-8') as f:
                        article_data = json.load(f)

                    if not isinstance(article_data, dict):
                        continue
                        
                    # 检查标题是否包含招聘相关关键词
                    title = article_data.get('title', '')
                    if not any(keyword in title for keyword in recruitment_keywords):
                        self.logger.debug(f"跳过非招聘文章: {title}")
                        continue

                    html_files = list(json_path.parent.glob('*.html'))
                    md_files = list(json_path.parent.glob('*.md'))

                    if not html_files or not md_files:
                        self.logger.debug(f"正在处理招聘相关文章: {title}")
                        await self.download_article(article_data)
                        self.counter['processed'] = self.counter.get('processed', 0) + 1
                        if self.counter['processed'] % 100 == 0:
                            self.logger.info(f"已处理 {self.counter['processed']} 篇招聘相关文章")
                        await self.random_sleep()
                except Exception as e:
                    self.counter['error'] = self.counter.get('error', 0) + 1
                    self.logger.error(f"处理文件 {json_path} 时出错: {e}")
                    if self.counter['error'] > 10 and self.counter['error'] % 10 == 0:
                        self.logger.warning("错误过多，暂停120秒")
                        await asyncio.sleep(120)
                        
        self.save_counter(start_time)
        self.logger.info(f"下载完成，共处理 {self.counter.get('processed', 0)} 篇招聘相关文章, " +
                         f"错误 {self.counter.get('error', 0)} 篇")

# 生产环境下设置debug=False！！！一定不要设置为True，debug模式没有反爬机制，很容易被封号！！！ max_article_num = 你想抓取的数量
# 调试可以设置debug=True，max_article_num <= 5
# 抓取公众号文章元信息需要cookies（高危操作），下载文章内容不需要cookies，两者分开处理

if __name__ == "__main__":
    import asyncio

    async def main():
        """异步主函数"""
        # for authors in ["company_accounts"]:
        #     try:
        #         # 创建爬虫实例
        #         wechat = Wechat(authors=authors, debug=True, headless=True, use_proxy=True)
        #         # 异步初始化playwright
        #         await wechat.async_init()
        #         # 执行爬取
        #         await wechat.scrape(max_article_num=10, total_max_article_num=1e10)
                
        #     except Exception as e:
        #         print(f"处理 {authors} 时出错: {e}")
        #         import traceback
        #         traceback.print_exc()
        
        # 下载处理（在单独的实例中）
        try:
            wechat = Wechat(debug=True, headless=True, use_proxy=True)
            await wechat.async_init()  # 确保在调用download前初始化
            await wechat.download()
        except Exception as e:
            print(f"下载处理时出错: {e}")
            import traceback
            traceback.print_exc()

    # 运行异步主函数
    asyncio.run(main())