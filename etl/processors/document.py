"""
文档处理器

整合文档解析、转换和预处理功能
"""

import io
import re
from typing import Dict, Callable, Optional, List
import requests
from pypdf import PdfReader
from docx import Document
from tenacity import retry, stop_after_attempt, wait_fixed
from core.utils import register_logger

logger = register_logger("etl.processors.document")

class DocumentProcessor:
    """
    统一的文档处理器，支持多种格式的文档解析和转换
    """

    def __init__(self):
        self._parsers: Dict[str, Callable[[io.BytesIO], str]] = {
            ".pdf": self._parse_pdf,
            ".docx": self._parse_docx,
        }

    def _parse_pdf(self, file_stream: io.BytesIO) -> str:
        """使用pypdf从PDF文件中提取文本"""
        try:
            reader = PdfReader(file_stream)
            text = "".join(page.extract_text() for page in reader.pages if page.extract_text())
            return text
        except Exception as e:
            logger.error(f"解析PDF错误: {e}")
            return ""

    def _parse_docx(self, file_stream: io.BytesIO) -> str:
        """使用python-docx从DOCX文件中提取文本"""
        try:
            document = Document(file_stream)
            text = "\n".join(para.text for para in document.paragraphs if para.text)
            return text
        except Exception as e:
            logger.error(f"解析DOCX错误: {e}")
            return ""

    def get_supported_formats(self) -> List[str]:
        """返回支持的文档格式列表"""
        return list(self._parsers.keys())

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
    def _fetch_from_url(self, url: str) -> Optional[io.BytesIO]:
        """从URL获取文件内容，带重试机制"""
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            return io.BytesIO(response.content)
        except requests.exceptions.RequestException as e:
            logger.error(f"从URL获取文档失败 {url}: {e}")
            return None

    def parse(self, source: str) -> Optional[str]:
        """解析文档内容
        
        Args:
            source: 文档的URL或本地文件路径
            
        Returns:
            提取的文本内容，失败返回None
        """
        # 判断是URL还是本地路径
        if source.startswith(("http://", "https://")):
            file_extension = "." + source.split('.')[-1].lower()
            file_stream = self._fetch_from_url(source)
        else:
            file_extension = "." + source.split('.')[-1].lower()
            try:
                with open(source, "rb") as f:
                    file_stream = io.BytesIO(f.read())
            except FileNotFoundError:
                logger.error(f"文件未找到: {source}")
                return None
        
        if not file_stream:
            return None

        # 根据文件扩展名选择解析器
        parser = self._parsers.get(file_extension)
        if parser:
            return parser(file_stream)
        else:
            logger.warning(f"不支持的文件格式: {file_extension}")
            return None

    def clean_text(self, text: str) -> str:
        """清理文本内容"""
        if not text:
            return ""
            
        # 移除多余的空白字符
        text = re.sub(r'\s+', ' ', text)
        
        # 移除HTML标签
        text = re.sub(r'<.*?>', '', text)
        
        # 移除特殊字符（保留中文和基本标点）
        text = re.sub(r'[^\w\s\u4e00-\u9fff\u3000-\u303f\uff00-\uffef]', '', text)
        
        return text.strip()

    def process(self, source: str, clean: bool = True) -> Optional[str]:
        """完整的文档处理流程
        
        Args:
            source: 文档源
            clean: 是否清理文本
            
        Returns:
            处理后的文本内容
        """
        text = self.parse(source)
        if text and clean:
            text = self.clean_text(text)
        return text

    # 向后兼容性别名
    def parse_from_url(self, url: str) -> Optional[str]:
        """从URL解析文档内容（向后兼容）"""
        return self.parse(url) 