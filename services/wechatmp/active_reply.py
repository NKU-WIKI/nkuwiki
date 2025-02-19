import asyncio
import time
from wechatpy import parse_message
from core.bridge.context import *
from core.bridge.reply import *
from services.wechatmp.common import *
from services.wechatmp.wechatmp_channel import WechatMPChannel
from services.wechatmp.wechatmp_message import WeChatMPMessage
from wechatpy.replies import TextReply, ImageReply, VoiceReply, create_reply
from app import App
from config import Config


# This class is instantiated once per query
class Query:
    async def process(self, params: dict, data: bytes) -> str:
        try:
            # 处理微信服务器验证（GET请求）
            if "echostr" in params:
                # App().logger.debug(f"[验证] 收到服务器验证请求 echostr={params['echostr']}")
                return params["echostr"]
            
            # 校验基本参数（FastAPI已通过依赖注入验证）
            required_params = ["signature", "timestamp", "nonce"]
            if any(p not in params for p in required_params):
                App().logger.error(f"[参数错误] 缺少必要参数 {required_params}")
                return "invalid request"
            
            channel = WechatMPChannel()
            encrypt_func = lambda x: x
            
            # 处理加密消息（AES模式）
            if params.get("encrypt_type") == "aes":
                # App().logger.debug(f"[解密] 加密数据长度={len(data)}字节")
                
                if not channel.crypto:
                    App().logger.error("[配置错误] 未找到AES密钥，请检查wechatmp_aes_key配置")
                    return "service error"
                
                try:
                    # 使用微信官方参数名进行解密
                    message = channel.crypto.decrypt_message(
                        data,
                        params["signature"],  # 修正参数名
                        params["timestamp"],
                        params["nonce"]
                    )
                    # App().logger.debug(f"[解密成功] 原始消息：{message.decode('utf-8')}")
                except Exception as e:
                    App().logger.exception("[解密失败] 可能原因：签名不匹配/消息被篡改")
                    return "decrypt error"
                
                # 设置加密响应函数
                encrypt_func = lambda x: channel.crypto.encrypt_message(
                    x, 
                    params["nonce"],
                    params["timestamp"]
                )
            else:
                message = data
                # App().logger.debug(f"[明文消息] 原始数据：{message.decode('utf-8')}")
            
            # 解析微信消息
            msg = parse_message(message)
            # App().logger.info(f"[消息处理] 类型={msg.type} 用户={msg.source}")
            
            # 文本/语音/图片消息处理
            if msg.type in ["text", "voice", "image"]:
                wechatmp_msg = WeChatMPMessage(msg, client=channel.client)
                context = channel._compose_context(
                    ctype=wechatmp_msg.ctype,
                    content=wechatmp_msg.content,
                    isgroup=False,
                    msg=wechatmp_msg
                )
                
                # 语音消息特殊处理
                if wechatmp_msg.ctype == ContextType.VOICE and Config().get("voice_reply_voice"):
                    context["desire_rtype"] = ReplyType.VOICE
                
                if context:
                    channel.produce(context)
                return "success"
            
            # 事件处理（关注/扫码）
            if msg.type == "event":
                App().logger.info(f"[事件处理] 类型={msg.event} 参数={getattr(msg, 'event_key', '')}")
                if msg.event in ["subscribe", "subscribe_scan"]:
                    if reply_text := Config().get("subscribe_msg"):
                        reply = create_reply(reply_text, msg)
                        return encrypt_func(reply.render())
                return "success"
            
            App().logger.warning(f"[未处理消息] 类型={msg.type}")
            return "success"
            
        except Exception as e:
            App().logger.exception(f"[处理异常] {str(e)}")
            return "server error"
