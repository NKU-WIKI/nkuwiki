"""
爬虫模块，负责从各种数据源抓取数据
"""

# 从根模块导入共享配置
import sys
from pathlib import Path
from datetime import timedelta
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from etl import RAW_PATH, PROXY_POOL, MARKET_TOKEN
from core.utils.logger import register_logger

# 从常量模块导入所有相关常量
from etl.utils.const import (
    university_official_accounts, school_official_accounts, 
    club_official_accounts, company_accounts, unofficial_accounts,
    default_user_agents, user_agents, default_timezone, default_locale
)

# 创建爬虫模块日志器
crawler_logger = register_logger("etl.crawler")

# 为了向后兼容，保留小写的别名
proxy_pool = PROXY_POOL
market_token = MARKET_TOKEN

__all__ = [
    'crawler_logger',
    'proxy_pool', 'market_token', 
    'unofficial_accounts', 'university_official_accounts', 'school_official_accounts', 
    'club_official_accounts', 'company_accounts', 'timedelta', 'RAW_PATH', 'default_user_agents',
    'default_timezone', 'default_locale', 'user_agents'
] 