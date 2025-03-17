"""
channel factory
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
    create a agent_type instance
    :param agent_type: agent type code
    :return: agent instance
    """
    if agent_type == const.HIAGENT:
        from core.agent.hiagent.hiagent_agent import HiagentAgent
        return HiagentAgent()
    elif agent_type == const.COZE:
        from core.agent.coze.coze_agent_sdk import CozeAgent
        return CozeAgent()
    else:
        logger.error(f"agent_type: {agent_type} not supported")
        raise RuntimeError
