import asyncio
import time

import textwrap
from wechatpy import parse_message
from wechatpy.replies import ImageReply, VoiceReply, create_reply
from core.bridge.context import *
from core.bridge.reply import *
from core.utils.common.string_utils import split_string_by_utf8_length

from services.wechatmp.common import *
from services.wechatmp.wechatmp_channel import WechatMPChannel
from services.wechatmp.wechatmp_message import WeChatMPMessage

from app import App
from config import Config


# This class is instantiated once per query
class Query:
    async def process(self, params: dict, data: bytes) -> str:
        try:
            verify_server(params)
            channel = WechatMPChannel()
            encrypt_func = lambda x: x
            if params.get("encrypt_type") == "aes":
                App().logger.debug(f"[解密前] 加密数据长度: {len(data)}")
                if not channel.crypto:
                    App().logger.error("未初始化加密模块，请检查wechatmp_aes_key配置")
                    return "service error"
                
                try:
                    message = channel.crypto.decrypt_message(
                        data,
                        params["msg_signature"],
                        params["timestamp"],
                        params["nonce"]
                    )
                    App().logger.debug(f"[解密后] 消息内容: {message.decode()}")
                except Exception as e:
                    App().logger.exception(f"解密失败")
                    return "decrypt error"
                
                encrypt_func = lambda x: channel.crypto.encrypt_message(
                    x, 
                    params["nonce"],
                    params["timestamp"]
                )
            else:
                # App.logger.debug("[明文消息]")
                message = data
            
            msg = parse_message(message)
            # App().logger.debug(f"消息类型: {msg.type}, 用户: {msg.source}")
            if msg.type in ["text", "voice", "image"]:
                wechatmp_msg = WeChatMPMessage(msg, client=channel.client)
                from_user = wechatmp_msg.from_user_id
                content = wechatmp_msg.content
                message_id = wechatmp_msg.msg_id

                supported = True
                if "【收到不支持的消息类型，暂无法显示】" in content:
                    supported = False  # not supported, used to refresh

                # New request
                if (
                    channel.cache_dict.get(from_user) is None
                    and from_user not in channel.running
                    or content and content.startswith(Config().get("plugin_trigger_prefix", "&"))
                    and message_id not in channel.request_cnt  # insert the godcmd
                ):
                    # The first query begin
                    if msg.type == "voice" and wechatmp_msg.ctype == ContextType.TEXT and Config().get("voice_reply_voice", False):
                        context = channel._compose_context(wechatmp_msg.ctype, content, isgroup=False, desire_rtype=ReplyType.VOICE, msg=wechatmp_msg)
                    else:
                        context = channel._compose_context(wechatmp_msg.ctype, content, isgroup=False, msg=wechatmp_msg)
                    # App().logger.debug(f"wechatmp_msg：{wechatmp_msg}")

                    if supported and context:
                        channel.running.add(from_user)
                        channel.produce(context)
                    else:
                        trigger_prefix = Config().get("single_chat_prefix", [""])[0]
                        if trigger_prefix or not supported:
                            if trigger_prefix:
                                reply_text = textwrap.dedent(
                                    f"""\
                                    请输入'{trigger_prefix}'接你想说的话跟我说话。
                                    例如:
                                    {trigger_prefix}你好，很高兴见到你。"""
                                )
                            else:
                                reply_text = textwrap.dedent(
                                    """\
                                    你好，很高兴见到你。
                                    请跟我说话吧。"""
                                )
                        else:
                            App().logger.error(f"[wechatmp] unknown error")
                            reply_text = textwrap.dedent(
                                """\
                                未知错误，请稍后再试"""
                            )

                        replyPost = create_reply(reply_text, msg)
                        return encrypt_func(replyPost.render())

                # Wechat official server will request 3 times (5 seconds each), with the same message_id.
                # Because the interval is 5 seconds, here assumed that do not have multithreading problems.
                request_cnt = channel.request_cnt.get(message_id, 0) + 1
                channel.request_cnt[message_id] = request_cnt
                # App().logger.debug(
                #     "[wechatmp] Request {} from {} {} {}:{}\ncontent:{}".format(
                #         request_cnt, from_user, message_id, params.get("REMOTE_ADDR"), params.get("REMOTE_PORT"), content
                #     )
                # )

                task_running = True
                waiting_until = time.time() + 3.5
                while time.time() < waiting_until:
                    if from_user in channel.running:
                        time.sleep(0.1)
                    else:
                        task_running = False
                        break

                reply_text = ""
                App().logger.debug(f"task_running: {task_running}")
                App().logger.debug(f"request_cnt: {request_cnt}")
                if task_running:
                    if request_cnt < 3:
                        # waiting for timeout (the POST request will be closed by Wechat official server)
                        time.sleep(2)
                        # and do nothing, waiting for the next request
                        return "success"
                    else:  # request_cnt == 3:
                        # return timeout message
                        App().logger.debug(f"time out")
                        reply_text = "【正在思考中，回复任意文字尝试获取回复】"
                        replyPost = create_reply(reply_text, msg)
                        return encrypt_func(replyPost.render())

                # reply is ready
                channel.request_cnt.pop(message_id)

                # no return because of bandwords or other reasons
                if from_user not in channel.cache_dict and from_user not in channel.running:
                    return "success"

                # Only one request can access to the cached data
                try:
                    (reply_type, reply_content) = channel.cache_dict[from_user].pop(0)
                    if not channel.cache_dict[from_user]:  # If popping the message makes the list empty, delete the user entry from cache
                        del channel.cache_dict[from_user]
                except IndexError:
                    return "success"

                if reply_type == "text":
                    if len(reply_content.encode("utf8")) <= MAX_UTF8_LEN:
                        reply_text = reply_content
                    else:
                        continue_text = "\n【未完待续，回复任意文字以继续】"
                        splits = split_string_by_utf8_length(
                            reply_content,
                            MAX_UTF8_LEN - len(continue_text.encode("utf-8")),
                            max_split=1,
                        )
                        reply_text = splits[0] + continue_text
                        channel.cache_dict[from_user].append(("text", splits[1]))

                    App().logger.info(
                        "[wechatmp] Request {} do send to {} {}: {}\n{}".format(
                            request_cnt,
                            from_user,
                            message_id,
                            content,
                            reply_text,
                        )
                    )
                    replyPost = create_reply(reply_text, msg)
                    return encrypt_func(replyPost.render())

                elif reply_type == "voice":
                    media_id = reply_content
                    asyncio.run_coroutine_threadsafe(channel.delete_media(media_id), channel.delete_media_loop)
                    App().logger.debug(
                        "[wechatmp] Request {} do send to {} {}: {} voice media_id {}".format(
                            request_cnt,
                            from_user,
                            message_id,
                            content,
                            media_id,
                        )
                    )
                    replyPost = VoiceReply(message=msg)
                    replyPost.media_id = media_id
                    return encrypt_func(replyPost.render())

                elif reply_type == "image":
                    media_id = reply_content
                    asyncio.run_coroutine_threadsafe(channel.delete_media(media_id), channel.delete_media_loop)
                    App().logger.debug(
                        "[wechatmp] Request {} do send to {} {}: {} image media_id {}".format(
                            request_cnt,
                            from_user,
                            message_id,
                            content,
                            media_id,
                        )
                    )
                    replyPost = ImageReply(message=msg)
                    replyPost.media_id = media_id
                    return encrypt_func(replyPost.render())

            elif msg.type == "event":
                App().logger.debug("[wechatmp] Event {} from {}".format(msg.event, msg.source))
                if msg.event in ["subscribe", "subscribe_scan"]:
                    reply_text = Config().subscribe_msg()
                    if reply_text:
                        replyPost = create_reply(reply_text, msg)
                        return encrypt_func(replyPost.render())
                else:
                    return "success"
            else:
                App().logger.debug("暂且不处理")
            return "success"
        except Exception as exc:
            App().logger.exception(f"处理请求时发生未捕获异常")
            return "server error"
