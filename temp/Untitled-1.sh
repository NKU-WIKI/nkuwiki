curl --location --request POST 'https://api.coze.cn/v1/files/upload' \
--header 'Authorization: Bearer pat_qggn0N7tEcxNBDc7VnsjQZVSSgYegBnjLgVLOA8l5Pl2xtK3bbqxrY6K46kteGoT' \
--form 'file=@"./etl/data/article2.txt"'

7478550099954647066

curl -X POST 'https://api.coze.cn/open_api/knowledge/document/create' \
-H "Authorization: Bearer pat_x7VCchMsVWYuPnYpTM4iArV1yCHSU3PMSFmL4bxOBIvnvLcITK2CfKm9VNFkKxjA" \
-H "Content-Type: application/json" \
-H "Agw-Js-Conv: str" \
-d '{
  "dataset_id": "7478545982721556507",
  "document_bases": [
    {
      "source_info": {
        "document_source": 0,
        "source_file_id": 7478556468640956450,
        "file_type": "txt"
      },
      "name": "article2.txt"
    }
  ],
  "chunk_strategy": {
    "caption_type": 0
  }
}'