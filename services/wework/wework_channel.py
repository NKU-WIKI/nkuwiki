"""企业微信通道模块，处理企业微信消息的接收和发送

基于ntwork库提供企业微信客户端消息的接收和回复
"""

import io
import json
import os
import random
import tempfile
import threading
import time
import re
import uuid
import requests
import hashlib
from PIL import Image
from concurrent.futures import Future
from core.utils.logger import register_logger
import ntwork

from core.bridge.context import *
from core.bridge.reply import *
from services.chat_channel import ChatChannel
from services.wework.wework_message import WeworkMessage, get_with_retry
from config import Config
from services.wework.run import wework, forever as run_forever

logger = register_logger("services.wework")


def get_wxid_by_name(room_members, group_wxid, name):
    """根据名称获取群成员ID
    
    Args:
        room_members: 群成员字典
        group_wxid: 群ID
        name: 要查找的名称
        
    Returns:
        匹配的用户ID，找不到返回None
    """
    if group_wxid in room_members:
        for member in room_members[group_wxid]['member_list']:
            if member['room_nickname'] == name or member['username'] == name:
                return member['user_id']
    return None  # 如果没有找到，则返回None


def download_and_compress_image(url, filename, quality=30):
    """下载并压缩图片
    
    Args:
        url: 图片URL
        filename: 文件名
        quality: 压缩质量
        
    Returns:
        本地图片路径
    """
    # 确定保存图片的目录
    directory = os.path.join(os.getcwd(), "tmp")
    # 如果目录不存在，则创建目录
    if not os.path.exists(directory):
        os.makedirs(directory)

    # 下载图片
    response = requests.get(url)
    image = Image.open(io.BytesIO(response.content))

    # 压缩图片
    image_path = os.path.join(directory, f"{filename}.jpg")
    image.save(image_path, "JPEG", quality=quality)

    return image_path


def download_video(url, filename):
    """下载视频文件
    
    Args:
        url: 视频URL
        filename: 文件名
        
    Returns:
        本地视频路径，超过30MB返回None
    """
    # 确定保存视频的目录
    directory = os.path.join(os.getcwd(), "tmp")
    # 如果目录不存在，则创建目录
    if not os.path.exists(directory):
        os.makedirs(directory)

    # 下载视频
    response = requests.get(url, stream=True)
    total_size = 0

    video_path = os.path.join(directory, f"{filename}.mp4")

    with open(video_path, 'wb') as f:
        for block in response.iter_content(1024):
            total_size += len(block)

            # 如果视频的总大小超过30MB (30 * 1024 * 1024 bytes)，则停止下载并返回
            if total_size > 30 * 1024 * 1024:
                logger.debug("视频大于30MB，跳过下载")
                return None

            f.write(block)

    return video_path


def create_message(wework_instance, message, is_group):
    """创建消息对象
    
    Args:
        wework_instance: 企业微信实例
        message: 原始消息
        is_group: 是否群聊
        
    Returns:
        WeworkMessage对象
    """
    logger.debug(f"正在为{'群聊' if is_group else '单聊'}创建 WeworkMessage")
    cmsg = WeworkMessage(message, wework=wework_instance, is_group=is_group)
    logger.debug(f"cmsg:{cmsg}")
    return cmsg


def handle_message(cmsg, is_group):
    """处理消息
    
    Args:
        cmsg: 消息对象
        is_group: 是否群聊
    """
    logger.debug(f"准备用 WeworkChannel 处理{'群聊' if is_group else '单聊'}消息")
    if is_group:
        WeworkChannel().handle_group(cmsg)
    else:
        WeworkChannel().handle_single(cmsg)
    logger.debug(f"已用 WeworkChannel 处理完{'群聊' if is_group else '单聊'}消息")


def _check(func):
    """消息检查装饰器，用于过滤旧消息"""
    def wrapper(self, cmsg):
        msgId = cmsg.msg_id
        create_time = cmsg.create_time  # 消息时间戳
        if create_time is None:
            return func(self, cmsg)
        if int(create_time) < int(time.time()) - 60:  # 跳过1分钟前的历史消息
            logger.debug(f"[企业微信]历史消息 {msgId} 已跳过")
            return
        return func(self, cmsg)
    return wrapper


# 注册企业微信消息处理函数
@wework.msg_register(
    [ntwork.MT_RECV_TEXT_MSG, ntwork.MT_RECV_IMAGE_MSG, 11072, ntwork.MT_RECV_VOICE_MSG])
