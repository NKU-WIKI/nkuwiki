import os  # 导入操作系统模块，用于处理文件和目录
import sys  # 导入系统模块，用于处理系统相关的操作
from pathlib import Path  # 导入Path类，用于处理文件路径
sys.path.append(str(Path(__file__).resolve().parent.parent))  # 将当前文件的父目录的父目录添加到系统路径中
import re  # 导入正则表达式模块，用于处理字符串匹配
import pytz  # 导入时区模块，用于处理时区相关的操作
import json  # 导入JSON模块，用于处理JSON数据
import time  # 导入时间模块，用于处理时间相关的操作
from datetime import datetime  # 导入datetime类，用于处理日期和时间
from dotenv import load_dotenv # 导入dotenv模块，用于加载环境变量
import requests  # 导入requests模块，用于发送HTTP请求
import random  # 导入随机数模块，用于生成随机数
from loguru import logger  # 导入loguru模块，用于日志记录
from collections import Counter  # 导入Counter类，用于计数
import pdfplumber  # 导入pdfplumber模块，用于处理PDF文件
from PyPDF2 import PdfWriter, PdfReader  # 导入PyPDF2模块，用于处理PDF文件
from selenium import webdriver  # 导入webdriver模块，用于自动化浏览器操作
from selenium.webdriver.chrome.options import Options  # 导入Chrome浏览器选项模块
from selenium.webdriver.common.by import By  # 导入By类，用于定位元素
from selenium.webdriver.support.ui import WebDriverWait  # 导入WebDriverWait类，用于等待元素加载
from selenium.webdriver.support import expected_conditions as EC  # 导入expected_conditions模块，用于等待条件

# find_element(By.XPATH)  # 通过XPath定位元素
# find_element(By.CSS_SELECTOR)  # 通过CSS选择器定位元素
# find_element(By.ID)  # 通过ID定位元素
# find_element(By.TAG_NAME)  # 通过标签名定位元素
# find_element(By.CLASS_NAME)  # 通过类名定位元素
# find_element(By.PARTIAL_LINK_TEXT)  # 通过部分链接文本定位元素
# find_element(By.LINK_TEXT)  # 通过链接文本定位元素
# find_element(By.NAME)  # 通过名称定位元素

