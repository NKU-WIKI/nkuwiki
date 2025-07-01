#!/usr/bin/env python3
"""
统一索引构建脚本

此脚本使用ETL模块的统一路径配置来构建所有类型的索引：
- MySQL索引（数据导入和表优化）
- BM25文本索引（支持中文分词和停用词）
- Qdrant向量索引（语义嵌入和文本分块）
- Elasticsearch全文索引（通配符查询和复杂文本匹配）

所有索引器现在支持多种数据源：
- raw_files: 混合模式，从原始文件加载数据并补充PageRank分数（推荐）
- mysql: 仅从MySQL数据库加载数据
- raw_only: 仅从原始JSON文件加载数据

使用方法:
    python etl/build_all_indexes.py [--limit 1000] [--test] [--data-source raw_files]
    python etl/build_all_indexes.py --only bm25 --data-source mysql --limit 100
    python etl/build_all_indexes.py --validate
    python etl/build_all_indexes.py --batch-size 5000 --start-batch 0 --max-batches 10
    python etl/build_all_indexes.py --batch-size -1  # 不分批，一次性处理
    
分批构建示例:
    # 每批5000条，处理所有数据
    python etl/build_all_indexes.py --batch-size 5000
    
    # 从第3批开始，只处理5个批次（断点续建）
    python etl/build_all_indexes.py --start-batch 3 --max-batches 5
    
    # 只构建BM25索引，每批1000条
    python etl/build_all_indexes.py --only bm25 --batch-size 1000
"""

import sys
import argparse
import asyncio
from pathlib import Path
from typing import Dict, Any
import logging

# 关键修改：配置Python内置的logging模块以捕获第三方库的DEBUG日志
# 这将使我们能够看到 elasticsearch-py 库详细的网络活动
logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).resolve().parent.parent))

from core.utils.logger import register_logger
logger = register_logger("etl.build_indexes")

# 导入配置和ETL路径
from etl import BASE_PATH, INDEX_PATH, QDRANT_PATH, MYSQL_PATH, NLTK_PATH, MODELS_PATH
from etl.indexing.bm25_indexer import BM25Indexer
from etl.indexing.qdrant_indexer import QdrantIndexer
from etl.indexing.elasticsearch_indexer import ElasticsearchIndexer
from etl.indexing.mysql_indexer import MySQLIndexer