def all_msg_handler(wework_instance, message):
    """企业微信消息处理回调
    
    Args:
        wework_instance: 企业微信实例
        message: 原始消息
        
    Returns:
        None
    """
    logger.debug(f"收到消息: {message}")
    if 'data' in message:
        # 首先查找conversation_id，如果没有找到，则查找room_conversation_id
        conversation_id = message['data'].get('conversation_id', message['data'].get('room_conversation_id'))
        if conversation_id is not None:
            is_group = "R:" in conversation_id
            try:
                cmsg = create_message(wework_instance=wework_instance, message=message, is_group=is_group)
            except NotImplementedError as e:
                logger.error(f"[企业微信]{message.get('MsgId', 'unknown')} 跳过: {e}")
                return None
            # 随机延迟1-2秒处理消息，避免被风控
            delay = random.randint(1, 2)
            timer = threading.Timer(delay, handle_message, args=(cmsg, is_group))
            timer.start()
        else:
            logger.debug("消息数据中无 conversation_id")
            return None
    return None


@wework.msg_register(ntwork.MT_RECV_FRIEND_MSG)
def friend_msg_handler(wework_instance, message):
    """好友请求处理回调
    
    Args:
        wework_instance: 企业微信实例
        message: 原始消息
        
    Returns:
        None
    """
    data = message["data"]
    user_id = data["user_id"]
    corp_id = data["corp_id"]
    logger.info(f"接收到好友请求，消息内容：{data}")
    
    # 检查是否自动接受好友请求
    if Config().get("services.wework.auto_accept_friend", True):
        delay = random.randint(1, 60)  # 随机延迟1-60秒接受请求
        logger.info(f"将在{delay}秒后自动接受好友请求")
        
        def accept_friend():
            try:
                result = wework_instance.accept_friend(user_id, corp_id)
                logger.info(f"接受好友请求结果: {result}")
            except Exception as e:
                logger.error(f"接受好友请求失败: {e}")
                
        threading.Timer(delay, accept_friend).start()
    
    return None


