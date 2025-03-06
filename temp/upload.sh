#!/bin/bash

# 将文件内容转为base64（确保article1.txt存在）
FILE_CONTENT=$(base64 -w 0 ./article1.txt)

# 构建JSON payload（修改了heredoc的引用方式）
read -r -d '' PAYLOAD << EOF
{
  "dataset_id": "7478545982721556507",
  "document_bases": [
    {
      "name": "article1.txt",
      "source_info": {
        "document_source": 0,
        "file_type": "txt",
        "file_base64": "${FILE_CONTENT}"
      }
    }
  ],
  "chunk_strategy": {
    "caption_type": 0
  }
}
EOF

# 发送请求（添加双引号包裹payload）
curl -X POST 'https://api.coze.cn/open_api/knowledge/document/create' \
  -H "Authorization: Bearer pat_qggn0N7tEcxNBDc7VnsjQZVSSgYegBnjLgVLOA8l5Pl2xtK3bbqxrY6K46kteGoT" \
  -H "Content-Type: application/json" \
  -H "Agw-Js-Conv: str" \
  -d "${PAYLOAD}"

