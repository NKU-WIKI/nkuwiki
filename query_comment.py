#!/usr/bin/env python3
"""
查询wxapp_comment表的各种统计信息
"""
import asyncio
import argparse
import sys
from etl.load.db_core import async_execute_custom_query
from core.utils.logger import register_logger

logger = register_logger('query')

async def get_recent_comments():
    """查询最近修改的10条评论记录"""
    query = """
    SELECT id, resource_id, resource_type, parent_id, openid, 
           nickname, content, like_count, reply_count, 
           status, is_deleted, create_time, update_time
    FROM wxapp_comment 
    ORDER BY update_time DESC 
    LIMIT 10
    """
    
    try:
        results = await async_execute_custom_query(query)
        if results:
            print("\n=== 最近修改的10条评论 ===")
            logger.info(f"共查询到 {len(results)} 条最近评论记录")
            for idx, record in enumerate(results, 1):
                print(f"\n--- 记录 {idx} ---")
                for key, value in record.items():
                    print(f"{key}: {value}")
        else:
            logger.info("未查询到任何评论记录")
    except Exception as e:
        logger.error(f"查询最近评论出错: {str(e)}")

async def get_comment_stats():
    """查询评论表的统计信息"""
    queries = {
        "总评论数": "SELECT COUNT(*) as count FROM wxapp_comment",
        "正常状态评论数": "SELECT COUNT(*) as count FROM wxapp_comment WHERE status = 1 AND is_deleted = 0",
        "禁用状态评论数": "SELECT COUNT(*) as count FROM wxapp_comment WHERE status = 0 AND is_deleted = 0",
        "已删除评论数": "SELECT COUNT(*) as count FROM wxapp_comment WHERE is_deleted = 1",
        "一级评论数": "SELECT COUNT(*) as count FROM wxapp_comment WHERE parent_id IS NULL",
        "回复评论数": "SELECT COUNT(*) as count FROM wxapp_comment WHERE parent_id IS NOT NULL",
        "有图片评论数": "SELECT COUNT(*) as count FROM wxapp_comment WHERE JSON_LENGTH(image) > 0",
        "最早评论时间": "SELECT MIN(create_time) as time FROM wxapp_comment",
        "最新评论时间": "SELECT MAX(create_time) as time FROM wxapp_comment"
    }
    
    try:
        print("\n=== 评论统计信息 ===")
        for desc, query in queries.items():
            result = await async_execute_custom_query(query)
            if result and len(result) > 0:
                if 'count' in result[0]:
                    print(f"{desc}: {result[0]['count']}")
                elif 'time' in result[0]:
                    print(f"{desc}: {result[0]['time']}")
    except Exception as e:
        logger.error(f"查询评论统计信息出错: {str(e)}")

async def get_post_comments_distribution():
    """查询各帖子的评论数量分布"""
    query = """
    SELECT resource_id, COUNT(*) as comment_count
    FROM wxapp_comment
    WHERE resource_type = 'post' AND is_deleted = 0
    GROUP BY resource_id
    ORDER BY comment_count DESC
    LIMIT 10
    """
    
    try:
        results = await async_execute_custom_query(query)
        if results:
            print("\n=== 评论最多的10个帖子 ===")
            for idx, record in enumerate(results, 1):
                print(f"帖子ID: {record['resource_id']}, 评论数: {record['comment_count']}")
    except Exception as e:
        logger.error(f"查询帖子评论分布出错: {str(e)}")

async def get_monthly_comments():
    """查询每月评论数量趋势"""
    query = """
    SELECT 
        DATE_FORMAT(create_time, '%Y-%m') as month,
        COUNT(*) as comment_count
    FROM wxapp_comment
    WHERE is_deleted = 0
    GROUP BY DATE_FORMAT(create_time, '%Y-%m')
    ORDER BY month DESC
    LIMIT 12
    """
    
    try:
        results = await async_execute_custom_query(query)
        if results:
            print("\n=== 最近12个月评论数量趋势 ===")
            for record in results:
                print(f"{record['month']}: {record['comment_count']}条评论")
    except Exception as e:
        logger.error(f"查询月度评论趋势出错: {str(e)}")

async def get_user_comments_distribution():
    """查询用户评论分布"""
    query = """
    SELECT openid, COUNT(*) as comment_count
    FROM wxapp_comment
    WHERE is_deleted = 0
    GROUP BY openid
    ORDER BY comment_count DESC
    LIMIT 10
    """
    
    try:
        results = await async_execute_custom_query(query)
        if results:
            print("\n=== 评论最多的10个用户 ===")
            for idx, record in enumerate(results, 1):
                print(f"用户openid: {record['openid']}, 评论数: {record['comment_count']}")
    except Exception as e:
        logger.error(f"查询用户评论分布出错: {str(e)}")

