# encoding:utf-8

from enum import Enum
from typing import Optional, Union, List, Tuple, Any


class ReplyType(Enum):
    TEXT = 1  # 文本
    VOICE = 2  # 音频文件
    IMAGE = 3  # 图片文件
    IMAGE_URL = 4  # 图片URL
    VIDEO_URL = 5  # 视频URL
    FILE = 6  # 文件
    CARD = 7  # 微信名片，仅支持ntchat
    INVITE_ROOM = 8  # 邀请好友进群
    INFO = 9  # 信息
    ERROR = 10  # 错误
    TEXT_ = 11  # 强制文本
    VIDEO = 12  # 视频文件
    MINIAPP = 13  # 小程序
    STREAM = 14  # 流式输出

    def __str__(self):
        return self.name


class Reply:
    """
    回复类，用于封装不同类型的回复内容
    支持文本、语音、图片、文件等多种类型
    支持流式输出（content为列表或生成器）
    """
    
    def __init__(self, type: ReplyType = None, content: Any = None):
        """
        初始化回复对象
        
        Args:
            type: 回复类型，必须是 ReplyType 枚举中的值
            content: 回复内容，可以是字符串、字节数据、文件对象或者流式内容(列表/元组/生成器)
        """
        self.type = type
        self.content = content
        
    def is_stream(self) -> bool:
        """
        检查内容是否为流式输出
        
        Returns:
            如果内容是列表、元组或生成器则返回True，否则返回False
        """
        return (self.type == ReplyType.STREAM or 
                isinstance(self.content, (list, tuple)) or 
                hasattr(self.content, '__iter__') and hasattr(self.content, '__next__'))

    def __str__(self):
        if self.is_stream():
            return "Reply(type={}, content=<stream>)".format(self.type)
        return "Reply(type={}, content={})".format(self.type, self.content)
