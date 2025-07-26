# 定义索引的settings和mappings
index_settings = {
    "analysis": {
        "analyzer": {
            "ik_smart_custom": {
                "type": "custom",
                "tokenizer": "ik_smart",
                "filter": ["user_dictionary_filter"]
            }
        },
        "filter": {
            "user_dictionary_filter": {
                "type": "user_dictionary",
                "user_dictionary": "custom_dictionary.dic"
            }
        }
    }
}

mappings = {
    "properties": {
        "title": {
            "type": "text",
            "analyzer": "ik_smart_custom",
            "fields": {
                "keyword": {
                    "type": "keyword"
                }
            }
        },
        "content": {
            "type": "text",
            "analyzer": "ik_smart_custom"
        },
        "author": {
            "type": "keyword"
        }
    }
} 