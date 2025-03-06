import base64
import json
import requests

# 读取并编码文件
with open("./article2.txt", "rb") as f:
    file_content = base64.b64encode(f.read()).decode("utf-8")

print(file_content)
# 构建请求数据
payload = {
    "dataset_id": "7478545982721556507",
    "document_bases": [{
        "name": "article2.txt",
        "source_info": {
            "document_source": 0,
            "file_type": "txt",
            "file_base64": file_content
        }
    }],
    "chunk_strategy": {
        "caption_type": 0
    }
}

headers = {
    "Authorization": "Bearer pat_qggn0N7tEcxNBDc7VnsjQZVSSgYegBnjLgVLOA8l5Pl2xtK3bbqxrY6K46kteGoT",
    "Content-Type": "application/json",
    "Agw-Js-Conv": "str"
}

# 发送请求
response = requests.post(
    "https://api.coze.cn/open_api/knowledge/document/create",
    headers=headers,
    data=json.dumps(payload)
)

print(f"Status Code: {response.status_code}")
print(f"Response: {response.text}") 