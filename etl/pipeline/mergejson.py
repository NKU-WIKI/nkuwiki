import os
import json
from pathlib import Path
from datetime import datetime
def find_json_files(directory):

    """
    查找指定目录及其子目录下的所有JSON文件
    :param directory: 要搜索的目录
    :return: JSON文件的路径列表
    """
    json_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.json'):
                if(file.startswith('scraped')):
                    pass
                else:
                    json_files.append(os.path.join(root, file))
    return json_files


def merge_json_files(json_files):
    """
    合并所有JSON文件的内容到一个JSON数组中
    :param json_files: JSON文件的路径列表
    :return: 合并后的JSON数组
    """
    merged_data = []
    for file in json_files:
        try:
            with open(file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    merged_data.extend(data)
                else:
                    merged_data.append(data)
        except Exception as e:
            print(f"Error reading {file}: {e}")
    return merged_data

def main(directory, output_file):
    """
    主函数，执行查找和合并操作，并将结果保存到输出文件中
    :param directory: 要搜索的目录
    :param output_file: 输出文件的路径
    """
    json_files = find_json_files(directory)
    merged_data = merge_json_files(json_files)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(merged_data, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    # 获取项目根目录
    project_root = Path(__file__).resolve().parent.parent.parent
    
    # 设置输入和输出路径，相对于项目根目录
    search_directory = project_root / 'etl/data/raw/wechat'
    output_file = project_root / 'etl/data/processed' / f'wechat_metadata_{datetime.now().strftime("%Y%m%d")}.json'
    


    # 确保目录存在
    print(f"搜索目录: {search_directory}")
    print(f"输出文件: {output_file}")
    
    main(search_directory, output_file)