async def build_all_indexes(limit: int = None, test_mode: bool = False, only: str = None, data_source: str = "raw_files", 
                          batch_size: int = -1, start_batch: int = 0, max_batches: int = None, incremental: bool = False) -> Dict[str, Any]:
    """
    构建所有索引
    
    Args:
        limit: 限制处理的记录数量
        test_mode: 测试模式，不实际创建索引文件
        only: 只构建指定类型的索引 ('mysql', 'bm25', 'qdrant', 'elasticsearch')
        data_source: 数据源类型 ("raw_files"=混合模式, "mysql"=仅MySQL, "raw_only"=仅原始文件)
        batch_size: 每批处理的记录数量，-1表示不分批（默认-1）
        start_batch: 从第几批开始处理（断点续建）
        max_batches: 最大批次数，None表示处理所有批次
        
    Returns:
        所有索引的构建结果
    """
    results = {}
    
    logger.info("=" * 60)
    logger.info("开始构建所有索引")
    logger.info(f"数据基础路径: {BASE_PATH}")
    logger.info(f"索引存储路径: {INDEX_PATH}")
    logger.info(f"向量存储路径: {QDRANT_PATH}")
    logger.info(f"MySQL数据路径: {MYSQL_PATH}")
    logger.info(f"NLTK数据路径: {NLTK_PATH}")
    logger.info(f"模型缓存路径: {MODELS_PATH}")
    if limit:
        logger.info(f"处理记录限制: {limit}")
    logger.info(f"数据源类型: {data_source}")
    if batch_size == -1:
        logger.info("分批配置: 不分批处理（一次性处理所有数据）")
    else:
        logger.info(f"分批配置: batch_size={batch_size}, start_batch={start_batch}, max_batches={max_batches}")
    if test_mode:
        logger.info("运行模式: 测试模式")
    logger.info("=" * 60)
    
    # 0. 构建MySQL索引（数据导入）
    if only is None or only == 'mysql':
        logger.info("🗄️ [0/4] 开始构建MySQL索引...")
        logger.info(f"   - 测试模式: {'是' if test_mode else '否'}")
        
        try:
            mysql_indexer = MySQLIndexer(logger)
            logger.info("   - 初始化MySQL索引器完成")
            
            # MySQL索引构建（数据导入和表优化）
            mysql_result = await mysql_indexer.build_indexes(dry_run=test_mode)
            results['mysql'] = {
                "success": mysql_result,
                "message": "MySQL索引构建成功" if mysql_result else "MySQL索引构建失败"
            }
            
            if mysql_result:
                # 获取统计信息
                stats = await mysql_indexer.get_statistics()
                total_records = stats.get('total_records', 0)
                logger.info(f"✅ MySQL索引构建成功！数据库包含 {total_records} 条记录")
                logger.info(f"   - 详情: {stats}")
            else:
                logger.error("❌ MySQL索引构建失败")
                
        except Exception as e:
            logger.error(f"❌ MySQL索引构建异常: {e}")
            results['mysql'] = {"success": False, "error": str(e)}
            
        logger.info("🗄️ MySQL索引构建阶段结束\n")
    else:
        logger.info("⏭️ 跳过MySQL索引构建（根据 --only 参数）")
    
    # 1. 构建BM25索引
    if only is None or only == 'bm25':
        logger.info("🔍 [1/4] 开始构建BM25索引...")
        logger.info(f"   - 记录限制: {limit if limit else '无限制'}")
        logger.info(f"   - 数据源: {data_source}")
        logger.info(f"   - 测试模式: {'是' if test_mode else '否'}")
        
        try:
            bm25_indexer = BM25Indexer(logger)
            logger.info("   - 初始化BM25索引器完成")
            
            bm25_result = await bm25_indexer.build_indexes(
                limit=limit,
                test_mode=test_mode,
                data_source=data_source,
                batch_size=batch_size,
                start_batch=start_batch,
                max_batches=max_batches
            )
            results['bm25'] = bm25_result
            
            if bm25_result['success']:
                node_count = bm25_result.get('total_nodes', 0)
                logger.info(f"✅ BM25索引构建成功！处理了 {node_count} 个节点")
                logger.info(f"   - 详情: {bm25_result['message']}")
            else:
                logger.error(f"❌ BM25索引构建失败: {bm25_result['message']}")
                if 'error' in bm25_result:
                    logger.error(f"   - 错误详情: {bm25_result['error']}")
                
        except Exception as e:
            logger.error(f"❌ BM25索引构建异常: {e}")
            results['bm25'] = {"success": False, "error": str(e)}
            
        logger.info("🔍 BM25索引构建阶段结束\n")
    else:
        logger.info("⏭️ 跳过BM25索引构建（根据 --only 参数）")
    
    # 2. 构建Qdrant向量索引  
    if only is None or only == 'qdrant':
        # QdrantIndexer的build_indexes也需要改造
        logger.warning("QdrantIndexer的改造尚未完成，暂时跳过。")
        # try:
        #     qdrant_indexer = QdrantIndexer(logger)
        # ...
    
    # 3. 构建Elasticsearch索引
    if only is None or only == 'elasticsearch':
        logger.info("🔎 [3/4] 开始构建Elasticsearch索引...")
        logger.info(f"   - 记录限制: {limit if limit else '无限制'}")
        logger.info(f"   - 数据源: {data_source}")
        logger.info(f"   - 测试模式: {'是' if test_mode else '否'}")
        
        try:
            es_indexer = ElasticsearchIndexer(logger)
            logger.info("   - 初始化Elasticsearch索引器完成")
            
            es_result = await es_indexer.build_indexes(
                limit=limit,
                test_mode=test_mode,
                data_source=data_source,
                batch_size=batch_size,
                start_batch=start_batch,
                max_batches=max_batches
            )
            results['elasticsearch'] = es_result
            
            if es_result['success']:
                record_count = es_result.get('total_records', 0)
                indexed_count = es_result.get('indexed', 0)
                logger.info(f"✅ Elasticsearch索引构建成功！索引了 {indexed_count}/{record_count} 条记录")
                logger.info(f"   - 详情: {es_result['message']}")
            else:
                logger.error(f"❌ Elasticsearch索引构建失败: {es_result['message']}")
                if 'error' in es_result:
                    logger.error(f"   - 错误详情: {es_result['error']}")
                
        except Exception as e:
            logger.error(f"❌ Elasticsearch索引构建异常: {e}")
            results['elasticsearch'] = {"success": False, "error": str(e)}
            
        logger.info("🔎 Elasticsearch索引构建阶段结束\n")
    else:
        logger.info("⏭️ 跳过Elasticsearch索引构建（根据 --only 参数）")
    
    return results


