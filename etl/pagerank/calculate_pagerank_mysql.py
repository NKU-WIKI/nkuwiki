#!/usr/bin/env python3
"""
MySQL版本的PageRank计算脚本

从MySQL的link_graph表读取链接关系，计算PageRank分数，
并将结果保存到pagerank_scores表，然后更新website_nku表。
"""

import asyncio
import sys
import logging
import networkx as nx
from pathlib import Path
from tqdm import tqdm
from typing import Dict, List, Tuple

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).resolve().parent))

from config import Config
from etl.load import db_core

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def load_link_graph_from_mysql() -> List[Tuple[str, str]]:
    """从MySQL的link_graph表加载链接关系"""
    try:
        logger.info("从MySQL加载链接图数据...")
        
        # 查询所有链接关系
        query = "SELECT source_url, target_url FROM link_graph"
        records = await db_core.execute_query(query, fetch=True)
        
        if not records:
            logger.warning("link_graph表中没有数据")
            return []
        
        # 转换为元组列表
        links = [(record['source_url'], record['target_url']) for record in records]
        logger.info(f"成功加载 {len(links)} 条链接关系")
        
        return links
        
    except Exception as e:
        logger.error(f"加载链接图数据失败: {e}")
        return []


def calculate_pagerank(links: List[Tuple[str, str]], alpha: float = 0.85, max_iter: int = 100) -> Dict[str, float]:
    """使用NetworkX计算PageRank分数"""
    if not links:
        logger.warning("链接列表为空，无法计算PageRank")
        return {}
    
    logger.info("构建有向图...")
    G = nx.DiGraph()
    
    # 添加边，带进度条
    with tqdm(links, desc="构建图", unit="链接") as pbar:
        for source, target in pbar:
            G.add_edge(source, target)
    
    logger.info(f"图构建完成: {G.number_of_nodes()} 个节点, {G.number_of_edges()} 条边")
    
    # 计算PageRank
    logger.info(f"开始计算PageRank (alpha={alpha}, max_iter={max_iter})...")
    with tqdm(total=1, desc="计算PageRank", unit="步骤") as pbar:
        pagerank_scores = nx.pagerank(G, alpha=alpha, max_iter=max_iter)
        pbar.update(1)
    
    logger.info(f"PageRank计算完成，得到 {len(pagerank_scores)} 个节点的分数")
    
    # 显示分数统计
    scores = list(pagerank_scores.values())
    logger.info(f"PageRank分数统计: 最大={max(scores):.6f}, 最小={min(scores):.6f}, 平均={sum(scores)/len(scores):.6f}")
    
    return pagerank_scores


async def save_pagerank_to_mysql(pagerank_scores: Dict[str, float]) -> bool:
    """将PageRank分数保存到MySQL的pagerank_scores表"""
    if not pagerank_scores:
        logger.warning("PageRank分数为空，跳过保存")
        return False
    
    try:
        logger.info("清空现有的pagerank_scores表...")
        await db_core.execute_query("DELETE FROM pagerank_scores", fetch=False)
        
        logger.info("保存PageRank分数到MySQL...")
        
        # 批量插入数据
        batch_size = 1000
        data_list = list(pagerank_scores.items())
        total_batches = (len(data_list) + batch_size - 1) // batch_size
        
        with tqdm(total=len(data_list), desc="保存PageRank分数", unit="记录") as pbar:
            for i in range(0, len(data_list), batch_size):
                batch = data_list[i:i + batch_size]
                
                # 准备批量插入语句，使用ON DUPLICATE KEY UPDATE处理重复
                placeholders = ",".join(["(%s, %s)"] * len(batch))
                query = f"""INSERT INTO pagerank_scores (url, pagerank_score) VALUES {placeholders}
                           ON DUPLICATE KEY UPDATE 
                           pagerank_score = VALUES(pagerank_score),
                           calculation_date = CURRENT_TIMESTAMP"""
                
                # 展平数据
                values = []
                for url, score in batch:
                    values.extend([url, float(score)])
                
                # 执行插入
                await db_core.execute_query(query, values, fetch=False)
                pbar.update(len(batch))
        
        logger.info(f"成功保存 {len(pagerank_scores)} 个PageRank分数")
        return True
        
    except Exception as e:
        logger.error(f"保存PageRank分数失败: {e}")
        return False


async def update_website_nku_pagerank() -> bool:
    """更新website_nku表中的pagerank_score字段"""
    try:
        logger.info("更新website_nku表中的PageRank分数...")
        
        # 执行联合更新
        query = """
        UPDATE website_nku w 
        JOIN pagerank_scores p ON w.original_url = p.url 
        SET w.pagerank_score = p.pagerank_score
        """
        
        await db_core.execute_query(query, fetch=False)
        
        # 统计更新结果
        stats_query = """
        SELECT 
            COUNT(*) as total,
            COUNT(CASE WHEN pagerank_score > 0 THEN 1 END) as updated,
            MAX(pagerank_score) as max_score,
            AVG(pagerank_score) as avg_score
        FROM website_nku
        """
        
        stats = await db_core.execute_query(stats_query, fetch=True)
        if stats:
            stat = stats[0]
            logger.info(f"更新统计: 总记录={stat['total']}, 已更新={stat['updated']}, "
                       f"最大分数={stat['max_score']:.6f}, 平均分数={stat['avg_score']:.6f}")
        
        return True
        
    except Exception as e:
        logger.error(f"更新website_nku表失败: {e}")
        return False


async def main():
    """主函数"""
    logger.info("=== MySQL PageRank计算开始 ===")
    
    try:
        # 1. 从MySQL加载链接图
        links = await load_link_graph_from_mysql()
        if not links:
            logger.error("没有链接数据，无法计算PageRank")
            return False
        
        # 2. 计算PageRank分数
        pagerank_scores = calculate_pagerank(links)
        if not pagerank_scores:
            logger.error("PageRank计算失败")
            return False
        
        # 3. 保存到pagerank_scores表
        if not await save_pagerank_to_mysql(pagerank_scores):
            logger.error("保存PageRank分数失败")
            return False
        
        # 4. 更新website_nku表
        if not await update_website_nku_pagerank():
            logger.error("更新website_nku表失败")
            return False
        
        logger.info("=== MySQL PageRank计算成功完成 ===")
        return True
        
    except Exception as e:
        logger.error(f"PageRank计算过程出错: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    if success:
        print("✅ PageRank计算成功")
    else:
        print("❌ PageRank计算失败")
        sys.exit(1) 