"""企业微信运行模块，负责ntwork库的初始化和运行"""

import os
import sys
import threading
from loguru import logger

# 设置ntwork的日志级别为ERROR，避免过多日志输出
os.environ['ntwork_LOG'] = "ERROR"

try:
    import ntwork
except ImportError:
    logger.error("未安装ntwork库，请执行 pip install ntwork")
    sys.exit(1)

# 全局wework实例
wework = ntwork.WeWork()

# 运行标志，用于控制forever循环
_running = True

def open(smart=True):
    """打开企业微信
    
    Args:
        smart: 是否智能模式
    """
    wework.open(smart=smart)
    
def wait_login():
    """等待登录完成"""
    wework.wait_login()
    
def get_login_info():
    """获取登录信息
    
    Returns:
        dict: 登录信息
    """
    return wework.get_login_info()
    
def get_external_contacts():
    """获取外部联系人
    
    Returns:
        dict: 外部联系人列表
    """
    return wework.get_external_contacts()
    
def get_rooms():
    """获取群聊列表
    
    Returns:
        dict: 群聊列表
    """
    return wework.get_rooms()
    
def get_room_members(room_id):
    """获取群成员
    
    Args:
        room_id: 群ID
        
    Returns:
        dict: 群成员列表
    """
    return wework.get_room_members(room_id)
    
def forever():
    """永久运行，直到_running为False"""
    global _running
    _thread = threading.Thread(target=_loop)
    _thread.setDaemon(True)
    _thread.start()
    
def _loop():
    """循环执行，保持连接活跃"""
    global _running
    while _running:
        try:
            wework.keep_alive()
        except Exception as e:
            logger.error(f"企业微信保持连接异常: {e}")
        ntwork.time.sleep(1)
        
def exit_():
    """退出企业微信"""
    global _running
    _running = False
    ntwork.exit_() 