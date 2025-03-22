import os
import logging
import tempfile
import requests
import json
from typing import Dict, Any, List, Optional
import datetime

from etl.embedding.ingestion import embed_document
from etl.embedding.hierarchical import create_document_hierarchy
from etl.load.json2mysql import store_document_metadata
from etl.utils.wx_cloud import wx_cloud

# 设置日志记录器
logger = logging.getLogger(__name__)

def index_document(file_path: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    为本地文档文件建立索引
    
    Args:
        file_path: 本地文件路径
        metadata: 文档元数据
    
    Returns:
        字典，包含索引结果
    """
    try:
        metadata = metadata or {}
        
        # 检查文件是否存在
        if not os.path.exists(file_path):
            return {
                "success": False,
                "message": f"文件不存在: {file_path}"
            }
            
        # 解析文件名和扩展名
        filename = os.path.basename(file_path)
        _, ext = os.path.splitext(filename)
        
        # 设置默认元数据
        if "title" not in metadata:
            metadata["title"] = filename
        
        if "source" not in metadata:
            metadata["source"] = "local_upload"
            
        if "created_at" not in metadata:
            metadata["created_at"] = datetime.datetime.now().isoformat()
        
        # 处理文档
        logger.debug(f"开始处理文档: {filename}")
        
        # 建立文档层次结构
        doc_hierarchy = create_document_hierarchy(file_path)
        
        # 嵌入文档
        document_id, chunks = embed_document(doc_hierarchy, metadata)
        
        # 存储文档元数据到MySQL
        store_document_metadata(document_id, metadata)
        
        # 获取关键词建议
        keywords = extract_keywords(doc_hierarchy.get("text", ""), max_keywords=5)
        
        return {
            "success": True,
            "message": "文档索引成功",
            "document_id": document_id,
            "chunks_count": len(chunks),
            "keywords": keywords
        }
        
    except Exception as e:
        logger.error(f"索引文档失败: {str(e)}")
        return {
            "success": False,
            "message": f"索引失败: {str(e)}"
        }

def index_cloud_document(cloud_file_id: str, file_name: str, user_id: str, 
                        metadata: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    为微信云存储中的文件建立索引
    
    Args:
        cloud_file_id: 微信云存储的文件ID
        file_name: 文件名
        user_id: 上传用户ID
        metadata: 额外元数据
    
    Returns:
        字典，包含索引结果
    """
    temp_file = None
    
    try:
        metadata = metadata or {}
        
        # 设置文件元数据
        if "title" not in metadata:
            metadata["title"] = file_name
            
        if "uploader" not in metadata:
            metadata["uploader"] = user_id
            
        if "cloud_file_id" not in metadata:
            metadata["cloud_file_id"] = cloud_file_id
            
        if "source" not in metadata:
            metadata["source"] = "wxapp_upload"
            
        if "created_at" not in metadata:
            metadata["created_at"] = datetime.datetime.now().isoformat()
        
        # 使用wx_cloud工具类下载云存储文件
        logger.debug(f"开始下载云存储文件: {cloud_file_id}")
        temp_file = wx_cloud.download_file(cloud_file_id)
        
        if not temp_file:
            return {
                "success": False,
                "message": "无法从云存储下载文件"
            }
        
        # 处理下载的临时文件
        return index_document(temp_file, metadata)
        
    except Exception as e:
        logger.error(f"处理云存储文件失败: {str(e)}")
        return {
            "success": False,
            "message": f"处理失败: {str(e)}"
        }
    finally:
        # 清理临时文件
        if temp_file and os.path.exists(temp_file):
            try:
                os.remove(temp_file)
                logger.debug(f"已删除临时文件: {temp_file}")
            except Exception as e:
                logger.error(f"删除临时文件失败: {str(e)}")

def extract_keywords(text: str, max_keywords: int = 5) -> List[str]:
    """
    从文本中提取关键词
    
    Args:
        text: 输入文本
        max_keywords: 最大关键词数量
        
    Returns:
        关键词列表
    """
    try:
        from collections import Counter
        import re
        import string
        
        # 预处理文本：转小写，去除标点和数字
        text = text.lower()
        text = re.sub(r'[{}1234567890]'.format(re.escape(string.punctuation)), ' ', text)
        
        # 分词
        words = text.split()
        
        # 去除停用词（简单版本）
        stopwords = {
            '的', '了', '和', '是', '在', '我', '有', '不', '这', '为', '你', '们',
            '他', '它', '以', '到', '也', '对', '都', '很', '但', '就', '与', '而',
            'the', 'a', 'an', 'and', 'or', 'in', 'on', 'at', 'to', 'for', 'with',
            'by', 'about', 'as', 'of', 'from', 'that', 'this', 'these', 'those'
        }
        
        filtered_words = [word for word in words if word not in stopwords and len(word) > 1]
        
        # 计数并返回最常见的词
        word_counts = Counter(filtered_words)
        most_common = word_counts.most_common(max_keywords)
        
        # 提取关键词
        keywords = [word for word, _ in most_common]
        
        return keywords
    except Exception as e:
        logger.error(f"提取关键词失败: {str(e)}")
        return [] 