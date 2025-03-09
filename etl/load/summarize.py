import os
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from collections import defaultdict

def load_json_files(directory: str, time_range: Optional[Tuple[str, str]] = None) -> List[Dict]:
    """
    加载指定目录下的所有JSON文件，但只处理包含abstract.md文件的文件夹
    
    Args:
        directory: 基础目录路径
        time_range: 可选的时间范围元组 (start_yyyymm, end_yyyymm)，例如 ('202301', '202303')
    """
    articles = []
    
    # 获取所有子目录
    base_dir = Path(directory)
    all_dirs = []
    
    # 如果指定了时间范围，首先过滤顶层目录
    if time_range:
        start_time, end_time = time_range
        year_month_dirs = []
        for d in base_dir.iterdir():
            if d.is_dir() and d.name.isdigit() and len(d.name) == 6:
                if start_time <= d.name <= end_time:
                    year_month_dirs.append(d)
        
        # 获取所有嵌套的子目录
        for year_month_dir in year_month_dirs:
            for nested_dir in year_month_dir.iterdir():
                if nested_dir.is_dir():
                    all_dirs.append(nested_dir)
    else:
        # 如果没有指定时间范围，则递归获取所有子目录
        for root, dirs, _ in os.walk(directory):
            for dir_name in dirs:
                all_dirs.append(Path(root) / dir_name)
    
    # 遍历所有符合条件的目录
    for dir_path in all_dirs:
        # 只处理包含abstract.md文件的文件夹
        if (dir_path / "abstract.md").exists():
            for file_path in dir_path.glob('*.json'):
                with open(file_path, 'r', encoding='utf-8') as f:
                    try:
                        data = json.load(f)
                        articles.append(data)
                    except json.JSONDecodeError:
                        print(f"Error loading {file_path}")
    
    return articles

def filter_recruitment_articles(articles: List[Dict]) -> List[Dict]:
    """
    过滤掉标题中含有招聘相关词汇的文章
    
    Args:
        articles: 原始文章列表
    
    Returns:
        过滤后的文章列表
    """
    filtered_articles = []
    recruitment_keywords = [
        # 招聘类型
        "社招", "校招", "招聘", "招募", "招人", "内推", "推荐", "猎头", 
        "秋招", "春招", "暑期", "实习", "应届", "毕业生", 
        
        # 求职相关
        "求职", "找工作", "就业", "简历", "面试", "笔试", "offer", "入职",
        "应聘", "岗位", "职位", "职场", "职业", "加入", "工作", "职责",
        
        # 人才/HR用语
        "人才", "候选人", "人事", "HR", "人力资源", "用人", "招才", "猎聘",
        "headhunter", "talent", "急聘", "高薪",
        
        # 行业招聘
        "算法岗", "开发岗", "研发", "测试", "工程师", "后端", "前端", "全栈",
        "产品", "设计", "运维", "安全", "大数据", "人工智能", "AI", "IT",
        "运营岗", "市场", "销售", "客服", "行政", "财务", "法务",
        
        # 招聘流程
        "投递", "筛选", "电话面", "视频面", "现场面", "笔试题", "技术面", "三轮面",
        "薪资", "待遇", "福利", "加薪", "晋升", "职级", "JD", "岗位描述",
        
        # 其他相关
        "求内推", "HC", "名额", "职缺", "空缺", "入场", "转正", "劳务",
        "简历模板", "面经", "面试题", "经验分享", "求职经验"
    ]
    
    for article in articles:
        title = article.get('title', '')
        if not any(keyword in title for keyword in recruitment_keywords):
            filtered_articles.append(article)
    
    return filtered_articles

