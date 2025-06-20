#!/usr/bin/env python3
"""
简化的查询功能测试脚本
专门测试RagPipeline的查询功能，避免重复加载大索引文件
"""

import sys
import os
import asyncio
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

from config import Config
from core.utils import register_logger
from etl.rag.pipeline import RagPipeline
from etl.rag.strategies import RetrievalStrategy, RerankStrategy

# 配置
config = Config()
logger = register_logger(__name__)

async def test_basic_query():
    """测试基本查询功能"""
    print("🔍 测试基本查询功能...")
    
    try:
        from etl.rag_pipeline import RagPipeline, RetrievalStrategy, RerankStrategy
        
        # 初始化管道
        pipeline = RagPipeline()
        
        # 测试查询
        test_queries = ["南开大学", "计算机学院"]
        
        for query in test_queries:
            try:
                print(f"\n测试查询: '{query}'")
                
                # 使用run方法进行查询
                results = pipeline.run(
                    query=query,
                    retrieval_strategy=RetrievalStrategy.HYBRID,  # 测试改进后的HYBRID
                    rerank_strategy=RerankStrategy.BGE_RERANKER,
                    skip_generation=True,
                    top_k_retrieve=5,
                    top_k_rerank=3
                )
                
                if results and 'retrieved_nodes' in results:
                    nodes = results['retrieved_nodes']
                    print(f"✅ 查询成功，返回{len(nodes)}个结果")
                    
                    # 显示前几个结果
                    for i, node in enumerate(nodes[:2]):
                        if hasattr(node, 'metadata') and hasattr(node, 'text'):
                            title = node.metadata.get('title', '无标题')[:50]
                            content = node.text[:100] if node.text else '无内容'
                            print(f"  结果{i+1}: {title} - {content}...")
                        else:
                            print(f"  结果{i+1}: {str(node)[:100]}...")
                else:
                    print("❌ 查询返回空结果")
                    
            except Exception as e:
                print(f"❌ 查询'{query}'失败: {e}")
                
    except Exception as e:
        print(f"❌ 测试失败: {e}")

async def test_wildcard_query():
    """测试通配符查询"""
    print("\n🔍 测试通配符查询功能...")
    
    try:
        from etl.rag_pipeline import RagPipeline
        
        pipeline = RagPipeline()
        
        # 测试通配符查询
        wildcard_queries = ["南开*", "计算机*"]
        
        for query in wildcard_queries:
            try:
                print(f"\n测试通配符查询: '{query}'")
                
                results = pipeline.run(
                    query=query,
                    skip_generation=True,
                    top_k_retrieve=3
                )
                
                if results and 'retrieved_nodes' in results:
                    nodes = results['retrieved_nodes']
                    print(f"✅ 通配符查询成功，返回{len(nodes)}个结果")
                else:
                    print("❌ 通配符查询返回空结果")
                    
            except Exception as e:
                print(f"❌ 通配符查询'{query}'失败: {e}")
                
    except Exception as e:
        print(f"❌ 通配符测试失败: {e}")

async def main():
    """主测试流程"""
    print("🚀 开始简化查询测试...")
    
    await test_basic_query()
    await test_wildcard_query()
    
    print("\n✅ 查询测试完成！")

def test_rag_functionalities():
    """测试RAG管道的核心功能"""
    logger.info("--- 测试RAG管道功能 ---")
    
    try:
        from etl.rag.pipeline import RagPipeline
        rag_pipeline = RagPipeline()
        logger.info("RAG管道初始化成功。")
    except Exception as e:
        logger.error(f"RAG管道初始化失败: {e}")
        assert False, f"RAG pipeline initialization failed: {e}"

if __name__ == "__main__":
    asyncio.run(main()) 