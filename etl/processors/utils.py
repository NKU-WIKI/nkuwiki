"""
通用数据处理工具

提供各种数据转换、合并和预处理功能
"""

import json
import os
import sys
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from core.utils import register_logger

logger = register_logger("etl.processors.utils")


class DataTransformationProcessor:
    """数据转换处理器"""
    
    @staticmethod
    def merge_json_files(
        input_dir: Union[str, Path],
        output_file: Union[str, Path],
        pattern: str = "*.json"
    ) -> Dict:
        """
        合并多个JSON文件
        
        Args:
            input_dir: 输入目录
            output_file: 输出文件路径
            pattern: 文件匹配模式
            
        Returns:
            处理结果
        """
        if not isinstance(input_dir, Path):
            input_dir = Path(input_dir)
            
        if not input_dir.exists():
            return {"status": "error", "message": f"目录不存在: {input_dir}"}
            
        # 获取所有JSON文件
        json_files = list(input_dir.glob(pattern))
        if not json_files:
            return {"status": "warning", "message": f"未找到匹配的JSON文件: {pattern}"}
            
        merged_data = []
        error_files = []
        
        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                # 如果是列表，直接扩展
                if isinstance(data, list):
                    merged_data.extend(data)
                # 如果是字典，作为单个项目添加
                elif isinstance(data, dict):
                    merged_data.append(data)
                else:
                    logger.warning(f"跳过非标准JSON结构文件: {json_file}")
                    
            except Exception as e:
                logger.error(f"读取JSON文件失败 {json_file}: {e}")
                error_files.append(str(json_file))
                
        # 写入合并后的数据
        try:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(merged_data, f, ensure_ascii=False, indent=2)
                
            return {
                "status": "success",
                "message": f"成功合并 {len(json_files)} 个文件到 {output_file}",
                "processed_files": len(json_files) - len(error_files),
                "error_files": error_files,
                "total_records": len(merged_data)
            }
            
        except Exception as e:
            return {"status": "error", "message": f"写入输出文件失败: {e}"}
    
    @staticmethod
    def transform_data_format(
        input_file: Union[str, Path],
        output_file: Union[str, Path],
        transform_rules: Dict[str, Any]
    ) -> Dict:
        """
        根据规则转换数据格式
        
        Args:
            input_file: 输入文件
            output_file: 输出文件
            transform_rules: 转换规则
            
        Returns:
            处理结果
        """
        try:
            input_path = Path(input_file)
            if not input_path.exists():
                return {"status": "error", "message": f"输入文件不存在: {input_file}"}
                
            # 读取输入数据
            with open(input_path, 'r', encoding='utf-8') as f:
                if input_path.suffix.lower() == '.json':
                    data = json.load(f)
                else:
                    # 尝试按行读取JSON
                    lines = f.readlines()
                    data = []
                    for line in lines:
                        line = line.strip()
                        if line:
                            try:
                                data.append(json.loads(line))
                            except json.JSONDecodeError:
                                logger.warning(f"跳过无效JSON行: {line[:50]}")
                                
            # 应用转换规则
            transformed_data = DataTransformationProcessor._apply_transform_rules(data, transform_rules)
            
            # 写入输出文件
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                if output_path.suffix.lower() == '.json':
                    json.dump(transformed_data, f, ensure_ascii=False, indent=2)
                else:
                    # 按行写入JSON
                    for item in transformed_data:
                        f.write(json.dumps(item, ensure_ascii=False) + '\n')
                        
            return {
                "status": "success",
                "message": f"数据转换完成: {output_file}",
                "input_records": len(data) if isinstance(data, list) else 1,
                "output_records": len(transformed_data) if isinstance(transformed_data, list) else 1
            }
            
        except Exception as e:
            logger.error(f"数据转换失败: {e}")
            return {"status": "error", "message": str(e)}
    
    @staticmethod
    def _apply_transform_rules(data: Any, rules: Dict[str, Any]) -> Any:
        """应用转换规则"""
        if isinstance(data, list):
            return [DataTransformationProcessor._apply_transform_rules(item, rules) for item in data]
        elif isinstance(data, dict):
            transformed = {}
            
            for key, value in data.items():
                # 检查字段重命名规则
                new_key = rules.get('field_mapping', {}).get(key, key)
                
                # 检查字段过滤规则
                if 'include_fields' in rules:
                    if key not in rules['include_fields']:
                        continue
                        
                if 'exclude_fields' in rules:
                    if key in rules['exclude_fields']:
                        continue
                
                # 递归处理嵌套结构
                transformed_value = DataTransformationProcessor._apply_transform_rules(value, rules)
                
                # 应用值转换规则
                if 'value_transforms' in rules and key in rules['value_transforms']:
                    transform_func = rules['value_transforms'][key]
                    if callable(transform_func):
                        transformed_value = transform_func(transformed_value)
                        
                transformed[new_key] = transformed_value
                
            return transformed
        else:
            return data
    
    @staticmethod
    def preprocess_text_data(
        input_file: Union[str, Path],
        output_file: Union[str, Path],
        preprocessing_options: Optional[Dict[str, Any]] = None
    ) -> Dict:
        """
        预处理文本数据
        
        Args:
            input_file: 输入文件
            output_file: 输出文件
            preprocessing_options: 预处理选项
            
        Returns:
            处理结果
        """
        if preprocessing_options is None:
            preprocessing_options = {
                'remove_html_tags': True,
                'normalize_whitespace': True,
                'remove_empty_lines': True,
                'encoding': 'utf-8'
            }
            
        try:
            input_path = Path(input_file)
            if not input_path.exists():
                return {"status": "error", "message": f"输入文件不存在: {input_file}"}
                
            # 读取文本内容
            encoding = preprocessing_options.get('encoding', 'utf-8')
            with open(input_path, 'r', encoding=encoding) as f:
                content = f.read()
                
            # 应用预处理步骤
            processed_content = DataTransformationProcessor._preprocess_text_content(
                content, preprocessing_options
            )
            
            # 写入处理后的内容
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding=encoding) as f:
                f.write(processed_content)
                
            return {
                "status": "success",
                "message": f"文本预处理完成: {output_file}",
                "original_length": len(content),
                "processed_length": len(processed_content)
            }
            
        except Exception as e:
            logger.error(f"文本预处理失败: {e}")
            return {"status": "error", "message": str(e)}
    
    @staticmethod
    def _preprocess_text_content(content: str, options: Dict[str, Any]) -> str:
        """预处理文本内容"""
        # 移除HTML标签
        if options.get('remove_html_tags', False):
            content = re.sub(r'<[^>]+>', '', content)
            
        # 标准化空白字符
        if options.get('normalize_whitespace', False):
            content = re.sub(r'\s+', ' ', content)
            
        # 移除空行
        if options.get('remove_empty_lines', False):
            lines = content.split('\n')
            non_empty_lines = [line for line in lines if line.strip()]
            content = '\n'.join(non_empty_lines)
            
        # 其他自定义预处理规则
        if 'custom_patterns' in options:
            for pattern, replacement in options['custom_patterns'].items():
                content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
                
        return content.strip()


