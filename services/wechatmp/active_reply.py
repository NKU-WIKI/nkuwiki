from core.bridge.context import *
from core.bridge.reply import *
from services.wechatmp.common import *
from services.wechatmp.wechatmp_channel import WechatMPChannel
from services.wechatmp.wechatmp_message import WeChatMPMessage
from wechatpy import parse_message
from wechatpy.replies import create_reply
from app import App
from config import Config


# This class is instantiated once per query
class Query:
    """微信公众平台主动消息处理类
    
    每个请求会独立实例化，处理单次微信服务器回调
    生命周期：请求处理完成后立即释放
    """
    
    async def process(self, params: dict, data: bytes) -> str:
        """处理微信服务器回调请求的核心方法
        
        Args:
            params: URL查询参数，包含 signature/timestamp/nonce 等验证参数
            data: 原始请求体数据（可能为加密消息）
            
        Returns:
            str: 返回给微信服务器的响应内容，可能是明文或加密格式
            
        Raises:
            隐式异常: 方法内部已捕获所有异常并记录日志
            
        处理流程:
        1. 验证服务器有效性
        2. 解密加密消息（AES模式）
        3. 解析消息类型并分发给对应处理器
        4. 生成符合微信要求的响应格式
        """
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
           
            # 文本/语音/图片消息处理
            if msg.type in ["text", "voice", "image"]:
                wechatmp_msg = WeChatMPMessage(msg, client=channel.client)
                context = channel._compose_context(
                    ctype=wechatmp_msg.ctype,
                    content=wechatmp_msg.content,
                    isgroup=False,
                    msg=wechatmp_msg
                )
                App().logger.info(f"[收到消息] 类型={msg.type}，内容={msg.content}，用户id={wechatmp_msg.other_user_id}，用户名={wechatmp_msg.other_user_nickname}")
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
