"""
爬虫模块，负责从各种数据源抓取数据
"""

# 从根模块导入共享配置
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from etl import config, etl_logger, RAW_PATH, DATA_PATH
from core.utils.logger import register_logger

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
import os
import re
import time
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

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
crawler_logger = register_logger("etl.crawler")

# 代理池配置
PROXY_LIST = config.get("crawler.proxy_list", [])
USE_PROXY = config.get("crawler.use_proxy", False)

# 市场账号token
MARKET_TOKENS = config.get("crawler.market_tokens", {})

# 用户代理配置
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1",
]

def clean_filename(filename: str) -> str:
    """清理文件名，移除不合法字符
    
    Args:
        filename: 原始文件名
        
    Returns:
        清理后的文件名
    """
    # 移除Windows和Linux中不允许的文件名字符
    illegal_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
    for char in illegal_chars:
        filename = filename.replace(char, '_')
    
    # 限制文件名长度，避免路径过长问题
    if len(filename) > 200:
        filename = filename[:197] + '...'
        
    return filename

def parse_date(date_str: str) -> datetime:
    """将字符串解析为日期对象
    
    支持多种常见格式如：
    - 2023年5月1日
    - 2023-05-01
    - 05/01/2023
    - 昨天、前天等相对日期
    
    Args:
        date_str: 日期字符串
        
    Returns:
        解析后的datetime对象
    """
    date_str = date_str.strip()
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    
    # 处理相对日期
    if '刚刚' in date_str or '分钟前' in date_str:
        minutes = 0
        if '分钟前' in date_str:
            try:
                minutes = int(re.search(r'(\d+)分钟前', date_str).group(1))
            except:
                minutes = 10  # 默认10分钟前
        return datetime.now() - timedelta(minutes=minutes)
    elif '小时前' in date_str:
        try:
            hours = int(re.search(r'(\d+)小时前', date_str).group(1))
        except:
            hours = 1  # 默认1小时前
        return datetime.now() - timedelta(hours=hours)
    elif '昨天' in date_str:
        return today - timedelta(days=1)
    elif '前天' in date_str:
        return today - timedelta(days=2)
    
    # 尝试不同格式解析
    date_formats = [
        '%Y年%m月%d日',
        '%Y-%m-%d',
        '%Y/%m/%d',
        '%m/%d/%Y',
        '%d/%m/%Y',
        '%Y.%m.%d',
    ]
    
    for fmt in date_formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
            
    # 无法解析时返回当天
    crawler_logger.warning(f"无法解析日期格式: {date_str}，使用当前日期")
    return today

__all__ = [
    'datetime', 'sys', 'Path', 'os', 're', 'pytz', 'json', 'time', 'requests', 'random', 'urlparse','tqdm',
    'crawler_logger', 'Counter', 'tempfile', 'shutil', 'async_playwright', 'config', 'Dict', 'List', 'clean_filename','parse_date',
    'Optional', 'Any', 'hashlib', 'hmac', 'asyncio', 'PROXY_POOL', 'MARKET_TOKEN', 
    'UNOFFICIAL_ACCOUNTS', 'UNIVERSITY_OFFICIAL_ACCOUNTS', 'SCHOOL_OFFICIAL_ACCOUNTS', 
    'CLUB_OFFICIAL_ACCOUNTS', 'COMPANY_ACCOUNTS', 'timedelta', 'RAW_PATH', 'LOG_PATH',
    'BASE_PATH', 'DEFAULT_USER_AGENTS', 'DEFAULT_TIMEZONE', 'DEFAULT_LOCALE',
    'PROXY_LIST', 'USE_PROXY', 'MARKET_TOKENS', 'USER_AGENTS'
] 