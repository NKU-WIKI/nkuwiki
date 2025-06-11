"""
文档摘要处理器

提供Markdown文档的摘要生成功能
"""

import os
import sys
import re
import time
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Union
from etl import config
from core.utils import register_logger
from .abstract import AbstractProcessor

logger = register_logger("etl.processors.summarize")


class SummarizeProcessor:
    """文档摘要处理器"""
    
    def __init__(self):
        self.abstract_processor = AbstractProcessor()
        
    async def process_file(
        self,
        file_path: Union[str, Path],
        output_path: Optional[Union[str, Path]] = None,
        max_length: int = 300,
        bot_tag: str = "summarize_md"
    ) -> Dict:
        """
        处理单个markdown文件，生成摘要
        
        Args:
            file_path: 输入文件路径
            output_path: 输出文件路径，如果为None则修改原文件
            max_length: 摘要最大长度
            bot_tag: 使用的bot标签
            
        Returns:
            处理结果字典
        """
        if not isinstance(file_path, Path):
            file_path = Path(file_path)
            
        if not file_path.exists():
            return {"status": "error", "message": f"文件不存在: {file_path}"}
            
        try:
            # 读取原文件内容
            content = file_path.read_text(encoding='utf-8')
            
            # 检查是否已经有摘要标记
            if self._has_abstract_marker(content):
                logger.info(f"文件已包含摘要标记，跳过: {file_path}")
                return {"status": "skip", "message": "文件已包含摘要"}
            
            # 生成摘要
            logger.info(f"正在为文件生成摘要: {file_path}")
            abstract = await self.abstract_processor.generate_abstract_async(
                file_path, max_length, bot_tag
            )
            
            if not abstract:
                return {"status": "error", "message": "摘要生成失败"}
                
            # 插入摘要到内容中
            new_content = self._insert_abstract(content, abstract)
            
            # 确定输出路径
            if output_path is None:
                output_path = file_path
            elif not isinstance(output_path, Path):
                output_path = Path(output_path)
                
            # 写入文件
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(new_content, encoding='utf-8')
            
            return {
                "status": "success", 
                "message": f"摘要生成完成: {output_path}",
                "abstract": abstract
            }
            
        except Exception as e:
            logger.error(f"处理文件时发生错误 {file_path}: {e}")
            return {"status": "error", "message": str(e)}
    
    async def process_directory(
        self,
        input_dir: Union[str, Path],
        output_dir: Optional[Union[str, Path]] = None,
        pattern: str = "*.md",
        max_length: int = 300,
        bot_tag: str = "summarize_md",
        max_workers: int = 3
    ) -> Dict:
        """
        批量处理目录中的markdown文件
        
        Args:
            input_dir: 输入目录
            output_dir: 输出目录，如果为None则在原位置修改
            pattern: 文件匹配模式
            max_length: 摘要最大长度
            bot_tag: 使用的bot标签
            max_workers: 最大并发数
            
        Returns:
            处理结果汇总
        """
        if not isinstance(input_dir, Path):
            input_dir = Path(input_dir)
            
        if not input_dir.exists():
            return {"status": "error", "message": f"目录不存在: {input_dir}"}
            
        # 获取所有匹配的文件
        files = list(input_dir.rglob(pattern))
        if not files:
            return {"status": "warning", "message": f"未找到匹配的文件: {pattern}"}
            
        logger.info(f"找到 {len(files)} 个文件需要处理")
        
        # 创建信号量控制并发数
        semaphore = asyncio.Semaphore(max_workers)
        
        async def process_single_file(file_path):
            async with semaphore:
                # 确定输出路径
                if output_dir is None:
                    output_path = None
                else:
                    if not isinstance(output_dir, Path):
                        output_dir_path = Path(output_dir)
                    else:
                        output_dir_path = output_dir
                        
                    relative_path = file_path.relative_to(input_dir)
                    output_path = output_dir_path / relative_path
                
                return await self.process_file(
                    file_path, output_path, max_length, bot_tag
                )
        
        # 并发处理所有文件
        results = await asyncio.gather(
            *[process_single_file(file_path) for file_path in files],
            return_exceptions=True
        )
        
        # 统计结果
        success_count = sum(1 for r in results if isinstance(r, dict) and r.get("status") == "success")
        skip_count = sum(1 for r in results if isinstance(r, dict) and r.get("status") == "skip")
        error_count = sum(1 for r in results if isinstance(r, dict) and r.get("status") == "error")
        exception_count = sum(1 for r in results if isinstance(r, Exception))
        
        return {
            "status": "completed",
            "total_files": len(files),
            "success": success_count,
            "skipped": skip_count,
            "errors": error_count + exception_count,
            "results": results
        }
    
    def _has_abstract_marker(self, content: str) -> bool:
        """检查内容是否已包含摘要标记"""
        patterns = [
            r'## 摘要',
            r'## Abstract',
            r'## 概述',
            r'## Summary',
            r'<!-- Abstract -->',
            r'<!-- 摘要 -->'
        ]
        
        for pattern in patterns:
            if re.search(pattern, content, re.IGNORECASE):
                return True
        return False
    
    def _insert_abstract(self, content: str, abstract: str) -> str:
        """在内容中插入摘要"""
        lines = content.split('\n')
        insert_index = 0
        
        # 寻找第一个标题后的位置
        for i, line in enumerate(lines):
            if line.strip().startswith('#'):
                insert_index = i + 1
                break
                
        # 跳过可能的空行
        while insert_index < len(lines) and not lines[insert_index].strip():
            insert_index += 1
            
        # 构建摘要内容
        abstract_section = [
            "",
            "## 摘要",
            "",
            abstract.strip(),
            ""
        ]
        
        # 插入摘要
        lines[insert_index:insert_index] = abstract_section
        
        return '\n'.join(lines)


