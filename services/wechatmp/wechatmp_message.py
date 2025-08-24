"""微信公众平台消息处理模块，将微信消息转换为统一消息格式"""

from core.bridge.context import ContextType
from services.chat_message import ChatMessage
from core.utils.common.tmp_dir import TmpDir
from app import App

class WeChatMPMessage(ChatMessage):
    """微信公众平台消息处理类
    
    Attributes:
        ctype: 上下文类型，继承自ChatMessage
        content: 消息内容，文本消息直接存储，媒体消息存储临时文件路径
        _prepare_fn: 媒体文件下载函数（延迟执行）
    """

    def __init__(self, msg, client=None):
        """初始化微信消息转换
        
        Args:
            msg: 原始微信消息对象
            client: 微信API客户端，用于媒体文件下载
            
        Raises:
            NotImplementedError: 遇到不支持的消息类型时抛出
        """
        super().__init__(msg)
        self.msg_id = msg.id
        self.create_time = msg.time
        self.is_group = False

        # 文本消息处理
        if msg.type == "text":
            self.ctype = ContextType.TEXT
            self.content = msg.content
            
        # 语音消息处理（含语音识别）
        elif msg.type == "voice":
            if msg.recognition is None:
                self.ctype = ContextType.VOICE
                self.content = TmpDir().path() + msg.media_id + "." + msg.format

                def download_voice():
                    """下载语音文件到临时目录"""
                    response = client.media.download(msg.media_id)
                    if response.status_code == 200:
                        with open(self.content, "wb") as f:
                            f.write(response.content)
                    else:
                        App().logger.error(f"[wechatmp] Failed to download voice file, {response.content}")

                self._prepare_fn = download_voice
            else:
                self.ctype = ContextType.TEXT
                self.content = msg.recognition
                
        # 图片消息处理        
        elif msg.type == "image":
            self.ctype = ContextType.IMAGE
            self.content = TmpDir().path() + msg.media_id + ".png"

            def download_image():
                """下载图片文件到临时目录"""
                response = client.media.download(msg.media_id)
                if response.status_code == 200:
                    with open(self.content, "wb") as f:
                        f.write(response.content)
                else:
                    App().logger.error(f"[wechatmp] Failed to download image file, {response.content}")

            self._prepare_fn = download_image
            
        else:
            raise NotImplementedError("Unsupported message type: Type:{} ".format(msg.type))

        self.from_user_id = msg.source
        self.to_user_id = msg.target
        self.other_user_id = msg.source
