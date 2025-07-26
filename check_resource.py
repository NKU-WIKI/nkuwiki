"""
检查资源是否存在
"""
import asyncio
from etl.load import db_core
from etl.load.db_pool_manager import init_db_pool, close_db_pool

async def check_resource():
    await init_db_pool()
    
    try:
        # 检查 wxapp_post 表中 id=21 的记录
        result = await db_core.query_records(
            "wxapp_post",
            conditions={"id": 21},
            limit=1
        )
        
        print(f"查询结果: {result}")
        
        if result['data']:
            post = result['data'][0]
            print(f"找到帖子: ID={post['id']}, 标题={post.get('title', 'N/A')}")
        else:
            print("未找到 ID=21 的帖子")
            
        # 也检查一下有哪些帖子
        all_posts = await db_core.query_records(
            "wxapp_post",
            limit=5,
            order_by={"id": "DESC"}
        )
        print(f"\n最近的5个帖子:")
        for post in all_posts['data']:
            print(f"  ID={post['id']}, 标题={post.get('title', 'N/A')}")
            
    finally:
        await close_db_pool()

if __name__ == "__main__":
    asyncio.run(check_resource()) 