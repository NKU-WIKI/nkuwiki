from core.utils.common.log import logger
from core.agent.session_manager import Session
from config import conf

class CozeSession(Session):
    def __init__(self, session_id, system_prompt=None, model="coze-pro"):
        super().__init__(session_id, system_prompt)
        self.model = model
        self.conversation_id = None  # Coze会话ID
        self.max_history = 5  # 控制历史记录长度
        self.response_buffer = ""  # 新增响应缓冲
        self.reset()

    def reset(self):
        super().reset()
        self.conversation_id = None
        # Coze需要的系统提示格式
        self.messages = [{
            "role": "system",
            "content": self.system_prompt,
            "variables": {}  # 根据API文档添加变量输入
        }]

    def add_query(self, query):
        self.messages.append({
            "role": "user",
            "content": query,
            "user_id": conf().get("coze_user_id")  # 添加用户ID
        })
        # 保持历史记录长度
        if len(self.messages) > self.max_history * 2 + 1:
            self.messages = [self.messages[0]] + self.messages[-(self.max_history*2):]

    def add_response(self, complete_part: str):
        # 直接操作messages列表
        self.messages.append({
            "role": "assistant",
            "content": complete_part
        })

    def get_last_query(self):
        """获取最后一条用户消息内容"""
        try:
            # 倒序遍历消息历史，找到最后一条用户消息
            for msg in reversed(self.messages):
                if msg["role"] == "user":
                    return msg["content"]
            return ""  # 如果没有找到用户消息，返回空字符串
        except Exception as e:
            logger.error(f"[COZE] 获取最后查询失败: {str(e)}")
            return ""

    def discard_exceeding(self, max_tokens, cur_tokens=None):
        """优化token计算和消息裁剪"""
        try:
            # 直接实现token计算逻辑
            def num_tokens_from_messages(messages, model):
                """移植自chat_gpt_session.py的token计算逻辑"""
                try:
                    import tiktoken
                except ImportError:
                    logger.error("请先安装tiktoken: pip install tiktoken")
                    raise
                
                try:
                    encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
                except KeyError:
                    encoding = tiktoken.get_encoding("cl100k_base")

                tokens_per_message = 4  # 每条消息的基础token
                tokens_per_name = -1     # 名称字段的token调整

                num_tokens = 0
                for message in messages:
                    num_tokens += tokens_per_message
                    for key, value in message.items():
                        num_tokens += len(encoding.encode(value))
                        if key == "name":
                            num_tokens += tokens_per_name
                num_tokens += 3  # 回复的初始token
                return num_tokens

            # 转换消息格式
            gpt_messages = [{
                "role": msg["role"],
                "content": msg["content"]
            } for msg in self.messages]
            
            total_tokens = num_tokens_from_messages(gpt_messages, self.model)
            
            # 裁剪策略
            while total_tokens > max_tokens and len(self.messages) > 3:
                removed = self.messages.pop(1)
                gpt_messages.pop(1)
                total_tokens = num_tokens_from_messages(gpt_messages, self.model)
                
            return total_tokens
            
        except Exception as e:
            logger.warning(f"Token计算异常: {str(e)}，使用字符长度估算")
            # 回退到简单字符数估算 (1 token ≈ 4个英文字符)
            total_chars = sum(len(msg["content"]) for msg in self.messages)
            estimated_tokens = total_chars // 4
            
            while estimated_tokens > max_tokens and len(self.messages) > 3:
                removed = self.messages.pop(1)
                total_chars -= len(removed["content"])
                estimated_tokens = total_chars // 4
                
            return estimated_tokens