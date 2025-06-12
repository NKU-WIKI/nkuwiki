#!/usr/bin/env python3
"""
通用文本分块缓存管理器

提供分块结果的持久化缓存，避免重复分块计算，提高索引构建效率。
支持多种缓存策略和自动过期机制。
"""

import os
import pickle
import hashlib
import json
import asyncio
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from datetime import datetime, timedelta
import aiofiles
from tqdm import tqdm

from llama_index.core.schema import BaseNode, TextNode
from llama_index.core.node_parser import SentenceSplitter
from core.utils import register_logger


class ChunkCacheManager:
    """文本分块缓存管理器"""
    
    def __init__(self, 
                 cache_dir: str = "/data/cache/chunks",
                 chunk_size: int = 512,
                 chunk_overlap: int = 200,
                 cache_ttl_days: int = 30,
                 logger=None):
        """
        初始化分块缓存管理器
        
        Args:
            cache_dir: 缓存目录
            chunk_size: 分块大小
            chunk_overlap: 分块重叠
            cache_ttl_days: 缓存有效期（天）
            logger: 日志器
        """
        self.cache_dir = Path(cache_dir)
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.cache_ttl = timedelta(days=cache_ttl_days)
        self.logger = logger or register_logger("chunk_cache")
        
        # 创建缓存目录
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化分割器
        self.splitter = SentenceSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        
        # 缓存元数据文件
        self.metadata_file = self.cache_dir / "cache_metadata.json"
        self.metadata = self._load_metadata()
        
        self.logger.info(f"分块缓存管理器初始化完成: {cache_dir}")
        self.logger.info(f"分块参数: chunk_size={chunk_size}, chunk_overlap={chunk_overlap}")
    
    def _load_metadata(self) -> Dict[str, Any]:
        """加载缓存元数据"""
        try:
            if self.metadata_file.exists():
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            self.logger.warning(f"加载缓存元数据失败: {e}")
        
        return {
            "cache_version": "1.0",
            "chunk_params": {
                "chunk_size": self.chunk_size,
                "chunk_overlap": self.chunk_overlap
            },
            "cached_items": {}
        }
    
    def _save_metadata(self):
        """保存缓存元数据"""
        try:
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(self.metadata, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"保存缓存元数据失败: {e}")
    
    def _generate_cache_key(self, doc_nodes: List[BaseNode]) -> str:
        """生成缓存键"""
        # 基于文档内容和分块参数生成哈希
        content_hash = hashlib.md5()
        
        # 添加分块参数
        params_str = f"chunk_size={self.chunk_size},chunk_overlap={self.chunk_overlap}"
        content_hash.update(params_str.encode('utf-8'))
        
        # 添加文档内容（取前1000个字符的哈希，避免过长）
        for node in doc_nodes[:100]:  # 限制节点数量避免哈希过长
            text_sample = node.text[:1000] if hasattr(node, 'text') else str(node)[:1000]
            content_hash.update(text_sample.encode('utf-8'))
        
        # 添加文档数量信息
        count_info = f"total_docs={len(doc_nodes)}"
        content_hash.update(count_info.encode('utf-8'))
        
        return content_hash.hexdigest()
    
    def _get_cache_path(self, cache_key: str) -> Path:
        """获取缓存文件路径"""
        return self.cache_dir / f"chunks_{cache_key}.pkl"
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """检查缓存是否有效"""
        # 检查缓存文件是否存在
        cache_path = self._get_cache_path(cache_key)
        if not cache_path.exists():
            return False
        
        # 检查分块参数是否匹配
        cached_params = self.metadata.get("chunk_params", {})
        current_params = {
            "chunk_size": self.chunk_size,
            "chunk_overlap": self.chunk_overlap
        }
        if cached_params != current_params:
            self.logger.info(f"分块参数已变更，缓存失效: {cache_key}")
            return False
        
        # 检查缓存时间
        cache_info = self.metadata.get("cached_items", {}).get(cache_key)
        if cache_info:
            cache_time = datetime.fromisoformat(cache_info["created_at"])
            if datetime.now() - cache_time > self.cache_ttl:
                self.logger.info(f"缓存已过期，失效: {cache_key}")
                return False
        
        return True
    
    async def _load_chunks_from_cache(self, cache_key: str) -> Optional[List[BaseNode]]:
        """从缓存加载分块结果"""
        try:
            cache_path = self._get_cache_path(cache_key)
            
            def _load():
                with open(cache_path, 'rb') as f:
                    return pickle.load(f)
            
            loop = asyncio.get_running_loop()
            chunks = await loop.run_in_executor(None, _load)
            
            self.logger.info(f"从缓存加载 {len(chunks)} 个分块: {cache_key}")
            return chunks
            
        except Exception as e:
            self.logger.warning(f"从缓存加载分块失败: {e}")
            return None
    
    async def _save_chunks_to_cache(self, cache_key: str, chunks: List[BaseNode]):
        """保存分块结果到缓存"""
        try:
            cache_path = self._get_cache_path(cache_key)
            
            def _save():
                with open(cache_path, 'wb') as f:
                    pickle.dump(chunks, f)
            
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, _save)
            
            # 更新元数据
            self.metadata["cached_items"][cache_key] = {
                "created_at": datetime.now().isoformat(),
                "chunk_count": len(chunks),
                "file_size": cache_path.stat().st_size
            }
            self._save_metadata()
            
            self.logger.info(f"保存 {len(chunks)} 个分块到缓存: {cache_key}")
            
        except Exception as e:
            self.logger.error(f"保存分块到缓存失败: {e}")
    
    async def chunk_documents_with_cache(self, doc_nodes: List[BaseNode], 
                                       force_refresh: bool = False,
                                       show_progress: bool = True) -> List[BaseNode]:
        """
        对文档进行分块，使用缓存优化
        
        Args:
            doc_nodes: 原始文档节点列表
            force_refresh: 强制刷新缓存
            show_progress: 显示进度条
            
        Returns:
            分块后的节点列表
        """
        if not doc_nodes:
            return []
        
        # 生成缓存键
        cache_key = self._generate_cache_key(doc_nodes)
        
        # 尝试从缓存加载
        if not force_refresh and self._is_cache_valid(cache_key):
            cached_chunks = await self._load_chunks_from_cache(cache_key)
            if cached_chunks is not None:
                return cached_chunks
        
        # 缓存未命中，执行分块
        self.logger.info(f"缓存未命中，开始分块 {len(doc_nodes)} 个文档")
        chunks = await self._chunk_documents(doc_nodes, show_progress)
        
        # 保存到缓存
        if chunks:
            await self._save_chunks_to_cache(cache_key, chunks)
        
        return chunks
    
    async def _chunk_documents(self, doc_nodes: List[BaseNode], show_progress: bool = True) -> List[BaseNode]:
        """执行实际的文档分块"""
        chunked_nodes = []
        
        progress_bar = tqdm(doc_nodes, desc="文本分块", unit="文档", disable=not show_progress)
        
        for doc_node in progress_bar:
            try:
                # 文本分块
                chunks = self.splitter.get_nodes_from_documents([doc_node])
                
                # 为每个分块添加原始元数据
                for chunk in chunks:
                    chunk.metadata.update(doc_node.metadata)
                    chunked_nodes.append(chunk)
                
                if show_progress:
                    progress_bar.set_postfix({'总块数': len(chunked_nodes)})
                
            except Exception as e:
                self.logger.warning(f"分块文档时出错: {e}")
                continue
        
        if show_progress:
            progress_bar.close()
        
        self.logger.info(f"分块完成，总计 {len(chunked_nodes)} 个文本块")
        return chunked_nodes
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        cached_items = self.metadata.get("cached_items", {})
        total_items = len(cached_items)
        total_chunks = sum(item.get("chunk_count", 0) for item in cached_items.values())
        
        # 计算总文件大小
        total_size = 0
        for cache_key in cached_items:
            cache_path = self._get_cache_path(cache_key)
            if cache_path.exists():
                total_size += cache_path.stat().st_size
        
        return {
            "cache_dir": str(self.cache_dir),
            "total_cached_items": total_items,
            "total_chunks": total_chunks,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "chunk_params": self.metadata.get("chunk_params", {}),
            "cache_ttl_days": self.cache_ttl.days
        }
    
    async def cleanup_expired_cache(self):
        """清理过期缓存"""
        cached_items = self.metadata.get("cached_items", {})
        expired_keys = []
        
        for cache_key, cache_info in cached_items.items():
            try:
                cache_time = datetime.fromisoformat(cache_info["created_at"])
                if datetime.now() - cache_time > self.cache_ttl:
                    expired_keys.append(cache_key)
            except Exception as e:
                self.logger.warning(f"检查缓存项时出错: {e}")
                expired_keys.append(cache_key)
        
        # 删除过期缓存
        for cache_key in expired_keys:
            cache_path = self._get_cache_path(cache_key)
            try:
                if cache_path.exists():
                    cache_path.unlink()
                del cached_items[cache_key]
                self.logger.info(f"删除过期缓存: {cache_key}")
            except Exception as e:
                self.logger.error(f"删除过期缓存失败 {cache_key}: {e}")
        
        if expired_keys:
            self._save_metadata()
            self.logger.info(f"清理了 {len(expired_keys)} 个过期缓存项")
    
    async def clear_all_cache(self):
        """清空所有缓存"""
        try:
            # 删除所有缓存文件
            for cache_file in self.cache_dir.glob("chunks_*.pkl"):
                cache_file.unlink()
            
            # 重置元数据
            self.metadata["cached_items"] = {}
            self._save_metadata()
            
            self.logger.info("已清空所有分块缓存")
            
        except Exception as e:
            self.logger.error(f"清空缓存失败: {e}")


