"""
数据处理器模块

整合了文档处理、文本转换、分割和压缩等核心数据处理功能：
- 文档解析和转换
- 文本分割和层次化处理  
- 上下文压缩
- 节点工具
"""

from etl import BASE_PATH, RAW_PATH, CACHE_PATH, config
from core.utils import register_logger

# 从常量模块导入处理相关常量
from etl.utils.const import (
    html_tags_pattern, special_chars_pattern, 
    max_text_length, min_text_length, default_batch_size
)

# 导入核心处理器
from .document import DocumentProcessor
from .text import TextSplitter, HierarchicalNodeParser
from .compress import ContextCompressor
from .nodes import get_node_content, merge_strings, extract_node_metadata, generate_doc_id
from .wechat import WechatProcessor, wechatmp2md, wechatmp2md_async
from .abstract import AbstractProcessor, generate_abstract, generate_abstract_async
from .summarize import SummarizeProcessor, summarize_markdown_file, summarize_markdown_directory
from .utils import (
    DataTransformationProcessor, 
    OCRDataProcessor,
    merge_json_files,
    transform_data_format,
    preprocess_text_data,
    extract_ocr_data
)

# 创建模块专用logger
logger = register_logger("etl.processors")

# 定义导出
__all__ = [
    # 路径配置
    'BASE_PATH', 'RAW_PATH', 'CACHE_PATH',
    'logger',
    # 处理器配置
    'html_tags_pattern', 'special_chars_pattern', 'max_text_length', 'min_text_length', 'default_batch_size',
    # 核心处理器
    'DocumentProcessor',
    'TextSplitter', 'HierarchicalNodeParser',
    'ContextCompressor',
    'WechatProcessor',
    # 节点工具
    'get_node_content', 'merge_strings', 'extract_node_metadata', 'generate_doc_id',
    # 微信处理向后兼容函数
    'wechatmp2md', 'wechatmp2md_async',
    # 摘要生成
    'AbstractProcessor', 'generate_abstract', 'generate_abstract_async',
    'SummarizeProcessor', 'summarize_markdown_file', 'summarize_markdown_directory',
    # 通用数据处理
    'DataTransformationProcessor', 'OCRDataProcessor',
    'merge_json_files', 'transform_data_format', 'preprocess_text_data', 'extract_ocr_data'
] 