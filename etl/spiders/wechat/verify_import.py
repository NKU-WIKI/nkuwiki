import psycopg2
from dotenv import load_dotenv
import os

def verify_import():
    load_dotenv()
    
    # 数据库连接配置
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        port=os.getenv('DB_PORT', '5432'),
        dbname=os.getenv('DB_NAME', 'nkuwiki_db'),
        user=os.getenv('DB_USER', 'nkuwiki_user'),
        password=os.getenv('DB_PASSWORD', '123456')
    )
    
    try:
        with conn.cursor() as cur:
            # 验证总记录数
            cur.execute("SELECT COUNT(*) FROM nkuwiki.wechat_articles")
            total = cur.fetchone()[0]
            print(f"总记录数: {total}")
            
            # 验证最新记录
            cur.execute("""
                SELECT original_url, title, publish_time 
                FROM nkuwiki.wechat_articles 
                ORDER BY publish_time DESC 
                LIMIT 1
            """)
            latest = cur.fetchone()
            print(f"最新记录: {latest}")
            
            # 验证字段完整性
            cur.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'wechat_articles'
            """)
            columns = [row[0] for row in cur.fetchall()]
            print("字段列表:", columns)
            
    finally:
        conn.close()

if __name__ == "__main__":
    verify_import() 