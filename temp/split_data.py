import json
import math
from pathlib import Path

def split_data(input_file, num_splits=100):
    # 读取JSON数组数据
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)  # data已经是列表形式
    
    total_items = len(data)
    base, remainder = divmod(total_items, num_splits)
    
    # 自动调整实际分片数（当数据量不足时）
    actual_splits = min(num_splits, total_items)
    
    output_dir = Path('etl/data/processed/splits')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    for i in range(actual_splits):  # 修改循环次数为实际需要分片数
        # 计算分片大小
        if i < remainder:
            chunk_size = base + 1
        else:
            chunk_size = base
        
        # 计算起始位置
        start_idx = i*base + min(i, remainder)
        end_idx = start_idx + chunk_size
        
        # 获取数组切片
        split_array = data[start_idx:end_idx]
        
        # 保持数组结构写入文件
        output_file = output_dir / f'split_{i+1:03d}.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(split_array, f, ensure_ascii=False, indent=4)

if __name__ == '__main__':
    input_file = 'etl/data/processed/wechat_metadata_20250222.json'
    split_data(input_file) 