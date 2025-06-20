"""
Agent工厂模块，负责创建不同类型的智能体实例
"""
from core.utils.logger import register_logger

logger = register_logger("core.agent.factory")

from core.agent.agent import Agent

class AgentFactory:
    """智能体工厂类，负责创建和管理不同类型的智能体实例"""
    
    _instance_cache = {}  # 智能体实例缓存
    
    @classmethod
    def get_agent(cls, agent_type: str, **kwargs) -> Agent:
        """
        获取智能体实例，优先从缓存获取，没有则创建新实例
        
        Args:
            agent_type: 智能体类型，如coze、openai等
            **kwargs: 附加参数
            
        Returns:
            Agent: 智能体实例
        """
        if not agent_type:
            logger.warning("未指定智能体类型，使用默认智能体")
            agent_type = "coze"  # 默认使用coze
            
        agent_type = agent_type.lower()
        
        # 检查缓存
        if agent_type in cls._instance_cache:
            logger.debug(f"从缓存获取{agent_type}智能体")
            return cls._instance_cache[agent_type]
        
        # 创建新实例
        agent = create_agent(agent_type, **kwargs)
        
        # 缓存实例
        cls._instance_cache[agent_type] = agent
        
        return agent
    
    @classmethod
    def clear_cache(cls):
        """清空智能体实例缓存"""
        cls._instance_cache.clear()

def create_agent(agent_type: str = "coze", **kwargs) -> Agent:
    """
    创建智能体实例
    
    Args:
        agent_type: 智能体类型，如coze、openai等
        **kwargs: 附加参数
        
    Returns:
        Agent: 智能体实例
    """
    agent_type = agent_type.lower()
   
    try:
        if agent_type == "coze":
            from core.agent.coze.coze_agent import CozeAgent
            # 如果提供了bot_id，则优先使用bot_id初始化
            if "bot_id" in kwargs:
                return CozeAgent(bot_id=kwargs["bot_id"])
            # 否则，使用tag
            tag = kwargs.get("tag", "default")
            return CozeAgent(tag=tag)
        elif agent_type == "chatgpt":
            from core.agent.chatgpt.chat_gpt_agent import ChatGPTAgent
            return ChatGPTAgent()
        elif agent_type == "dify":
            from core.agent.dify.dify_agent import DifyAgent
            return DifyAgent()
        elif agent_type == "openai":
            from core.agent.openai.open_ai_agent import OpenAIAgent
            return OpenAIAgent()
        elif agent_type == "claude":
            from core.agent.claudeapi.claude_api_agent import ClaudeAPIAgent
            return ClaudeAPIAgent()
        elif agent_type == "baidu":
            from core.agent.baidu.baidu_wenxin import BaiduWenxin
            return BaiduWenxin()
        elif agent_type == "gemini":
            from core.agent.gemini.google_gemini_agent import GoogleGeminiAgent
            return GoogleGeminiAgent()
        elif agent_type == "dashscope":
            from core.agent.dashscope.dashscope_agent import DashscopeAgent
            return DashscopeAgent()
        elif agent_type == "zhipuai":
            from core.agent.zhipuai.zhipuai_agent import ZhipuAIAgent
            return ZhipuAIAgent()
        elif agent_type == "tongyi":
            from core.agent.ali.ali_qwen_agent import AliQwenAgent
            return AliQwenAgent()
        elif agent_type == "minimax":
            from core.agent.minimax.minimax_agent import MinimaxAgent
            return MinimaxAgent()
        elif agent_type == "moonshot":
            from core.agent.moonshot.moonshot_agent import MoonshotAgent
            return MoonshotAgent()
        elif agent_type == "deepseek":
            from core.agent.deepseek.deepseek_agent import DeepseekAgent
            return DeepseekAgent()
        elif agent_type == "hiagent":
            from core.agent.hiagent.hiagent_agent import HiAgentAgent
            return HiAgentAgent()
        elif agent_type == "xunfei":
            from core.agent.xunfei.xunfei_spark_agent import XunfeiSparkAgent
            return XunfeiSparkAgent()
        else:
            raise ValueError(f"不支持的智能体类型: {agent_type}")
    except Exception as e:
        logger.exception(e)
        return Agent()

# 导出工厂方法为模块级函数
get_agent = AgentFactory.get_agent