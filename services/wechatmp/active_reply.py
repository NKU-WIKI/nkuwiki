# from wechatpy import parse_message
# from wechatpy.replies import create_reply, TextReply

# from core.bridge.context import *
# from core.bridge.reply import *
# from services.wechatmp.common import *
# from services.wechatmp.wechatmp_channel import WechatMPChannel
# from services.wechatmp.wechatmp_message import WeChatMPMessage
# from config import conf, subscribe_msg
# from infra.deploy.app import logger


# # This class is instantiated once per query
# class Query:
#     def process(self, params: dict, data: bytes) -> str:
#         # 验证服务器
#         if "echostr" in params:
#             return params["echostr"]
        
#         # 解析消息
#         msg = parse_message(data)
        
#         # 构造回复
#         reply = TextReply(content="FastAPI响应成功", message=msg)
#         return reply.render()

#     def GET(self):
#         return verify_server(web.input())

#     def POST(self):
#         # Make sure to return the instance that first created, @singleton will do that.
#         try:
#             args = web.input()
#             verify_server(args)
#             channel = WechatMPChannel()
#             message = web.data()
#             encrypt_func = lambda x: x
#             if args.get("encrypt_type") == "aes":
#                 logger.debug("[wechatmp] Receive encrypted post data:\n" + message.decode("utf-8"))
#                 if not channel.crypto:
#                     raise Exception("Crypto not initialized, Please set wechatmp_aes_key in config.json")
#                 message = channel.crypto.decrypt_message(message, args.msg_signature, args.timestamp, args.nonce)
#                 encrypt_func = lambda x: channel.crypto.encrypt_message(x, args.nonce, args.timestamp)
#             else:
#                 logger.debug("[wechatmp] Receive post data:\n" + message.decode("utf-8"))
#             msg = parse_message(message)
#             if msg.type in ["text", "voice", "image"]:
#                 wechatmp_msg = WeChatMPMessage(msg, client=channel.client)
#                 from_user = wechatmp_msg.from_user_id
#                 content = wechatmp_msg.content
#                 message_id = wechatmp_msg.msg_id

#                 logger.info(
#                     "[wechatmp] {}:{} Receive post query {} {}: {}".format(
#                         web.ctx.env.get("REMOTE_ADDR"),
#                         web.ctx.env.get("REMOTE_PORT"),
#                         from_user,
#                         message_id,
#                         content,
#                     )
#                 )
#                 if msg.type == "voice" and wechatmp_msg.ctype == ContextType.TEXT and conf().get("voice_reply_voice", False):
#                     context = channel._compose_context(wechatmp_msg.ctype, content, isgroup=False, desire_rtype=ReplyType.VOICE, msg=wechatmp_msg)
#                 else:
#                     context = channel._compose_context(wechatmp_msg.ctype, content, isgroup=False, msg=wechatmp_msg)
#                 if context:
#                     channel.produce(context)
#                 # The reply will be sent by channel.send() in another thread
#                 return "success"
#             elif msg.type == "event":
#                 logger.info("[wechatmp] Event {} from {}".format(msg.event, msg.source))
#                 if msg.event in ["subscribe", "subscribe_scan"]:
#                     reply_text = subscribe_msg()
#                     if reply_text:
#                         replyPost = create_reply(reply_text, msg)
#                         return encrypt_func(replyPost.render())
#                 else:
#                     return "success"
#             else:
#                 logger.info("暂且不处理")
#             return "success"
#         except Exception as exc:
#             logger.exception(exc)
#             return exc
