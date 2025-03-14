#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import argparse
import subprocess
import platform
import asyncio
from pathlib import Path

def find_executable():
    """根据操作系统查找wechatmp2markdown可执行文件"""
    # 检测操作系统类型
    system = platform.system().lower()
    
    # 设置可执行文件匹配模式
    if system == "windows":
        pattern = "wechatmp2markdown*.exe"
    else:
        pattern = "wechatmp2markdown*"
    
    possible_paths = [
        # 同目录下
        Path(__file__).parent,
        # 项目根目录下
        Path(__file__).parent.parent.parent,
    ]
    
    # 在可能的路径中查找匹配的可执行文件
    for path in possible_paths:
        matches = list(path.glob(pattern))
        if matches:
            return str(matches[0])  # 返回找到的第一个匹配文件
            
    # 在系统PATH中查找
    if os.getenv('PATH'):
        for path in os.getenv('PATH').split(os.pathsep):
            matches = list(Path(path).glob(pattern))
            if matches:
                return str(matches[0])
    
    return None

# 用于控制并发数的信号量
conversion_semaphore = asyncio.Semaphore(20)  # 进一步提高并发数到20

async def wechatmp2md_async(original_url, data_path, image_option='url'):
    """
    异步调用wechatmp2markdown将微信公众号文章转换为Markdown
    
    Args:
        original_url: 微信公众号文章URL
        data_path: 输出目录路径
        image_option: 图片处理选项 ('save'或'url')
        
    Returns:
        bool: 转换是否成功
    """
    async with conversion_semaphore:
        # 查找可执行文件
        exe_path = find_executable()
        if not exe_path:
            print(f"未找到wechatmp2markdown可执行文件")
            return False
        # 构建命令
        cmd = [exe_path, original_url, str(data_path), f"--image={image_option}"]
        try:
            # 使用线程池执行外部命令，避免阻塞事件循环
            print(f"执行命令: {' '.join(cmd)}")
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, lambda: subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False
            ))
            
            if result.returncode == 0:
                print("转换完成!")
                return True
            else:
                print(f"错误: 转换失败 (返回码: {result.returncode})")
                if result.stdout:
                    print(f"输出: {result.stdout}")
                if result.stderr:
                    print(f"错误输出: {result.stderr}")
                return False
        except Exception as e:
            print(f"错误: {str(e)}")
            return False

def wechatmp2md(original_url, data_path, image_option='url'):
    """
    调用wechatmp2markdown将微信公众号文章转换为Markdown
    
    Args:
        original_url: 微信公众号文章URL
        data_path: 输出目录路径
        image_option: 图片处理选项 ('save'或'url')
        
    Returns:
        bool: 转换是否成功
    """
    # 检查当前是否有正在运行的事件循环
    try:
        loop = asyncio.get_running_loop()
        # 在已有事件循环中，直接创建任务执行
        return asyncio.run_coroutine_threadsafe(
            wechatmp2md_async(original_url, data_path, image_option), 
            loop
        ).result()
    except RuntimeError:
        # 如果没有正在运行的事件循环，则创建一个新的
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(wechatmp2md_async(original_url, data_path, image_option))
        finally:
            loop.close()

async def main_async():
    """异步版本的main函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='将微信公众号文章转换为Markdown格式')
    parser.add_argument('url', help='微信公众号文章URL')
    parser.add_argument('output_dir', help='输出目录路径')
    parser.add_argument('--image', choices=['save', 'url'], default='save', 
                        help='图片处理选项: save - 保存到本地 (默认), url - 使用原始URL')
    
    args = parser.parse_args()
    
    try:
        # 调用异步wechatmp2md函数
        success = await wechatmp2md_async(args.url, args.output_dir, args.image)
        return 0 if success else 1
    except Exception as e:
        print(f"错误: {str(e)}")
        return 1

def main():
    """
    调用wechatmp2markdown来转换微信公众号文章到Markdown
    用法: python wechatmp2md.py <微信文章URL> <输出目录> [--image=save|url]
    """
    # 运行异步main函数
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(main_async())
    finally:
        loop.close()

if __name__ == "__main__":
    sys.exit(main())