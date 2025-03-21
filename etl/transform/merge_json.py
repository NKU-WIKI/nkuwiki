import json
from pathlib import Path
from tqdm import tqdm

def find_json_files(directory: Path) -> list[Path]:
    """查找指定目录下的非scraped开头的JSON文件"""
    return [
        f for f in directory.glob('**/*.json') 
        if not f.name.startswith('scraped')
    ]

def merge_json_files(json_files: list[Path]) -> list[dict]:
    """合并JSON文件并自动去重（基于original_url字段）"""
    seen_urls = set()
    merged_data = []
    
    total_items = 0
    url_duplicates = 0
    
    for file in tqdm(json_files, desc="Merging files"):
        try:
            # 添加内容长度检查
            content = file.read_text(encoding='utf-8')
            if not content.strip():
                # print(f"空文件: {file}")
                continue
                
            data = json.loads(content)
            
            for item in data if isinstance(data, list) else [data]:
                total_items += 1
                unique_key = item.get('link') or item.get('title')
                if unique_key and unique_key not in seen_urls:
                    merged_data.append(item)
                    seen_urls.add(unique_key)
            
                
            # print(f"\n文件 {file} 首条数据字段:", list(data[0].keys())) if len(data) > 0 else None
            
        except json.JSONDecodeError as e:
            print(f"JSON解析错误 {file}: {e}")
        except Exception as e:
            print(f"处理文件 {file} 时出错: {e}")
    
    print(f"\n处理统计:")
    print(f"总条目: {total_items}")
    print(f"URL重复: {url_duplicates}")
    print(f"有效条目: {len(merged_data)}")
    
    return merged_data

def main(directory: Path, output_file: Path):
    """主函数添加目录验证"""
    if not directory.exists():
        raise ValueError(f"输入目录不存在: {directory}")
        
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    json_files = find_json_files(directory)
    print(f"找到 {len(json_files)} 个JSON文件")
    
    merged_data = merge_json_files(json_files)
    
    # 添加合并结果检查
    print(f"合并后条目数量: {len(merged_data)}")
    if len(merged_data) > 0:
        print("示例数据:", json.dumps(merged_data[0], ensure_ascii=False, indent=2))
    else:
        print("警告: 合并结果为空！")
    
    with output_file.open('w', encoding='utf-8') as f:
        json.dump(merged_data, f, 
                 ensure_ascii=False, 
                 indent=4,
                 sort_keys=True)  # 保持输出一致性

if __name__ == "__main__":
    # 获取项目根目录
    project_root = Path(__file__).resolve().parent.parent.parent
    
    # 设置输入和输出路径，相对于项目根目录
    search_directory = project_root / 'etl/data/raw/wechat1'
    output_file = project_root / 'etl/data/processed' / 'wechat_metadata_20250222.json'
    
    # 添加路径验证调试信息
    print(f"项目根目录: {project_root}")
    print(f"输入目录是否存在: {search_directory.exists()}")
    
    # 确保目录存在
    print(f"搜索目录: {search_directory}")
    print(f"输出文件: {output_file}")
    
    main(search_directory, output_file)