class WeworkChannel(ChatChannel):
    """企业微信通道类，实现对企业微信消息的处理"""
    
    # 企业微信支持所有回复类型
    NOT_SUPPORT_REPLYTYPE = []

    def __init__(self):
        """初始化企业微信通道"""
        super().__init__()
        
    def startup(self):
        """启动企业微信通道"""
        # 读取配置
        smart = Config().get("services.wework.smart", True)  # 是否智能模式
        
        # 初始化企业微信
        wework.open(smart)
        logger.info("等待登录......")
        wework.wait_login()
        
        # 获取登录信息
        login_info = wework.get_login_info()
        self.user_id = login_info['user_id']
        self.name = login_info['nickname']
        logger.info(f"登录信息: user_id: {self.user_id}, name: {self.name}")
        
        # 等待客户端刷新数据
        logger.info("静默延迟60s，等待客户端刷新数据，请勿进行任何操作......")
        time.sleep(60)
        
        # 获取联系人和群聊数据
        contacts = get_with_retry(wework.get_external_contacts)
        rooms = get_with_retry(wework.get_rooms)
        
        # 创建tmp目录保存数据
        directory = os.path.join(os.getcwd(), "tmp")
        if not os.path.exists(directory):
            os.makedirs(directory)
            
        # 检查数据获取是否成功
        if not contacts or not rooms:
            logger.error("获取contacts或rooms失败，程序将退出")
            ntwork.exit_()
            import sys
            sys.exit(0)
            
        # 将联系人数据保存到文件
        with open(os.path.join(directory, 'wework_contacts.json'), 'w', encoding='utf-8') as f:
            json.dump(contacts, f, ensure_ascii=False, indent=4)
        with open(os.path.join(directory, 'wework_rooms.json'), 'w', encoding='utf-8') as f:
            json.dump(rooms, f, ensure_ascii=False, indent=4)
            
        # 获取并保存群成员数据
        result = {}
        for room in rooms['room_list']:
            room_wxid = room['conversation_id']
            room_members = wework.get_room_members(room_wxid)
            result[room_wxid] = room_members
        with open(os.path.join(directory, 'wework_room_members.json'), 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=4)
            
        logger.info("企业微信通道初始化完成")
        # 永久运行保持连接
        run_forever()

    @_check
    def handle_single(self, cmsg):
        """处理私聊消息
        
        Args:
            cmsg: 聊天消息对象
        """
        if cmsg.ctype == ContextType.VOICE:
            if not Config().get("services.wework.speech_recognition", True):
                return
            logger.debug(f"[企业微信]收到语音消息: {cmsg.content}")
        elif cmsg.ctype == ContextType.IMAGE:
            logger.debug(f"[企业微信]收到图片消息: {cmsg.content}")
        elif cmsg.ctype == ContextType.PATPAT:
            logger.debug(f"[企业微信]收到拍一拍消息: {cmsg.content}")
        elif cmsg.ctype == ContextType.TEXT:
            logger.debug(f"[企业微信]收到文本消息: {cmsg.content}")
        else:
            logger.debug(f"[企业微信]收到消息: {cmsg.content}")
            
        context = self._compose_context(cmsg.ctype, cmsg.content, isgroup=False, msg=cmsg)
        if context:
            self.produce(context)

    @_check
    def handle_group(self, cmsg):
        """处理群聊消息
        
        Args:
            cmsg: 聊天消息对象
        """
        if cmsg.ctype == ContextType.VOICE:
            if not Config().get("services.wework.speech_recognition", True):
                return
            logger.debug(f"[企业微信]收到群语音消息: {cmsg.content}")
        elif cmsg.ctype == ContextType.IMAGE:
            logger.debug(f"[企业微信]收到群图片消息: {cmsg.content}")
        elif cmsg.ctype in [ContextType.JOIN_GROUP, ContextType.PATPAT]:
            logger.debug(f"[企业微信]收到群通知消息: {cmsg.content}")
        elif cmsg.ctype == ContextType.TEXT:
            logger.debug(f"[企业微信]收到群文本消息: {cmsg.content}")
        else:
            logger.debug(f"[企业微信]收到群消息: {cmsg.content}")
            
        context = self._compose_context(cmsg.ctype, cmsg.content, isgroup=True, msg=cmsg)
        if context:
            self.produce(context)

    def send(self, reply: Reply, context: Context):
        """发送回复消息
        
        Args:
            reply: 回复内容
            context: 对话上下文
        """
        if reply.type == ReplyType.TEXT:
            self._send_text(reply, context)
        elif reply.type == ReplyType.ERROR or reply.type == ReplyType.INFO:
            self._send_text(reply, context)
        elif reply.type == ReplyType.IMAGE_URL:  # 图片URL
            self._send_image_url(reply, context)
        elif reply.type == ReplyType.IMAGE:  # 图片文件
            self._send_image(reply, context)
        elif reply.type == ReplyType.VOICE:  # 语音
            self._send_voice(reply, context)
        else:
            logger.error(f"[企业微信]暂不支持的消息类型: {reply.type}")
            
    def _send_text(self, reply: Reply, context: Context):
        """发送文本消息
        
        Args:
            reply: 回复内容
            context: 对话上下文
        """
        try:
            cmsg = context["msg"]
            if context.get("isgroup", False):
                # 群聊消息
                conversation_id = cmsg.other_user_id
                wework.send_room_message(conversation_id, reply.content)
            else:
                # 私聊消息
                conversation_id = cmsg.from_user_id
                corp_id = ""  # 留空使用默认企业
                wework.send_message(corp_id, conversation_id, reply.content)
        except Exception as e:
            logger.error(f"[企业微信]发送文本消息失败: {e}")
            
    def _send_image_url(self, reply: Reply, context: Context):
        """发送图片URL消息
        
        Args:
            reply: 回复内容
            context: 对话上下文
        """
        try:
            cmsg = context["msg"]
            url = reply.content
            pic_path = download_and_compress_image(url, uuid.uuid4().hex)
            
            if context.get("isgroup", False):
                # 群聊消息
                conversation_id = cmsg.other_user_id
                wework.send_room_image(conversation_id, pic_path)
            else:
                # 私聊消息
                conversation_id = cmsg.from_user_id
                corp_id = ""  # 留空使用默认企业
                wework.send_image(corp_id, conversation_id, pic_path)
                
            # 删除临时文件
            try:
                os.remove(pic_path)
            except:
                pass
        except Exception as e:
            logger.error(f"[企业微信]发送图片URL消息失败: {e}")
    
    def _send_image(self, reply: Reply, context: Context):
        """发送图片文件消息
        
        Args:
            reply: 回复内容
            context: 对话上下文
        """
        try:
            cmsg = context["msg"]
            file_path = reply.content
            
            if context.get("isgroup", False):
                # 群聊消息
                conversation_id = cmsg.other_user_id
                wework.send_room_image(conversation_id, file_path)
            else:
                # 私聊消息
                conversation_id = cmsg.from_user_id
                corp_id = ""  # 留空使用默认企业
                wework.send_image(corp_id, conversation_id, file_path)
        except Exception as e:
            logger.error(f"[企业微信]发送图片文件消息失败: {e}")
            
    def _send_voice(self, reply: Reply, context: Context):
        """发送语音消息
        
        Args:
            reply: 回复内容
            context: 对话上下文
        """
        try:
            cmsg = context["msg"]
            file_path = reply.content
            
            if context.get("isgroup", False):
                # 群聊消息
                logger.warning("[企业微信]暂不支持发送群语音消息")
                # 转为文本发送
                content = "[语音消息暂不支持]"
                conversation_id = cmsg.other_user_id
                wework.send_room_message(conversation_id, content)
            else:
                # 私聊消息
                logger.warning("[企业微信]暂不支持发送语音消息")
                # 转为文本发送
                content = "[语音消息暂不支持]"
                conversation_id = cmsg.from_user_id
                corp_id = ""  # 留空使用默认企业
                wework.send_message(corp_id, conversation_id, content)
        except Exception as e:
            logger.error(f"[企业微信]发送语音消息失败: {e}") 