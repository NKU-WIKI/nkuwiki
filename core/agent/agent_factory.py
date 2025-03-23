"""
Agent工厂模块，负责创建不同类型的智能体实例
"""

import importlib
import sys
from core.utils.logger import register_logger

logger = register_logger("core.agent.factory")

from core.agent.agent import Agent
from config import Config

def create_agent(agent_type: str, **kwargs) -> Agent:
    """
    创建智能体实例
    
    Args:
        agent_type: 智能体类型，如coze、openai等
        **kwargs: 附加参数
        
    Returns:
        Agent: 智能体实例
    """
    agent_type = agent_type.lower()
    config = Config()
    
    # 尝试动态导入对应的Agent类
    try:
        if agent_type == "chatgpt":
            from core.agent.chatgpt.chatgpt_session import ChatGPTSession
            return ChatGPTSession()
        elif agent_type == "dify":
            from core.agent.dify.dify_agent import DifyAgent
            return DifyAgent()
        elif agent_type == "openai":
            from core.agent.openai.openai_session import OpenAISession
            return OpenAISession()
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
        elif agent_type == "coze":
            from core.agent.coze.coze_agent import CozeAgent
            # 直接返回CozeAgent实例，CozeAgent自己会从config获取必要参数
            return CozeAgent()
            
        logger.error(f"未知的智能体类型: {agent_type}")
        return Agent()  # 返回基础Agent作为默认值
        
    except ImportError as e:
        logger.error(f"无法导入{agent_type}模块: {e}")
        return Agent()
    except Exception as e:
        logger.error(f"创建{agent_type}智能体时发生错误: {e}")
        return Agent()
