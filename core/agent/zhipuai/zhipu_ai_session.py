"""
智谱AI 会话管理
"""
import time
from loguru import logger
from config import Config
from core.agent.session_manager import Session, SessionManager


class ZhipuAISession(Session):
    def __init__(self, session_id, system_prompt=None):
        super().__init__(session_id, system_prompt)
        self.config = Config()
        self.max_tokens = self.config.get("core.agent.zhipu.max_tokens", 1500)
        self.reset()

    def reset(self):
        system_content = self.system_prompt
        self.messages = []
        if system_content:
            system_item = {"role": "system", "content": system_content}
            self.messages.append(system_item)
    
    def discard_exceeding(self, max_tokens=None, cur_tokens=None):
        if max_tokens is None:
            max_tokens = self.max_tokens
        if max_tokens <= 0:
            return 0

        # 根据约束，计算要保留的消息数量
        num_of_tokens = 0
        for idx, message in enumerate(self.messages[::-1]):
            content = message.get("content", "")
            num_of_tokens += len(content) * 4  # 简单字数估算
            if num_of_tokens > max_tokens and idx > 0:
                self.messages = self.messages[-(idx):]
                break
        return num_of_tokens

    def calc_tokens(self):
        num_of_tokens = 0
        for message in self.messages:
            content = message.get("content", "")
            num_of_tokens += len(content) * 4  # 简单字数估算
        return num_of_tokens


class ZhipuAISessionManager(SessionManager):
    def __init__(self):
        super().__init__(ZhipuAISession) 