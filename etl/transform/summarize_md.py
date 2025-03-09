from __init__ import *
from etl.transform import transform_logger

def summarize_md(input_dir: str, output_dir: str, time_range=None, title: str = 'summarize', header_text: str = ''):
    """
    加载指定目录下的JSON文件并生成markdown格式的总结，按块分割
    每块小于2000行，同一作者不会被分成两块
    输出为job1.md, job2.md等多个文件
    
    Args:
        input_dir: 基础目录路径
        output_dir: 输出文件路径基础名
        time_range: 可选的时间范围元组 (start_date, end_date)，例如 ('2025-01-01', '2025-03-01') 或 (datetime对象, datetime对象)
        title: 生成文件的标题基础名
        header_text: 在每个生成的文件顶部添加的文本
    """
    # 处理标题中的路径分隔符，避免被当做目录路径
    safe_title = title.replace('/', '-').replace('\\', '-')
    # 去除标题中可能存在的特殊字符或不可见字符
    safe_title = ''.join(c for c in safe_title if c.isprintable() and c != '\t')
    # 记录原始安全标题
    title_text = title + '（{date}）[{block_num}]'
    title_text_single = title + '（{date}）'
    title_template = safe_title+'（{date}）[{block_num}]'
    title_template_single = safe_title+'（{date}）'  # 当只有一个块时使用的模板
    articles = []
    
    # 获取所有子目录
    base_dir = Path(input_dir)
    all_dirs = []
    
    transform_logger.info("正在收集目录...")
    # 如果指定了时间范围，首先过滤顶层目录
    if time_range:
        start_time, end_time = time_range
        # 如果是datetime对象，转换为字符串
        if isinstance(start_time, datetime):
            start_time = start_time.strftime('%Y-%m-%d')
        if isinstance(end_time, datetime):
            end_time = end_time.strftime('%Y-%m-%d')
            
        # 提取年月部分用于过滤顶级目录
        start_yyyymm = start_time.replace('-', '')[:6]
        end_yyyymm = end_time.replace('-', '')[:6]
        
        year_month_dirs = []
        for d in base_dir.iterdir():
            if d.is_dir() and d.name.isdigit() and len(d.name) == 6:
                if start_yyyymm <= d.name <= end_yyyymm:
                    year_month_dirs.append(d)
        
        # 获取所有嵌套的子目录
        for year_month_dir in tqdm(year_month_dirs, desc="扫描年月目录"):
            for nested_dir in year_month_dir.iterdir():
                if nested_dir.is_dir():
                    all_dirs.append(nested_dir)
    else:
        # 如果没有指定时间范围，则递归获取所有子目录
        for root, dirs, _ in os.walk(input_dir):
            for dir_name in dirs:
                all_dirs.append(Path(root) / dir_name)
    
    # 计算含有abstract.md的文件夹数量
    valid_dirs = [d for d in all_dirs if (d / "abstract.md").exists()]
    transform_logger.info(f"找到 {len(all_dirs)} 个嵌套目录，其中 {len(valid_dirs)} 个包含 abstract.md")
    
    # 遍历所有符合条件的目录
    transform_logger.info("正在加载文章数据...")
    for dir_path in tqdm(valid_dirs, desc="处理数据目录"):
        # 读取并处理abstract.md文件
        abstract_path = dir_path / "abstract.md"
        abstract_content = ""
        has_abstract = False
        if abstract_path.exists():
            try:
                with open(abstract_path, 'r', encoding='utf-8') as af:
                    abstract_content = af.read().strip()
                    has_abstract = bool(abstract_content)
            except Exception as e:
                transform_logger.error(f"读取abstract.md时出错: {e}, 路径: {abstract_path}")
        
        # 直接处理目录下的 JSON 文件，无需再次检查 abstract.md
        for file_path in dir_path.glob('*.json'):
            with open(file_path, 'r', encoding='utf-8') as f:
                try:
                    data = json.load(f)
                    # 跳过没有publish_time字段的文章
                    if 'publish_time' not in data:
                        transform_logger.warning(f"跳过没有发布时间的文章: {file_path}")
                        continue
                    
                    # 标记这篇文章是否有abstract
                    data['has_abstract'] = has_abstract
                    
                    # 如果有abstract内容，添加到文章内容
                    if has_abstract:
                        # 如果原内容不为空，先添加分隔行
                        if data.get('content'):
                            data['content'] = abstract_content + "\n\n---\n\n" + data.get('content', '')
                        else:
                            data['content'] = abstract_content
                        
                    # 如果指定了时间范围，进一步按文章日期过滤
                    if time_range:
                        publish_date = data.get('publish_time', '')
                        # 只处理日期在范围内的文章
                        if start_time <= publish_date <= end_time:
                            articles.append(data)
                    else:
                        articles.append(data)
                except json.JSONDecodeError:
                    transform_logger.error(f"Error loading {file_path}")
    
    transform_logger.info(f"找到 {len(articles)} 篇文章")
    
    # 按作者分组
    transform_logger.info("正在按作者分组...")
    author_groups = defaultdict(list)
    for article in articles:
        author = article.get('author', '未知作者')
        author_groups[author].append(article)
    
    # 对每个作者的文章按时间排序
    transform_logger.info("正在排序文章...")
    for author, posts in tqdm(author_groups.items(), desc="排序作者文章"):
        posts.sort(key=lambda x: datetime.strptime(x['publish_time'], '%Y-%m-%d'), reverse=True)
    
    # 获取所有文章中最新的发布时间
    latest_date = datetime.now()  # 默认为当前日期
    if articles:
        try:
            # 找出所有文章中最新的发布日期
            latest_date_str = max(article.get('publish_time', '') for article in articles)
            latest_date = datetime.strptime(latest_date_str, '%Y-%m-%d')
        except (ValueError, KeyError) as e:
            transform_logger.error(f"获取最新发布日期时出错: {e}，使用当前日期")
    
    # 使用简短日期格式：MMDD
    latest_short_date = f"{latest_date.month:02d}{latest_date.day:02d}"
    output_file_base = Path(output_dir).with_suffix('')  # 移除扩展名
    
    # 预计算每个作者内容的行数
    transform_logger.info("正在计算内容行数...")
    author_line_counts = {}
    
    # 如果有头部文本，计入总行数
    header_lines = 2  # 标题 + 空行
    if header_text:
        header_lines += header_text.count('\n') + 2  # 头部文本的行数 + 额外空行
    
    for author, posts in tqdm(author_groups.items(), desc="计算内容行数"):
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
    transform_logger.info("正在分组内容...")
    current_block = []
    current_block_lines = 0
    blocks = []
    
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
    transform_logger.info("正在生成Markdown文件...")
    # 确保输出目录存在，使用绝对路径
    if not os.path.isabs(output_dir):
        output_dir = os.path.abspath(output_dir)
    
    os.makedirs(output_dir, exist_ok=True)
    
    # 获取总块数
    total_blocks = len(blocks)
    
    for i, (authors_in_block, _) in enumerate(tqdm(blocks, desc="生成文件"), 1):
        # 构建文件名和完整路径
        # 如果只有一个块，使用不含块号的标题格式
        if total_blocks == 1:
            file_name = title_template_single.format(date=latest_short_date) + '.md'
            title_text = title_text_single.format(date=latest_short_date)
        else:
            file_name = title_template.format(date=latest_short_date, block_num=i) + '.md'
            title_text = title_text.format(date=latest_short_date, block_num=i)
            
        output_file = os.path.join(output_dir, file_name)
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(f'## {title_text}\n\n')
                
                # 如果有头部文本，在标题后写入头部文本
                if header_text:
                    f.write(f'*{header_text}*\n\n')
                
                for author in authors_in_block:
                    posts = author_groups[author]
                    f.write(f'### {author}\n\n')
                    for post in posts:
                        title = post['title']
                        publish_time = post['publish_time']
                        url = post.get('original_url', '#')
                        has_abstract = post.get('has_abstract', False)
                        
                        f.write(f'#### [{title}]({url}) - {publish_time}\n\n')
                        
                        # 只有存在abstract.md的文章才写入内容
                        if has_abstract:
                            content = post.get('content', '')
                            # 截断过长的内容
                            if len(content) > 500:
                                content = content[:500] + "..."
                            
                            f.write(f'{content}\n\n')
                    f.write('\n')
            
            # 验证文件是否成功创建
            if os.path.exists(output_file):
                transform_logger.info(f"成功生成第{i}块文件: {output_file} {file_name}")
            else:
                transform_logger.error(f"文件创建失败: {output_file}")
        except Exception as e:
            transform_logger.error(f"写入文件时出错: {e}")
