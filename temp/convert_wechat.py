import json
from datetime import datetime

# 读取源数据文件
with open('etl/data/processed/wechat_metadata_20250222.json', 'r', encoding='utf-8') as f:
    source_data = json.load(f)

transformed_list = []

for item in source_data:
    # 处理时间格式转换
    try:
        scrape_time = datetime.fromisoformat(item["run_time"]).strftime("%Y-%m-%d")
    except (KeyError, ValueError):
        scrape_time = "2025-02-12"  # 默认值
    
    transformed = {
        "platform": "wechat",
        "original_url": item.get("link", ""),
        "title": item.get("title", "无标题"),
        "author": item["author"] if item["author"] else "匿名作者",
        "publish_time": item.get("publish_time", "1970-01-01"),
        "scrape_time": scrape_time,
        "content_type": "article"  # 将原来的wechat改为article
    }
    transformed_list.append(transformed)

# 保存转换结果
with open('wechat_metadata_20250222', 'w', encoding='utf-8') as f:
    json.dump(transformed_list, f, ensure_ascii=False, indent=4, default=str)

print(f"成功转换 {len(transformed_list)} 条记录") 