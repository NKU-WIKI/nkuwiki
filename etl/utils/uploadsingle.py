import sys
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
                    "file_type": "txt"  # 修改文件类型为 txt
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
    # 示例使用
    dataset_id = 7482712868396908556  # 替换为你的 dataset_id
    result = upload_document("C:/Users/hpkjy/NKUCS.ICU/README.md", dataset_id)  # 修改为你的 .md 文件路径
    print(result)