# 全局缓存管理器实例
_global_chunk_cache: Optional[ChunkCacheManager] = None


def get_chunk_cache_manager(cache_dir: str = None, 
                          chunk_size: int = 512, 
                          chunk_overlap: int = 200,
                          cache_ttl_days: int = 30) -> ChunkCacheManager:
    """获取全局分块缓存管理器实例"""
    global _global_chunk_cache
    
    if _global_chunk_cache is None:
        from etl import CACHE_PATH
        default_cache_dir = str(CACHE_PATH / "chunks")
        
        _global_chunk_cache = ChunkCacheManager(
            cache_dir=cache_dir or default_cache_dir,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            cache_ttl_days=cache_ttl_days
        )
    
    return _global_chunk_cache


async def chunk_documents_cached(doc_nodes: List[BaseNode],
                               chunk_size: int = 512,
                               chunk_overlap: int = 200,
                               force_refresh: bool = False,
                               show_progress: bool = True) -> List[BaseNode]:
    """
    便捷函数：使用缓存进行文档分块
    
    Args:
        doc_nodes: 原始文档节点列表
        chunk_size: 分块大小
        chunk_overlap: 分块重叠
        force_refresh: 强制刷新缓存
        show_progress: 显示进度条
        
    Returns:
        分块后的节点列表
    """
    cache_manager = get_chunk_cache_manager(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )
    
    return await cache_manager.chunk_documents_with_cache(
        doc_nodes=doc_nodes,
        force_refresh=force_refresh,
        show_progress=show_progress
    ) 