import asyncio
import sys
from pathlib import Path

# 将项目根目录添加到Python路径中，以便可以导入我们的模块
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from etl.load import db_core

async def ensure_table_exists():
    """
    读取SQL文件并执行，以确保insights表存在。
    """
    print("🔧 正在检查并确保 'insights' 表存在...")
    try:
        sql_file_path = Path(__file__).resolve().parent.parent / "load" / "mysql_tables" / "insights.sql"
        with open(sql_file_path, 'r', encoding='utf-8') as f:
            create_table_sql = f.read()
        
        # execute_query 在执行非查询语句时返回影响的行数
        await db_core.execute_query(create_table_sql, fetch=False)
        print("✅ 'insights' 表已确认存在。")
        return True
    except Exception as e:
        print(f"❌ 创建 'insights' 表时失败: {e}")
        return False

async def verify_latest_insights():
    """
    查询并打印数据库中最新的10条洞察记录。
    """
    # 步骤1: 确保表存在
    if not await ensure_table_exists():
        return

    # 步骤2: 查询数据
    print("🚀 开始查询数据库，获取最新的洞察记录...")
    
    query = "SELECT id, title, category, relevance_score, create_time FROM insights ORDER BY create_time DESC LIMIT 10;"
    
    try:
        results = await db_core.execute_query(query)
        
        if not results:
            print("❌ 在 'insights' 表中没有找到任何记录。")
            return

        print("✅ 查询成功！最新的洞察记录如下：")
        print("-" * 80)
        for row in results:
            print(f"  - ID: {row['id']}")
            print(f"    标题: {row['title']}")
            print(f"    分类: {row['category']}")
            print(f"    相关性: {row['relevance_score']}")
            print(f"    创建时间: {row['create_time']}")
            print("-" * 80)
            
    except Exception as e:
        print(f"❌ 查询数据库时发生错误: {e}")

if __name__ == "__main__":
    asyncio.run(verify_latest_insights()) 