# 全局实例
_summarize_processor = SummarizeProcessor()

# 向后兼容函数
async def summarize_markdown_file(
    file_path: Union[str, Path],
    output_path: Optional[Union[str, Path]] = None,
    max_length: int = 300,
    bot_tag: str = "summarize_md"
) -> Dict:
    """向后兼容的文件摘要函数"""
    return await _summarize_processor.process_file(file_path, output_path, max_length, bot_tag)

async def summarize_markdown_directory(
    input_dir: Union[str, Path],
    output_dir: Optional[Union[str, Path]] = None,
    pattern: str = "*.md",
    max_length: int = 300,
    bot_tag: str = "summarize_md",
    max_workers: int = 3
) -> Dict:
    """向后兼容的目录摘要函数"""
    return await _summarize_processor.process_directory(
        input_dir, output_dir, pattern, max_length, bot_tag, max_workers
    )


# CLI接口
async def main():
    """命令行入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Markdown文档摘要生成工具')
    parser.add_argument('input', help='输入文件或目录路径')
    parser.add_argument('-o', '--output', help='输出路径（可选）')
    parser.add_argument('-p', '--pattern', default='*.md', help='文件匹配模式（目录模式）')
    parser.add_argument('-l', '--max-length', type=int, default=300, help='摘要最大长度')
    parser.add_argument('-t', '--bot-tag', default='summarize_md', help='Bot标签')
    parser.add_argument('-w', '--workers', type=int, default=3, help='最大并发数')
    
    args = parser.parse_args()
    
    input_path = Path(args.input)
    
    if input_path.is_file():
        result = await _summarize_processor.process_file(
            input_path, args.output, args.max_length, args.bot_tag
        )
        print(f"处理结果: {result}")
    elif input_path.is_dir():
        result = await _summarize_processor.process_directory(
            input_path, args.output, args.pattern, 
            args.max_length, args.bot_tag, args.workers
        )
        print(f"批量处理结果: {result}")
    else:
        print(f"错误: 路径不存在 {input_path}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main()) 