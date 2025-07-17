def clean_filename(filename: str) -> str:
    """清理文件名，移除不合法字符
    Args:
        filename: 原始文件名
    Returns:
        清理后的文件名
    """
    illegal_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
    for char in illegal_chars:
        filename = filename.replace(char, '_')
    if len(filename) > 200:
        filename = filename[:197] + '...'
    return filename

def upload_document(file_path, dataset_id):
    """
    上传文档到Coze知识库
    """
    import base64
    import os
    import requests
    from etl.utils import api_key, base_url
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
                "name": os.path.basename(file_path).replace('.md', '.txt'),
                "source_info": {
                    "document_source": 0,
                    "file_base64": file_content,
                    "file_type": "txt"
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

__all__ = ['clean_filename', 'upload_document'] 