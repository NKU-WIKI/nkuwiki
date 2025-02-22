"""
channel factory
"""
from core.utils.common import const
from app import App

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
        from core.agent.coze.coze_agent import CozeAgent
        return CozeAgent()
    else:
        App().logger.error(f"agent_type: {agent_type} not supported")
        raise RuntimeError
