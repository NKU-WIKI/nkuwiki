"""
agent factory
"""
import os
import sys
from loguru import logger

# 添加项目根目录到 sys.path
current_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if current_dir not in sys.path:
    sys.path.append(current_dir)

from core.utils.common import const


def create_agent(agent_type):
    """
    创建指定类型的智能体实例
    :param agent_type: 智能体类型代码
    :return: 智能体实例
    """
    try:
        if agent_type == const.HIAGENT:
            from core.agent.hiagent.hiagent_agent import HiagentAgent
            return HiagentAgent()
        elif agent_type == const.COZE:
            from core.agent.coze.coze_agent import CozeAgent
            return CozeAgent()
        elif agent_type == const.BAIDU:
            from core.agent.baidu.baidu_wenxin import BaiduWenxinAgent
            return BaiduWenxinAgent()
        elif agent_type == const.CHATGPT:
            from core.agent.chatgpt.chat_gpt_agent import ChatGPTAgent
            return ChatGPTAgent()
        elif agent_type == const.OPEN_AI:
            from core.agent.openai.open_ai_agent import OpenAIAgent
            return OpenAIAgent()
        elif agent_type == const.CHATGPTONAZURE:
            from core.agent.chatgpt.chat_gpt_agent import AzureChatGPTAgent
            return AzureChatGPTAgent()
        elif agent_type == const.LINKAI:
            from core.agent.linkai.link_ai_agent import LinkAIAgent
            return LinkAIAgent()
        elif agent_type == const.XUNFEI:
            from core.agent.xunfei.xunfei_spark_agent import XunFeiAgent
            return XunFeiAgent()
        elif agent_type == const.CLAUDEAPI:
            from core.agent.claudeapi.claude_api_agent import ClaudeAPIAgent
            return ClaudeAPIAgent()
        elif agent_type == const.GEMINI:
            from core.agent.gemini.google_gemini_agent import GoogleGeminiAgent
            return GoogleGeminiAgent()
        elif agent_type == const.DEEPSEEK:
            from core.agent.deepseek.deepseek_agent import DeepSeekAgent
            return DeepSeekAgent()
        elif agent_type == const.BYTEDANCE_COZE:
            from core.agent.bytedance.bytedance_coze_agent import ByteDanceCozeAgent
            return ByteDanceCozeAgent()
        elif agent_type == const.QWEN:
            from core.agent.ali.ali_qwen_agent import AliQwenAgent
            return AliQwenAgent()
        elif agent_type == const.QWEN_DASHSCOPE:
            from core.agent.dashscope.dashscope_agent import DashscopeAgent
            return DashscopeAgent()
        elif agent_type == const.ZHIPU_AI:
            from core.agent.zhipuai.zhipuai_agent import ZHIPUAIAgent
            return ZHIPUAIAgent()
        elif agent_type == const.MOONSHOT:
            from core.agent.moonshot.moonshot_agent import MoonshotAgent
            return MoonshotAgent()
        elif agent_type == const.MiniMax:
            from core.agent.minimax.minimax_agent import MinimaxAgent
            return MinimaxAgent()
        elif agent_type == const.DIFY:
            from core.agent.dify.dify_agent import DifyAgent
            return DifyAgent()
        else:
            logger.error(f"不支持的智能体类型: {agent_type}")
            raise ValueError(f"不支持的智能体类型: {agent_type}")
    except ImportError as e:
        logger.error(f"导入智能体模块失败: {e}")
        raise ImportError(f"导入智能体模块失败，请确保安装了相应的依赖: {e}")
    except Exception as e:
        logger.error(f"创建智能体实例失败: {e}")
        raise RuntimeError(f"创建智能体实例失败: {e}")
