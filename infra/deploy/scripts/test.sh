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