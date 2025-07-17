import io
import os
import time
import asyncio
import imghdr
import threading
import requests

import uvicorn
from wechatpy.crypto import WeChatCrypto
from wechatpy.exceptions import WeChatClientException
from collections import defaultdict
from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
from core.utils.logger import register_logger
import config
from core.agent.agent_factory import create_agent
from core.bridge.context import Context
from core.bridge.reply import Reply, ReplyType
from singleton_decorator import singleton
from core.utils.string import split_string_by_utf8_length, remove_markdown_symbol
from core.utils.voice.audio_convert import any_to_mp3, split_audio
from services.chat_channel import ChatChannel
from services.wechatmp.common import *
from services.wechatmp.wechatmp_client import WechatMPClient

logger = register_logger("services.wechatmp")

# If using SSL, uncomment the following lines, and modify the certificate path.
# from cheroot.server import HTTPServer
# from cheroot.ssl.builtin import BuiltinSSLAdapter
# HTTPServer.ssl_adapter = BuiltinSSLAdapter(
#         certificate='/ssl/cert.pem',
#         private_key='/ssl/cert.key')

app = FastAPI()

@app.api_route("/wx", methods=["GET", "POST"], response_class=PlainTextResponse)
async def wechat_handler(request: Request) -> PlainTextResponse:
    """处理微信服务器验证和消息推送
    
    Args:
        request: FastAPI请求对象，包含查询参数和请求体
        
    Returns:
        PlainTextResponse: 验证请求返回明文响应，消息处理返回XML响应
    """
    params = dict(request.query_params)
    data = await request.body()
    # 微信服务器验证（GET请求）
    if request.method == "GET":
        logger.debug("收到微信服务器验证请求")
        return PlainTextResponse(content=params.get("echostr", ""))
    
    # 消息处理（POST请求）
    # App().logger.debug("收到微信消息")
    # 根据配置选择处理器
    if Config().get("channel_type") == "wechatmp":
        from services.wechatmp.passive_reply import Query
    else: 
        from services.wechatmp.active_reply import Query
    handler = Query()
    return await handler.process(params, data)

