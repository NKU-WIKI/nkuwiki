import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from etl.transform import *
bot_id = config.get("core.agent.coze.job_bot_id", "")
from core.agent.coze.coze_agent_new import CozeAgentNew

def generate_abstract(file_path, max_length: int = 300) -> Optional[str]:
    """
    为指定的Markdown文件生成摘要
    
    Args:
        file_path: Markdown文件路径 (pathlib.Path对象或字符串)
        max_length: 摘要的最大长度
        
    Returns:
        生成的摘要文本，如果失败则返回None
    """     
    # 确保file_path是Path对象
    content = file_path.read_text(encoding='utf-8')
    coze_agent = CozeAgentNew(bot_id)
    reply = coze_agent.reply(content)
    if(reply is None):
        transform_logger.error(f"生成摘要失败: {file_path}")
        return None
    transform_logger.debug(f"生成摘要预览: {reply[:100]}")
    return reply

# 如果作为脚本直接运行
if __name__ == "__main__":
    file_path = Path("D:\\Code\\nkuwiki\\etl\\data\\raw\\wechat\\company\\202503\\专场招聘伯乐校招全国重点高校届毕业生春季巡回招聘会国防军工专场西北工业大学站第一场\\专场招聘伯乐校招全国重点高校届毕业生春季巡回招聘会国防军工专场西北工业大学站第一场.md")
    abstract = generate_abstract(file_path)
    print(abstract)