async def validate_all_indexes() -> Dict[str, Any]:
    """
    验证所有索引的健康状态
    """
    results = {}
    config = Config()
    
    logger.info("=" * 60)
    logger.info("开始验证所有索引")
    logger.info("=" * 60)

    # 验证MySQL索引
    try:
        mysql_indexer = MySQLIndexer(logger)
        stats = await mysql_indexer.get_statistics()
        total_records = stats.get('total_records', 0)
        results['mysql'] = {"success": total_records > 0, "total_records": total_records}
    except Exception as e:
        results['mysql'] = {"success": False, "error": str(e)}

    # 验证BM25索引
    try:
        bm25_indexer = BM25Indexer(logger)
        results['bm25'] = await bm25_indexer.validate_index()
    except Exception as e:
        results['bm25'] = {"success": False, "error": str(e)}

    # 验证Qdrant索引
    try:
        qdrant_indexer = QdrantIndexer(logger)
        results['qdrant'] = await qdrant_indexer.validate_index()
    except Exception as e:
        results['qdrant'] = {"success": False, "error": str(e)}

    # 验证Elasticsearch索引
    try:
        es_indexer = ElasticsearchIndexer(logger)
        results['elasticsearch'] = await es_indexer.validate_index()
    except Exception as e:
        results['elasticsearch'] = {"success": False, "error": str(e)}
        
    # 统计结果
    logger.info("\n" + "=" * 60)
    logger.info("索引验证完成！")
    
    success_count = sum(1 for r in results.values() if r.get('success', False))
    total_count = len(results)
    
    logger.info(f"健康索引: {success_count}/{total_count}")
    
    for index_type, result in results.items():
        status = "✅" if result.get('success', False) else "❌"
        message = result.get('message', 'N/A')
        if not result.get('success', False):
            message = result.get('error', '未知错误')
            
        logger.info(f"  {status} {index_type.upper()}: {message}")
    
    logger.info("=" * 60)
    
    return {
        'success': success_count == total_count,
        'results': results,
        'summary': {
            'total': total_count,
            'success': success_count,
            'failed': total_count - success_count
        }
    }


def main():
    """
    主函数
    """
    parser = argparse.ArgumentParser(description='构建所有类型的索引')
    parser.add_argument('--limit', type=int, default=None, help='限制处理的记录数量')
    parser.add_argument('--test', action='store_true', help='测试模式，不实际创建索引')
    parser.add_argument('--only', type=str, default=None, help='只构建指定索引 (mysql, bm25, qdrant, elasticsearch)')
    parser.add_argument('--data-source', type=str, default='raw_files', help='数据源 (raw_files, mysql, raw_only)')
    parser.add_argument('--validate', action='store_true', help='验证所有索引的健康状态')
    parser.add_argument('--batch-size', type=int, default=-1, help='每批处理的记录数量（-1表示不分批）')
    parser.add_argument('--start-batch', type=int, default=0, help='从第几批开始处理')
    parser.add_argument('--max-batches', type=int, default=None, help='最大批次数')
    parser.add_argument('--incremental', action='store_true', help='是否为增量构建（仅Qdrant）')
    
    args = parser.parse_args()

    if args.validate:
        asyncio.run(validate_all_indexes())
    else:
        results = asyncio.run(build_all_indexes(
            limit=args.limit, 
            test_mode=args.test, 
            only=args.only,
            data_source=args.data_source,
            batch_size=args.batch_size,
            start_batch=args.start_batch,
            max_batches=args.max_batches,
            incremental=args.incremental
        ))
        
        # 打印最终统计结果
        success_count = sum(1 for r in results.values() if r.get('success', False))
        total_count = len(results)
        
        logger.info("\n" + "=" * 60)
        logger.info("所有索引构建任务已完成！")
        logger.info(f"成功构建: {success_count}/{total_count} 个索引类型")
        
        for index_type, result in results.items():
            status = "✅" if result.get('success', False) else "❌"
            message = result.get('message', result.get('error', '未知状态'))
            logger.info(f"  {status} {index_type.upper()}: {message}")
        logger.info("=" * 60)

if __name__ == '__main__':
    main() 