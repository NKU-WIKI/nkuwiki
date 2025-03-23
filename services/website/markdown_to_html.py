#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
import shutil
import markdown
import logging
from pathlib import Path

# 配置日志
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 项目根目录
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DOCS_DIR = PROJECT_ROOT / 'docs'
OUTPUT_DIR = Path(__file__).resolve().parent / 'markdown'

# 确保输出目录存在
OUTPUT_DIR.mkdir(exist_ok=True)

# HTML模板
HTML_TEMPLATE = '''<!doctype html>
<html lang="zh-CN" data-theme="light">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width,initial-scale=1" />
    <meta name="generator" content="Markdown" />
    <meta name="theme" content="VuePress Theme Hope" />
    <title>{title} | 南开WIKI</title>
    <meta name="description" content="{description}" />
    <style>
      :root {{
        --vp-c-bg: #fff;
        --vp-c-text: #2c3e50;
        --vp-c-border: #eaecef;
        --vp-c-code-bg: #f6f8fa;
        --vp-c-brand: #3eaf7c;
        --vp-c-brand-light: #4abf8a;
      }}

      [data-theme="dark"] {{
        --vp-c-bg: #1b1b1f;
        --vp-c-text: #f0f0f0;
        --vp-c-border: #3e3e3e;
        --vp-c-code-bg: #282c34;
        --vp-c-brand: #3aa675;
        --vp-c-brand-light: #349469;
      }}

      html, body {{
        background: var(--vp-c-bg);
        color: var(--vp-c-text);
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen, Ubuntu, Cantarell, "Fira Sans", "Droid Sans", "Helvetica Neue", sans-serif;
        line-height: 1.7;
      }}

      .markdown-container {{
        max-width: 960px;
        margin: 0 auto;
        padding: 2rem 2.5rem;
      }}

      .markdown-content {{
        background-color: var(--vp-c-bg);
        border-radius: 8px;
        padding: 2rem;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
      }}

      .markdown-content h1 {{
        font-size: 2.2rem;
        border-bottom: 1px solid var(--vp-c-border);
        padding-bottom: 0.3rem;
        margin-top: 0;
      }}

      .markdown-content h2 {{
        font-size: 1.65rem;
        border-bottom: 1px solid var(--vp-c-border);
        padding-bottom: 0.3rem;
      }}

      .markdown-content h3 {{
        font-size: 1.35rem;
      }}

      .markdown-content h4 {{
        font-size: 1.15rem;
      }}

      .markdown-content p {{
        margin: 1rem 0;
      }}

      .markdown-content blockquote {{
        border-left: 4px solid var(--vp-c-brand);
        padding: 0.5rem 1rem;
        color: #6a737d;
        background-color: rgba(66, 185, 131, 0.1);
        margin: 1rem 0;
      }}

      .markdown-content pre {{
        background-color: var(--vp-c-code-bg);
        border-radius: 6px;
        padding: 1rem;
        overflow: auto;
      }}

      .markdown-content code {{
        font-family: Consolas, Monaco, 'Andale Mono', 'Ubuntu Mono', monospace;
        padding: 0.2rem 0.4rem;
        background-color: var(--vp-c-code-bg);
        border-radius: 3px;
      }}

      .markdown-content pre code {{
        padding: 0;
        background-color: transparent;
      }}

      .markdown-content table {{
        border-collapse: collapse;
        width: 100%;
        margin: 1rem 0;
      }}

      .markdown-content table th, .markdown-content table td {{
        border: 1px solid var(--vp-c-border);
        padding: 0.6rem 1rem;
        text-align: left;
      }}

      .markdown-content table th {{
        background-color: rgba(0, 0, 0, 0.05);
      }}

      .markdown-content img {{
        max-width: 100%;
      }}

      .markdown-content a {{
        color: var(--vp-c-brand);
        text-decoration: none;
      }}

      .markdown-content a:hover {{
        text-decoration: underline;
        color: var(--vp-c-brand-light);
      }}

      .markdown-content ul, .markdown-content ol {{
        padding-left: 2rem;
      }}

      .markdown-content li {{
        margin: 0.5rem 0;
      }}

      /* 返回按钮 */
      .back-button {{
        display: inline-block;
        margin-bottom: 1rem;
        padding: 0.5rem 1rem;
        background-color: var(--vp-c-brand);
        color: white;
        border-radius: 4px;
        text-decoration: none;
        font-weight: 500;
      }}

      .back-button:hover {{
        background-color: var(--vp-c-brand-light);
      }}

      /* 暗黑模式切换按钮 */
      .theme-toggle {{
        position: fixed;
        right: 1.5rem;
        bottom: 1.5rem;
        width: 3rem;
        height: 3rem;
        border-radius: 50%;
        background-color: var(--vp-c-brand);
        color: white;
        text-align: center;
        line-height: 3rem;
        cursor: pointer;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
      }}
    </style>
    <script>
      const userMode = localStorage.getItem("vuepress-theme-hope-scheme");
      const systemDarkMode =
        window.matchMedia &&
        window.matchMedia("(prefers-color-scheme: dark)").matches;

      if (userMode === "dark" || (userMode !== "light" && systemDarkMode)) {{
        document.documentElement.setAttribute("data-theme", "dark");
      }}
    </script>
  </head>
  <body>
    <div class="markdown-container">
      <a href="/docs.html" class="back-button">« 返回文档列表</a>
      <div class="markdown-content">
        {content}
      </div>
      <div class="theme-toggle" id="themeToggle">🌓</div>
    </div>

    <script>
      document.addEventListener('DOMContentLoaded', function() {{
        const themeToggle = document.getElementById('themeToggle');
        
        themeToggle.addEventListener('click', function() {{
          const currentTheme = document.documentElement.getAttribute('data-theme');
          const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
          document.documentElement.setAttribute('data-theme', newTheme);
          localStorage.setItem('vuepress-theme-hope-scheme', newTheme);
        }});
      }});
    </script>
  </body>
</html>
'''

