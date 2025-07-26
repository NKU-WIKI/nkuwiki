"""
PageRank计算模块

负责计算网页的PageRank分数，提供链接图分析和权威性评估功能。

主要功能：
- 从MySQL链接图数据计算PageRank分数
- 支持增量更新和批量处理
- 集成到检索排序系统中
"""

# PageRank计算参数
PAGERANK_ALPHA = 0.85  # 阻尼系数
PAGERANK_MAX_ITER = 100  # 最大迭代次数
PAGERANK_TOL = 1e-6  # 收敛阈值

# 导入主要功能函数
from .calculate_pagerank_mysql import (
    load_link_graph_from_mysql,
    calculate_pagerank, 
    save_pagerank_to_mysql,
    update_website_nku_pagerank,
    main as calculate_pagerank_main
)

__all__ = [
    'PAGERANK_ALPHA', 'PAGERANK_MAX_ITER', 'PAGERANK_TOL',
    'load_link_graph_from_mysql', 'calculate_pagerank', 
    'save_pagerank_to_mysql', 'update_website_nku_pagerank',
    'calculate_pagerank_main'
] 