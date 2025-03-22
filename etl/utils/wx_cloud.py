import os
import sys
import json
import time
import random
import string
import requests
import logging
from pathlib import Path
from typing import Dict, Optional, Tuple, Union, List

# 添加项目根目录到系统路径
sys.path.append(str(Path(__file__).parent.parent.parent))
from config import config

# 初始化日志
logger = logging.getLogger(__name__)

class WxCloudStorage:
    """
    微信云存储工具类
    
    提供微信小程序云存储文件的上传、下载和删除功能
    """
    
    def __init__(self):
        """初始化微信云存储工具类"""
        self.env = config.get("wx_cloud.env")
        self.download_url = config.get("wx_cloud.download_url")
        self.upload_url = config.get("wx_cloud.upload_url")
        
        if not self.env:
            logger.error("微信云环境ID未配置")
        
    def get_access_token(self) -> str:
        """
        获取微信小程序接口调用凭证
        
        Returns:
            str: 接口调用凭证
        """
        app_id = config.get("wx.app_id")
        app_secret = config.get("wx.app_secret")
        
        if not app_id or not app_secret:
            logger.error("微信小程序AppID或AppSecret未配置")
            return ""
            
        url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={app_id}&secret={app_secret}"
        try:
            response = requests.get(url)
            result = response.json()
            
            if "access_token" in result:
                return result["access_token"]
            else:
                logger.error(f"获取接口调用凭证失败: {result}")
                return ""
        except Exception as e:
            logger.error(f"获取接口调用凭证异常: {e}")
            return ""
    
    def download_file(self, file_id: str, save_path: Optional[str] = None) -> str:
        """
        下载云存储文件
        
        Args:
            file_id: 云存储文件ID
            save_path: 保存路径，如果为None则保存到临时目录
            
        Returns:
            str: 下载文件的本地路径，下载失败则返回空字符串
        """
        if not file_id:
            logger.error("文件ID不能为空")
            return ""
            
        # 获取access_token
        access_token = self.get_access_token()
        if not access_token:
            return ""
            
        # 准备下载请求
        headers = {"Content-Type": "application/json"}
        data = {
            "env": self.env,
            "file_list": [{
                "fileid": file_id,
                "max_age": 7200  # 文件链接有效期，单位秒
            }]
        }
        
        try:
            response = requests.post(
                f"{self.download_url}?access_token={access_token}",
                headers=headers,
                json=data
            )
            result = response.json()
            
            if result.get("errcode") == 0 and result.get("file_list"):
                download_url = result["file_list"][0].get("download_url", "")
                
                if not download_url:
                    logger.error(f"获取下载链接失败: {result}")
                    return ""
                
                # 下载文件
                file_response = requests.get(download_url)
                
                if file_response.status_code != 200:
                    logger.error(f"下载文件失败，状态码: {file_response.status_code}")
                    return ""
                
                # 确定保存路径
                if not save_path:
                    # 创建临时目录
                    tmp_dir = Path(config.get("data_dir.cache")) / "wx_cloud_tmp"
                    tmp_dir.mkdir(parents=True, exist_ok=True)
                    
                    # 提取文件名
                    filename = file_id.split("/")[-1]
                    save_path = str(tmp_dir / filename)
                
                # 保存文件
                with open(save_path, "wb") as f:
                    f.write(file_response.content)
                
                logger.debug(f"文件下载成功: {save_path}")
                return save_path
            else:
                logger.error(f"获取下载链接失败: {result}")
                return ""
        except Exception as e:
            logger.error(f"下载文件异常: {e}")
            return ""
    
    def upload_file(self, local_path: str, cloud_path: str) -> str:
        """
        上传文件到云存储
        
        Args:
            local_path: 本地文件路径
            cloud_path: 云存储路径，格式为: 'folder/filename.ext'
            
        Returns:
            str: 成功返回文件ID，失败返回空字符串
        """
        if not os.path.exists(local_path):
            logger.error(f"本地文件不存在: {local_path}")
            return ""
            
        # 获取access_token
        access_token = self.get_access_token()
        if not access_token:
            return ""
            
        # 1. 获取上传链接
        headers = {"Content-Type": "application/json"}
        data = {
            "env": self.env,
            "path": cloud_path
        }
        
        try:
            response = requests.post(
                f"{self.upload_url}?access_token={access_token}",
                headers=headers,
                json=data
            )
            result = response.json()
            
            if result.get("errcode") == 0:
                # 2. 上传文件
                upload_url = result.get("url", "")
                token = result.get("token", "")
                file_id = result.get("file_id", "")
                
                if not upload_url or not token or not file_id:
                    logger.error(f"获取上传参数失败: {result}")
                    return ""
                
                with open(local_path, "rb") as f:
                    files = {"file": f}
                    upload_response = requests.post(
                        upload_url,
                        files=files,
                        data={"key": cloud_path, "Signature": token, "x-cos-security-token": token}
                    )
                    
                    if upload_response.status_code == 204:
                        logger.debug(f"文件上传成功: {file_id}")
                        return file_id
                    else:
                        logger.error(f"文件上传失败，状态码: {upload_response.status_code}, 响应: {upload_response.text}")
                        return ""
            else:
                logger.error(f"获取上传链接失败: {result}")
                return ""
        except Exception as e:
            logger.error(f"上传文件异常: {e}")
            return ""
    
    def delete_file(self, file_id_list: List[str]) -> bool:
        """
        删除云存储文件
        
        Args:
            file_id_list: 云存储文件ID列表
            
        Returns:
            bool: 是否全部删除成功
        """
        if not file_id_list:
            logger.warning("文件ID列表为空")
            return True
            
        # 获取access_token
        access_token = self.get_access_token()
        if not access_token:
            return False
            
        # 准备删除请求
        headers = {"Content-Type": "application/json"}
        data = {
            "env": self.env,
            "fileid_list": file_id_list
        }
        
        try:
            response = requests.post(
                f"https://api.weixin.qq.com/tcb/batchdeletefile?access_token={access_token}",
                headers=headers,
                json=data
            )
            result = response.json()
            
            if result.get("errcode") == 0:
                # 检查是否有删除失败的文件
                delete_list = result.get("delete_list", [])
                all_success = all(item.get("status") == 0 for item in delete_list)
                
                if all_success:
                    logger.debug(f"所有文件删除成功")
                    return True
                else:
                    failed_files = [item.get("fileid") for item in delete_list if item.get("status") != 0]
                    logger.error(f"部分文件删除失败: {failed_files}")
                    return False
            else:
                logger.error(f"删除文件失败: {result}")
                return False
        except Exception as e:
            logger.error(f"删除文件异常: {e}")
            return False

    @staticmethod
    def generate_cloud_path(module: str, user_id: str, filename: str) -> str:
        """
        生成标准的云存储路径
        
        Args:
            module: 模块名，如'avatars', 'posts', 'feedback'等
            user_id: 用户ID，用于权限隔离
            filename: 文件名
            
        Returns:
            str: 云存储路径
        """
        timestamp = int(time.time())
        random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
        
        # 提取文件扩展名
        _, ext = os.path.splitext(filename)
        if not ext:
            ext = '.unknown'
        
        # 构建路径: module/user_id/timestamp_random.ext
        cloud_path = f"{module}/{user_id}/{timestamp}_{random_str}{ext.lower()}"
        return cloud_path

# 创建全局实例
wx_cloud = WxCloudStorage() 