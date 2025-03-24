# 现在需要实现rag，并在前端展示，详见https://github.com/ghost233lism/Nkuwiki/issues/13

# 用CozeAgent（core/agent/coze）实现智能体交互。
# 1. 首先用查询改写bot（对应的bot_id为config.json中的rewrite_bot_id），将用户查询改写为更精确的查询。
# 2. 然后在数据库中检索文本，使用回答生成bot（对应的bot_id为config.json中的knowledge_bot_id），生成回答和来源。
# 3. 最后使用markdown格式化回答和来源，返回给前端。