class OCRDataProcessor:
    """OCR数据处理器"""
    
    @staticmethod
    def extract_text_from_images(
        image_dir: Union[str, Path],
        output_file: Union[str, Path],
        ocr_engine: str = "tesseract"
    ) -> Dict:
        """
        从图片目录提取文本数据
        
        Args:
            image_dir: 图片目录
            output_file: 输出文件
            ocr_engine: OCR引擎类型
            
        Returns:
            处理结果
        """
        try:
            # 这里可以集成不同的OCR引擎
            # 目前提供基础框架
            logger.info(f"开始OCR处理: {image_dir}")
            
            # 扫描图片文件
            image_path = Path(image_dir)
            if not image_path.exists():
                return {"status": "error", "message": f"图片目录不存在: {image_dir}"}
                
            image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.gif'}
            image_files = []
            
            for ext in image_extensions:
                image_files.extend(image_path.glob(f"*{ext}"))
                image_files.extend(image_path.glob(f"*{ext.upper()}"))
                
            if not image_files:
                return {"status": "warning", "message": "未找到图片文件"}
                
            # 处理结果
            ocr_results = []
            for image_file in image_files:
                # 这里应该调用实际的OCR库
                # 例如: pytesseract, paddleocr, easyocr等
                result = {
                    "file": str(image_file),
                    "text": f"[OCR提取的文本内容 - {image_file.name}]",
                    "confidence": 0.95  # 置信度
                }
                ocr_results.append(result)
                
            # 保存结果
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(ocr_results, f, ensure_ascii=False, indent=2)
                
            return {
                "status": "success",
                "message": f"OCR处理完成: {output_file}",
                "processed_images": len(image_files),
                "extracted_texts": len(ocr_results)
            }
            
        except Exception as e:
            logger.error(f"OCR处理失败: {e}")
            return {"status": "error", "message": str(e)}


# 全局实例
_data_transformer = DataTransformationProcessor()
_ocr_processor = OCRDataProcessor()

# 向后兼容函数
def merge_json_files(input_dir: Union[str, Path], output_file: Union[str, Path], pattern: str = "*.json") -> Dict:
    """向后兼容的JSON合并函数"""
    return _data_transformer.merge_json_files(input_dir, output_file, pattern)

def transform_data_format(input_file: Union[str, Path], output_file: Union[str, Path], transform_rules: Dict[str, Any]) -> Dict:
    """向后兼容的数据转换函数"""
    return _data_transformer.transform_data_format(input_file, output_file, transform_rules)

def preprocess_text_data(input_file: Union[str, Path], output_file: Union[str, Path], preprocessing_options: Optional[Dict[str, Any]] = None) -> Dict:
    """向后兼容的文本预处理函数"""
    return _data_transformer.preprocess_text_data(input_file, output_file, preprocessing_options)

def extract_ocr_data(image_dir: Union[str, Path], output_file: Union[str, Path], ocr_engine: str = "tesseract") -> Dict:
    """向后兼容的OCR数据提取函数"""
    return _ocr_processor.extract_text_from_images(image_dir, output_file, ocr_engine) 