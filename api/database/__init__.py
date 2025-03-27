"""
数据库访问层
提供数据库操作的统一接口
"""


from api.database.vector import (
    index_document, search_documents,
    retrieve_from_qdrant, retrieve_hybrid
)

__all__ = [
    "insert_record", 
    "update_record", 
    "delete_record", 
    "query_records", 
    "count_records", 
    "get_record_by_id",
    "execute_raw_query",
    "search_posts",
    "search_comments",
    "search_users",
    "get_table_structure",
    "get_all_tables",
    "index_document", 
    "search_documents",
    "retrieve_from_qdrant", 
    "retrieve_hybrid"
] 