async def find_sensitive_comments():
    """查找可能包含敏感内容的评论"""
    # 构建敏感词列表
    sensitive_keywords = [
        # 色情相关
        '色情', '淫秽', '性爱', '做爱', '内射', '性交', '奸', '操', '艹', '日', '草',
        # 赌博相关
        '赌博', '博彩', '娱乐城', '菠菜', '红色鱼庄',
        # 政治人物
        '习近平', '李克强', '蔡奇', '李鸿忠', '尹力', '李希',
        # 联系方式相关 
        '微信', 'QQ', 'V', '飞机', 'tg',
        # 交易相关
        '点券', '代充',
        # 其他敏感词
        '翻墙', '梯子'
    ]
    
    # 构建查询的WHERE条件
    conditions = []
    for keyword in sensitive_keywords:
        conditions.append(f"content LIKE '%{keyword}%'")
    
    where_clause = " OR ".join(conditions)
    
    query = f"""
    SELECT id, resource_id, resource_type, openid, content, 
           status, create_time, update_time
    FROM wxapp_comment
    WHERE ({where_clause}) AND is_deleted = 0
    ORDER BY update_time DESC
    LIMIT 20
    """
    
    try:
        results = await async_execute_custom_query(query)
        if results:
            print(f"\n=== 找到 {len(results)} 条可能包含敏感内容的评论 ===")
            print("\n敏感评论详情：")
            for idx, record in enumerate(results, 1):
                status_text = "正常" if record['status'] == 1 else "已禁用"
                print(f"\n--- 敏感评论 {idx} ---")
                print(f"ID: {record['id']}")
                print(f"资源ID: {record['resource_id']}, 类型: {record['resource_type']}")
                print(f"用户: {record['openid']}")
                print(f"内容: {record['content']}")
                print(f"状态: {status_text}")
                print(f"创建时间: {record['create_time']}")
                print(f"更新时间: {record['update_time']}")
                
            # 统计敏感评论的状态分布
            status_query = f"""
            SELECT status, COUNT(*) as count
            FROM wxapp_comment
            WHERE ({where_clause}) AND is_deleted = 0
            GROUP BY status
            """
            
            status_results = await async_execute_custom_query(status_query)
            if status_results:
                print("\n敏感评论状态分布：")
                for record in status_results:
                    status_text = "正常" if record['status'] == 1 else "已禁用"
                    print(f"{status_text}: {record['count']}条")
        else:
            print("\n未发现敏感评论")
    except Exception as e:
        logger.error(f"查询敏感评论出错: {str(e)}")

async def get_comment_length_distribution():
    """分析评论长度分布"""
    query = """
    SELECT 
        CASE 
            WHEN CHAR_LENGTH(content) <= 10 THEN '10字以内'
            WHEN CHAR_LENGTH(content) <= 30 THEN '11-30字'
            WHEN CHAR_LENGTH(content) <= 50 THEN '31-50字'
            WHEN CHAR_LENGTH(content) <= 100 THEN '51-100字'
            ELSE '100字以上'
        END as length_range,
        COUNT(*) as count,
        AVG(CHAR_LENGTH(content)) as avg_length
    FROM wxapp_comment
    WHERE is_deleted = 0
    GROUP BY length_range
    ORDER BY MIN(CHAR_LENGTH(content))
    """
    
    try:
        results = await async_execute_custom_query(query)
        if results:
            print("\n=== 评论长度分布 ===")
            for record in results:
                print(f"{record['length_range']}: {record['count']}条, 平均{record['avg_length']:.1f}字")
    except Exception as e:
        logger.error(f"查询评论长度分布出错: {str(e)}")

async def get_comment_details_by_id(comment_id):
    """根据ID查询评论详情"""
    query = f"""
    SELECT *
    FROM wxapp_comment
    WHERE id = {comment_id}
    """
    
    try:
        results = await async_execute_custom_query(query)
        if results and len(results) > 0:
            print(f"\n=== 评论ID: {comment_id} 的详情 ===")
            for key, value in results[0].items():
                print(f"{key}: {value}")
        else:
            print(f"\n未找到ID为 {comment_id} 的评论")
    except Exception as e:
        logger.error(f"查询评论详情出错: {str(e)}")

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='wxapp_comment表查询工具')
    
    # 添加命令行选项
    parser.add_argument('--recent', action='store_true', help='查询最近修改的评论')
    parser.add_argument('--stats', action='store_true', help='查询评论统计信息')
    parser.add_argument('--distribution', action='store_true', help='查询帖子评论分布')
    parser.add_argument('--monthly', action='store_true', help='查询每月评论数量趋势')
    parser.add_argument('--users', action='store_true', help='查询用户评论分布')
    parser.add_argument('--sensitive', action='store_true', help='查找敏感评论')
    parser.add_argument('--length', action='store_true', help='分析评论长度分布')
    parser.add_argument('--id', type=int, help='根据ID查询评论详情')
    parser.add_argument('--all', action='store_true', help='执行所有查询')
    
    # 如果没有提供参数，显示帮助信息
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)
        
    return parser.parse_args()

async def main():
    args = parse_args()
    
    if args.all:
        await get_recent_comments()
        await get_comment_stats()
        await get_post_comments_distribution()
        await get_monthly_comments()
        await get_user_comments_distribution()
        await find_sensitive_comments()
        await get_comment_length_distribution()
    else:
        if args.recent:
            await get_recent_comments()
        if args.stats:
            await get_comment_stats()
        if args.distribution:
            await get_post_comments_distribution()
        if args.monthly:
            await get_monthly_comments()
        if args.users:
            await get_user_comments_distribution()
        if args.sensitive:
            await find_sensitive_comments()
        if args.length:
            await get_comment_length_distribution()
        if args.id:
            await get_comment_details_by_id(args.id)

if __name__ == "__main__":
    asyncio.run(main()) 