"""
Auto-replay chat agent abstract class
"""


from bridge.context import Context
from bridge.reply import Reply


class Agent:
    def reply(self, query, context: Context = None) -> Reply:
        """
        agent auto-reply content
        :param req: received message
        :return: reply content
        """
        raise NotImplementedError
