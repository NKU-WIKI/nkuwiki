#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import argparse
import subprocess
import platform
from pathlib import Path

def find_executable():
    """根据操作系统查找wechatmp2markdown可执行文件"""
    # 检测操作系统类型
    system = platform.system().lower()
    
    if system == "windows":
        executable_name = "wechatmp2markdown-v1.1.10_win64.exe"
    elif system == "linux":
        executable_name = "wechatmp2markdown-v1.1.10_linux_amd64"
    else:
        # 默认使用Windows版本，如果需要支持更多平台可以添加
        executable_name = "wechatmp2markdown-v1.1.10_win64.exe"
        print(f"警告: 未针对 {system} 系统优化，尝试使用默认可执行文件")
    
    possible_paths = [
        # 同目录下
        Path(__file__).parent / executable_name,
        # 项目根目录下
        Path(__file__).parent.parent.parent / executable_name,
        # 系统PATH中
        executable_name
    ]
    
    for path in possible_paths:
        if isinstance(path, str) or path.exists():
            return str(path)
    
    return None

def wechatmp2md(original_url, data_path, image_option='save'):
    """
    调用wechatmp2markdown将微信公众号文章转换为Markdown
    
    Args:
        original_url: 微信公众号文章URL
        data_path: 输出目录路径
        image_option: 图片处理选项 ('save'或'url')
        
    Returns:
        bool: 转换是否成功
    
    Raises:
        FileNotFoundError: 如果找不到可执行程序
        Exception: 如果转换过程中出错
    """
    # 确保输出目录存在
    output_dir = Path(data_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 查找可执行文件
    exe_path = find_executable()
    if not exe_path:
        system = platform.system().lower()
        if system == "windows":
            executable_name = "wechatmp2markdown-v1.1.10_win64.exe"
        elif system == "linux":
            executable_name = "wechatmp2markdown-v1.1.10_linux_amd64"
        else:
            executable_name = "wechatmp2markdown可执行文件"
        raise FileNotFoundError(f"未找到{executable_name}程序")
    
    # 构建命令
    cmd = [exe_path, original_url, str(output_dir), f"--image={image_option}"]
    
    try:
        # 运行外部程序
        print(f"执行命令: {' '.join(cmd)}")
        result = subprocess.run(cmd, check=True, text=True, capture_output=True)
        print("转换完成!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"错误: 转换失败 (返回码: {e.returncode})")
        if e.stdout:
            print(f"输出: {e.stdout}")
        if e.stderr:
            print(f"错误输出: {e.stderr}")
        return False
    except Exception as e:
        print(f"错误: {str(e)}")
        return False

def main():
    """
    调用wechatmp2markdown来转换微信公众号文章到Markdown
    用法: python wechatmp2md.py <微信文章URL> <输出目录> [--image=save|url]
    """
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='将微信公众号文章转换为Markdown格式')
    parser.add_argument('url', help='微信公众号文章URL')
    parser.add_argument('output_dir', help='输出目录路径')
    parser.add_argument('--image', choices=['save', 'url'], default='save', 
                        help='图片处理选项: save - 保存到本地 (默认), url - 使用原始URL')
    
    args = parser.parse_args()
    
    try:
        # 调用wechatmp2md函数
        success = wechatmp2md(args.url, args.output_dir, args.image)
        return 0 if success else 1
    except FileNotFoundError as e:
        print(f"错误: {str(e)}")
        system = platform.system().lower()
        if system == "windows":
            executable_name = "wechatmp2markdown-v1.1.10_win64.exe"
        elif system == "linux":
            executable_name = "wechatmp2markdown-v1.1.10_linux_amd64"
        else:
            executable_name = "wechatmp2markdown可执行文件"
        
        print(f"请确保{executable_name}在以下路径之一:")
        for path in [
            Path(__file__).parent / executable_name,
            Path(__file__).parent.parent.parent / executable_name
        ]:
            print(f"- {path}")
        print("或者添加到系统PATH中")
        return 1
    except Exception as e:
        print(f"错误: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())