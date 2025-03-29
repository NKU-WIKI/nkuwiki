from etl.load.db_core import execute_query
from api.models.search import SearchRequest, SearchResponse, SearchResultItem
from api.config import config

class SearchDAO:
    async def search_contents(self, db, request: SearchRequest) -> SearchResponse:
        sql, params = self._build_query(request)
        records, total = await execute_query(
            db, 
            sql, 
            params, 
            page=request.page, 
            page_size=request.page_size
        )
        
        return SearchResponse(
            results=[self._format_result(r) for r in records],
            total=total,
            current_page=request.page
        )

    def _build_query(self, request):
        hl_length = config.search.highlight_fragment_size  # 从配置读取高亮片段长度
        
        base_sql = f"""
        SELECT p.id as post_id,
            p.title,
            p.content,
            DATE_FORMAT(p.create_time, '%%Y-%%m-%%d %%H:%%i:%%s') as create_time,
            p.nick_name as author,
            COUNT(c.id) as comment_count,
            p.title as hl_title,
            p.content as hl_content
        FROM wxapp_posts p
        LEFT JOIN wxapp_comments c ON p.id = c.post_id
        WHERE (p.title LIKE %s OR p.content LIKE %s)
        """
        params = [f'%{request.keyword}%', f'%{request.keyword}%']
        
        if request.search_type == "post":
            base_sql += " AND c.id IS NULL"
        elif request.search_type == "comment":
            base_sql = base_sql.replace("LEFT JOIN", "INNER JOIN")
        
        base_sql += " GROUP BY p.id"
        return base_sql, params

    def _format_result(self, record):
        return SearchResultItem(**{
            'post_id': record['post_id'],
            'title': record['title'],
            'content': record['content'],
            'highlight_title': self._highlight_text(record.get('hl_title'), record.get('keyword', ''), 50),
            'highlight_content': self._highlight_text(record.get('hl_content'), record.get('keyword', ''), 150),
            'create_time': record['create_time'],
            'author': record['author'],
            'comment_count': record['comment_count']
        })

    def _highlight_text(self, text, keyword, max_length):
        if not text or not keyword:
            return text
        
        # 查找关键词位置
        pos = text.lower().find(keyword.lower())
        if pos == -1:
            return text[:max_length] + '...' if len(text) > max_length else text
            
        # 计算摘要位置
        start = max(0, pos - max_length // 2)
        end = min(len(text), start + max_length)
        
        # 截取摘要
        snippet = text[start:end]
        if start > 0:
            snippet = '...' + snippet
        if end < len(text):
            snippet = snippet + '...'
            
        return snippet

    async def get_suggestions(self, db, keyword):
        sql = """
        SELECT DISTINCT title AS suggestion 
        FROM wxapp_posts 
        WHERE title LIKE %s
        UNION
        SELECT DISTINCT content AS suggestion
        FROM wxapp_comments
        WHERE content LIKE %s
        LIMIT %s
        """
        params = [f"%{keyword}%", f"%{keyword}%", config.search.max_suggestions]
        results = await execute_query(db, sql, params)
        return [r['suggestion'] for r in results] 