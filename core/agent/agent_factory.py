"""
channel factory
"""
from core.utils.common import const
from core.utils.common.log import logger

def create_agent(agent_type):
    """
    create a agent_type instance
    :param agent_type: agent type code
    :return: agent instance
    """
    if agent_type == const.COZE:
        from core.agent.coze.coze_agent import CozeBot
        return CozeBot()
    else :
        logger.error(f"agent_type: {agent_type} not supported")
        raise RuntimeError
