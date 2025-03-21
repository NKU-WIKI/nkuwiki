import sys
import os
from pathlib import Path
import base64
import requests

# 添加项目根目录到系统路径
sys.path.append(str(Path(__file__).parent.parent.parent))
from etl.utils import *


def upload_document(file_path, dataset_id):
    """
    上传文档到Coze知识库
    """
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Agw-Js-Conv": "str"
    }

    with open(file_path, 'rb') as f:
        file_content = base64.b64encode(f.read()).decode('utf-8')

    data = {
        "dataset_id": dataset_id,
        "document_bases": [
            {
                "name": os.path.basename(file_path).replace('.md', '.txt'),  # 修改文件名后缀
                "source_info": {
                    "document_source": 0,
                    "file_base64": file_content,
                    "file_type": "txt"  # 确保文件类型为 txt
                }
            }
        ],
        "chunk_strategy": {
            "caption_type": 0
        }
    }
    response = requests.post(
        f'{base_url}/open_api/knowledge/document/create',
        headers=headers,
        json=data
    )
    return response.json()


def main():
    dataset_id = 7482712868396908556  # 替换为coze的 dataset_id
    md_dir = "C:/Users/hpkjy/NKUCS.ICU/experiences/others"  # 指定 .md 文件目录

    # 获取目录中的所有 .md 文件
    md_files = [f for f in os.listdir(md_dir) if f.endswith(".md")]

    if len(md_files) == 1:
        # 执行单个文件上传
        file_path = os.path.join(md_dir, md_files[0])
        result = upload_document(file_path, dataset_id)
        print(f"文件 {md_files[0]} 上传结果:", result)
    elif len(md_files) > 1:
        # 执行批量上传
        for filename in md_files:
            file_path = os.path.join(md_dir, filename)
            result = upload_document(file_path, dataset_id)
            print(f"文件 {filename} 上传结果:", result)
    else:
        print("目录中没有 .md 文件，请检查路径是否正确。")


if __name__ == "__main__":
    main()