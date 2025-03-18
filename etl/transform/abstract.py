import sys
from pathlib import Path
import asyncio
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from etl.transform import *
from core.agent.coze.coze_agent import CozeAgent
from core.bridge.context import Context, ContextType
from core.bridge.reply import ReplyType

def get_bot_ids_by_tag(bot_tag="abstract"):
    """
    根据bot_tag从配置中获取所有相关的bot_id
    
    Args:
        bot_tag: 机器人标签，默认为"abstract"（抽象摘要）
    
    Returns:
        bot_id列表
    """
    # 尝试直接获取数组形式的配置
    try:
        bot_ids = config.get(f"core.agent.coze.{bot_tag}_bot_id", [])
        # 如果返回的是字符串而非列表，则包装成列表
        if isinstance(bot_ids, str):
            bot_ids = [bot_ids] if bot_ids else []
    except Exception as e:
        transform_logger.warning(f"获取{bot_tag}_bot_id数组时出错: {e}")
        bot_ids = []
    
    # 如果数组形式没有配置，尝试获取原来格式的配置（兼容性）
    if not bot_ids:
        # 获取不带索引的bot_id
        base_bot_id = config.get(f"core.agent.coze.{bot_tag}_bot_id", "")
        if base_bot_id:
            bot_ids.append(base_bot_id)
        
        # 获取带索引的bot_id (bot_tag_bot_id_1, bot_tag_bot_id_2, ...)
        for i in range(1, 10):  # 假设最多有10个索引
            bot_id = config.get(f"core.agent.coze.{bot_tag}_bot_id_{i}", "")
            if bot_id:
                bot_ids.append(bot_id)
    
    # 过滤掉空的bot_id
    bot_ids = [bid for bid in bot_ids if bid]
    transform_logger.info(f"为标签 '{bot_tag}' 加载了 {len(bot_ids)} 个有效的bot_id")
    return bot_ids

# 创建bot_id池
class BotIdPool:
    def __init__(self, bot_ids):
        self.bot_ids = bot_ids
        self.in_use = set()
        self.lock = asyncio.Lock()
        self.waiting = asyncio.Queue()  # 等待队列
        # 初始化每个bot_id的使用频率统计
        self.usage_count = {bid: 0 for bid in bot_ids}
        # 允许的最大等待时间(秒)
        self.max_wait_time = 30

    async def get_bot_id(self):
        """获取一个可用的bot_id"""
        async with self.lock:
            available = [bid for bid in self.bot_ids if bid not in self.in_use]
            if available:
                # 选择使用次数最少的bot_id
                selected = min(available, key=lambda bid: self.usage_count[bid])
                self.in_use.add(selected)
                self.usage_count[selected] += 1
                return selected
                
        # 如果没有可用的bot_id，则等待
        transform_logger.warning("所有bot_id都在使用中，等待可用bot_id...")
        
        # 创建future并放入等待队列
        future = asyncio.Future()
        await self.waiting.put(future)
        
        # 等待被通知有可用bot_id或超时
        try:
            return await asyncio.wait_for(future, timeout=self.max_wait_time)
        except asyncio.TimeoutError:
            # 超时后尝试再次获取
            transform_logger.warning(f"等待bot_id超时({self.max_wait_time}秒)，尝试再次获取")
            async with self.lock:
                # 如果仍然没有可用的，则选择使用次数最少的bot_id
                selected = min(self.bot_ids, key=lambda bid: self.usage_count[bid])
                self.usage_count[selected] += 1
                return selected
                
    async def release_bot_id(self, bot_id):
        """释放一个bot_id"""
        async with self.lock:
            if bot_id in self.in_use:
                self.in_use.remove(bot_id)
                
                # 如果有等待的请求，通知其可以获取bot_id
                if not self.waiting.empty():
                    future = await self.waiting.get()
                    if not future.done():
                        future.set_result(bot_id)

# 默认使用抽象摘要(abstract)标签的bot_ids
bot_ids = get_bot_ids_by_tag("abstract")

# 创建不同标签的bot_id池的缓存
bot_id_pools = {}
# 初始化默认的"abstract"标签池
bot_id_pools["abstract"] = BotIdPool(bot_ids)

