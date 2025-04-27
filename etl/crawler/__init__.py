"""
爬虫模块，负责从各种数据源抓取数据
"""

# 从根模块导入共享配置
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from etl import config, RAW_PATH, DATA_PATH
from core.utils.logger import register_logger
crawler_logger = register_logger("etl.crawler")

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

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1",
]

__all__ = [
    'crawler_logger', 'config',
    'PROXY_POOL', 'MARKET_TOKEN', 
    'UNOFFICIAL_ACCOUNTS', 'UNIVERSITY_OFFICIAL_ACCOUNTS', 'SCHOOL_OFFICIAL_ACCOUNTS', 
    'CLUB_OFFICIAL_ACCOUNTS', 'COMPANY_ACCOUNTS', 'timedelta', 'RAW_PATH', 'DEFAULT_USER_AGENTS',
    'DEFAULT_TIMEZONE', 'DEFAULT_LOCALE', 'USER_AGENTS'
] 