def parse_date(date_str: str) -> 'datetime':
    """将字符串解析为日期对象，支持多种常见格式和相对日期"""
    import re
    from datetime import datetime, timedelta
    date_str = date_str.strip()
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    if '刚刚' in date_str or '分钟前' in date_str:
        minutes = 0
        if '分钟前' in date_str:
            try:
                minutes = int(re.search(r'(\\d+)分钟前', date_str).group(1))
            except:
                minutes = 10
        return datetime.now() - timedelta(minutes=minutes)
    elif '小时前' in date_str:
        try:
            hours = int(re.search(r'(\\d+)小时前', date_str).group(1))
        except:
            hours = 1
        return datetime.now() - timedelta(hours=hours)
    elif '昨天' in date_str:
        return today - timedelta(days=1)
    elif '前天' in date_str:
        return today - timedelta(days=2)
    date_formats = [
        '%Y年%m月%d日', '%Y-%m-%d', '%Y/%m/%d', '%m/%d/%Y', '%d/%m/%Y', '%Y.%m.%d',
    ]
    for fmt in date_formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    # 无法解析时返回当天
    try:
        from etl.crawler import crawler_logger
        crawler_logger.warning(f"无法解析日期格式: {date_str}，使用当前日期")
    except Exception:
        pass
    return today 