# 爬虫类
class Crawler():
    def __init__(self, name, debug = False, headless = True):
        """
        传入名称、是否调试模式、是否无头模式
        """
        self.debug = debug
        self.headless = headless
        log_day_str = '{time:%Y-%m-%d}'
        if(self.debug):
            self.base_data_dir = str(Path(__file__).resolve().parent.parent) + '/data/' # 本地调试数据目录
        else:
            self.base_data_dir = '/data/'# 初始化数据目录
        self.base_log_dir = str(Path(__file__).resolve().parent.parent) + '/logs/' # 日志目录  
        self.process_name = name
        self.content_type = name
        logger.add(f'{self.base_log_dir}/{self.process_name}.{log_day_str}.log', rotation="1 day", retention='3 months', level="INFO")# 配置日志记录器
        self.logger = logger
        self.base_dir = Path(self.base_data_dir) / self.content_type
        self.base_dir.mkdir(exist_ok=True, parents=True)  # 创建目录，如果目录不存在
        self.counter = Counter()  # 初始化计数器
        self.lock_file = 'lock.txt'  # 锁文件，用于防止重复运行
        self.counter_file = 'counter.txt'  # 计数器文件，用于记录运行统计
        self.update_file = 'update.txt'  # 更新文件，用于记录更新信息
        self.update_f = open(self.base_dir / self.update_file, 'a+', encoding='utf-8')  # 打开更新文件
        self.scraped_file = 'scraped.json'  # 已抓取记录文件
        self.cookies_file = 'cookies.txt'  # cookies文件，用于保存登录信息
        self.tz = pytz.timezone('Asia/Shanghai')  # 设置时区
        chrome_options = Options()  # 初始化Chrome浏览器选项
        prefs = {
            "download.prompt_for_download": True,  # 下载前提示
            "download.directory_upgrade": True,
            "plugins.always_open_pdf_externally": False  # 禁用自动打开PDF
        }
        chrome_options.add_experimental_option("prefs", prefs)  # 添加浏览器选项
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')#绕过无头模式检测
        if headless:
            chrome_options.add_argument('--headless=new')  # Chrome 112+ 推荐的无头模式
        else:
            pass
        chrome_options.add_argument(f"--window-size=3840x2160")  # 设置窗口大小
        self.driver = webdriver.Chrome(options=chrome_options)  # 初始化Chrome浏览器驱动
        self.driver.maximize_window()  # 最大化窗口
        self.wait = WebDriverWait(self.driver, 30)  # 初始化等待对象，超时时间为30秒
        self.min_sleep_microsec = 3000  # 最小休眠时间
        self.max_sleep_microsec = 8000  # 最大休眠时间
        self.max_retry = 5  # 最大重试次数
        self.login_url = self.base_url  # 登录URL
        self.wait = WebDriverWait(self.driver, 10)  # 设置等待时间
        # 请求头
        self.headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Connection': 'keep-alive',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36',
            'sec-ch-ua': '"Chromium";v="116", "Not)A;Brand";v="24", "Google Chrome";v="116"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
        }
    """
    通用函数
    """
    def random_sleep(self):
        if(self.debug): 
            pass
        else:
            # 随机休眠一段时间
            time.sleep(random.randint(self.min_sleep_microsec, self.max_sleep_microsec)/1000.0)

    def read_cookies(self, timeout=6*3600):
        # 从文件中读取cookies
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
    
    def save_cookies(self, cookies):
        # 保存cookies到文件
        f = self.base_dir / self.cookies_file
        now_ts = int(time.time())
        lines = f'{now_ts}\n'
        for k, v in cookies.items():
            lines += f'{k}: {v}\n'
        f.write_text(lines) 

    def init_cookies(self, cookies, go_base_url=False):
        # 初始化cookies
        try:
            self.driver.get(self.cookie_init_url)  # 打开初始化cookies的URL
            self.counter['visit'] += 1  # 访问计数器加1
            self.random_sleep()  # 随机休眠
            for name, value in cookies.items():
                cookie_dict = {'name': name, 'value': value}
                self.driver.add_cookie(cookie_dict)  # 添加cookies
                self.random_sleep()  # 随机休眠
            if go_base_url:
                self.driver.get(self.base_url)  # 打开基础URL
                self.counter['visit'] += 1  # 访问计数器加1
                self.random_sleep()  # 随机休眠
        except Exception as e:
            self.counter['error'] += 1  # 错误计数器加1
            self.logger.error(e)  # 记录错误日志

    def save_scraped_records(self, add_scraped_links):
        # 保存已抓取链接
        total_f = self.base_dir / self.scraped_file
        scraped_records = self.get_scraped_records()
        scraped_records = list(set(scraped_records) | set(add_scraped_links))  # 合并已抓取链接
        try:
            total_f.write_text(json.dumps(scraped_records, ensure_ascii=False, indent=0))  # 写入已抓取链接
        except Exception as e:
            self.counter['error'] += 1  # 错误计数器加1
            self.logger.error(e)  # 记录错误日志

    def get_scraped_records(self):
        # 获取已抓取链接
        total_f = self.base_dir / self.scraped_file
        if total_f.exists():
            content = total_f.read_text()
            if len(content) > 0:  
                try:
                    return json.loads(content)  # 返回已抓取链接
                except:
                    pass
        return []

    def save_counter(self, start_time):
        # 保存计数器
        path = self.base_dir / self.counter_file
        with path.open('a+', encoding='utf-8') as h:
            visit = self.counter.get('visit', 0)
            download = self.counter.get('download', 0)
            error = self.counter.get('error', 0)
            noneed = self.counter.get('noneed', 0)
            time_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            used_time = int(time.time() - start_time)
            self.logger.info(f'#summary# {used_time}s, visit: {visit}, error: {error}, download: {download}, noneed: {noneed}')  # 记录日志
            h.write(f'{time_str},{used_time},{visit},{error},{download},{noneed}\n')  # 写入计数器文件
          
  

    def remove_disclosures(self, pdf_path, match):
        """
        使用 pdfplumber 检查文本，使用 PyPDF2 修改并保存 PDF。
        """
        try:
            # 提取文本以找到 match 起始页
            start_deleting_from = None
            with pdfplumber.open(pdf_path) as pdf:
                for i, page in enumerate(pdf.pages):
                    text = page.extract_text()
                    if match in text:
                        start_deleting_from = i
                        break

            # 如果找到 match，删除相应页面
            if start_deleting_from is not None:
                reader = PdfReader(pdf_path)
                writer = PdfWriter()
                for i in range(start_deleting_from):
                    writer.add_page(reader.pages[i])

                with open(pdf_path, "wb") as f:
                    writer.write(f)
        except Exception as e:
            self.counter['error'] += 1  # 错误计数器加1
            self.logger.error(f"An error occurred while cleaning {pdf_path}: {e}")  # 记录错误日志
            
    def remove_disclosures(self, pdf_path):
        """
        使用 pdfplumber 检查文本，使用 PyPDF2 修改并保存 PDF。
        """
        try:
            # 提取文本以找到 "Required Disclosures" 起始页
            start_deleting_from = None
            with pdfplumber.open(pdf_path) as pdf:
                for i, page in enumerate(pdf.pages):
                    text = page.extract_text()
                    if "Required Disclosures" in text:
                        start_deleting_from = i
                        break

            # 如果找到 "Required Disclosures"，删除相应页面
            if start_deleting_from is not None:
                reader = PdfReader(pdf_path)
                writer = PdfWriter()
                for i in range(start_deleting_from):
                    writer.add_page(reader.pages[i])

                with open(pdf_path, "wb") as f:
                    writer.write(f)
        except Exception as e:
            self.counter['error'] += 1  # 错误计数器加1
            self.logger.error(f"An error occurred while cleaning {pdf_path}: {e}")  # 记录错误日志

    def save_metadata(self, article):
        # 生成存储路径
        save_dir = self.base_dir / article['publish_time'].strftime("%Y-%m")
        save_dir.mkdir(exist_ok=True, parents=True)
        save_path = save_dir / f"{article['title']}_{article['publish_time'].strftime('%Y%m%d%H%M')}"
        
        meta = {
            "url": article.get('url'), 
            "nickname": article['nickname'],
            "publish_time": article['publish_time'].strftime("%Y-%m-%d"),
            "publish_time_detail": article['publish_time'].isoformat(),
            "run_time": datetime.now().isoformat(),
            "title": article['title'],
            "author": article.get('author'),
            "read_count": article.get('read_count', 0),
            "like_count": article.get('like_count', 0),
            "content_type": self.content_type,
            "file_path": str(save_path)
        }
        with open(save_path.with_suffix('.meta.json'), 'w', encoding='utf-8') as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)