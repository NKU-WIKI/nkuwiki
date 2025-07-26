"""
字符串工具模块
提供字符串分割、处理等基础字符串操作函数
"""
import re
from typing import List


def split_string_by_utf8_length(s: str, max_length: int, encoding: str = 'utf-8', max_split: int = -1) -> List[str]:
    """
    按照UTF-8编码长度分割字符串，确保每个分割后的部分不会破坏UTF-8编码
    
    Args:
        s: 要分割的字符串
        max_length: 每部分的最大字节长度
        encoding: 编码方式，默认为'utf-8'
        max_split: 最大分割次数，-1表示不限制
        
    Returns:
        分割后的字符串列表
    """
    encoded = s.encode(encoding)
    parts = []
    split_count = 0
    while encoded:
        if max_split != -1 and split_count >= max_split:
            parts.append(encoded.decode(encoding))
            break
        part = encoded[:max_length]
        while True:
            try:
                part.decode(encoding)
                break
            except UnicodeDecodeError:
                part = part[:-1]
        parts.append(part.decode(encoding))
        encoded = encoded[len(part):]
        split_count += 1
    return parts


def remove_markdown_symbol(text: str) -> str:
    """
    移除Markdown格式符号
    
    Args:
        text: 包含Markdown格式的文本
        
    Returns:
        移除Markdown格式后的文本
    """
    if not text:
        return text
    # 移除常见的Markdown格式标记
    md_chars = r'*_~`#<>[]{}\|'
    return re.sub(f'[{re.escape(md_chars)}]', '', text)


def remove_markdown_format(text: str) -> str:
    """
    移除Markdown格式，保留文本内容
    
    Args:
        text: 包含Markdown格式的文本
        
    Returns:
        移除Markdown格式后的文本
    """
    if not text:
        return text
    
    # 替换Markdown的粗体、斜体、代码等格式
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)  # 粗体
    text = re.sub(r'\*(.*?)\*', r'\1', text)      # 斜体
    text = re.sub(r'__(.*?)__', r'\1', text)      # 粗体
    text = re.sub(r'_(.*?)_', r'\1', text)        # 斜体
    text = re.sub(r'`(.*?)`', r'\1', text)        # 行内代码
    
    # 去除标题标记
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
    
    # 去除链接外部括号，保留链接文本和URL
    text = re.sub(r'\[(.*?)\]\((https?://[^\s\)]+)\)', r'\1 \2', text)
    
    # 去除图片标记，只保留描述文本
    text = re.sub(r'!\[(.*?)\]\(.*?\)', r'\1', text)
    
    return text 