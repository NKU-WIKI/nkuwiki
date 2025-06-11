"""
爬虫模块，负责从各种数据源抓取数据
"""

# 从根模块导入共享配置
import sys
from pathlib import Path
from datetime import timedelta
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from etl import config, RAW_PATH, DATA_PATH
from core.utils.logger import register_logger

# 从常量模块导入所有相关常量
from etl.utils.const import (
    university_official_accounts, school_official_accounts, 
    club_official_accounts, company_accounts, unofficial_accounts,
    default_user_agents, user_agents, default_timezone, default_locale
)

# 创建爬虫模块日志器
crawler_logger = register_logger("etl.crawler")

# 爬虫配置从config读取
proxy_pool = config.get("etl.crawler.proxy_pool", "http://127.0.0.1:7897")
market_token = config.get("etl.crawler.market_token", "")

__all__ = [
    'crawler_logger', 'config',
    'proxy_pool', 'market_token', 
    'unofficial_accounts', 'university_official_accounts', 'school_official_accounts', 
    'club_official_accounts', 'company_accounts', 'timedelta', 'RAW_PATH', 'default_user_agents',
    'default_timezone', 'default_locale', 'user_agents'
] 