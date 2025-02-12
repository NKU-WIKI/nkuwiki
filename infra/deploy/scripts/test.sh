curl -X POST "https://coze.nankai.edu.cn/api/proxy/api/v1/create_conversation" \
-H "Apikey: " \
-H "AppID: " \
-H "Content-Type: application/json" \
-d '{
    "AppKey": "",
    "UserID": "default_user",
    "Inputs": {},
    "AppID": ""
}'
curl -X POST "https://coze.nankai.edu.cn/api/proxy/api/v1/chat_query" \
-H "Apikey: " \
-H "Content-Type: application/json" \
-d '{
    "AppKey": "",
    "AppConversationID": "",
    "Query": "南开大学有哪些特色专业？",
    "ResponseMode": "blocking",
    "UserID": "default_user"
}'> response2.txt

curl -X POST "https://coze.nankai.edu.cn/api/proxy/api/v1/run_app_workflow" \
-H "Apikey: cul2lbcpkp8br094cmvg" \
-H "Content-Type: application/json" \
-d '{
    "AppKey": "cul2lbcpkp8br094cmvg",
    "AppID": "cul2jsombmfmr3qnsm1g",
    "InputData": "{\"input\": \"你好，你是什么模型？\"}",
    "UserID": "default_user"
}'> response3.txt

curl -X POST "https://coze.nankai.edu.cn/api/proxy/api/v1/query_run_app_process" \
-H "Apikey: cul2lbcpkp8br094cmvg" \
-H "Content-Type: application/json" \
-d '{
    "AppKey": "cul2lbcpkp8br094cmvg",
    "AppID": "cul2jsombmfmr3qnsm1g",
    "RunID": "feba714aa8b346ebb4778bec9920fa00",
    "UserID": "default_user"
}'> response4.txt