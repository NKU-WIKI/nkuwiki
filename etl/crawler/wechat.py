import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from etl.crawler import (
    crawler_logger, proxy_pool, market_token,
    timedelta, RAW_PATH,
    default_user_agents, default_timezone, default_locale, user_agents
)
from etl.utils.const import (
    unofficial_accounts,
    university_official_accounts,
    school_official_accounts,
    club_official_accounts,
    company_accounts
)
from etl.crawler.base_crawler import BaseCrawler
from etl.utils.date import parse_date
from etl.utils.file import clean_filename
from tqdm import tqdm
from typing import Any
from pathlib import Path
import asyncio
import json
import time
import re
from datetime import datetime
from etl.load import db_core
from etl.processors.document import DocumentProcessor
from core.agent.abstract import get_bot_ids_by_tag

class Wechat(BaseCrawler):
    """微信公众号爬虫
    
    Attributes:
        authors: 配置名称，包含要爬取的公众号昵称列表
        debug: 调试模式开关
        headless: 是否使用无头浏览器模式
        use_proxy: 是否使用代理
    """
    def __init__(self, authors: list[str], tag: str = "nku", debug: bool = False, headless: bool = True, use_proxy: bool = False) -> None:
        """初始化微信公众号爬虫
        
        Args:
            authors: 要爬取的公众号昵称列表
            tag: 标签
            debug: 调试模式开关
            headless: 是否使用无头浏览器模式
            use_proxy: 是否使用代理
        """
        self.platform = "wechat"
        self.tag = tag
        self.content_type = "article"
        self.base_url = "https://mp.weixin.qq.com/"
        super().__init__(debug, headless, use_proxy)
        
        if not authors:
            self.logger.error("公众号列表不能为空")
            raise ValueError("公众号列表不能为空")
            
        self.authors = authors
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
                return {cookie['name']: cookie['value'] for cookie in await self.context.cookies()}

            while max_wait > 0:
                self.logger.info('请扫描二维码登录...')
                # 持续监测二维码元素是否存在
                if not await self.page.query_selector('img[class="login__type__container__scan__qrcode"]'):
                    time.sleep(5)  # 给登录后页面加载留出时间
                    self.logger.info('登录成功')
                    return {cookie['name']: cookie['value'] for cookie in await self.context.cookies()}
                time.sleep(5)
                max_wait -= 5
                
            if max_wait <= 0:
                raise TimeoutError("登录超时")
        except Exception as e:
            # 增加失败后清理
            # self.context.clear_cache()  # BrowserContext没有clear_cache方法
            raise e

    async def scrape_articles_from_authors(self, scraped_original_urls: set, max_article_num: int, 
                                     total_max_article_num: int, time_range: tuple = None, recruitment_keywords: list[str] = None, pbar: Any = None) -> list[dict]:
        """从指定公众号列表抓取文章元数据
        
        Args:
            scraped_original_urls: 已抓取链接集合（用于去重）
            max_article_num: 单个公众号最大抓取数量
            total_max_article_num: 总最大抓取数量
            time_range: 可选的时间范围元组 (start_date, end_date)，支持字符串('2025-01-01')或datetime对象
            recruitment_keywords: 可选的关键词列表，只抓取标题包含关键词的文章
            pbar: 进度条对象
            
        Returns:
            包含文章信息的字典列表，格式:
            [{
                'author': 公众号名称,
                'publish_time': 发布时间,
                'title': 文章标题,
                'original_url': 文章链接
            }]
        """
        # 处理时间范围
        start_date = end_date = None
        if time_range and len(time_range) == 2:
            start_date = parse_date(time_range[0])
            end_date = parse_date(time_range[1])
            
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
            if(author == '统院拾光'):
                fg = True
                continue
            if(not fg):
                continue
     

            await self.random_sleep()
            try:
                button = self.page.get_by_text('选择其他账号')
                await button.click()
            except Exception as e:
                self.logger.error(f'Failed to find account button: {e}')
                continue
            await self.random_sleep()
            retry_count = 0
            
            while retry_count < self.max_retries:
                try:
                    # 清空搜索框重新输入
                    search_account_field = await self.page.wait_for_selector(
                        'input[placeholder="输入文章来源的账号名称或微信号，回车进行搜索"]',
                        timeout=3000
                    )
                    await search_account_field.fill("")  # 先清空
                    await search_account_field.fill(author)
                    
                    await self.random_sleep()
                    search_button = await self.page.wait_for_selector(
                        'button[class="weui-desktop-icon-btn weui-desktop-search__btn"]',
                        timeout=3000
                    )
                    await search_button.click()
                    
                    await self.random_sleep()
                    # 等待账号选择器出现
                    account_selector = await self.page.wait_for_selector(
                        '//li[@class="inner_link_account_item"]/div[1]',
                        timeout=6000
                    )
                    await account_selector.click()
                    # 如果成功找到并点击了账号，跳出重试循环
                    break
                    
                except Exception as e:
                    retry_count += 1
                    if retry_count >= self.max_retries:
                        self.logger.error(f'Failed to search and select account after {self.max_retries} retries: {author}, error: {e}')
                        break
                    self.logger.warning(f'Retry {retry_count}/{self.max_retries} for account: {author}, error: {e}')
                    await self.random_sleep()  # 失败后多等待一会
            
            if retry_count >= self.max_retries:
                if pbar:
                    pbar.update(1)
                continue  # 重试次数用完，跳过当前作者
                
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
                        
                        # 检查时间范围
                        if time_range:
                            try:
                                pub_date = datetime.strptime(article_publish_time, '%Y-%m-%d')
                                if start_date and pub_date < start_date:
                                    # 如果文章时间早于开始时间，直接跳到下一个作者
                                    self.logger.debug(f'Article date {pub_date} is earlier than start_date {start_date}, skip to next author')
                                    page = max_page_num + 1  # 强制退出当前作者的循环
                                    break
                                if end_date and pub_date > end_date:
                                    # 如果文章时间晚于结束时间，跳过当前文章继续检查
                                    continue
                            except:
                                self.logger.warning(f'无法解析文章发布时间: {article_publish_time}')
                                
                        if recruitment_keywords and not any(keyword in article_title for keyword in recruitment_keywords):
                            continue
                        
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
            if(len(articles) > 0):
                self.logger.info(f'save {len(articles)} articles from {author}')
                total_articles.extend(articles)
                if len(total_articles) >= total_max_article_num:
                    if pbar:
                        pbar.update(1)
                    break
            else:
                self.logger.debug(f'no articles from {author}')
            if pbar:
                pbar.update(1)

        self.logger.info(f'save total {len(total_articles)} articles from {self.authors}')
        return total_articles

    async def scrape(self, max_article_num: int = 5, total_max_article_num: int = 20, time_range: tuple = None, recruitment_keywords: list[str] = None) -> None:
        """抓取微信公众号文章

        Args:
            max_article_num: 每个公众号最大抓取数量
            total_max_article_num: 总共最大抓取数量
            time_range: 可选的时间范围元组 (start_date, end_date)，支持字符串('2025-01-01')或datetime对象
            recruitment_keywords: 可选的招聘关键词列表，只抓取标题包含关键词的文章
        """
        # lock_path = self.base_dir / self.lock_file
        # if not self.debug and lock_path.exists():
        #     self.logger.warning(f"Lock file {lock_path} exists, another instance may be running. Exiting.")
        #     return

        # try:
        #     if not self.debug:
        #         lock_path.touch()  # 创建锁文件

        scraped_original_urls = self.get_scraped_original_urls()
        # 检查cookies是否存在，不存在则登录获取
        cookie_ts, cookies = self.read_cookies(timeout=3*24*3600)
        if cookies is None:
            cookies = await self.login_for_cookies()
            self.save_cookies(cookies)
        else:
            await self.init_cookies(cookies, go_base_url=True)

        start_time = time.time()
        with tqdm(total=len(self.authors), desc="抓取公众号", unit="个") as pbar:
            articles = await self.scrape_articles_from_authors(scraped_original_urls, max_article_num, total_max_article_num, time_range, recruitment_keywords, pbar)
        
        # 这里使用 all_articles_urls 来更新，而不是 scraped_original_urls
        all_articles_urls = [article['original_url'] for article in articles]
        self.update_scraped_articles(list(set(all_articles_urls)), articles)

        self.save_counter(start_time)
        self.update_f.close()

        # except Exception as e:
        #     self.logger.error(f"抓取出错: {e}")
        # finally:
        #     if not self.debug and lock_path.exists():
        #         lock_path.unlink()  # 删除锁文件

    async def download_article(self, article: dict, save_dir: Path = None, bot_tag: str = 'abstract', enable_abstract: bool = True) -> None:
        """下载单篇文章内容
        Args:
            article: 文章信息字典（需包含original_url）
            save_dir: 文章保存目录，如果为None则使用默认目录
            bot_tag: 机器人标签，默认为'abstract'
            enable_abstract: 是否生成摘要，默认为True
        """
        try:
            title = article.get('title', '未知标题')
            clean_title = clean_filename(title)
            original_url = article['original_url']
            
            # self.logger.debug(f"开始处理文章: {title}, URL: {original_url}")
            
            md_file = save_dir / f"{clean_title}.md"
            from etl.processors.wechat import wechatmp2md_async
            try:
                success = await wechatmp2md_async(original_url, md_file, 'url')
            except Exception as e:
                self.logger.exception(e)
            if success:
                with open(md_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                content = re.sub(r'!\[.*?\]\(.*?\)', '', content)
                content = re.sub(r'\n\s*\n', '\n', content).strip()
                if content:
                    with open(md_file, 'w', encoding='utf-8') as f:
                        f.write(content.strip())
                else:
                    self.logger.error(f"转换失败，MD文件内容为空: {md_file}")
                    return
                    
                # 根据开关决定是否生成摘要
                if enable_abstract:
                    from etl.processors import generate_abstract_async
                    try:
                        abstract = await generate_abstract_async(md_file, bot_tag=bot_tag)
                    except Exception as e:
                        self.logger.error(f"生成摘要时发生错误: {e}")
                        abstract = None
                    if abstract:
                        try:
                            # article['content'] = abstract
                            with open(save_dir / f"{clean_title}.json", 'w', encoding='utf-8') as f:
                                json.dump(article, f, ensure_ascii=False,indent=4)
                            with open(save_dir / 'abstract.md', 'w', encoding='utf-8') as f:
                                f.write(abstract)
                            self.logger.debug(f"生成摘要成功: {clean_title}")
                            preview_abstract = abstract[:100] + "..." if len(abstract) > 100 else abstract
                            self.logger.debug(f"原始URL: {original_url}\n摘要内容预览: {preview_abstract}")
                        except Exception as e:
                            self.logger.exception(e)
                    else:
                        try:
                            article['content'] = ""
                            with open(save_dir / f"{clean_title}.json", 'w', encoding='utf-8') as f:
                                json.dump(article, f, ensure_ascii=False, indent=4)
                            self.logger.debug(f"摘要生成失败，已将content置空保存: {clean_title}")
                        except Exception as e:
                            self.logger.exception(e)
                else:
                    # 不生成摘要，直接保存文章信息
                    try:
                        article['content'] = content  # 使用原始内容
                        with open(save_dir / f"{clean_title}.json", 'w', encoding='utf-8') as f:
                            json.dump(article, f, ensure_ascii=False, indent=4)
                        # self.logger.debug(f"跳过摘要生成，保存原始内容: {clean_title}")
                    except Exception as e:
                        self.logger.exception(e)
        except Exception as e:
            self.logger.exception(e)

    async def download(self, time_range: tuple = None, bot_tag: str = 'abstract', enable_abstract: bool = True):
        """下载爬取到的文章
        
        Args:
            time_range: 可选的时间范围元组 (start_date, end_date)，支持字符串('2025-01-01')或datetime对象
            bot_tag: 机器人标签，默认为'abstract'
            enable_abstract: 是否生成摘要，默认为True
        """
        # 处理时间范围
        start_date = end_date = None
        if time_range and len(time_range) == 2:
            start_date = parse_date(time_range[0])
            end_date = parse_date(time_range[1])
            
        self.logger.debug("开始下载文章...")
        data_dir = self.data_dir
        data_dir.mkdir(parents=True, exist_ok=True)
        
        # 获取可用的bot_id数量（仅在启用摘要时需要）
        if enable_abstract:
            bot_ids = get_bot_ids_by_tag(bot_tag)
            max_concurrency = len(bot_ids)
            if max_concurrency == 0:
                self.logger.error(f"没有找到可用的bot_id(标签:{bot_tag})")
                return
            self.logger.info(f"找到 {max_concurrency} 个可用的bot_id")
        else:
            # 不生成摘要时，使用更高的并发数
            max_concurrency = 10
            self.logger.info(f"摘要生成已禁用，使用并发数: {max_concurrency}")
        
        # 递归查找所有JSON文件
        json_files = list(data_dir.glob('**/*.json'))
        self.logger.debug(f"找到 {len(json_files)} 个JSON文件")
        
        if not json_files:
            self.logger.error("没有找到需要处理的文章，任务结束")
            return
        
        # 创建计数器，用于进度展示
        total_files = len(json_files)
        processed = 0
        success = 0
        skipped = 0
        failed = 0
        
        # 创建进度条
        pbar = tqdm(total=total_files, desc="下载文章", unit="篇")
        
        # 创建任务列表用于并行处理
        tasks = []
        for json_file in json_files:
            try:
                # 检查文件是否为空
                if json_file.stat().st_size == 0:
                    self.logger.warning(f"跳过空JSON文件: {json_file}")
                    skipped += 1
                    pbar.update(1)
                    continue
                    
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        article = json.load(f)
                except json.JSONDecodeError as je:
                    self.logger.warning(f"无法解析JSON文件: {json_file}, 错误: {je}")
                    failed += 1
                    pbar.update(1)
                    continue
                except UnicodeDecodeError as ue:
                    # 尝试其他编码
                    try:
                        with open(json_file, 'r', encoding='gbk') as f:
                            article = json.load(f)
                    except:
                        self.logger.warning(f"无法解码JSON文件: {json_file}, 错误: {ue}")
                        failed += 1
                        pbar.update(1)
                        continue
                
                if not isinstance(article, dict) or 'original_url' not in article:
                    self.logger.warning(f"跳过无效文章: {json_file}")
                    skipped += 1
                    pbar.update(1)
                    continue
                    
                # 检查时间范围
                if time_range and 'publish_time' in article:
                    try:
                        pub_date = datetime.strptime(article['publish_time'], '%Y-%m-%d')
                        if start_date and pub_date < start_date:
                            skipped += 1
                            pbar.update(1)
                            continue
                        if end_date and pub_date > end_date:
                            skipped += 1
                            pbar.update(1)
                            continue
                    except:
                        self.logger.warning(f"无法解析文章发布时间: {article.get('publish_time')}")
                
                # 使用文章所在目录作为保存目录
                save_dir = json_file.parent
                # 创建自定义任务，包含文件信息用于进度更新
                tasks.append((self.download_article(article, save_dir, bot_tag, enable_abstract), json_file))
            except Exception as e:
                self.logger.error(f"处理JSON文件失败: {json_file}, 错误: {e}")
                failed += 1
                pbar.update(1)
        
        # 并行执行所有下载任务，但限制并发数
        if tasks:
            self.logger.info(f"开始并行处理 {len(tasks)} 篇文章，并发数限制为{max_concurrency}")
            # 创建信号量以限制并发数
            semaphore = asyncio.Semaphore(max_concurrency)
            
            async def process_with_semaphore(task_info):
                task, json_file = task_info
                try:
                    async with semaphore:
                        result = await task
                        nonlocal success
                        success += 1
                        return result
                except Exception as e:
                    self.logger.error(f"任务执行失败: {json_file}, 错误: {e}")
                    nonlocal failed
                    failed += 1
                    return None
                finally:
                    nonlocal processed
                    processed += 1
                    # 更新进度条
                    pbar.update(1)
                    pbar.set_postfix({"成功": success, "跳过": skipped, "失败": failed})
                    
            # 用信号量包装所有任务
            limited_tasks = [process_with_semaphore(task_info) for task_info in tasks]
            
            try:
                # 并行执行任务，但受信号量限制
                await asyncio.gather(*limited_tasks)
            except Exception as e:
                self.logger.error(f"任务执行过程中发生错误: {e}")
            finally:
                # 关闭进度条
                pbar.close()
                
            self.logger.info(f"所有文章下载完成: 总数 {total_files}, 成功 {success}, 跳过 {skipped}, 失败 {failed}")
        else:
            pbar.close()
            self.logger.warning("没有有效的文章需要处理")

# 生产环境下设置debug=False！！！一定不要设置为True，debug模式没有反爬机制，很容易被封号！！！ max_article_num = 你想抓取的数量
# 调试可以设置debug=True，max_article_num <= 5
# 抓取公众号文章元信息需要cookies（高危操作），下载文章内容不需要cookies，两者分开处理

# /opt/venvs/base/bin/python '/mnt/c/Users/aokimi/Code/nkuwiki/etl/crawler/wechat.py'

if __name__ == "__main__":
    async def main():
        """异步主函数"""
        # accounts = school_official_accounts + club_official_accounts + company_accounts
        accounts = university_official_accounts + school_official_accounts + club_official_accounts + unofficial_accounts
        wechat = Wechat(authors=accounts, debug=False, headless=True, use_proxy=False)
        
        try:
            await wechat.async_init()  # 确保在调用download前初始化
            
            today_str = datetime.now().strftime('%Y-%m-%d')
            start_time = today_str
            end_time = today_str
            enable_abstract = False
            start_time = '2025-03-25'
            end_time = '2025-06-26'
            try:
                await wechat.scrape(max_article_num=1000, total_max_article_num=1e10, time_range=(start_time, end_time))
            finally:
                # 清理cookies并关闭当前页面
                if wechat.context:
                    await wechat.context.clear_cookies()
                if wechat.page and not wechat.page.is_closed():
                    await wechat.page.close()
                # 开新页面
                if wechat.context:
                    wechat.page = await wechat.context.new_page()
            
            await wechat.download(time_range=(start_time, end_time), enable_abstract=enable_abstract)
        finally:
            # 优雅地关闭浏览器和playwright资源，防止事件循环错误
            if wechat:
                await wechat.close()

    # 运行异步主函数
    asyncio.run(main())