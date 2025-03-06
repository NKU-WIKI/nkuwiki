"""
示例模块，展示如何在模块文件中使用共享的logger实例
"""
from __init__ import *

class ExampleCrawler:
    """示例爬虫类，演示日志使用"""
    
    def __init__(self, name):
        self.name = name
        self.logger = crawler_logger.bind(crawler=name)
        
    def crawl(self, url):
        """模拟爬取过程"""
        try:
            # 使用模块共享的logger实例
            self.logger.info(f"开始爬取: {url}")
            
            # 模拟操作过程
            self.logger.debug(f"使用代理: {PROXY_POOL}")
            
            # 模拟成功
            self.logger.success(f"成功爬取: {url}")
            return {"url": url, "status": "success"}
            
        except Exception as e:
            # 错误日志
            self.logger.error(f"爬取失败: {url} - {str(e)}")
            return {"url": url, "status": "failed"}
            
    def save_data(self, data, path=None):
        """模拟保存数据"""
        if path is None:
            path = BASE_PATH / "sample_data.json"
            
        self.logger.info(f"保存数据到: {path}")
        
        # 模拟错误处理
        try:
            # 实际保存逻辑
            pass
        except Exception as e:
            self.logger.warning(f"保存数据警告: {str(e)}")
            
        self.logger.success(f"数据保存完成: {len(data)} 条记录")


def main():
    """示例函数"""
    crawler_logger.info("初始化爬虫...")
    crawler = ExampleCrawler("Demo")
    
    urls = ["https://example.com", "https://test.com"]
    for url in urls:
        crawler_logger.info(f"处理URL: {url}")
        result = crawler.crawl(url)
        
    crawler_logger.success("爬取任务完成")
    
    
if __name__ == "__main__":
    main() 