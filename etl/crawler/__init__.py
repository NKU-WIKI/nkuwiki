import os  # 导入操作系统模块，用于处理文件和目录
import sys  # 导入系统模块，用于处理系统相关的操作
import tempfile  # 导入临时目录模块，用于处理临时目录
from pathlib import Path  # 导入Path类，用于处理文件路径
import shutil # 导入shutil模块，用于处理文件和目录
import re  # 导入正则表达式模块，用于处理字符串匹配
import pytz  # 导入时区模块，用于处理时区相关的操作
import json  # 导入JSON模块，用于处理JSON数据
import time  # 导入时间模块，用于处理时间相关的操作
from datetime import datetime  # 导入datetime类，用于处理日期和时间
from dotenv import load_dotenv # 导入dotenv模块，用于加载环境变量
import requests  # 导入requests模块，用于发送HTTP请求
import random  # 导入随机数模块，用于生成随机数
from loguru import logger  # 导入loguru模块，用于日志记录
from collections import Counter  # 导入Counter类，用于计数
import pdfplumber  # 导入pdfplumber模块，用于处理PDF文件
from PyPDF2 import PdfWriter, PdfReader  # 导入PyPDF2模块，用于处理PDF文件
from playwright.sync_api import sync_playwright  # 新增Playwright导入

__all__ = ['datetime', 'sys', 'Path', 'os', 're', 'pytz', 'json', 'time', 'requests', 'random', 'logger', 'Counter', 'pdfplumber', 'PdfWriter', 'PdfReader', 'load_dotenv', 'tempfile', 'shutil', 'logger', 'sync_playwright'] 