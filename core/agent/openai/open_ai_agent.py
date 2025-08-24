# core.agent.openai.open_ai_agent module
from core.agent import Agent
from core.bridge.reply import Reply

class OpenAiAgent(Agent):
    def __init__(self):
        super().__init__()
        
    def reply(self, query, context=None):
        return Reply(None, "Not implemented")
