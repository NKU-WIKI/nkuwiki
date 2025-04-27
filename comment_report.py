#!/usr/bin/env python3
"""
生成wxapp_comment表的分析报告
可以定期运行，监控评论状态和风险评论
"""
import asyncio
import datetime
import os
from etl.load.db_core import async_execute_custom_query
from core.utils.logger import register_logger

logger = register_logger('comment_report')

async def get_comment_stats():
    """获取评论统计信息"""
    queries = {
        "总评论数": "SELECT COUNT(*) as count FROM wxapp_comment",
        "正常状态评论数": "SELECT COUNT(*) as count FROM wxapp_comment WHERE status = 1 AND is_deleted = 0",
        "禁用状态评论数": "SELECT COUNT(*) as count FROM wxapp_comment WHERE status = 0 AND is_deleted = 0",
        "今日新增评论": f"SELECT COUNT(*) as count FROM wxapp_comment WHERE DATE(create_time) = CURDATE()",
        "今日禁用评论": f"SELECT COUNT(*) as count FROM wxapp_comment WHERE status = 0 AND DATE(update_time) = CURDATE()",
        "一级评论数": "SELECT COUNT(*) as count FROM wxapp_comment WHERE parent_id IS NULL",
        "回复评论数": "SELECT COUNT(*) as count FROM wxapp_comment WHERE parent_id IS NOT NULL"
    }
    
    stats = {}
    try:
        for desc, query in queries.items():
            result = await async_execute_custom_query(query)
            if result and len(result) > 0:
                stats[desc] = result[0]['count']
    except Exception as e:
        logger.error(f"获取评论统计出错: {str(e)}")
    
    return stats

async def get_recent_sensitive_comments(days=1):
    """获取最近几天的敏感评论"""
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
          AND create_time >= DATE_SUB(NOW(), INTERVAL {days} DAY)
    ORDER BY create_time DESC
    """
    
    try:
        return await async_execute_custom_query(query)
    except Exception as e:
        logger.error(f"获取敏感评论出错: {str(e)}")
        return []

async def get_active_users(limit=5):
    """获取最活跃的用户"""
    query = f"""
    SELECT openid, COUNT(*) as comment_count
    FROM wxapp_comment
    WHERE is_deleted = 0 AND create_time >= DATE_SUB(NOW(), INTERVAL 7 DAY)
    GROUP BY openid
    ORDER BY comment_count DESC
    LIMIT {limit}
    """
    
    try:
        return await async_execute_custom_query(query)
    except Exception as e:
        logger.error(f"获取活跃用户出错: {str(e)}")
        return []

async def get_popular_posts(limit=5):
    """获取最热门的帖子"""
    query = f"""
    SELECT resource_id, COUNT(*) as comment_count
    FROM wxapp_comment
    WHERE resource_type = 'post' AND is_deleted = 0
          AND create_time >= DATE_SUB(NOW(), INTERVAL 7 DAY)
    GROUP BY resource_id
    ORDER BY comment_count DESC
    LIMIT {limit}
    """
    
    try:
        return await async_execute_custom_query(query)
    except Exception as e:
        logger.error(f"获取热门帖子出错: {str(e)}")
        return []

def format_comment(comment):
    """格式化评论信息"""
    status_text = "正常" if comment['status'] == 1 else "已禁用"
    return (f"ID: {comment['id']}, 资源: {comment['resource_type']} {comment['resource_id']}\n"
            f"用户: {comment['openid']}\n"
            f"内容: {comment['content']}\n"
            f"状态: {status_text}, 创建时间: {comment['create_time']}\n")

async def generate_report():
    """生成评论分析报告"""
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 创建报告目录
    report_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reports")
    os.makedirs(report_dir, exist_ok=True)
    
    # 报告文件名
    filename = os.path.join(report_dir, f"comment_report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
    
    # 获取数据
    stats = await get_comment_stats()
    recent_sensitive = await get_recent_sensitive_comments(days=3)
    active_users = await get_active_users()
    popular_posts = await get_popular_posts()
    
    # 构建报告内容
    report = [
        f"南开Wiki小程序评论分析报告",
        f"生成时间: {now}",
        f"\n=============== 基本统计 ===============\n"
    ]
    
    # 添加统计信息
    for key, value in stats.items():
        report.append(f"{key}: {value}")
    
    # 添加最近敏感评论
    report.append(f"\n============ 最近敏感评论 ({len(recent_sensitive)}条) ============\n")
    if recent_sensitive:
        for i, comment in enumerate(recent_sensitive, 1):
            report.append(f"--- 敏感评论 {i} ---")
            report.append(format_comment(comment))
    else:
        report.append("最近3天无敏感评论")
    
    # 添加活跃用户
    report.append(f"\n============ 最活跃用户 (近7天) ============\n")
    if active_users:
        for i, user in enumerate(active_users, 1):
            report.append(f"{i}. 用户: {user['openid']}, 评论数: {user['comment_count']}")
    else:
        report.append("近7天无活跃用户数据")
    
    # 添加热门帖子
    report.append(f"\n============ 最热门帖子 (近7天) ============\n")
    if popular_posts:
        for i, post in enumerate(popular_posts, 1):
            report.append(f"{i}. 帖子ID: {post['resource_id']}, 评论数: {post['comment_count']}")
    else:
        report.append("近7天无热门帖子数据")
    
    # 写入报告文件
    with open(filename, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report))
    
    logger.info(f"评论报告已生成: {filename}")
    print(f"评论报告已生成: {filename}")
    
    # 在控制台打印报告
    print('\n'.join(report))

async def main():
    await generate_report()

if __name__ == "__main__":
    asyncio.run(main()) 