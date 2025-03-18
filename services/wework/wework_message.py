"""企业微信消息模块，处理企业微信各种消息类型的转换和处理

提供从企业微信原始消息到统一ChatMessage格式的转换功能
"""

import datetime
import json
import os
import re
import time
import threading

from core.bridge.context import ContextType
from services.chat_message import ChatMessage
from loguru import logger

try:
    import pilk  # 用于SILK编码的语音文件转WAV
except ImportError:
    logger.warning("未安装pilk库，语音转写功能不可用。请执行: pip install pilk")


def get_with_retry(get_func, max_retries=5, delay=5):
    """带有重试机制的函数执行器
    
    Args:
        get_func: 要执行的函数
        max_retries: 最大重试次数
        delay: 重试间隔(秒)
        
    Returns:
        函数执行结果，失败返回None
    """
    retries = 0
    result = None
    while retries < max_retries:
        result = get_func()
        if result:
            break
        logger.warning(f"获取数据失败，重试第{retries + 1}次......")
        retries += 1
        time.sleep(delay)  # 等待一段时间后重试
    return result


def get_room_info(wework, conversation_id):
    """获取群聊信息
    
    Args:
        wework: 企业微信实例
        conversation_id: 会话ID
        
    Returns:
        群聊信息，失败返回None
    """
    logger.debug(f"传入的 conversation_id: {conversation_id}")
    rooms = wework.get_rooms()
    logger.debug(f"获取到的群聊信息: {rooms}")
    if not rooms or 'room_list' not in rooms:
        logger.error(f"获取群聊信息失败")
        return None

    for room in rooms['room_list']:
        if room['conversation_id'] == conversation_id:
            return room
    return None


def cdn_download(wework, wework_msg, file_name):
    """下载文件CDN资源
    
    Args:
        wework: 企业微信实例
        wework_msg: 原始消息
        file_name: 保存的文件名
    """
    data = wework_msg["data"]
    url = data["cdn"]["url"]
    auth_key = data["cdn"]["auth_key"]
    aes_key = data["cdn"]["aes_key"]
    
    # 确保tmp目录存在
    tmp_dir = os.path.join(os.getcwd(), "tmp")
    if not os.path.exists(tmp_dir):
        os.makedirs(tmp_dir)
        
    # 获取保存路径
    save_path = os.path.join(tmp_dir, file_name)

    result = wework.wx_cdn_download(url, auth_key, aes_key, save_path)
    logger.debug(f"CDN下载结果: {result}")
    return save_path


def c2c_download_and_convert(wework, message, file_name):
    """下载C2C语音消息并转换为WAV格式
    
    Args:
        wework: 企业微信实例
        message: 原始消息
        file_name: 保存的文件名
    """
    data = message["data"]
    aes_key = data["cdn"]["aes_key"]
    file_size = data["cdn"]["size"]
    file_id = data["cdn"]["file_id"]

    # 确保tmp目录存在
    tmp_dir = os.path.join(os.getcwd(), "tmp")
    if not os.path.exists(tmp_dir):
        os.makedirs(tmp_dir)
        
    # 获取保存路径
    save_path = os.path.join(tmp_dir, file_name)
    
    result = wework.c2c_cdn_download(file_id, aes_key, file_size, save_path)
    logger.debug(f"C2C下载结果: {result}")

    # 在下载完SILK文件之后，立即将其转换为WAV文件
    try:
        base_name, _ = os.path.splitext(save_path)
        wav_file = base_name + ".wav"
        pilk.silk_to_wav(save_path, wav_file, rate=24000)
        return wav_file
    except Exception as e:
        logger.error(f"转换语音文件失败: {e}")
        return save_path


class WeworkMessage(ChatMessage):
    """企业微信消息类，处理企业微信原始消息到ChatMessage的转换"""
    
    def __init__(self, wework_msg, wework, is_group=False):
        """初始化企业微信消息
        
        Args:
            wework_msg: 企业微信原始消息
            wework: 企业微信实例
            is_group: 是否群消息
        """
        try:
            super().__init__(wework_msg)
            self.msg_id = wework_msg['data'].get('conversation_id', wework_msg['data'].get('room_conversation_id'))
            # 使用.get()防止 'send_time' 键不存在时抛出错误
            self.create_time = wework_msg['data'].get("send_time")
            self.is_group = is_group
            self.wework = wework

            # 获取发送者和接收者信息
            if is_group:
                # 群聊消息
                self.from_user_id = wework_msg['data'].get('sender', {}).get('user_id', '')
                self.from_user_nickname = wework_msg['data'].get('sender', {}).get('name', '')
                self.to_user_id = 'self'
                self.to_user_nickname = wework.get_login_info().get('nickname', '')
                # 群ID和群名称
                self.other_user_id = wework_msg['data'].get('conversation_id', '')
                room_info = get_room_info(wework, self.other_user_id)
                self.other_user_nickname = room_info.get('name', '') if room_info else '未知群聊'
                # 实际发送者信息
                self.actual_user_id = self.from_user_id
                self.actual_user_nickname = self.from_user_nickname
                # 检查是否被@
                content = wework_msg['data'].get('content', '')
                self.is_at = f'@{self.to_user_nickname}' in content
            else:
                # 私聊消息
                self.from_user_id = wework_msg['data'].get('sender', {}).get('user_id', '')
                self.from_user_nickname = wework_msg['data'].get('sender', {}).get('name', '')
                self.to_user_id = 'self'
                self.to_user_nickname = wework.get_login_info().get('nickname', '')
                self.other_user_id = self.from_user_id
                self.other_user_nickname = self.from_user_nickname

            # 根据消息类型设置内容
            msg_type = wework_msg["type"]
            
            if msg_type == 11041:  # 文本消息类型
                content = wework_msg['data'].get('content', '')
                if any(substring in content for substring in ("该消息类型暂不能展示", "不支持的消息类型")):
                    raise NotImplementedError("不支持的消息类型")
                self.ctype = ContextType.TEXT
                self.content = content
                
            elif msg_type == 11044:  # 语音消息类型，需要缓存文件
                file_name = datetime.datetime.now().strftime('%Y%m%d%H%M%S') + ".silk"
                base_name, _ = os.path.splitext(file_name)
                file_name_wav = base_name + ".wav"
                self.ctype = ContextType.VOICE
                self.content = os.path.join(os.getcwd(), "tmp", file_name_wav)
                self._prepare_fn = lambda: c2c_download_and_convert(wework, wework_msg, file_name)
                
            elif msg_type == 11042:  # 图片消息类型，需要下载文件
                file_name = datetime.datetime.now().strftime('%Y%m%d%H%M%S') + ".jpg"
                self.ctype = ContextType.IMAGE
                self.content = os.path.join(os.getcwd(), "tmp", file_name)
                self._prepare_fn = lambda: cdn_download(wework, wework_msg, file_name)
                
            else:
                logger.warning(f"暂不支持的消息类型: {msg_type}")
                raise NotImplementedError(f"暂不支持的消息类型: {msg_type}")
                
        except Exception as e:
            logger.error(f"处理企业微信消息出错: {e}")
            raise NotImplementedError(f"消息处理失败: {e}") 