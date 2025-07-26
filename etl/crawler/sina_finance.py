import os
import re
import json
import time
from datetime import datetime
from pathlib import Path
from etl.utils.file import clean_filename
from etl.utils.date import parse_date
from .__init__ import crawler_logger

class SinaFinance(BaseCrawler):
    """新浪财经国内新闻爬虫
    
    Attributes:
        debug: 调试模式开关
        headless: 是否使用无头浏览器模式
    """
    def __init__(self, debug: bool = False, headless: bool = False, use_proxy: bool = False) -> None:
        self.platform = "sina_finance"
        self.content_type = "news"
        self.base_url = "https://finance.sina.com.cn/china"
        super().__init__(platform=self.platform, debug=debug, headless=headless, use_proxy=use_proxy)
        self.page = self.context.new_page()
        self.inject_anti_detection_script()

    def scrape_news(self, scraped_original_urls: list, max_news_num: int = 50) -> list[dict]:
        """抓取国内新闻列表
        
        Args:
            scraped_urls: 已抓取链接集合（用于去重）
            max_news_num: 最大抓取数量
            
        Returns:
            包含新闻信息的字典列表，格式:
            [{
                'title': 新闻标题,
                'original_url': 新闻链接,
            }]
        """
        self.page.goto(self.base_url)
        self.random_sleep()
        # time.sleep(5)
        # homepage = self.page.get_by_text('财经首页')
        # homepage.click()
        # time.sleep(5)
        # self.page.keyboard.press('Control+L')  # Windows/Linux
        # self.page.keyboard.type(self.base_url + '/china')
        # self.page.keyboard.press('Enter')
        # self.page.wait_for_load_state('networkidle')
        # self.page.get_by_text('宏观经济').click()
        page = 1
        num = 0
        news = []
        while(num < max_news_num):
            try:
                time.sleep(0.2)
                # self.page.get_by_text('下一页').wait_for(
                #     state="visible",
                #     timeout=10000  # 10秒超时
                # )
                next_page = self.page.get_by_text('下一页')
            except Exception as e:
                self.logger.exception(f"{e}")
                break

            news_items = self.page.query_selector_all('h2 > a[href]')
            
            for item in news_items:
                title = item.inner_text().strip()
                original_url = item.get_attribute('href')
                if original_url not in scraped_original_urls:
                    news.append({
                        'title': title,
                        'original_url': original_url,
                    })
            try:
                next_page.click()
            except Exception as e:
                self.logger.exception(f"{e}")
                break
            page += 1

            if(page % 100 == 0):
                self.update_scraped_articles(scraped_original_urls, news)
                self.logger.info(f"爬到第 {page} 页，新抓取 {len(news)} 条新新闻")
                num += len(news)
                news = []
         

    def download_article(self, article: dict) -> dict:
        """下载单篇新闻内容
        
        Args:
            article: 包含url等信息的新闻字典
            
        Returns:
            包含完整内容的新闻字典
        """
        try:
            self.page.goto(article['original_url'])
            
            # 提取所有段落内容（包含子元素文本）
            article_div = self.page.query_selector('div[class="article"]')
            paragraphs = article_div.query_selector_all('p') if article_div else []
            content = "\n".join([
                p.inner_text().strip() 
                for p in paragraphs 
                if p.inner_text().strip()
            ]) if paragraphs else ""
            
            # 提取发布时间（根据实际页面结构调整选择器）
            publish_time_element = self.page.query_selector('span.date')
            publish_time = publish_time_element.inner_text().strip() if publish_time_element else ""
            
            # 格式转换（示例格式："2024年03月15日 10:30" -> "2024-03-15"）
            if publish_time:
                try:
                    # 处理不同时间格式
                    for fmt in ('%Y年%m月%d日 %H:%M', '%Y-%m-%d %H:%M'):
                        try:
                            dt = datetime.strptime(publish_time, fmt)
                            publish_time = dt.strftime("%Y-%m-%d")
                            break
                        except ValueError:
                            continue
                except Exception as e:
                    self.logger.warning(f"时间格式解析失败: {publish_time} - {str(e)}")
                    publish_time = ""  # 解析失败时置空
            
            # 补充元数据
            article['content'] = content
            article['publish_time'] = publish_time
            
            return article
            
        except Exception as e:
            self.logger.error(f"下载新闻内容失败: {article['original_url']} - {str(e)}")
            return article

    def scrape(self, max_news_num: int = 50) -> None:
        """执行完整爬取流程
        
        Args:
            max_news_num: 最大抓取数量
        """
        try:
            scraped_original_urls = self.get_scraped_original_urls()
            self.scrape_news(scraped_original_urls, max_news_num)
        except Exception as e:
            self.logger.error(f"爬取流程异常: {str(e)}")
        finally:
            self.context.close()
    

    def download(self):
        """下载并补充文章内容及发布时间"""
        import json
        from pathlib import Path
        
        data_dir = Path(self.base_dir)
        processed_count = 0
        
        # 递归查找所有JSON文件
        for json_path in data_dir.glob('**/*.json'):
            # 跳过以scraped开头的文件
            if json_path.name.startswith('scraped'):
                continue
            
            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    article_data = json.load(f)
                
                # 强制重新处理所有文章
                if article_data.get('content', '') != '' and article_data.get('publish_time', '') != '':  # 取消跳过条件
                    continue
                    
                # 调用下载方法
                updated_article = self.download_article(article_data)
                
                # 更新数据
                article_data.update({
                    'content': updated_article.get('content', ''),
                    'publish_time': updated_article.get('publish_time', '')
                })
                
                # 写回文件
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(article_data, f, ensure_ascii=False, indent=4)
                    
                processed_count += 1
                self.logger.debug(f"成功更新：{json_path}")
                self.logger.debug(f"更新内容：{json_path}\n"
                                     f"标题：{article_data.get('title')}\n"
                                     f"发布时间：{article_data['publish_time']}\n"
                                     f"内容摘要：{article_data['content'][:50]}...")
                
                if(processed_count % 100 == 0):
                    self.logger.info(f"已处理 {processed_count} 篇文章")
                
            except Exception as e:
                self.logger.error(f"处理文件 {json_path} 失败: {str(e)}")
        
        self.logger.info(f"下载完成，共处理 {processed_count} 篇文章")

if __name__ == "__main__":
    crawler = SinaFinance(debug=True, headless=True)
    # crawler.scrape(max_news_num=1e11)
    crawler.download()
