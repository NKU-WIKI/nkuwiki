import sys
from pathlib import Path
import asyncio
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from etl.transform import *
from core.agent.coze.coze_agent_new import CozeAgentNew

# 获取所有可用的bot_id
bot_ids = [
    config.get("core.agent.coze.ab_bot_id", ""),
    config.get("core.agent.coze.ab_bot_id_1", ""),
    config.get("core.agent.coze.ab_bot_id_2", ""),
    config.get("core.agent.coze.ab_bot_id_3", ""),
    config.get("core.agent.coze.ab_bot_id_4", ""),
    config.get("core.agent.coze.ab_bot_id_5", ""),
    config.get("core.agent.coze.ab_bot_id_6", ""),
    config.get("core.agent.coze.ab_bot_id_7", ""),
    config.get("core.agent.coze.ab_bot_id_8", ""),
    config.get("core.agent.coze.ab_bot_id_9", ""),
]

# 过滤掉空的bot_id
bot_ids = [bid for bid in bot_ids if bid]
transform_logger.info(f"加载了 {len(bot_ids)} 个有效的bot_id")

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
        self.max_wait_time = 10

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

# 创建全局bot_id池
bot_id_pool = BotIdPool(bot_ids)

async def generate_abstract_async(file_path, max_length: int = 300) -> Optional[str]:
    """
    异步为指定的Markdown文件生成摘要
    
    Args:
        file_path: Markdown文件路径 (pathlib.Path对象或字符串)
        max_length: 摘要的最大长度
        
    Returns:
        生成的摘要文本，如果失败则返回None
    """
    # 确保file_path是Path对象
    if not isinstance(file_path, Path):
        file_path = Path(file_path)
    
    # 从池中获取一个bot_id
    bot_id = await bot_id_pool.get_bot_id()
    if not bot_id:
        transform_logger.error(f"无法获取可用的bot_id: {file_path}")
        return None
    
    try:
        content = file_path.read_text(encoding='utf-8')
        coze_agent = CozeAgentNew(bot_id)
        
        # 在线程池中执行同步reply方法
        reply = await asyncio.to_thread(coze_agent.reply, content)
        
        if(reply is None):
            transform_logger.error(f"生成摘要失败: {file_path}")
            return None
        transform_logger.debug(f"生成摘要预览: {reply[:100]}")
        return reply
    except Exception as e:
        transform_logger.error(f"生成摘要时发生错误: {e}")
        return None
    finally:
        # 释放bot_id
        await bot_id_pool.release_bot_id(bot_id)

def generate_abstract(file_path, max_length: int = 300) -> Optional[str]:
    """
    为了兼容性保留的同步版本，内部使用异步版本实现
    """
    if not isinstance(file_path, Path):
        file_path = Path(file_path)
        
    # 创建事件循环并运行异步函数
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(generate_abstract_async(file_path, max_length))
    finally:
        loop.close()

# 如果作为脚本直接运行
if __name__ == "__main__":
    file_path = Path("D:\\Code\\nkuwiki\\etl\\data\\raw\\wechat\\company\\202503\\专场招聘伯乐校招全国重点高校届毕业生春季巡回招聘会国防军工专场西北工业大学站第一场\\专场招聘伯乐校招全国重点高校届毕业生春季巡回招聘会国防军工专场西北工业大学站第一场.md")
    abstract = generate_abstract(file_path)
    print(abstract)


