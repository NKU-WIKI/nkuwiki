"""
Message sending channel abstract class
"""

from core.bridge.bridge import Bridge
from core.bridge.context import Context
from core.bridge.reply import *


class Channel(object):
    """消息通道基类
    
    Attributes:
        channel_type: 通道类型字符串标识
        NOT_SUPPORT_REPLYTYPE: 本通道不支持的回复类型列表
    """
    channel_type = ""
    NOT_SUPPORT_REPLYTYPE = [ReplyType.VOICE, ReplyType.IMAGE]

    def startup(self):
        """初始化通道，子类必须实现"""
        raise NotImplementedError

    def handle_text(self, msg: str):
        """处理接收到的文本消息
        Args:
            msg: 接收到的消息内容
        """
        raise NotImplementedError

    # 统一的发送函数，每个Channel自行实现，根据reply的type字段发送不同类型的消息
    def send(self, reply: Reply, context: Context) -> None:
        """发送消息给用户
        Args:
            reply: 回复对象，包含回复内容和类型
            context: 对话上下文信息
        """
        raise NotImplementedError

    def build_reply_content(self, query: str, context: Context = None) -> Reply:
        """构建文本回复内容
        Returns:
            Reply: 包含文本回复的应答对象
        """
        return Bridge().fetch_reply_content(query, context)

    def build_voice_to_text(self, voice_file: str) -> Reply:
        """语音转文字
        Args:
            voice_file: 语音文件路径
        Returns:
            Reply: 包含文字转写结果的应答对象
        """
        return Bridge().fetch_voice_to_text(voice_file)

    def build_text_to_voice(self, text: str) -> Reply:
        """文字转语音
        Returns:
            Reply: 包含语音文件的应答对象
        """
        return Bridge().fetch_text_to_voice(text)
