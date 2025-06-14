#!/usr/bin/env python3
"""
清理自定义词典脚本
移除注释行、空行和重复项，生成干净的词典文件
"""

import os
from pathlib import Path

def clean_dictionary():
    """清理自定义词典文件"""
    
    # 文件路径
    dict_file = Path("etl/utils/dictionary/custom_dictionary.dic")
    
    if not dict_file.exists():
        print(f"词典文件不存在: {dict_file}")
        return
    
    print(f"正在处理词典文件: {dict_file}")
    
    # 读取原文件
    with open(dict_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # 清理词汇
    clean_words = set()
    
    for line in lines:
        line = line.strip()
        
        # 跳过空行和注释行
        if not line or line.startswith('#') or line.startswith('='):
            continue
            
        # 添加到集合中（自动去重）
        clean_words.add(line)
    
    # 排序词汇
    sorted_words = sorted(clean_words)
    
    print(f"原始行数: {len(lines)}")
    print(f"清理后词汇数: {len(sorted_words)}")
    
    # 写入清理后的文件
    with open(dict_file, 'w', encoding='utf-8') as f:
        for word in sorted_words:
            f.write(word + '\n')
    
    print(f"词典文件已清理完成")
    
    # 显示前10个词汇作为示例
    print("\n前10个词汇:")
    for i, word in enumerate(sorted_words[:10]):
        print(f"  {i+1}. {word}")

if __name__ == "__main__":
    clean_dictionary() 