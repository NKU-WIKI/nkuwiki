import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from etl.crawler import (
    crawler_logger, config, proxy_pool, default_user_agents, 
    default_timezone, default_locale, RAW_PATH
)
from etl.utils.const import domain_source_map, nankai_url_maps, nankai_start_urls
from etl.crawler.base_crawler import BaseCrawler
from etl.utils.date import parse_date
from etl.utils.file import clean_filename
from tqdm import tqdm
from typing import Any, List, Dict, Set
from pathlib import Path
import asyncio
import json
import time
import re
import hashlib
from datetime import datetime
from urllib.parse import urlparse, urljoin
try:
    import requests
    import aiohttp
    from bs4 import BeautifulSoup
except ImportError as e:
    print(f"缺少依赖包: {e}")
    print("请运行: pip install requests aiohttp beautifulsoup4 lxml")
    sys.exit(1)

class WebpageCrawler(BaseCrawler):
    """网页爬虫，继承BaseCrawler
    
    Attributes:
        start_urls: 起始URL列表
        debug: 调试模式开关
        headless: 是否使用无头浏览器模式
        use_proxy: 是否使用代理
        max_depth: 最大爬取深度
        max_pages: 最大爬取页面数
    """
    def __init__(self, start_urls: List[str], tag: str = "nku", debug: bool = False, 
                 headless: bool = True, use_proxy: bool = False, max_depth: int = 3, max_pages: int = 1000) -> None:
        """初始化网页爬虫
        
        Args:
            start_urls: 起始URL列表
            tag: 标签
            debug: 调试模式开关
            headless: 是否使用无头浏览器模式
            use_proxy: 是否使用代理
            max_depth: 最大爬取深度
            max_pages: 最大爬取页面数
        """
        self.platform = "website"  # 修改为website以兼容原有目录结构
        self.tag = tag
        self.content_type = "webpage"
        super().__init__(debug, headless, use_proxy, tag)
        
        if not start_urls:
            self.logger.error("起始URL列表不能为空")
            raise ValueError("起始URL列表不能为空")
            
        self.start_urls = start_urls
        self.max_depth = max_depth
        self.max_pages = max_pages
        self.visited_urls: Set[str] = set()
        self.crawled_count = 0
        
        # 允许的域名列表（提取自起始URL并扩展相关域名）
        self.allowed_domains = set()
        for url in start_urls:
            parsed = urlparse(url)
            if parsed.netloc:
                self.allowed_domains.add(parsed.netloc)
                
        # 添加南开大学相关的所有域名
        additional_domains = {
            'nankai.edu.cn', 'www.nankai.edu.cn', 'news.nankai.edu.cn',
            'jwc.nankai.edu.cn', 'graduate.nankai.edu.cn', 'career.nankai.edu.cn',
            'std.nankai.edu.cn', 'rsc.nankai.edu.cn', 'international.nankai.edu.cn',
            'lib.nankai.edu.cn', 'hq.nankai.edu.cn', 'cwc.nankai.edu.cn',
            'zzb.nankai.edu.cn', 'gh.nankai.edu.cn', 'guard.nankai.edu.cn',
            'museum.nankai.edu.cn', 'nkuaa.nankai.edu.cn', 'teda.nankai.edu.cn',
            'en.nankai.edu.cn', 'yzb.nankai.edu.cn', 'tyb.nankai.edu.cn',
            'fy.nankai.edu.cn', 'jsfz.nankai.edu.cn', 'nkuef.nankai.edu.cn',
            'nkzbb.nankai.edu.cn', 'nkjd.nankai.edu.cn', 'kexie.nankai.edu.cn',
        }
        self.allowed_domains.update(additional_domains)
        
        # 移除独立的快照目录，快照将保存在各文章目录下
        
        # 链接图数据库将在crawl方法中异步初始化
        
        depth_info = "无限制" if self.max_depth == -1 else str(self.max_depth)
        self.logger.info(f"初始化网页爬虫，起始URL数量: {len(self.start_urls)}, 最大深度: {depth_info}, 允许域名: {self.allowed_domains}")

    def is_valid_url(self, url: str) -> bool:
        """检查URL是否有效且在允许的域名内"""
        try:
            parsed_url = urlparse(url)
            
            # 基本URL格式检查
            if not (parsed_url.scheme in ['http', 'https'] and parsed_url.netloc):
                return False
                
            # 跳过特殊协议
            if url.startswith(('javascript:', 'mailto:', 'tel:', 'ftp:')):
                return False
                
            # 域名检查 - 允许子域名
            netloc = parsed_url.netloc
            domain_allowed = False
            for allowed_domain in self.allowed_domains:
                if netloc == allowed_domain or netloc.endswith('.' + allowed_domain):
                    domain_allowed = True
                    break
                    
            if not domain_allowed:
                return False
                
            # 检查是否已访问（用于避免重复）
            if url in self.visited_urls:
                return False
                
            # 检查URL路径是否包含明显的非内容标识（放宽限制）
            path = parsed_url.path.lower()
            exclude_patterns = ['/admin', '/login', '/logout', '/api/']
            if any(exclude in path for exclude in exclude_patterns):
                return False
                
            return True
        except:
            return False

    def is_content_url(self, url: str) -> bool:
        """判断是否为内容页面URL - 大幅优化识别逻辑，提高内容发现率"""
        # 文档文件（扩展更多格式）
        doc_extensions = ['.pdf', '.docx', '.doc', '.xlsx', '.xls', '.ppt', '.pptx', 
                         '.txt', '.rtf', '.zip', '.rar', '.7z']
        if any(url.lower().endswith(ext) for ext in doc_extensions):
            return True
            
        # 特定的招聘和企业信息URL（原scrapy爬虫逻辑）
        if 'https://career.nankai.edu.cn/company/index/id' in url:
            return True
            
        # 扩展特殊URL列表
        special_url_patterns = [
            r'career\.nankai\.edu\.cn/download/',
            r'career\.nankai\.edu\.cn/zpxx/',
            r'career\.nankai\.edu\.cn/jydt/',
            r'career\.nankai\.edu\.cn/jyzd/',
            r'jwc\.nankai\.edu\.cn/info/',
            r'graduate\.nankai\.edu\.cn/info/',
        ]
        for pattern in special_url_patterns:
            if re.search(pattern, url):
                return True
            
        # 严格排除明确的非内容页面
        strict_exclude_patterns = [
            r'/search[/?]',         # 搜索页面
            r'\?page=\d+&',         # 分页参数中的一部分
            r'/(login|logout|admin|register)/?$', # 管理和登录页面
            r'/sitemap\.xml',       # 站点地图
            r'/robots\.txt',        # robots文件
            r'\.css$',              # CSS文件
            r'\.js$',               # JavaScript文件
            r'\.png$|\.jpg$|\.jpeg$|\.gif$|\.bmp$|\.svg$', # 图片文件
        ]
        
        for pattern in strict_exclude_patterns:
            if re.search(pattern, url, re.IGNORECASE):
                return False
        
        # 大幅扩展内容页面识别模式
        content_indicators = [
            # 文件扩展名
            r'\.html?$',                      # HTML文件
            r'\.htm$',                        # HTM文件  
            r'\.shtml$',                      # SHTML文件
            r'\.php(\?|$)',                   # PHP文件
            r'\.asp(\?|$)',                   # ASP文件
            r'\.jsp(\?|$)',                   # JSP文件
            
            # 数字ID模式（更宽泛）
            r'/\d+',                          # 任何包含数字的路径
            r'\d{3,}',                        # 3位以上数字
            r'id=\d+',                        # URL参数中的ID
            r'articleid=\d+',                 # 文章ID
            r'newsid=\d+',                    # 新闻ID
            
            # 目录结构模式
            r'/info/',                        # info目录
            r'/news/',                        # news目录
            r'/notice/',                      # notice目录
            r'/article/',                     # article目录
            r'/post/',                        # post目录
            r'/content/',                     # content目录
            r'/detail/',                      # detail目录
            r'/view/',                        # view目录
            r'/show/',                        # show目录
            r'/read/',                        # read目录
            r'/page/',                        # page目录
            r'/item/',                        # item目录
            
            # 南开大学特有模式
            r'page\.htm',                     # page.htm
            r'news-detail',                   # 新闻详情
            r'/c\d+a\d+/',                    # 南开特有的c+a模式
            r'/_upload/',                     # 上传文件路径
            r'/system/',                      # 系统路径
            
            # 外部链接
            r'mp\.weixin\.qq\.com',           # 微信公众号链接
            
            # 内容关键词
            r'/(announcement|bulletin|notification|notice)/', # 公告、通知
            r'/(academic|research|science|study)/',           # 学术、研究
            r'/(student|teacher|faculty|professor)/',         # 学生、教师
            r'/(event|activity|conference|seminar)/',         # 事件、活动、会议
            r'/(publication|paper|journal)/',                 # 出版物、论文
            r'/(course|curriculum|education)/',               # 课程、教育
            r'/(lab|laboratory|center|institute)/',           # 实验室、中心、研究所
            r'/(download|file|document)/',                    # 下载、文件、文档
            
            # 中文关键词拼音
            r'/(xinwen|tongzhi|gonggao|xuesheng|jiaoshi)/',   # 新闻、通知、公告、学生、教师
            r'/(keyan|xueshu|huodong|huiyi)/',                # 科研、学术、活动、会议
            r'/(zhaosheng|jiuye|jiaoxue)/',                   # 招生、就业、教学
            
            # 南开网站常见栏目缩写
            r'/(xwzx|tzgg|xwdt|kydt|xsdt)/',                  # 新闻中心、通知公告、新闻动态、科研动态、学术动态
            r'/(ywsd|mtjj|zhxw|tbft)/',                       # 要闻速递、媒体聚焦、综合新闻、图片报道
            r'/(nkyw|xshd|rcpy|kxyj)/',                       # 南开要闻、学术活动、人才培养、科学研究
        ]
        
        # 如果URL匹配任何内容指示器，认为是内容页面
        for pattern in content_indicators:
            if re.search(pattern, url, re.IGNORECASE):
                return True
        
        # 路径结构分析 - 更宽松的条件
        parsed_url = urlparse(url)
        path = parsed_url.path
        query = parsed_url.query
        
        if path and len(path) > 1:
            # 排除明确的目录页面
            directory_patterns = [
                r'^/(index|home|main|default)/?$',
                r'^/(list|category|tag|archive)/?$',
                r'^/[^/]+/?$',  # 只有一级路径的可能是目录
            ]
            
            is_directory = False
            for pattern in directory_patterns:
                if re.search(pattern, path, re.IGNORECASE):
                    is_directory = True
                    break
            
            if not is_directory:
                # 如果路径包含多个段或有查询参数，很可能是内容页面
                path_segments = [seg for seg in path.split('/') if seg]
                if len(path_segments) >= 2 or query:
                    return True
                    
                # 如果路径包含特殊字符或数字，也可能是内容页面
                if re.search(r'[_\-\d]', path):
                    return True
        
        # 查询参数分析
        if query:
            # 常见的内容页面查询参数
            content_params = ['id', 'aid', 'pid', 'nid', 'cid', 'articleid', 'newsid']
            for param in content_params:
                if param in query.lower():
                    return True
        
        return False

    def extract_links(self, html_content: str, base_url: str) -> List[str]:
        """从HTML内容中提取链接 - 优化链接发现策略"""
        soup = BeautifulSoup(html_content, 'html.parser')
        links = []
        
        # 提取a标签链接
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href'].strip()
            
            # 跳过无效链接
            if not href or href == '#' or href.startswith('javascript:') or href.startswith('mailto:'):
                continue
                
            # 转换为绝对URL
            if not href.startswith('http'):
                href = urljoin(base_url, href)
                
            if self.is_valid_url(href):
                links.append(href)
        
        # 提取frame和iframe中的链接
        for frame_tag in soup.find_all(['frame', 'iframe'], src=True):
            src = frame_tag['src'].strip()
            if src and not src.startswith('javascript:'):
                if not src.startswith('http'):
                    src = urljoin(base_url, src)
                if self.is_valid_url(src):
                    links.append(src)
        
        # 提取页面中的分页链接（常见模式）
        page_patterns = [
            r'href=["\']([^"\']+page[^"\']*)["\']',
            r'href=["\']([^"\']+\d+\.html?)["\']',
            r'href=["\']([^"\']+list[^"\']*)["\']',
        ]
        
        for pattern in page_patterns:
            matches = re.findall(pattern, html_content, re.IGNORECASE)
            for match in matches:
                if not match.startswith('http'):
                    match = urljoin(base_url, match)
                if self.is_valid_url(match):
                    links.append(match)
        
        # 特别搜索南开网站常见的链接模式
        nankai_patterns = [
            r'href=["\']([^"\']*nankai\.edu\.cn[^"\']*)["\']',
            r'href=["\']([^"\']*info/\d+[^"\']*)["\']',
            r'href=["\']([^"\']*news/\d+[^"\']*)["\']',
            r'href=["\']([^"\']*article/\d+[^"\']*)["\']',
        ]
        
        for pattern in nankai_patterns:
            matches = re.findall(pattern, html_content, re.IGNORECASE)
            for match in matches:
                if not match.startswith('http'):
                    match = urljoin(base_url, match)
                if self.is_valid_url(match):
                    links.append(match)
        
        # 从JavaScript代码中提取链接（常见于动态页面）
        js_link_patterns = [
            r'window\.open\(["\']([^"\']+)["\']',
            r'location\.href\s*=\s*["\']([^"\']+)["\']',
            r'url:\s*["\']([^"\']+)["\']',
        ]
        
        for pattern in js_link_patterns:
            matches = re.findall(pattern, html_content, re.IGNORECASE)
            for match in matches:
                if not match.startswith('http'):
                    match = urljoin(base_url, match)
                if self.is_valid_url(match):
                    links.append(match)
        
        # 提取meta refresh重定向链接
        meta_refresh = soup.find('meta', attrs={'http-equiv': re.compile(r'^refresh$', re.I)})
        if meta_refresh and meta_refresh.get('content'):
            content = meta_refresh['content']
            url_match = re.search(r'url=(.+)', content, re.IGNORECASE)
            if url_match:
                refresh_url = url_match.group(1).strip('\'"')
                if not refresh_url.startswith('http'):
                    refresh_url = urljoin(base_url, refresh_url)
                if self.is_valid_url(refresh_url):
                    links.append(refresh_url)
        
        # 去重并返回
        return list(set(links))

    def get_source_name(self, url: str) -> str:
        """根据URL确定来源（学院名称） - 与scrapy爬虫逻辑一致"""
        parsed_url = urlparse(url)
        netloc = parsed_url.netloc
        
        # 查找匹配的学院名称
        for college_name, college_url in nankai_url_maps.items():
            college_parsed = urlparse(college_url)
            if netloc == college_parsed.netloc:
                return college_name
                
        # 使用导入的域名映射字典
        if netloc in domain_source_map:
            return domain_source_map[netloc]
                
        # 如果没有找到，返回域名
        return netloc

    def extract_content(self, html_content: str, url: str) -> Dict[str, Any]:
        """从HTML内容中提取文章信息"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # 提取标题
        title = ""
        if soup.title:
            title = soup.title.get_text().strip()
        elif soup.find('h1'):
            title = soup.find('h1').get_text().strip()
            
        # 提取发布时间 - 更精确的时间提取
        publish_time = ""
        
        # 首先从URL中提取时间（如原scrapy爬虫的get_datestr_from_url）
        # 只匹配真正的日期格式：2024/01/01
        date_match = re.search(r"(\d{4})/(\d{2})/(\d{2})", url)
        if date_match:
            year, month, day = date_match.groups()
            # 严格验证日期合理性
            try:
                year_int = int(year)
                month_int = int(month)
                day_int = int(day)
                if (2000 <= year_int <= 2030 and 
                    1 <= month_int <= 12 and 
                    1 <= day_int <= 31):
                    publish_time = f"{year}-{month}-{day}"
            except ValueError:
                pass
        
        if not publish_time:
            # 匹配紧凑格式：2024/0312，但要验证月日
            date_match = re.search(r"(\d{4})/(\d{2})(\d{2})", url)
            if date_match:
                year, month, day = date_match.groups()
                try:
                    year_int = int(year)
                    month_int = int(month)
                    day_int = int(day)
                    if (2000 <= year_int <= 2030 and 
                        1 <= month_int <= 12 and 
                        1 <= day_int <= 31):
                        publish_time = f"{year}-{month}-{day}"
                except ValueError:
                    pass
        
        # 如果URL中没有时间，从页面内容中提取
        if not publish_time:
            time_patterns = [
                r'(\d{4})[-/](\d{1,2})[-/](\d{1,2})',
                r'(\d{4})年(\d{1,2})月(\d{1,2})日',
                r'发布时间[：:]?\s*(\d{4})[-/](\d{1,2})[-/](\d{1,2})',
                r'时间[：:]?\s*(\d{4})[-/](\d{1,2})[-/](\d{1,2})',
                r'日期[：:]?\s*(\d{4})[-/](\d{1,2})[-/](\d{1,2})'
            ]
            
            page_text = soup.get_text()
            for pattern in time_patterns:
                match = re.search(pattern, page_text)
                if match:
                    groups = match.groups()
                    if len(groups) >= 3:
                        year, month, day = groups[:3]
                        # 验证日期的合理性
                        try:
                            month = int(month)
                            day = int(day)
                            year = int(year)
                            if 1990 <= year <= 2030 and 1 <= month <= 12 and 1 <= day <= 31:
                                publish_time = f"{year}-{month:02d}-{day:02d}"
                                break
                        except ValueError:
                            continue
                    else:
                        publish_time = match.group(0)
                        break
        
        # 提取正文内容 - 更精确的内容提取
        content = ""
        # 移除脚本和样式标签
        for tag in soup(["script", "style", "nav", "header", "footer"]):
            tag.decompose()
            
        # 尝试找到主要内容区域（优先查找wp_articlecontent类，这是南开网站常用的）
        main_content = (
            soup.find('div', class_='wp_articlecontent') or
            soup.find('div', class_=re.compile(r'content|article|main', re.I)) or
            soup.find('article') or
            soup.find('main') or
            soup.body
        )
        
        if main_content:
            content = main_content.get_text(separator='\n', strip=True)
            # 清理内容
            content = re.sub(r'\n\s*\n', '\n', content).strip()
            content = content.replace('\xa0', ' ')  # 替换不间断空格
            
        # 确定来源 - 使用映射表
        source = self.get_source_name(url)
        
        # 检查是否为PDF等文档
        file_url = None
        if any(url.lower().endswith(ext) for ext in ['.pdf', '.docx', '.doc', '.xlsx', '.xls']):
            file_url = url
            
        # 检查页面中是否有PDF播放器（南开网站特有）
        if not file_url and not content.replace(' ', ''):
            pdf_player = soup.find('div', class_='wp_pdf_player')
            if pdf_player and pdf_player.get('pdfsrc'):
                pdf_src = pdf_player.get('pdfsrc')
                if not pdf_src.startswith('http'):
                    parsed_url = urlparse(url)
                    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
                    pdf_src = base_url + pdf_src
                file_url = pdf_src
        
        return {
            'title': title,
            'publish_time': publish_time,
            'content': content,
            'source': source,
            'url': url,
            'file_url': file_url
        }

    def save_snapshot(self, html_content: str, url: str, article_dir: Path) -> None:
        """保存网页快照到文章目录下
        
        Args:
            html_content: HTML内容
            url: 原始URL
            article_dir: 文章目录路径
        """
        try:
            # 保存为原始文件名.html
            snapshot_file = article_dir / "original.html"
            
            if isinstance(html_content, str):
                html_content = html_content.encode('utf-8')
                
            with open(snapshot_file, 'wb') as f:
                f.write(html_content)
                
            self.logger.debug(f"网页快照已保存: {snapshot_file}")
        except Exception as e:
            self.logger.error(f"保存网页快照失败: {e}")

    async def init_link_graph_db(self) -> None:
        """初始化链接图数据库（使用MySQL）"""
        try:
            from etl.load.db_core import execute_query
            
            # 创建链接图表（如果不存在）- 使用已创建的表结构
            await execute_query('''
                CREATE TABLE IF NOT EXISTS link_graph (
                    id bigint(20) NOT NULL AUTO_INCREMENT,
                    source_url varchar(255) NOT NULL COMMENT '源页面URL',
                    target_url varchar(255) NOT NULL COMMENT '目标页面URL',
                    anchor_text varchar(255) DEFAULT NULL COMMENT '链接锚文本',
                    link_type varchar(20) DEFAULT 'internal' COMMENT '链接类型：internal-内部链接, external-外部链接',
                    create_time datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                    update_time datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                    PRIMARY KEY (id),
                    UNIQUE KEY uk_source_target (source_url, target_url),
                    KEY idx_source_url (source_url),
                    KEY idx_target_url (target_url),
                    KEY idx_link_type (link_type)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='页面链接关系表'
            ''', fetch=False)
            
            # 创建PageRank分数表（如果不存在）- 使用已创建的表结构
            await execute_query('''
                CREATE TABLE IF NOT EXISTS pagerank_scores (
                    id bigint(20) NOT NULL AUTO_INCREMENT,
                    url varchar(255) NOT NULL COMMENT '页面URL',
                    pagerank_score double NOT NULL DEFAULT '0' COMMENT 'PageRank分数',
                    in_degree int(11) NOT NULL DEFAULT '0' COMMENT '入度（指向该页面的链接数）',
                    out_degree int(11) NOT NULL DEFAULT '0' COMMENT '出度（该页面指向其他页面的链接数）',
                    calculation_date datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'PageRank计算时间',
                    create_time datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                    update_time datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                    PRIMARY KEY (id),
                    UNIQUE KEY uk_url (url),
                    KEY idx_pagerank_score (pagerank_score DESC),
                    KEY idx_calculation_date (calculation_date)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='PageRank分数表'
            ''', fetch=False)
            
            self.logger.info("链接图MySQL数据库初始化完成")
            
        except Exception as e:
            self.logger.error(f"初始化链接图MySQL数据库失败: {e}")

    async def save_link_graph(self, source_url: str, target_urls: List[str]) -> None:
        """保存链接关系到MySQL数据库
        
        Args:
            source_url: 源URL
            target_urls: 目标URL列表
        """
        if not target_urls:
            return
            
        try:
            from etl.load.db_core import execute_query
            
            # 批量插入链接关系 - 逐个插入以避免重复
            for target_url in target_urls:
                try:
                    # 使用INSERT IGNORE来避免重复插入
                    await execute_query('''
                        INSERT IGNORE INTO link_graph (source_url, target_url, link_type)
                        VALUES (%s, %s, %s)
                    ''', [source_url, target_url, 'internal'], fetch=False)
                except Exception as insert_error:
                    self.logger.warning(f"插入链接关系失败: {source_url} -> {target_url}, 错误: {insert_error}")
                    continue
            
            self.logger.debug(f"保存了 {len(target_urls)} 个链接关系到MySQL，源URL: {source_url[:50]}...")
            
        except Exception as e:
            self.logger.error(f"保存链接关系到MySQL失败: {e}")

    async def crawl_url(self, url: str, depth: int, session: 'aiohttp.ClientSession' = None) -> Dict[str, Any]:
        """爬取单个URL（并发版本）"""
        # 检查深度限制（-1表示无限制）和页面数量限制
        if ((self.max_depth != -1 and depth > self.max_depth) or 
            self.crawled_count >= self.max_pages):
            return {"url": url, "links": [], "article_data": None, "success": False}
            
        if url in self.visited_urls:
            return {"url": url, "links": [], "article_data": None, "success": False}
            
        self.visited_urls.add(url)
        
        try:
            if session:
                # 使用aiohttp进行更快的HTTP请求
                async with session.get(url, timeout=15) as response:
                    if response.status == 200:
                        html_content = await response.text()
                    else:
                        raise Exception(f"HTTP {response.status}")
            else:
                # 回退到playwright
                await self.page.goto(url, wait_until='domcontentloaded', timeout=15000)
                html_content = await self.page.content()
            
            # 提取链接用于进一步爬取
            links = self.extract_links(html_content, url)
            
            # 提取内容
            article_data = None
            if self.is_content_url(url):
                article_data = self.extract_content(html_content, url)
                
                # 检查是否有有效内容
                if article_data['title'] or article_data['content']:
                    article_data['html_content'] = html_content  # 保存HTML用于批量处理
                    self.crawled_count += 1
                    self.counter['scrape'] += 1
                    
            self.counter['visit'] += 1
            
            return {
                "url": url, 
                "links": links, 
                "article_data": article_data, 
                "success": True
            }
            
        except Exception as e:
            self.logger.debug(f"爬取URL失败: {url}, 错误: {e}")
            self.counter['error'] += 1
            return {"url": url, "links": [], "article_data": None, "success": False}

    def save_article(self, article_data: Dict[str, Any], html_content: str = None) -> None:
        """保存文章数据（包括HTML快照）
        
        Args:
            article_data: 文章数据字典
            html_content: 原始HTML内容，如果提供则保存为快照
        """
        try:
            title = article_data.get('title', '未知标题')
            clean_title = clean_filename(title)
            
            # 根据发布时间组织目录结构
            publish_time = article_data.get('publish_time', '')
            if publish_time:
                try:
                    # 尝试多种日期格式
                    date_match = re.search(r'(\d{4})[-/](\d{1,2})[-/]\d{1,2}', publish_time)
                    if date_match:
                        year = date_match.group(1)
                        month = date_match.group(2).zfill(2)  # 补零到两位数
                        year_month = f"{year}{month}"
                    else:
                        # 如果没有匹配到完整日期，尝试匹配年月
                        year_month_match = re.search(r'(\d{4})[-/](\d{1,2})', publish_time)
                        if year_month_match:
                            year = year_month_match.group(1)
                            month = year_month_match.group(2).zfill(2)
                            year_month = f"{year}{month}"
                        else:
                            year_month = datetime.now().strftime("%Y%m")
                except:
                    year_month = datetime.now().strftime("%Y%m")
            else:
                year_month = datetime.now().strftime("%Y%m")
                
            save_dir = self.data_dir / year_month
            save_dir.mkdir(exist_ok=True, parents=True)
            
            # 创建文章专属目录
            article_dir = save_dir / clean_title[:50]  # 限制目录名长度
            article_dir.mkdir(exist_ok=True, parents=True)
            
            # 保存文章元数据
            meta = {
                "platform": self.platform,
                "original_url": article_data.get('url', ''),
                "title": title,
                "publish_time": publish_time,
                "scrape_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "content_type": self.content_type,
                "content": article_data.get('content', ''),
                "file_url": article_data.get('file_url', '')
            }
            
            with open(article_dir / f"{clean_title[:50]}.json", 'w', encoding='utf-8') as f:
                json.dump(meta, f, ensure_ascii=False, indent=2)
                
            # 保存内容到markdown文件
            content = article_data.get('content', '')
            if content:
                with open(article_dir / f"{clean_title[:50]}.md", 'w', encoding='utf-8') as f:
                    f.write(f"# {title}\n\n")
                    f.write(f"发布时间: {publish_time}\n\n")
                    f.write(f"来源: {article_data.get('platform', '')}\n\n")
                    f.write(f"链接: {article_data.get('url', '')}\n\n")
                    f.write("---\n\n")
                    f.write(content)
            
            # 保存HTML快照（如果提供）
            if html_content:
                self.save_snapshot(html_content, article_data.get('url', ''), article_dir)
                    
            self.logger.debug(f"文章已保存: {clean_title}")
            
        except Exception as e:
            self.logger.error(f"保存文章失败: {e}")
            self.counter['error'] += 1

    async def batch_save_articles(self, article_batch: List[Dict[str, Any]]) -> None:
        """批量保存文章数据"""
        if not article_batch:
            return
            
        link_relations = []  # 收集链接关系用于批量保存
        
        for item in article_batch:
            try:
                article_data = item['article_data']
                if not article_data:
                    continue
                    
                # 保存文章
                html_content = article_data.pop('html_content', None)
                self.save_article(article_data, html_content)
                
                # 收集链接关系
                url = item['url']
                links = item['links']
                if links:
                    link_relations.append((url, links))
                    
            except Exception as e:
                self.logger.error(f"批量保存文章失败: {e}")
        
        # 批量保存链接关系
        if link_relations:
            await self.batch_save_link_graph(link_relations)

    async def batch_save_link_graph(self, link_relations: List[tuple]) -> None:
        """批量保存链接关系"""
        try:
            from etl.load.db_core import execute_query
            
            # 准备批量插入数据
            insert_data = []
            for source_url, target_urls in link_relations:
                for target_url in target_urls:
                    insert_data.append((source_url, target_url, 'internal'))
            
            if insert_data:
                # 批量插入，每次最多500条
                batch_size = 500
                for i in range(0, len(insert_data), batch_size):
                    batch = insert_data[i:i + batch_size]
                    
                    placeholders = ','.join(['(%s, %s, %s)'] * len(batch))
                    sql = f'''
                        INSERT IGNORE INTO link_graph (source_url, target_url, link_type)
                        VALUES {placeholders}
                    '''
                    
                    flat_data = [item for row in batch for item in row]
                    await execute_query(sql, flat_data, fetch=False)
                    
                self.logger.debug(f"批量保存了 {len(insert_data)} 个链接关系")
                
        except Exception as e:
            self.logger.error(f"批量保存链接关系失败: {e}")

    async def crawl(self, concurrent_limit: int = 20, batch_size: int = 50, fresh_start: bool = False) -> None:
        """执行爬取任务（并发优化版本）"""
        try:
            import aiohttp
            
            # 初始化链接图数据库
            await self.init_link_graph_db()
            
            # 先获取已经抓取的链接（除非是全新开始）
            if not fresh_start:
                scraped_original_urls = self.get_scraped_original_urls()
                self.visited_urls.update(scraped_original_urls)
                self.logger.info(f"已加载 {len(scraped_original_urls)} 个历史URL记录")
            else:
                self.logger.info("全新开始爬取，忽略历史记录")
            
            start_time = time.time()
            
            if not self.debug:
                lock_path = self.base_dir / self.lock_file
                lock_path.write_text(str(int(start_time)))
                
            # 使用队列管理URL
            url_queue = list(self.start_urls)
            depth_map = {url: 0 for url in self.start_urls}
            
            self.logger.info(f"初始URL队列大小: {len(url_queue)}")
            self.logger.info(f"已访问URL数量: {len(self.visited_urls)}")
            
            # 过滤掉已访问的URL
            original_queue_size = len(url_queue)
            url_queue = [url for url in url_queue if url not in self.visited_urls]
            self.logger.info(f"过滤后URL队列大小: {len(url_queue)} (过滤掉 {original_queue_size - len(url_queue)} 个已访问URL)")
            
            # 并发和批处理配置
            save_batch_size = max(10, batch_size // 3)  # 每次保存的文章数量
            
            # 创建aiohttp会话，用于快速HTTP请求
            # 处理无限制并发的情况
            if concurrent_limit is None:
                connector = aiohttp.TCPConnector(
                    limit=None,  # 无限制
                    limit_per_host=None,  # 每个主机也无限制
                    ttl_dns_cache=300,
                    use_dns_cache=True,
                )
            else:
                connector = aiohttp.TCPConnector(
                    limit=concurrent_limit,
                    limit_per_host=min(10, concurrent_limit // 2),  # 每个主机限制为总限制的一半
                    ttl_dns_cache=300,
                    use_dns_cache=True,
                )
            
            timeout = aiohttp.ClientTimeout(total=15, connect=5)
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            article_buffer = []  # 文章缓冲区
            
            async with aiohttp.ClientSession(
                connector=connector, 
                timeout=timeout,
                headers=headers
            ) as session:
                
                # 创建进度条
                with tqdm(total=self.max_pages, desc="🕷️ 网页爬取进度", unit="页") as pbar:
                    batch_count = 0
                    
                    while url_queue and self.crawled_count < self.max_pages:
                        # 获取当前批次的URL
                        current_batch = []
                        batch_urls = []
                        batch_depths = []
                        
                        for _ in range(min(batch_size, len(url_queue), self.max_pages - self.crawled_count)):
                            if url_queue:
                                url = url_queue.pop(0)
                                depth = depth_map.get(url, 0)
                                # 检查深度限制（-1表示无限制）
                                if self.max_depth == -1 or depth <= self.max_depth:
                                    current_batch.append(url)
                                    batch_urls.append(url)
                                    batch_depths.append(depth)
                        
                        if not current_batch:
                            break
                            
                        batch_count += 1
                        
                        # 并发爬取当前批次
                        tasks = []
                        for url, depth in zip(batch_urls, batch_depths):
                            task = self.crawl_url(url, depth, session)
                            tasks.append(task)
                        
                        # 执行并发任务
                        results = await asyncio.gather(*tasks, return_exceptions=True)
                        
                        # 处理结果
                        new_articles = []
                        total_new_links = 0
                        
                        for result in results:
                            if isinstance(result, dict) and result['success']:
                                # 添加新链接到队列 - 优化队列管理
                                current_depth = depth_map.get(result['url'], 0)
                                for link in result['links']:
                                    if (link not in self.visited_urls and 
                                        link not in depth_map and 
                                        len(url_queue) < 200000 and  # 增加队列大小限制到20万
                                        (self.max_depth == -1 or current_depth < self.max_depth)):  # 检查深度限制（-1表示无限制）
                                        
                                        # 优先添加内容页面到队列前部
                                        if self.is_content_url(link):
                                            url_queue.insert(0, link)  # 内容页面优先处理
                                        else:
                                            url_queue.append(link)  # 普通页面放在后面
                                            
                                        depth_map[link] = current_depth + 1
                                        total_new_links += 1
                                
                                # 收集文章数据
                                if result['article_data']:
                                    new_articles.append(result)
                        
                        # 添加到缓冲区
                        article_buffer.extend(new_articles)
                        
                        # 达到保存批次大小时进行批量保存
                        if len(article_buffer) >= save_batch_size:
                            await self.batch_save_articles(article_buffer[:save_batch_size])
                            article_buffer = article_buffer[save_batch_size:]
                        
                        # 更新进度条
                        pbar.set_postfix({
                            "批次": batch_count,
                            "并发": len(current_batch),
                            "成功": len([r for r in results if isinstance(r, dict) and r['success']]),
                            "新文章": len(new_articles),
                            "缓冲": len(article_buffer),
                            "队列": len(url_queue),
                            "新链接": total_new_links,
                            "已访问": len(self.visited_urls),
                            "深度图": len(depth_map),
                            "成功率": f"{(self.counter['visit'] - self.counter['error']) / max(1, self.counter['visit']) * 100:.1f}%"
                        })
                        
                        if self.crawled_count > pbar.n:
                            pbar.update(self.crawled_count - pbar.n)
                        
                        # 每100个批次输出详细统计
                        if batch_count % 100 == 0:
                            self.logger.info(f"批次 {batch_count}: 队列={len(url_queue)}, 已访问={len(self.visited_urls)}, 爬取文章={self.crawled_count}")
                            # 统计队列中各种深度的URL数量
                            depth_stats = {}
                            for url in url_queue[:1000]:  # 只统计前1000个避免性能问题
                                depth = depth_map.get(url, 0)
                                depth_stats[depth] = depth_stats.get(depth, 0) + 1
                            self.logger.info(f"深度分布: {depth_stats}")
                        
                        # 短暂休息避免过于频繁的请求
                        if not self.debug:
                            await asyncio.sleep(0.1)
                
                # 保存剩余的文章
                if article_buffer:
                    await self.batch_save_articles(article_buffer)
                    
                # 记录退出原因
                if not url_queue:
                    self.logger.info(f"爬取结束：URL队列为空")
                elif self.crawled_count >= self.max_pages:
                    self.logger.info(f"爬取结束：达到最大页面数限制 {self.max_pages}")
                else:
                    self.logger.info(f"爬取结束：未知原因，队列大小={len(url_queue)}, 爬取数量={self.crawled_count}")
                        
            # 保存已爬取的URL列表
            all_visited = list(self.visited_urls)
            self.update_scraped_articles(all_visited, [])
            
            if not self.debug:
                lock_path.unlink()
                
            elapsed_time = time.time() - start_time
            self.save_counter(start_time)
            
            self.logger.info(f"🎉 爬取完成！统计信息：")
            self.logger.info(f"  - 共爬取页面: {self.crawled_count}")
            self.logger.info(f"  - 访问URL数: {self.counter['visit']}")
            self.logger.info(f"  - 发现链接数: {len(self.visited_urls)}")
            self.logger.info(f"  - 错误次数: {self.counter['error']}")
            self.logger.info(f"  - 成功率: {(self.counter['visit'] - self.counter['error']) / max(1, self.counter['visit']) * 100:.1f}%")
            self.logger.info(f"  - 平均速度: {self.counter['visit'] / elapsed_time:.1f} 页/秒")
            self.logger.info(f"  - 用时: {elapsed_time:.1f} 秒")
            
        except Exception as e:
            self.logger.error(f"爬取出错: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
        finally:
            if hasattr(self, 'update_f') and self.update_f:
                self.update_f.close()

    async def download(self, time_range: tuple = None):
        """下载功能（网页爬虫中实际上是在crawl中完成的）"""
        self.logger.info("网页爬虫的下载功能已集成在crawl方法中")

    def import_from_scrapy_db(self, db_path: str = None) -> int:
        """从scrapy的sqlite数据库导入数据到统一格式
        
        Args:
            db_path: sqlite数据库路径，如果为None则使用默认路径
            
        Returns:
            导入的记录数量
        """
        import sqlite3
        
        if db_path is None:
            # 使用默认的scrapy数据库路径
            scrapy_dir = Path(__file__).parent / "webpage_spider" / "counselor"
            db_path = scrapy_dir / "nk_database.db"
            
        if not Path(db_path).exists():
            self.logger.error(f"数据库文件不存在: {db_path}")
            return 0
            
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # 查询所有记录
            cursor.execute("""
                SELECT title, push_time, url, content, file_url, source, push_time_date 
                FROM entries 
                ORDER BY id
            """)
            
            rows = cursor.fetchall()
            imported_count = 0
            
            with tqdm(total=len(rows), desc="导入scrapy数据", unit="条") as pbar:
                for row in rows:
                    title, push_time, url, content, file_url, source, push_time_date = row
                    
                    # 转换为统一格式
                    article_data = {
                        'title': title or '未知标题',
                        'publish_time': push_time or '',
                        'content': content or '',
                        'source': source or 'unknown',
                        'url': url,
                        'file_url': file_url or None
                    }
                    
                    # 保存文章数据
                    try:
                        self.save_article(article_data)
                        imported_count += 1
                    except Exception as e:
                        self.logger.error(f"导入记录失败: {url}, 错误: {e}")
                        
                    pbar.update(1)
                    pbar.set_postfix({"已导入": imported_count})
                    
            conn.close()
            self.logger.info(f"从scrapy数据库成功导入 {imported_count} 条记录")
            return imported_count
            
        except Exception as e:
            self.logger.error(f"导入scrapy数据时出错: {e}")
            return 0

    def export_to_mysql(self) -> bool:
        """导出数据到MySQL数据库（与ETL流程兼容）"""
        try:
            from etl.load.import_data import main as import_main
            
            # 调用现有的导入脚本
            self.logger.info("开始导出数据到MySQL...")
            success = import_main()
            
            if success:
                self.logger.info("数据导出到MySQL成功")
            else:
                self.logger.error("数据导出到MySQL失败")
                
            return success
            
        except Exception as e:
            self.logger.error(f"导出到MySQL时出错: {e}")
            return False

    def calculate_pagerank(self) -> bool:
        """计算PageRank分数"""
        try:
            # 直接导入并运行PageRank计算脚本
            import sys
            pagerank_dir = Path(__file__).parent.parent / "pagerank"
            sys.path.append(str(pagerank_dir))
            
            from calculate_pagerank import main as pagerank_main
            
            self.logger.info("开始计算PageRank分数...")
            pagerank_main()
            self.logger.info("PageRank计算完成")
            return True
            
        except Exception as e:
            self.logger.error(f"计算PageRank失败: {e}")
            return False

    def get_statistics(self) -> Dict[str, Any]:
        """获取爬虫统计信息"""
        stats = {
            "platform": self.platform,
            "tag": self.tag,
            "start_urls_count": len(self.start_urls),
            "allowed_domains": list(self.allowed_domains),
            "max_depth": self.max_depth,
            "max_pages": self.max_pages,
            "visited_urls_count": len(self.visited_urls),
            "crawled_count": self.crawled_count,
            "counters": dict(self.counter),
            "data_dir": str(self.data_dir)
        }
        
        # 统计保存的文件数量
        json_files = list(self.data_dir.glob("**/*.json"))
        md_files = list(self.data_dir.glob("**/*.md"))
        html_files = list(self.data_dir.glob("**/original.html"))
        
        stats.update({
            "saved_json_files": len(json_files),
            "saved_md_files": len(md_files),
            "saved_html_snapshots": len(html_files)
        })
        
        return stats



if __name__ == "__main__":
    async def main():
        """异步主函数"""
        import argparse
        
        parser = argparse.ArgumentParser(description="网页爬虫工具")
        parser.add_argument("--mode", choices=["crawl", "import", "export", "pagerank", "stats"], 
                          default="crawl", help="运行模式")
        parser.add_argument("--debug", action="store_true", help="调试模式")
        parser.add_argument("--headless", action="store_true", default=True, help="无头模式")
        parser.add_argument("--proxy", action="store_true", help="使用代理")
        parser.add_argument("--max-depth", type=int, default=-1, help="最大爬取深度，-1表示无限制")
        parser.add_argument("--max-pages", type=int, default=110000, help="最大爬取页面数")
        parser.add_argument("--start-urls", type=int, default=-1, help="使用的起始URL数量，-1表示使用全部")
        parser.add_argument("--concurrent", type=int, default=-1, help="并发请求数量，-1表示无限制")
        parser.add_argument("--batch-size", type=int, default=1000, help="每批处理的URL数量")
        parser.add_argument("--fresh-start", action="store_true",default=True, help="全新开始，忽略历史记录")
        
        args = parser.parse_args()
        
        # 处理起始URL数量参数
        if args.start_urls == -1:
            start_urls = nankai_start_urls  # 使用全部URL
        else:
            start_urls = nankai_start_urls[:args.start_urls]  # 使用指定数量
            
        # 处理并发数量参数
        concurrent_limit = None if args.concurrent == -1 else args.concurrent
            
        crawler = WebpageCrawler(
            start_urls=start_urls,
            tag="nku",
            debug=args.debug,
            headless=args.headless,
            use_proxy=args.proxy,
            max_depth=args.max_depth,
            max_pages=args.max_pages
        )
        
        try:
            if args.mode in ["crawl", "export", "stats"]:
                await crawler.async_init()
            
            if args.mode == "crawl":
                print("🚀 开始网页爬取...")
                concurrent_display = "无限制" if args.concurrent == -1 else str(args.concurrent)
                print(f"⚙️  配置: 并发={concurrent_display}, 批次大小={args.batch_size}, 最大页面={args.max_pages}")
                print(f"🔗 起始URL: {len(start_urls)} 个 (总共可用: {len(nankai_start_urls)} 个)")
                if args.fresh_start:
                    print("🆕 全新开始模式，将忽略历史爬取记录")
                await crawler.crawl(
                    concurrent_limit=concurrent_limit,
                    batch_size=args.batch_size,
                    fresh_start=args.fresh_start
                )
                
                # 显示统计信息
                stats = crawler.get_statistics()
                print("\n📊 爬取统计:")
                for key, value in stats.items():
                    if key not in ["allowed_domains", "data_dir"]:
                        print(f"  {key}: {value}")
                        
            elif args.mode == "import":
                print("📥 从scrapy数据库导入数据...")
                count = crawler.import_from_scrapy_db()
                print(f"✅ 成功导入 {count} 条记录")
                
            elif args.mode == "export":
                print("📤 导出数据到MySQL...")
                success = crawler.export_to_mysql()
                if success:
                    print("✅ 数据导出成功")
                else:
                    print("❌ 数据导出失败")
                    
            elif args.mode == "pagerank":
                print("🔗 计算PageRank分数...")
                success = crawler.calculate_pagerank()
                if success:
                    print("✅ PageRank计算成功")
                else:
                    print("❌ PageRank计算失败")
                    
            elif args.mode == "stats":
                stats = crawler.get_statistics()
                print("\n📊 详细统计信息:")
                import json
                print(json.dumps(stats, indent=2, ensure_ascii=False))
                
        except KeyboardInterrupt:
            print("\n⚠️  用户中断操作")
        except Exception as e:
            print(f"❌ 运行出错: {e}")
        finally:
            if hasattr(crawler, 'browser') and crawler.browser:
                await crawler.close()

    # 运行异步主函数
    asyncio.run(main()) 