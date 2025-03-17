import sys
import os  # 新增导入
from pathlib import Path

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


if __name__ == "__main__":
    # 修改部分：遍历目录下的所有 .md 文件
    dataset_id = 7482712868396908556
    md_dir = "C:/Users/hpkjy/NKUCS.ICU/experiences/others"  # 指定你的 .md 文件目录

    # 遍历目录中的所有 .md 文件
    for filename in os.listdir(md_dir):
        if filename.endswith(".md"):
            file_path = os.path.join(md_dir, filename)
            result = upload_document(file_path, dataset_id)
            print(f"文件 {filename} 上传结果:", result)