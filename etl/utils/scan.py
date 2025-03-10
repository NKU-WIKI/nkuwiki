#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
import random  # 添加random模块
from collections import defaultdict
from pathlib import Path
from datetime import datetime
import argparse

def scan_wechat_nku_directories():
    """
    扫描/data/raw/wechat/nku目录下的所有目录结构，找到包含json文件的底层叶子目录，并统计：
    1. 不同时间段有多少个包含json文件的叶子目录
    2. 有多少叶子目录中的json文件content字段非空
    3. 有多少叶子目录有abstract.md文件
    4. 有多少叶子目录有html文件
    5. 随机展示一些非空content
    """
    # 基础路径
    base_path = "/data/raw/wechat/nku"
    
    # 计数统计
    time_periods = defaultdict(int)  # 按年份分组
    non_empty_content_dirs = 0
    has_abstract_dirs = 0
    has_html_dirs = 0
    total_json_dirs = 0
    
    # 存储所有找到的包含json文件的目录
    json_dirs = []
    
    # 存储非空content
    non_empty_contents = []
    
    # 是否打印过示例目录内容
    printed_example = False
    
    # 收集可能的abstract文件名变体
    abstract_variants = []
    
    # 遍历所有年月目录
    for year_month_dir in sorted(Path(base_path).iterdir()):
        if not year_month_dir.is_dir():
            continue
            
        # 目录名格式应为YYYYMM
        dir_name = year_month_dir.name
        if len(dir_name) != 6 or not dir_name.isdigit():
            print(f"跳过非标准目录名: {dir_name}")
            continue
            
        year = dir_name[:4]
        
        # 递归查找所有子目录
        for root, dirs, files in os.walk(year_month_dir):
            # 如果当前目录包含json文件，则认为它是我们要找的叶子目录
            json_files = [f for f in files if f.endswith('.json')]
            if json_files:
                root_path = Path(root)
                json_dirs.append(root_path)
                time_periods[year] += 1
                total_json_dirs += 1
                
                # 打印第一个找到的json目录的内容，了解文件结构
                if not printed_example and len(files) > 0:
                    print(f"\n示例目录 {root_path} 的内容:")
                    for file in sorted(files):
                        print(f"  - {file}")
                    printed_example = True
                
                # 检查各种可能的abstract.md文件命名
                # 不区分大小写的方式检查
                abstract_file_found = False
                for file in files:
                    if file.lower() == "abstract.md":
                        has_abstract_dirs += 1
                        abstract_file_found = True
                        # 收集实际的文件名
                        if file not in abstract_variants:
                            abstract_variants.append(file)
                        break
                
                # 如果没有找到abstract文件，检查是否有其他可能相关的md文件
                if not abstract_file_found:
                    md_files = [f for f in files if f.endswith('.md')]
                    if md_files and len(abstract_variants) < 10:  # 限制收集的变体数量
                        for md_file in md_files:
                            if md_file not in abstract_variants:
                                abstract_variants.append(md_file)
                
                # 检查是否有html文件
                html_files = [f for f in files if f.endswith('.html') or f.endswith('.htm')]
                if html_files:
                    has_html_dirs += 1
                
                # 检查json文件中的content字段
                has_non_empty_content = False
                for json_file in json_files:
                    file_path = root_path / json_file
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            data = json.load(f)
                            # 如果缺少content字段，添加空字符串
                            if isinstance(data, dict):
                                if "content" not in data:
                                    data["content"] = ""
                                    # 保存修改后的文件
                                    with open(file_path, "w", encoding="utf-8") as f:
                                        json.dump(data, f, ensure_ascii=False, indent=2)
                                
                                if data["content"].strip():
                                    has_non_empty_content = True
                                    # 收集非空content
                                    non_empty_contents.append({
                                        'path': str(file_path),
                                        'content': data["content"][:200]  # 只保存前200个字符
                                    })
                                    break
                    except (json.JSONDecodeError, UnicodeDecodeError, IOError) as e:
                        print(f"处理文件 {file_path} 时出错: {str(e)}")
                        continue
                
                if has_non_empty_content:
                    non_empty_content_dirs += 1
    
    # 打印结果
    print("\n===== 扫描结果 =====")
    print(f"总共找到 {total_json_dirs} 个包含json文件的叶子目录")
    
    print("\n按年份统计叶子目录数量:")
    for year in sorted(time_periods.keys()):
        print(f"  {year}年: {time_periods[year]}个叶子目录")
    
    if total_json_dirs > 0:
        print(f"\n有非空content字段的json文件的叶子目录数: {non_empty_content_dirs} ({non_empty_content_dirs/total_json_dirs*100:.2f}%)")
        print(f"有abstract.md文件的叶子目录数: {has_abstract_dirs} ({has_abstract_dirs/total_json_dirs*100:.2f}%)")
        print(f"有html文件的叶子目录数: {has_html_dirs} ({has_html_dirs/total_json_dirs*100:.2f}%)")
        
        # 随机展示5个非空content
        if non_empty_contents:
            print("\n随机展示5个非空content示例:")
            samples = random.sample(non_empty_contents, min(5, len(non_empty_contents)))
            for i, sample in enumerate(samples, 1):
                print(f"\n{i}. 文件: {sample['path']}")
                print(f"   内容预览: {sample['content']}...")
        
        if abstract_variants:
            print("\n找到的可能的abstract相关文件名:")
            for variant in abstract_variants:
                print(f"  - {variant}")
        else:
            print("\n未找到任何abstract.md或类似文件")
    else:
        print("\n未找到任何包含json文件的叶子目录")

def main():
    parser = argparse.ArgumentParser(description="扫描微信公众号数据目录")
    parser.add_argument("--path", type=str, default="/data/raw/wechat/nku", 
                        help="要扫描的基础路径，默认为/data/raw/wechat/nku")
    args = parser.parse_args()
    
    print(f"开始扫描目录: {args.path}")
    scan_wechat_nku_directories()
    print("扫描完成!")

if __name__ == "__main__":
    main()
