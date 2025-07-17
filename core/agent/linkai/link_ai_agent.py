# core.agent.linkai.link_ai_agent module
from core.agent import Agent
from core.bridge.reply import Reply

class LinkAiAgent(Agent):
    def __init__(self):
        super().__init__()
        
    def reply(self, query, context=None):
        return Reply(None, "Not implemented")