@singleton
class WechatMPChannel(ChatChannel):
    """微信公众号消息处理通道
    
    Attributes:
        passive_reply: 是否使用被动回复模式
        client: 微信客户端实例
        crypto: 微信消息加解密工具
    """
    
    def __init__(self, passive_reply: bool = False):
        super().__init__()
        self.passive_reply: bool = passive_reply
        self.NOT_SUPPORT_REPLYTYPE: list = []
        appid = Config().get("services.wechatmp_service.app_id")
        secret = Config().get("services.wechatmp_service.app_secret")
        token = Config().get("services.wechatmp_service.token")
        aes_key = Config().get("services.wechatmp_service.aes_key")
        self.client = WechatMPClient(appid, secret)
        self.crypto = None
        if aes_key:
            self.crypto = WeChatCrypto(token, aes_key, appid)
        if self.passive_reply:
            # Cache the reply to the user's first message
            self.cache_dict: defaultdict[str, list] = defaultdict(list)
            # Record whether the current message is being processed
            self.running: set[str] = set()
            # Count the request from wechat official server by message_id
            self.request_cnt: dict[str, int] = dict()
            # The permanent media need to be deleted to avoid media number limit
            self.delete_media_loop = asyncio.new_event_loop()
            t = threading.Thread(target=self.start_loop, args=(self.delete_media_loop,))
            t.setDaemon(True)
            t.start()

    def startup(self):
        """启动FastAPI服务"""
        port = Config().get("services.wechatmp_service.port", 80)
        thread = threading.Thread(target=self.run_uvicorn, args=(port,))
        thread.start()
        logger.info(f"Channel wechatmp started successfully on port {port}")

    def run_uvicorn(self, port):
        """UVicorn服务运行方法"""
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=port,
            log_level="critical",
            access_log=False
        )

    def start_loop(self, loop):
        asyncio.set_event_loop(loop)
        loop.run_forever()

    async def delete_media(self, media_id):
        logger.debug("[wechatmp] permanent media {} will be deleted in 10s".format(media_id))
        await asyncio.sleep(10)
        self.client.material.delete(media_id)
        logger.info("[wechatmp] permanent media {} has been deleted".format(media_id))

    def send(self, reply: Reply, context: Context) -> None:
        """发送回复消息到微信平台
        
        Args:
            reply: 回复消息对象，包含消息类型和内容
            context: 消息上下文，包含接收者等信息
            
        Raises:
            WeChatClientException: 微信API调用异常
        """
        receiver = context["receiver"]
        if self.passive_reply:
            if reply.type in [ReplyType.TEXT, ReplyType.INFO, ReplyType.ERROR, ReplyType.IMAGE, ReplyType.VOICE]:
                logger.debug(f"[wechatmp] 处理{reply.type}类型回复")
                if reply.type == ReplyType.TEXT or reply.type == ReplyType.INFO or reply.type == ReplyType.ERROR:
                    reply_text = remove_markdown_symbol(reply.content)
                    self.cache_dict[receiver].append(("text", reply_text))
                    if receiver not in self.running:
                        self.running.add(receiver)
                elif reply.type == ReplyType.VOICE:
                    voice_file_path = reply.content
                    duration, files = split_audio(voice_file_path, 60 * 1000)
                    if len(files) > 1:
                        logger.info("[wechatmp] voice too long {}s > 60s , split into {} parts".format(duration / 1000.0, len(files)))

                    for path in files:
                        # support: <2M, <60s, mp3/wma/wav/amr
                        try:
                            with open(path, "rb") as f:
                                response = self.client.material.add("voice", f)
                                logger.debug("[wechatmp] upload voice response: {}".format(response))
                                f_size = os.fstat(f.fileno()).st_size
                                time.sleep(1.0 + 2 * f_size / 1024 / 1024)
                                # todo check media_id
                        except WeChatClientException as e:
                            logger.error("[wechatmp] upload voice failed: {}".format(e))
                            return
                        media_id = response["media_id"]
                        logger.info("[wechatmp] voice uploaded, receiver {}, media_id {}".format(receiver, media_id))
                        self.cache_dict[receiver].append(("voice", media_id))

                elif reply.type == ReplyType.IMAGE_URL:  # 从网络下载图片
                    img_url = reply.content
                    pic_res = requests.get(img_url, stream=True)
                    image_storage = io.BytesIO()
                    for block in pic_res.iter_content(1024):
                        image_storage.write(block)
                    image_storage.seek(0)
                    image_type = imghdr.what(image_storage)
                    filename = receiver + "-" + str(context["msg"].msg_id) + "." + image_type
                    content_type = "image/" + image_type
                    try:
                        response = self.client.material.add("image", (filename, image_storage, content_type))
                        logger.debug("[wechatmp] upload image response: {}".format(response))
                    except WeChatClientException as e:
                        logger.error("[wechatmp] upload image failed: {}".format(e))
                        return
                    media_id = response["media_id"]
                    logger.info("[wechatmp] image uploaded, receiver {}, media_id {}".format(receiver, media_id))
                    self.cache_dict[receiver].append(("image", media_id))
                elif reply.type == ReplyType.IMAGE:  # 从文件读取图片
                    image_storage = reply.content
                    image_storage.seek(0)
                    image_type = imghdr.what(image_storage)
                    filename = receiver + "-" + str(context["msg"].msg_id) + "." + image_type
                    content_type = "image/" + image_type
                    try:
                        response = self.client.material.add("image", (filename, image_storage, content_type))
                        logger.debug("[wechatmp] upload image response: {}".format(response))
                    except WeChatClientException as e:
                        logger.error("[wechatmp] upload image failed: {}".format(e))
                        return
                    media_id = response["media_id"]
                    logger.info("[wechatmp] image uploaded, receiver {}, media_id {}".format(receiver, media_id))
                    self.cache_dict[receiver].append(("image", media_id))
                elif reply.type == ReplyType.VIDEO_URL:  # 从网络下载视频
                    video_url = reply.content
                    video_res = requests.get(video_url, stream=True)
                    video_storage = io.BytesIO()
                    for block in video_res.iter_content(1024):
                        video_storage.write(block)
                    video_storage.seek(0)
                    video_type = 'mp4'
                    filename = receiver + "-" + str(context["msg"].msg_id) + "." + video_type
                    content_type = "video/" + video_type
                    try:
                        response = self.client.material.add("video", (filename, video_storage, content_type))
                        logger.debug("[wechatmp] upload video response: {}".format(response))
                    except WeChatClientException as e:
                        logger.error("[wechatmp] upload video failed: {}".format(e))
                        return
                    media_id = response["media_id"]
                    logger.info("[wechatmp] video uploaded, receiver {}, media_id {}".format(receiver, media_id))
                    self.cache_dict[receiver].append(("video", media_id))

                elif reply.type == ReplyType.VIDEO:  # 从文件读取视频
                    video_storage = reply.content
                    video_storage.seek(0)
                    video_type = 'mp4'
                    filename = receiver + "-" + str(context["msg"].msg_id) + "." + video_type
                    content_type = "video/" + video_type
                    try:
                        response = self.client.material.add("video", (filename, video_storage, content_type))
                        logger.debug("[wechatmp] upload video response: {}".format(response))
                    except WeChatClientException as e:
                        logger.error("[wechatmp] upload video failed: {}".format(e))
                        return
                    media_id = response["media_id"]
                    logger.info("[wechatmp] video uploaded, receiver {}, media_id {}".format(receiver, media_id))
                    self.cache_dict[receiver].append(("video", media_id))

        else:
            if reply.type in [ReplyType.TEXT, ReplyType.INFO, ReplyType.ERROR]:
                reply_text = reply.content
                texts = split_string_by_utf8_length(reply_text, MAX_UTF8_LEN)
                if len(texts) > 1:
                    logger.info("[wechatmp] text too long, split into {} parts".format(len(texts)))
                for i, text in enumerate(texts):
                    self.client.message.send_text(receiver, text)
                    if i != len(texts) - 1:
                        time.sleep(0.5)  # 休眠0.5秒，防止发送过快乱序
                logger.info("[wechatmp] Do send text to {}: {}".format(receiver, reply_text))
            elif reply.type == ReplyType.VOICE:
                try:
                    file_path = reply.content
                    file_name = os.path.basename(file_path)
                    file_type = os.path.splitext(file_name)[1]
                    if file_type == ".mp3":
                        file_type = "audio/mpeg"
                    elif file_type == ".amr":
                        file_type = "audio/amr"
                    else:
                        mp3_file = os.path.splitext(file_path)[0] + ".mp3"
                        any_to_mp3(file_path, mp3_file)
                        file_path = mp3_file
                        file_name = os.path.basename(file_path)
                        file_type = "audio/mpeg"
                    logger.info("[wechatmp] file_name: {}, file_type: {} ".format(file_name, file_type))
                    media_ids = []
                    duration, files = split_audio(file_path, 60 * 1000)
                    if len(files) > 1:
                        logger.info("[wechatmp] voice too long {}s > 60s , split into {} parts".format(duration / 1000.0, len(files)))
                    for path in files:
                        # support: <2M, <60s, AMR\MP3
                        response = self.client.media.upload("voice", (os.path.basename(path), open(path, "rb"), file_type))
                        logger.debug("[wechatcom] upload voice response: {}".format(response))
                        media_ids.append(response["media_id"])
                        os.remove(path)
                except WeChatClientException as e:
                    logger.error("[wechatmp] upload voice failed: {}".format(e))
                    return

                try:
                    os.remove(file_path)
                except Exception:
                    pass

                for media_id in media_ids:
                    self.client.message.send_voice(receiver, media_id)
                    time.sleep(1)
                logger.info("[wechatmp] Do send voice to {}".format(receiver))
            elif reply.type == ReplyType.IMAGE_URL:  # 从网络下载图片
                img_url = reply.content
                pic_res = requests.get(img_url, stream=True)
                image_storage = io.BytesIO()
                for block in pic_res.iter_content(1024):
                    image_storage.write(block)
                image_storage.seek(0)
                image_type = imghdr.what(image_storage)
                filename = receiver + "-" + str(context["msg"].msg_id) + "." + image_type
                content_type = "image/" + image_type
                try:
                    response = self.client.media.upload("image", (filename, image_storage, content_type))
                    logger.debug("[wechatmp] upload image response: {}".format(response))
                except WeChatClientException as e:
                    logger.error("[wechatmp] upload image failed: {}".format(e))
                    return
                self.client.message.send_image(receiver, response["media_id"])
                logger.info("[wechatmp] Do send image to {}".format(receiver))
            elif reply.type == ReplyType.IMAGE:  # 从文件读取图片
                image_storage = reply.content
                image_storage.seek(0)
                image_type = imghdr.what(image_storage)
                filename = receiver + "-" + str(context["msg"].msg_id) + "." + image_type
                content_type = "image/" + image_type
                try:
                    response = self.client.media.upload("image", (filename, image_storage, content_type))
                    logger.debug("[wechatmp] upload image response: {}".format(response))
                except WeChatClientException as e:
                    logger.error("[wechatmp] upload image failed: {}".format(e))
                    return
                self.client.message.send_image(receiver, response["media_id"])
                logger.debug("[wechatmp] Do send image to {}".format(receiver))
            elif reply.type == ReplyType.VIDEO_URL:  # 从网络下载视频
                video_url = reply.content
                video_res = requests.get(video_url, stream=True)
                video_storage = io.BytesIO()
                for block in video_res.iter_content(1024):
                    video_storage.write(block)
                video_storage.seek(0)
                video_type = 'mp4'
                filename = receiver + "-" + str(context["msg"].msg_id) + "." + video_type
                content_type = "video/" + video_type
                try:
                    response = self.client.media.upload("video", (filename, video_storage, content_type))
                    logger.debug("[wechatmp] upload video response: {}".format(response))
                except WeChatClientException as e:
                    logger.exception("[wechatmp] upload video failed")
                    return
                self.client.message.send_video(receiver, response["media_id"])
                logger.info("[wechatmp] Do send video to {}".format(receiver))
            elif reply.type == ReplyType.VIDEO:  # 从文件读取视频
                video_storage = reply.content
                video_storage.seek(0)
                video_type = 'mp4'
                filename = receiver + "-" + str(context["msg"].msg_id) + "." + video_type
                content_type = "video/" + video_type
                try:
                    response = self.client.media.upload("video", (filename, video_storage, content_type))
                    logger.debug("[wechatmp] upload video response: {}".format(response))
                except WeChatClientException as e:
                    logger.exception("[wechatmp] upload video failed")
                    return
                self.client.message.send_video(receiver, response["media_id"])
                logger.info("[wechatmp] Do send video to {}".format(receiver))
        return

    def _success_callback(self, session_id: str, context: Context, **kwargs) -> None:
        """消息处理成功回调
        
        Args:
            session_id: 会话ID
            context: 消息上下文
        """
        logger.debug("[wechatmp] Success to generate reply, msgId={}".format(context["msg"].msg_id))
        receiver = context["receiver"]
        if self.passive_reply:
            if receiver in self.running:
                self.running.remove(receiver)

    def _fail_callback(self, session_id: str, exception: Exception, context: Context, **kwargs) -> None:
        """消息处理失败回调
        
        Args:
            session_id: 会话ID 
            exception: 异常对象
            context: 消息上下文
        """
        logger.exception("[wechatmp] Fail to generate reply to user, msgId={}, exception={}".format(context["msg"].msg_id, exception))
        receiver = context["receiver"]
        if self.passive_reply:
            if receiver in self.running:
                self.running.remove(receiver)
