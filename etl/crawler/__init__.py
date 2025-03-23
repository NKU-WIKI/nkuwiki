"""
爬虫模块，负责从各种数据源抓取数据
"""

# 从根模块导入共享配置
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from etl import *
from core.utils.logger import get_module_logger

# crawler模块专用配置
import tempfile  
import shutil  
import pytz  
import requests  
import random  
from collections import Counter  
from playwright.async_api import async_playwright  
import hashlib
import hmac
from urllib.parse import urlparse

PROXY_POOL = config.get("etl.crawler.proxy_pool", "http://127.0.0.1:7897")
MARKET_TOKEN = config.get("etl.crawler.market_token", "")
UNOFFICIAL_ACCOUNTS = config.get("etl.crawler.accounts.unofficial_accounts", "")
UNIVERSITY_OFFICIAL_ACCOUNTS = config.get("etl.crawler.accounts.university_official_accounts", "")
SCHOOL_OFFICIAL_ACCOUNTS = config.get("etl.crawler.accounts.school_official_accounts", "")
CLUB_OFFICIAL_ACCOUNTS = config.get("etl.crawler.accounts.club_official_accounts", "")
COMPANY_ACCOUNTS = config.get("etl.crawler.accounts.company_accounts", "")

# 浏览器配置
DEFAULT_USER_AGENTS = [
    # Windows Chrome
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
    # Mac Chrome
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
    # Safari
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.1 Safari/605.1.15",
    # Firefox
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/116.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/117.0",
    # Edge
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36 Edg/116.0.1938.69",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36 Edg/116.0.1938.62",
    # Mobile
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 13; SM-S908B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Mobile Safari/537.36"
]
DEFAULT_TIMEZONE = "Asia/Shanghai"
DEFAULT_LOCALE = "zh-CN"

# 创建crawler模块专用logger
crawler_logger = get_module_logger("etl.crawler")

def clean_filename(filename):
    """清理文件名，使其符合Windows和Linux文件系统规范，只保留汉字和字母"""
    clean_name = re.sub(r'[^\u4e00-\u9fa5a-zA-Z]', '', filename)

    # 确保文件名不为空
    if not clean_name:
        clean_name = 'untitled'

    # 限制文件名长度（考虑中文字符）
    while len(clean_name.encode('utf-8')) > 200:
        clean_name = clean_name[:-1]

    return clean_name

def parse_date(date_str):
    """解析日期字符串为datetime对象
    
    Args:
        date_str: 日期字符串('2025-01-01')或datetime对象
        
    Returns:
        datetime对象或None（如果解析失败）
    """
    if isinstance(date_str, datetime):
        return date_str
    try:
        return datetime.strptime(date_str, '%Y-%m-%d')
    except:
        return None

__all__ = [
    'datetime', 'sys', 'Path', 'os', 're', 'pytz', 'json', 'time', 'requests', 'random', 'urlparse','tqdm',
    'crawler_logger', 'Counter', 'tempfile', 'shutil', 'async_playwright', 'config', 'Dict', 'List', 'clean_filename','parse_date',
    'Optional', 'Any', 'hashlib', 'hmac', 'asyncio', 'PROXY_POOL', 'MARKET_TOKEN', 
    'UNOFFICIAL_ACCOUNTS', 'UNIVERSITY_OFFICIAL_ACCOUNTS', 'SCHOOL_OFFICIAL_ACCOUNTS', 
    'CLUB_OFFICIAL_ACCOUNTS', 'COMPANY_ACCOUNTS', 'timedelta', 'RAW_PATH', 'LOG_PATH',
    'BASE_PATH', 'DEFAULT_USER_AGENTS', 'DEFAULT_TIMEZONE', 'DEFAULT_LOCALE'
] 