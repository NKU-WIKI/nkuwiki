"""
爬虫模块，负责从各种数据源抓取数据
"""

# 从根模块导入共享配置
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from etl import *

# crawler模块通用配置
import tempfile  
import shutil  
import pytz  
import requests  
import random  
from collections import Counter  
from playwright.sync_api import sync_playwright  
import hashlib
import hmac
import asyncio

# crawler模块通用配置
PROXY_POOL = config.get("etl.crawler.proxy_pool", "http://127.0.0.1:7897")
MARKET_TOKEN = config.get("etl.crawler.market_token", "")
UNOFFICIAL_ACCOUNTS = config.get("etl.crawler.accounts.unofficial_accounts", "")
UNIVERSITY_OFFICIAL_ACCOUNTS = config.get("etl.crawler.accounts.university_official_accounts", "")
SCHOOL_OFFICIAL_ACCOUNTS = config.get("etl.crawler.accounts.school_official_accounts", "")
CLUB_OFFICIAL_ACCOUNTS = config.get("etl.crawler.accounts.club_official_accounts", "")
os.environ["UNOFFICIAL_ACCOUNTS"] = UNOFFICIAL_ACCOUNTS
os.environ["UNIVERSITY_OFFICIAL_ACCOUNTS"] = UNIVERSITY_OFFICIAL_ACCOUNTS
os.environ["SCHOOL_OFFICIAL_ACCOUNTS"] = SCHOOL_OFFICIAL_ACCOUNTS
os.environ["CLUB_OFFICIAL_ACCOUNTS"] = CLUB_OFFICIAL_ACCOUNTS

# 浏览器配置
DEFAULT_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36"
DEFAULT_TIMEZONE = "Asia/Shanghai"
DEFAULT_LOCALE = "zh-CN"

# 创建crawler模块专用logger
crawler_logger = logger.bind(module="crawler")
log_path = LOG_PATH / "crawler.log"
log_format = "{time:YYYY-MM-DD HH:mm:ss} | {level} | {module} | {message}"
logger.configure(
    handlers=[
        {"sink": sys.stdout, "format": log_format},
        {"sink": log_path, "format": log_format, "rotation": "1 day", "retention": "3 months", "level": "INFO"},
    ]
)

def clean_filename(filename):
    """清理文件名，使其符合Windows和Linux文件系统规范，只保留汉字和字母"""
    # 只保留汉字和字母，删除其他所有字符
    clean_name = re.sub(r'[^\u4e00-\u9fa5a-zA-Z]', '', filename)

    # 确保文件名不为空
    if not clean_name:
        clean_name = 'untitled'

    # 限制文件名长度（考虑中文字符）
    while len(clean_name.encode('utf-8')) > 200:
        clean_name = clean_name[:-1]

    return clean_name

__all__ = [
    'datetime', 'sys', 'Path', 'os', 're', 'pytz', 'json', 'time', 'requests', 'random', 
    'crawler_logger', 'Counter', 'tempfile', 'shutil', 'sync_playwright', 'config', 'Dict', 'List', 'clean_filename',
    'Optional', 'Any', 'hashlib', 'hmac', 'asyncio', 'PROXY_POOL', 'MARKET_TOKEN', 
    'UNOFFICIAL_ACCOUNTS', 'UNIVERSITY_OFFICIAL_ACCOUNTS', 'SCHOOL_OFFICIAL_ACCOUNTS', 
    'CLUB_OFFICIAL_ACCOUNTS', 'timedelta', 'RAW_PATH', 'LOG_PATH',
    'BASE_PATH', 'DEFAULT_USER_AGENT', 'DEFAULT_TIMEZONE', 'DEFAULT_LOCALE'
] 