def generate_markdown_summary(articles: List[Dict], output_file_base: str):
    """
    生成markdown格式的总结，按块分割
    每块小于2000行，同一作者不会被分成两块
    输出为job1.md, job2.md等多个文件
    """
    # 按作者分组
    author_groups = defaultdict(list)
    for article in articles:
        author = article.get('author', '未知作者')
        author_groups[author].append(article)
    
    # 对每个作者的文章按时间排序
    for author, posts in author_groups.items():
        posts.sort(key=lambda x: datetime.strptime(x['publish_time'], '%Y-%m-%d'), reverse=True)
    
    # 获取所有文章中最新的发布时间
    latest_date = datetime.now()  # 默认为当前日期
    if articles:
        try:
            # 找出所有文章中最新的发布日期
            latest_date_str = max(article['publish_time'] for article in articles)
            latest_date = datetime.strptime(latest_date_str, '%Y-%m-%d')
        except (ValueError, KeyError) as e:
            print(f"获取最新发布日期时出错: {e}，使用当前日期")
    
    # 使用简短日期格式：MMDD
    latest_short_date = f"{latest_date.month:02d}{latest_date.day:02d}"
    output_file_base = Path(output_file_base).with_suffix('')  # 移除扩展名
    
    # 预计算每个作者内容的行数
    author_line_counts = {}
    for author, posts in author_groups.items():
        # 计算作者标题行 + 每篇文章的行数
        total_lines = 2  # 作者标题 + 空行
        for post in posts:
            title = post['title']
            content = post.get('content', '')
            
            # 截断过长的内容
            if len(content) > 500:
                content = content[:500] + "..."
            
            # 标题行 + 内容行 + 空行
            content_lines = content.count('\n') + 1
            post_lines = 2 + content_lines + 1
            total_lines += post_lines
        
        author_line_counts[author] = total_lines
    
    # 分组作者到不同的块，每块小于2000行
    current_block = []
    current_block_lines = 0
    blocks = []
    
    # 添加标题计入总行数
    header_lines = 2  # 标题 + 空行
    
    # 按照行数从大到小排序作者，优先放大块
    sorted_authors = sorted(author_line_counts.items(), key=lambda x: x[1], reverse=True)
    
    for author, lines in sorted_authors:
        # 如果当前作者的内容太大，超过2000行，单独成块
        if lines > 2000:
            if current_block:
                blocks.append((current_block.copy(), current_block_lines + header_lines))
                current_block = []
                current_block_lines = 0
            
            blocks.append(([author], lines + header_lines))
            continue
        
        # 如果添加当前作者会超过2000行，创建新块
        if current_block_lines + lines + header_lines > 2000 and current_block:
            blocks.append((current_block.copy(), current_block_lines + header_lines))
            current_block = []
            current_block_lines = 0
        
        current_block.append(author)
        current_block_lines += lines
    
    # 最后一个块
    if current_block:
        blocks.append((current_block, current_block_lines + header_lines))
    
    # 生成多个markdown文件
    for i, (authors_in_block, _) in enumerate(blocks, 1):
        output_file = f"{output_file_base}{i}.md"
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f'## 2025大厂实习/春招/社招官方信息汇总（截至{latest_short_date}）[{i}]\n\n')
            
            for author in authors_in_block:
                posts = author_groups[author]
                f.write(f'### {author}\n\n')
                for post in posts:
                    title = post['title']
                    publish_time = post['publish_time']
                    url = post.get('original_url', '#')
                    content = post.get('content', '')
                    
                    # 截断过长的内容
                    if len(content) > 500:
                        content = content[:500] + "..."
                    
                    f.write(f'#### [{title}]({url}) - {publish_time}\n\n')
                    f.write(f'{content}\n\n')
                f.write('\n')
        
        print(f"生成第{i}块文件: {output_file}")
    
    return len(blocks)

def main():
    input_dir = './etl/data/raw/company'  # 指定JSON文件所在目录
    output_file_base = './etl/data/summary/job'   # 输出文件路径基础名
    
    # 时间范围参数 (开始时间, 结束时间)，格式为'YYYYmm'
    # 例如: ('202301', '202312') 表示2023年1月到12月
    time_range = ('202501', '202503')  # 默认值，可以根据需要修改
    
    # 获取所有符合时间范围的子目录
    base_dir = Path(input_dir)
    all_dirs = []
    
    # 首先过滤顶层目录
    start_time, end_time = time_range
    year_month_dirs = []
    for d in base_dir.iterdir():
        if d.is_dir() and d.name.isdigit() and len(d.name) == 6:
            if start_time <= d.name <= end_time:
                year_month_dirs.append(d)
    
    # 获取所有嵌套的子目录
    for year_month_dir in year_month_dirs:
        for nested_dir in year_month_dir.iterdir():
            if nested_dir.is_dir():
                all_dirs.append(nested_dir)
    
    # 计算含有abstract.md的文件夹数量
    valid_dirs = [d for d in all_dirs if (d / "abstract.md").exists()]
    
    print(f"Found {len(all_dirs)} nested directories, {len(valid_dirs)} contain abstract.md")
    
    articles = load_json_files(input_dir, time_range)
    # 不再过滤招聘相关文章
    print(f"Found {len(articles)} articles")
    
    num_blocks = generate_markdown_summary(articles, output_file_base)
    print(f"Summary generated: {output_file_base}[1-{num_blocks}].md (time range: {time_range[0]} to {time_range[1]})")

if __name__ == '__main__':
    main()
