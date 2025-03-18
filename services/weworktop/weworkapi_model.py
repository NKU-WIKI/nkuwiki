"""
企业微信API接口封装
"""
import json
import time
import requests
from loguru import logger

class WeworkApiClient:
    """企业微信API客户端"""
    
    def __init__(self, corp_id, corp_secret, agent_id):
        """
        初始化API客户端
        
        参数:
        - corp_id: 企业ID
        - corp_secret: 应用Secret
        - agent_id: 应用ID
        """
        self.corp_id = corp_id
        self.corp_secret = corp_secret
        self.agent_id = agent_id
        self.access_token = ""
        self.token_expires_at = 0
        
        # API接口定义
        self.API_GET_TOKEN = "https://qyapi.weixin.qq.com/cgi-bin/gettoken"
        self.API_SEND_MESSAGE = "https://qyapi.weixin.qq.com/cgi-bin/message/send"
        self.API_GET_USER_INFO = "https://qyapi.weixin.qq.com/cgi-bin/user/get"
        self.API_GET_DEPARTMENT_LIST = "https://qyapi.weixin.qq.com/cgi-bin/department/list"
        self.API_MEDIA_UPLOAD = "https://qyapi.weixin.qq.com/cgi-bin/media/upload"
        
        # 获取初始token
        self.refresh_token()
    
    def refresh_token(self):
        """
        刷新access_token
        
        返回:
        - bool: 是否成功刷新
        """
        try:
            params = {
                "corpid": self.corp_id,
                "corpsecret": self.corp_secret
            }
            response = requests.get(self.API_GET_TOKEN, params=params)
            if response.status_code != 200:
                logger.error(f"获取企业微信token失败: HTTP状态码 {response.status_code}")
                return False
                
            data = response.json()
            if data["errcode"] != 0:
                logger.error(f"获取企业微信token失败: {data['errmsg']}")
                return False
                
            self.access_token = data["access_token"]
            # token有效期为7200秒，提前5分钟过期
            self.token_expires_at = time.time() + data["expires_in"] - 300
            logger.debug("企业微信token刷新成功")
            return True
        except Exception as e:
            logger.error(f"获取企业微信token异常: {str(e)}")
            return False
    
    def _check_token(self):
        """
        检查token是否有效，无效则刷新
        
        返回:
        - bool: token是否有效
        """
        if time.time() >= self.token_expires_at:
            return self.refresh_token()
        return True
    
    def send_text(self, user_id, content):
        """
        发送文本消息给用户
        
        参数:
        - user_id: 用户ID
        - content: 消息内容
        
        返回:
        - bool: 是否发送成功
        """
        try:
            if not self._check_token():
                return False
                
            data = {
                "touser": user_id,
                "msgtype": "text",
                "agentid": self.agent_id,
                "text": {
                    "content": content
                },
                "safe": 0
            }
            
            return self._send_message(data)
        except Exception as e:
            logger.error(f"发送文本消息异常: {str(e)}")
            return False
    
    def send_group_text(self, chat_id, content):
        """
        发送文本消息到群聊
        
        参数:
        - chat_id: 群聊ID
        - content: 消息内容
        
        返回:
        - bool: 是否发送成功
        """
        try:
            if not self._check_token():
                return False
                
            data = {
                "chatid": chat_id,
                "msgtype": "text",
                "text": {
                    "content": content
                },
                "safe": 0
            }
            
            return self._send_appchat_message(data)
        except Exception as e:
            logger.error(f"发送群聊消息异常: {str(e)}")
            return False
    
    def send_image(self, user_id, media_id):
        """
        发送图片消息
        
        参数:
        - user_id: 用户ID
        - media_id: 媒体ID
        
        返回:
        - bool: 是否发送成功
        """
        try:
            if not self._check_token():
                return False
                
            data = {
                "touser": user_id,
                "msgtype": "image",
                "agentid": self.agent_id,
                "image": {
                    "media_id": media_id
                },
                "safe": 0
            }
            
            return self._send_message(data)
        except Exception as e:
            logger.error(f"发送图片消息异常: {str(e)}")
            return False
    
    def _send_message(self, data):
        """
        公共发送消息方法
        
        参数:
        - data: 消息数据
        
        返回:
        - bool: 是否发送成功
        """
        try:
            params = {"access_token": self.access_token}
            response = requests.post(self.API_SEND_MESSAGE, params=params, json=data)
            
            if response.status_code != 200:
                logger.error(f"发送消息HTTP请求失败: {response.status_code}")
                return False
                
            result = response.json()
            if result["errcode"] != 0:
                logger.error(f"发送消息失败: {result['errmsg']}")
                return False
                
            return True
        except Exception as e:
            logger.error(f"发送消息异常: {str(e)}")
            return False
    
    def _send_appchat_message(self, data):
        """
        发送群聊消息
        
        参数:
        - data: 消息数据
        
        返回:
        - bool: 是否发送成功
        """
        try:
            api_url = "https://qyapi.weixin.qq.com/cgi-bin/appchat/send"
            params = {"access_token": self.access_token}
            response = requests.post(api_url, params=params, json=data)
            
            if response.status_code != 200:
                logger.error(f"发送群聊消息HTTP请求失败: {response.status_code}")
                return False
                
            result = response.json()
            if result["errcode"] != 0:
                logger.error(f"发送群聊消息失败: {result['errmsg']}")
                return False
                
            return True
        except Exception as e:
            logger.error(f"发送群聊消息异常: {str(e)}")
            return False
    
    def get_user_info(self, user_id):
        """
        获取用户信息
        
        参数:
        - user_id: 用户ID
        
        返回:
        - dict: 用户信息
        """
        try:
            if not self._check_token():
                return None
                
            params = {
                "access_token": self.access_token,
                "userid": user_id
            }
            
            response = requests.get(self.API_GET_USER_INFO, params=params)
            if response.status_code != 200:
                logger.error(f"获取用户信息HTTP请求失败: {response.status_code}")
                return None
                
            result = response.json()
            if result["errcode"] != 0:
                logger.error(f"获取用户信息失败: {result['errmsg']}")
                return None
                
            return result
        except Exception as e:
            logger.error(f"获取用户信息异常: {str(e)}")
            return None
    
    def upload_media(self, media_type, file_path):
        """
        上传临时素材
        
        参数:
        - media_type: 素材类型 (image/voice/video/file)
        - file_path: 文件路径
        
        返回:
        - str: 媒体ID，失败返回None
        """
        try:
            if not self._check_token():
                return None
                
            params = {
                "access_token": self.access_token,
                "type": media_type
            }
            
            with open(file_path, 'rb') as f:
                files = {'media': f}
                response = requests.post(self.API_MEDIA_UPLOAD, params=params, files=files)
            
            if response.status_code != 200:
                logger.error(f"上传素材HTTP请求失败: {response.status_code}")
                return None
                
            result = response.json()
            if result["errcode"] != 0:
                logger.error(f"上传素材失败: {result['errmsg']}")
                return None
                
            return result.get("media_id")
        except Exception as e:
            logger.error(f"上传素材异常: {str(e)}")
            return None 