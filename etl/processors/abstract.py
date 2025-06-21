"""
摘要生成处理器

提供基于AI的文档摘要生成功能
"""

import sys
import asyncio
from pathlib import Path
from typing import Optional
from core.utils import register_logger

logger = register_logger("etl.processors.abstract")

def get_bot_ids_by_tag(bot_tag="abstract"):
    """根据bot_tag从配置中获取所有相关的bot_id"""
    try:
        bot_ids = config.get(f"core.agent.coze.{bot_tag}_bot_id", [])
        if isinstance(bot_ids, str):
            bot_ids = [bot_ids] if bot_ids else []
    except Exception as e:
        logger.warning(f"获取{bot_tag}_bot_id数组时出错: {e}")
        bot_ids = []
    
    if not bot_ids:
        base_bot_id = config.get(f"core.agent.coze.{bot_tag}_bot_id", "")
        if base_bot_id:
            bot_ids.append(base_bot_id)
        
        for i in range(1, 10):
            bot_id = config.get(f"core.agent.coze.{bot_tag}_bot_id_{i}", "")
            if bot_id:
                bot_ids.append(bot_id)
    
    bot_ids = [bid for bid in bot_ids if bid]
    # logger.info(f"为标签 '{bot_tag}' 加载了 {len(bot_ids)} 个有效的bot_id")
    return bot_ids


class BotIdPool:
    """Bot ID池管理器"""
    
    def __init__(self, bot_ids):
        self.bot_ids = bot_ids
        self.in_use = set()
        self.lock = asyncio.Lock()
        self.waiting = asyncio.Queue
        self.usage_count = {bid: 0 for bid in bot_ids}
        self.max_wait_time = 30

    async def get_bot_id(self):
        """获取一个可用的bot_id"""
        async with self.lock:
            available = [bid for bid in self.bot_ids if bid not in self.in_use]
            if available:
                selected = min(available, key=lambda bid: self.usage_count[bid])
                self.in_use.add(selected)
                self.usage_count[selected] += 1
                return selected
                
        logger.warning("所有bot_id都在使用中，等待可用bot_id...")
        
        future = asyncio.Future()
        await self.waiting.put(future)
        
        try:
            return await asyncio.wait_for(future, timeout=self.max_wait_time)
        except asyncio.TimeoutError:
            logger.warning(f"等待bot_id超时({self.max_wait_time}秒)，尝试再次获取")
            async with self.lock:
                selected = min(self.bot_ids, key=lambda bid: self.usage_count[bid])
                self.usage_count[selected] += 1
                return selected
                
    async def release_bot_id(self, bot_id):
        """释放一个bot_id"""
        async with self.lock:
            if bot_id in self.in_use:
                self.in_use.remove(bot_id)
                
                if not self.waiting.empty():
                    future = await self.waiting.get()
                    if not future.done():
                        future.set_result(bot_id)


class AbstractProcessor:
    """摘要生成处理器"""
    
    def __init__(self):
        self._bot_id_pools = {}
        # 初始化默认的"abstract"标签池
        bot_ids = get_bot_ids_by_tag("abstract")
        self._bot_id_pools["abstract"] = BotIdPool(bot_ids)
    
    def get_bot_id_pool(self, bot_tag="abstract"):
        """获取指定标签的bot_id池"""
        if bot_tag not in self._bot_id_pools:
            tag_bot_ids = get_bot_ids_by_tag(bot_tag)
            if not tag_bot_ids:
                logger.warning(f"标签'{bot_tag}'没有配置有效的bot_id，使用默认标签'abstract'")
                return self._bot_id_pools["abstract"]
            self._bot_id_pools[bot_tag] = BotIdPool(tag_bot_ids)
        return self._bot_id_pools[bot_tag]

    async def generate_abstract_async(
        self, 
        file_path, 
        max_length: int = 300, 
        bot_tag: str = "abstract"
    ) -> Optional[str]:
        """异步为指定的Markdown文件生成摘要"""
        if not isinstance(file_path, Path):
            file_path = Path(file_path)
        
        pool = self.get_bot_id_pool(bot_tag)
        bot_id = await pool.get_bot_id()
        if not bot_id:
            logger.error(f"无法获取可用的bot_id(标签:{bot_tag}): {file_path}")
            return None
        
        try:
            content = file_path.read_text(encoding='utf-8')
            
            # 动态导入以避免循环依赖
            from core.agent.coze.coze_agent import CozeAgent
            from core.bridge.context import Context, ContextType
            from core.bridge.reply import ReplyType
            
            coze_agent = CozeAgent()
            coze_agent.bot_id = bot_id
            
            context = Context(ContextType.TEXT)
            context["session_id"] = "abstract_generation"
            
            reply = await asyncio.to_thread(lambda: coze_agent.reply(content, context))
            
            if reply is None or reply.type != ReplyType.STREAM:
                logger.error(f"生成摘要失败: {file_path}")
                return None
                
            full_reply = ""
            for chunk in reply.content:
                full_reply += chunk
                
            logger.debug(f"生成摘要预览: {full_reply[:100]}")
            return full_reply
            
        except Exception as e:
            logger.error(f"生成摘要时发生错误: {e}")
            return None
        finally:
            await pool.release_bot_id(bot_id)

    def generate_abstract_sync(
        self, 
        file_path, 
        max_length: int = 300, 
        bot_tag: str = "abstract"
    ) -> Optional[str]:
        """生成文档摘要的同步包装函数"""
        if not isinstance(file_path, Path):
            file_path = Path(file_path)
            
        try:
            loop = asyncio.get_running_loop()
            return asyncio.run_coroutine_threadsafe(
                self.generate_abstract_async(file_path, max_length, bot_tag), 
                loop
            ).result()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(
                    self.generate_abstract_async(file_path, max_length, bot_tag)
                )
            finally:
                loop.close()


# 全局实例
_abstract_processor = AbstractProcessor()

# 向后兼容函数
async def generate_abstract_async(file_path, max_length: int = 300, bot_tag: str = "abstract") -> Optional[str]:
    """向后兼容的异步摘要生成函数"""
    return await _abstract_processor.generate_abstract_async(file_path, max_length, bot_tag)

def generate_abstract(file_path, max_length: int = 300, bot_tag: str = "abstract") -> Optional[str]:
    """向后兼容的同步摘要生成函数"""
    return _abstract_processor.generate_abstract_sync(file_path, max_length, bot_tag)

def get_bot_ids_by_tag_compat(bot_tag="abstract"):
    """向后兼容的bot_ids获取函数"""
    return get_bot_ids_by_tag(bot_tag) 