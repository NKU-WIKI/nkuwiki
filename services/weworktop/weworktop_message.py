"""
企业微信自建应用消息类
"""
from typing import Optional
from services.chat_message import ChatMessage

class WeWorkTopMessage(ChatMessage):
    """企业微信自建应用消息类"""
    
    def __init__(self, content: str, content_type: Optional[str] = None):
        """
        初始化消息
        
        参数:
        - content: 消息内容
        - content_type: 内容类型 (text/image/voice)
        """
        super().__init__(content)
        
        # 基本属性
        self.msg_id: str = ""  # 消息ID
        self.msg_type: str = "text"  # 消息类型 (text/image/voice)
        self.content: str = content  # 消息内容
        self.create_time: int = 0  # 消息创建时间戳
        
        # 发送方信息
        self.from_user_id: str = ""  # 发送者ID
        self.from_user_nickname: str = ""  # 发送者昵称
        
        # 接收方信息
        self.to_user_id: str = ""  # 接收者ID
        
        # 环境信息
        self.room_id: str = ""  # 群聊ID
        self.is_group: bool = False  # 是否为群聊消息
        
        # 媒体信息
        self.media_id: str = ""  # 媒体ID (图片/语音等)
        self.format: str = ""  # 媒体格式
        self.voice_duration: int = 0  # 语音时长(秒)
        
        # 标记信息
        self.is_at_me: bool = False  # 是否@机器人
        
        # 其他
        self.extras = {}  # 额外信息，可用于存储任意数据
    
    def build_reply_message(self, reply_content: str) -> 'WeWorkTopMessage':
        """
        构建回复消息
        
        参数:
        - reply_content: 回复内容
        
        返回:
        - WeWorkTopMessage: 回复消息对象
        """
        reply = WeWorkTopMessage(reply_content)
        reply.msg_type = "text"
        reply.from_user_id = "bot"  # 使用固定的机器人ID
        reply.to_user_id = self.from_user_id
        reply.room_id = self.room_id
        reply.is_group = self.is_group
        reply.extras = self.extras.copy()  # 复制额外信息
        
        return reply
    
    def to_dict(self) -> dict:
        """
        将消息转换为字典
        
        返回:
        - dict: 包含消息所有属性的字典
        """
        return {
            "msg_id": self.msg_id,
            "msg_type": self.msg_type,
            "content": self.content,
            "create_time": self.create_time,
            "from_user_id": self.from_user_id,
            "from_user_nickname": self.from_user_nickname,
            "to_user_id": self.to_user_id,
            "room_id": self.room_id,
            "is_group": self.is_group,
            "media_id": self.media_id,
            "format": self.format,
            "voice_duration": self.voice_duration,
            "is_at_me": self.is_at_me,
            "extras": self.extras
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'WeWorkTopMessage':
        """
        从字典创建消息对象
        
        参数:
        - data: 包含消息属性的字典
        
        返回:
        - WeWorkTopMessage: 消息对象
        """
        msg = cls(data.get("content", ""))
        msg.msg_id = data.get("msg_id", "")
        msg.msg_type = data.get("msg_type", "text")
        msg.create_time = data.get("create_time", 0)
        msg.from_user_id = data.get("from_user_id", "")
        msg.from_user_nickname = data.get("from_user_nickname", "")
        msg.to_user_id = data.get("to_user_id", "")
        msg.room_id = data.get("room_id", "")
        msg.is_group = data.get("is_group", False)
        msg.media_id = data.get("media_id", "")
        msg.format = data.get("format", "")
        msg.voice_duration = data.get("voice_duration", 0)
        msg.is_at_me = data.get("is_at_me", False)
        msg.extras = data.get("extras", {})
        
        return msg 