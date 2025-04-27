"""
转换模块，负责数据格式转换和处理
"""
from etl import BASE_PATH, RAW_PATH, CACHE_PATH, config
from core.utils import register_logger
# 转换配置
HTML_TAGS_PATTERN = r'<.*?>'
SPECIAL_CHARS_PATTERN = r'[^\w\s\u4e00-\u9fff]'
MAX_TEXT_LENGTH = config.get('etl.transform.max_text_length', 1000000)
MIN_TEXT_LENGTH = config.get('etl.transform.min_text_length', 10)

# 创建转换模块专用logger
logger = register_logger("etl.transform")

# 定义导出的变量和函数
__all__ = [
    # 路径配置
    'BASE_PATH', 'RAW_PATH', 'CACHE_PATH',
    'logger',
    # 转换配置
    'HTML_TAGS_PATTERN', 'SPECIAL_CHARS_PATTERN', 'MAX_TEXT_LENGTH', 'MIN_TEXT_LENGTH'
]