def get_bot_id_pool(bot_tag="abstract"):
    """
    获取指定标签的bot_id池，如果不存在则创建
    
    Args:
        bot_tag: A机器人标签
        
    Returns:
        BotIdPool实例
    """
    if bot_tag not in bot_id_pools:
        tag_bot_ids = get_bot_ids_by_tag(bot_tag)
        if not tag_bot_ids:
            transform_logger.warning(f"标签'{bot_tag}'没有配置有效的bot_id，使用默认标签'abstract'")
            return bot_id_pools["abstract"]
        bot_id_pools[bot_tag] = BotIdPool(tag_bot_ids)
    return bot_id_pools[bot_tag]

async def generate_abstract_async(file_path, max_length: int = 300, bot_tag: str = "abstract") -> Optional[str]:
    """
    异步为指定的Markdown文件生成摘要
    
    Args:
        file_path: Markdown文件路径 (pathlib.Path对象或字符串)
        max_length: 摘要的最大长度
        bot_tag: 机器人标签，默认为"abstract"（抽象摘要）
        
    Returns:
        生成的摘要文本，如果失败则返回None
    """
    # 确保file_path是Path对象
    if not isinstance(file_path, Path):
        file_path = Path(file_path)
    
    # 获取指定标签的bot_id池
    pool = get_bot_id_pool(bot_tag)
    
    # 从池中获取一个bot_id
    bot_id = await pool.get_bot_id()
    if not bot_id:
        transform_logger.error(f"无法获取可用的bot_id(标签:{bot_tag}): {file_path}")
        return None
    
    try:
        content = file_path.read_text(encoding='utf-8')
        coze_agent = CozeAgent()
        coze_agent.bot_id = bot_id  # 直接设置bot_id
        
        # 构造Context对象
        context = Context(ContextType.TEXT)
        context["session_id"] = "abstract_generation"
        
        # 在线程池中执行同步reply方法
        reply = await asyncio.to_thread(lambda: coze_agent.reply(content, context))
        
        if reply is None or reply.type != ReplyType.STREAM:
            transform_logger.error(f"生成摘要失败: {file_path}")
            return None
            
        # 从流式回复中获取完整内容
        full_reply = ""
        for chunk in reply.content:
            full_reply += chunk
            
        transform_logger.debug(f"生成摘要预览: {full_reply[:100]}")
        return full_reply
    except Exception as e:
        transform_logger.error(f"生成摘要时发生错误: {e}")
        return None
    finally:
        # 释放bot_id
        await pool.release_bot_id(bot_id)

def generate_abstract(file_path, max_length: int = 300, bot_tag: str = "abstract") -> Optional[str]:
    """
    生成文档摘要的同步包装函数
    
    Args:
        file_path: 文档路径
        max_length: 摘要最大长度
        bot_tag: 机器人标签
        
    Returns:
        生成的摘要文本，如果失败则返回None
    """
    if not isinstance(file_path, Path):
        file_path = Path(file_path)
        
    try:
        # 检查是否已有事件循环在运行
        loop = asyncio.get_running_loop()
        # 如果有，直接在当前循环中运行
        return asyncio.run_coroutine_threadsafe(
            generate_abstract_async(file_path, max_length, bot_tag),
            loop
        ).result()
    except RuntimeError:
        # 如果没有事件循环，创建一个新的
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(generate_abstract_async(file_path, max_length, bot_tag))
        finally:
            loop.close()

# 如果作为脚本直接运行
if __name__ == "__main__":
    file_path = Path("D:\\Code\\nkuwiki\\etl\\data\\raw\\wechat\\company\\202503\\专场招聘伯乐校招全国重点高校届毕业生春季巡回招聘会国防军工专场西北工业大学站第一场\\专场招聘伯乐校招全国重点高校届毕业生春季巡回招聘会国防军工专场西北工业大学站第一场.md")
    # 使用默认的"abstract"标签生成摘要
    abstract = generate_abstract(file_path)
    print("使用默认标签生成的摘要:", abstract)
    
    # 也可以指定其他标签，例如使用job标签
    # abstract2 = generate_abstract(file_path, bot_tag="job")
    # print("使用job标签生成的摘要:", abstract2)


