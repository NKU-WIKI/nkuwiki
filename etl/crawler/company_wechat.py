from etl.crawler import *
from etl.crawler.wechat import Wechat
from tqdm import tqdm

 # 定义招聘相关关键词，模糊匹配所有招聘信息
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
        
class CompanyWechat(Wechat):
    """大厂公众号招聘信息爬虫
    
    Attributes:
        authors: 配置名称，包含要爬取的公众号昵称列表
        debug: 调试模式开关
        headless: 是否使用无头浏览器模式
        use_proxy: 是否使用代理
    """
    def __init__(self,debug: bool = True, headless: bool = True, use_proxy: bool = True) -> None:
        super().__init__(authors="company_accounts",tag="company",debug=debug, headless=headless, use_proxy=use_proxy)

    async def scrape_articles_from_authors(self, scraped_original_urls: set, max_article_num: int, 
                                     total_max_article_num: int) -> list[dict]:
        total_articles = []
        # 获取今天的日期字符串，格式为"YYYY-MM-DD"
        today_date = datetime.now().strftime('%Y-%m-%d')
        self.logger.info(f'Only scraping articles published today ({today_date}) with recruitment keywords')
        
        # 创建作者处理进度条
        author_pbar = tqdm(total=len(self.authors), desc="处理公众号", unit="个")
        
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
        for author in self.authors:
            await self.random_sleep()
            try:
                # 尝试两种可能的按钮选择方式
                try:
                    # 首先尝试使用文本选择
                    button = self.page.get_by_text('选择其他账号')
                    await button.click()
                except Exception:
                    # 如果失败，尝试使用选择器
                    button = await self.page.wait_for_selector('p[class="inner_link_account_msg"] > div > button', 
                        timeout=3000,
                        state='visible'
                    )
                    await button.click()
            except Exception as e:
                self.logger.error(f'Failed to find account button: {e}')
                await self.page.screenshot(path='viewport.png', full_page=True)
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
                    timeout=6000
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
            # 创建文章处理进度条
            article_pbar = tqdm(total=max_article_num, desc=f"抓取{author}文章", unit="篇", leave=False)
            
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
                        
                        # 检查是否为今天发布的文章
                        if not article_publish_time.startswith(today_date):
                            continue
                            
                        # 检查标题是否包含招聘关键词
                        has_recruitment_keyword = False
                        for keyword in recruitment_keywords:
                            if keyword in article_title:
                                has_recruitment_keyword = True
                                break
                                
                        if not has_recruitment_keyword:
                            continue
                            
                        if(article_original_url not in scraped_original_urls):
                            articles.append({
                                'author': author,
                                'publish_time': article_publish_time,
                                'title': article_title,
                                'original_url': article_original_url
                            })
                            cnt += 1
                            self.logger.info(f'找到有效招聘文章: {article_title} ({author})')
                            article_pbar.update(1)
                            
                    page += 1
                    if cnt > 0:
                        self.logger.info(f'从 {author} 抓取到 {cnt} 篇今日发布的招聘文章')
                    
                    # 如果当前页面没有今天的文章，停止翻页
                    found_today_article = False
                    for i in range(len(article_publish_times_elements)):
                        if str(await article_publish_times_elements[i].inner_text()).startswith(today_date):
                            found_today_article = True
                            break
                            
                    if not found_today_article:
                        break
                        
                    try: 
                        # 通过文本内容定位"下一页"按钮
                        next_page_button = self.page.get_by_text("下一页")
                        await next_page_button.click()
                    except Exception as e:
                        self.counter['error'] += 1
                        break
                except Exception as e:
                    self.counter['error'] += 1
                    self.logger.error(f'抓取 {author} 文章时出错: {type(e).__name__}')
                    break  # 如果处理页面出错，跳出当前账号的处理

            article_pbar.close()
            author_pbar.update(1)
            
            self.update_scraped_articles(scraped_original_urls, articles)
            if len(articles) > 0:
                self.logger.info(f'已保存 {len(articles)} 篇来自 {author} 的今日招聘文章')
            total_articles.extend(articles)
            if len(total_articles) >= total_max_article_num:
                break

        author_pbar.close()
        if len(total_articles) > 0:
            self.logger.info(f'总共保存了 {len(total_articles)} 篇来自 {self.authors} 的今日招聘文章')
        return total_articles

    async def download_article(self, article: dict) -> None:
        """下载单篇文章内容
        Args:
            article: 文章信息字典（需包含original_url）
        """
        try:
            # 初始化变量，防止未定义错误
            content = ""
            abstract = ""
            title = "untitled"

            year_month = article.get('publish_time', datetime.now().strftime("%Y-%m%d"))[0:7].replace('-', '')
            title = clean_filename(article.get('title', 'untitled'))

            save_dir = self.data_dir / year_month / title
            Path(save_dir).mkdir(parents=True, exist_ok=True)

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
                                with open(save_dir / "abstract.md", 'w', encoding='utf-8') as f:
                                    f.write(abstract)
                                with open(save_dir / f"{title}.json", 'w', encoding='utf-8') as f:
                                    json.dump(article, f, ensure_ascii=False, indent=4)
                                self.logger.debug(f"生成摘要成功并保存为abstract.md: {title}")
                                preview_abstract = abstract[:100] + "..." if len(abstract) > 100 else abstract
                                self.logger.info(f"原始URL: {article['original_url']}\n摘要内容预览: {preview_abstract}")
                            else:
                                self.logger.error(f"生成摘要失败: {title}")
                                self.counter['error'] += 1
                            # 删除md_with_imgs目录
                            shutil.rmtree(md_with_imgs_dir)
                            self.logger.info(f"Removed md_with_imgs directory after extracting content")
                    else:
                        self.logger.error(f"转换失败，未生成新的文件夹: {title}")
                        self.counter['error'] += 1
                else:
                    self.logger.error(f"Markdown转换命令执行失败: {title}")
                    self.counter['error'] += 1

            # 使用安全方法获取内容长度
            content_length = len(content.strip()) if content else 0
            abstract_length = len(abstract) if abstract else 0
            self.logger.info(f'已下载文章: {title}, md长度: {content_length}, 摘要长度: {abstract_length}')

        except Exception as e:
            self.counter['error'] += 1
            self.logger.exception(f'下载文章内容失败: {e}, URL: {article.get("original_url", "未知URL")}')

    async def download(self):
        data_dir = self.data_dir
        start_time = time.time()
        try:
            # 获取当前日期
            today = datetime.now().date()
            today_str = today.strftime('%Y-%m-%d')
            current_ym = today.strftime('%Y%m')  # 当前年月，格式为YYYYMM
            self.logger.info(f"只处理发布时间为今天 ({today_str}) 的文章")
            
            # 过滤出当前年月及之后的文件夹
            target_folders = []
            for folder in Path(data_dir).iterdir():
                if folder.is_dir() and folder.name.isdigit() and len(folder.name) == 6:
                    # 判断文件夹名是否为数字格式的年月(YYYYMM)且大于等于当前年月
                    if folder.name >= current_ym:
                        target_folders.append(folder.name)
            
            self.logger.info(f"找到符合条件的文件夹 (>= {current_ym}): {target_folders}")
            
            # 找出发布时间为当天的文件
            today_files = []
            for folder_name in target_folders:
                folder_path = data_dir / folder_name
                for json_path in Path(folder_path).glob('**/*.json'):
                    try:
                        # 读取JSON文件内容
                        with open(json_path, 'r', encoding='utf-8') as f:
                            article_data = json.load(f)
                        
                        # 检查是否是字典类型
                        if not isinstance(article_data, dict):
                            continue
                            
                        # 检查publish_time字段是否存在
                        publish_time = article_data.get('publish_time')
                        if not publish_time:
                            continue
                            
                        # 如果publish_time是日期格式的字符串（如"2023-06-15"），直接比较
                        if publish_time.startswith(today_str):
                            today_files.append((json_path, article_data))
                    except Exception as e:
                        self.logger.warning(f"读取文件 {json_path} 时出错: {e}")
            
            total_files = len(today_files)
            self.logger.info(f"找到发布时间为今天 ({today_str}) 的 {total_files} 个JSON文件需要处理")
            
            if total_files == 0:
                self.logger.info("没有找到今天发布的文章，任务结束")
                return
            
            # 创建进度条
            pbar = tqdm(total=total_files, desc="下载文章", unit="篇")
            processed_count = 0
            
            # 只处理当天发布的文章
            for json_path, article_data in today_files:
                try:
                    md_files = list(json_path.parent.glob('*.md'))

                    if not md_files:
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
                finally:
                    # 更新进度条
                    processed_count += 1
                    pbar.update(1)
                    pbar.set_postfix({"成功": self.counter.get('processed', 0), "错误": self.counter.get('error', 0)})
        finally:            
            # 关闭进度条
            if 'pbar' in locals():
                pbar.close()
            self.save_counter(start_time)
            self.logger.info(f"下载完成，共处理 {self.counter.get('processed', 0)} 篇招聘相关文章, " +
                            f"错误 {self.counter.get('error', 0)} 篇")

# 生产环境下设置debug=False！！！一定不要设置为True，debug模式没有反爬机制，很容易被封号！！！ max_article_num = 你想抓取的数量
# 调试可以设置debug=True，max_article_num <= 5
# 抓取公众号文章元信息需要cookies（高危操作），下载文章内容不需要cookies，两者分开处理

if __name__ == "__main__":

    async def main():
        """异步主函数"""
        company_crawler = CompanyWechat(debug=True, headless=True, use_proxy=True)
        try:
            await company_crawler.async_init()
            # await company_crawler.scrape(max_article_num=10, total_max_article_num=1e10)
            await company_crawler.download()
        finally:
            # 确保资源正确关闭
            await company_crawler.close()

    # 运行异步主函数
    asyncio.run(main())