def extract_title_and_description(content):
    """从Markdown内容中提取标题和描述"""
    title = "文档"
    description = "南开Wiki项目文档"
    
    # 尝试从一级标题提取
    title_match = re.search(r'^# (.*?)$', content, re.MULTILINE)
    if title_match:
        title = title_match.group(1)
    
    # 尝试从内容第二行或第三行提取描述
    lines = content.split('\n')
    for line in lines[:5]:
        if line and not line.startswith('#') and len(line) > 10:
            description = line.strip()
            break
    
    return title, description

def convert_markdown_to_html(md_file, output_dir):
    """将单个Markdown文件转换为HTML"""
    try:
        md_path = Path(md_file)
        html_filename = md_path.stem + '.html'
        html_path = output_dir / html_filename
        
        logger.debug(f"处理文件: {md_path}")
        
        # 读取Markdown内容
        with open(md_path, 'r', encoding='utf-8') as f:
            md_content = f.read()
        
        # 提取标题和描述
        title, description = extract_title_and_description(md_content)
        
        # 转换Markdown为HTML
        html_content = markdown.markdown(
            md_content,
            extensions=[
                'markdown.extensions.fenced_code',
                'markdown.extensions.tables',
                'markdown.extensions.toc',
                'markdown.extensions.codehilite',
                'markdown.extensions.extra'
            ]
        )
        
        # 将HTML内容插入模板
        complete_html = HTML_TEMPLATE.format(
            title=title,
            description=description,
            content=html_content
        )
        
        # 写入HTML文件
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(complete_html)
        
        logger.debug(f"转换完成: {html_path}")
        return True
    except Exception as e:
        logger.error(f"转换 {md_file} 失败: {str(e)}")
        return False

def process_all_markdown_files():
    """处理docs目录下的所有Markdown文件"""
    success_count = 0
    fail_count = 0
    
    # 处理docs目录下的.md文件
    for md_file in DOCS_DIR.glob('*.md'):
        if convert_markdown_to_html(md_file, OUTPUT_DIR):
            success_count += 1
        else:
            fail_count += 1
    
    # 处理docs/api目录下的.md文件
    api_dir = DOCS_DIR / 'api'
    if api_dir.exists():
        api_output_dir = OUTPUT_DIR / 'api'
        api_output_dir.mkdir(exist_ok=True)
        
        for md_file in api_dir.glob('*.md'):
            if convert_markdown_to_html(md_file, api_output_dir):
                success_count += 1
            else:
                fail_count += 1
                
    # 复制相关的图片和资源文件
    assets_dir = DOCS_DIR / 'assets'
    if assets_dir.exists():
        assets_output_dir = OUTPUT_DIR / 'assets'
        if assets_output_dir.exists():
            shutil.rmtree(assets_output_dir)
        shutil.copytree(assets_dir, assets_output_dir)
        logger.debug(f"已复制资源文件夹: {assets_dir} -> {assets_output_dir}")
    
    logger.info(f"转换完成! 成功: {success_count}, 失败: {fail_count}")
    
if __name__ == "__main__":
    logger.info("开始转换Markdown文件...")
    process_all_markdown_files() 