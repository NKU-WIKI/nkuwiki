import time
import threading
from typing import Optional, Any, Dict

from wechatpy.client import WeChatClient
from wechatpy.exceptions import APILimitedException

from app import App
from services.wechatmp.common import *

class WechatMPClient(WeChatClient):
    def __init__(
        self,
        appid: str,
        secret: str,
        access_token: Optional[str] = None,
        session: Optional[Any] = None,
        timeout: Optional[int] = None,
        auto_retry: bool = True
    ):
        """微信公众号API客户端
        Args:
            appid: 微信公众号appid
            secret: 微信公众号appsecret
            access_token: 初始access_token
            session: 自定义session对象
            timeout: 请求超时时间
            auto_retry: 是否自动重试
        """
        super().__init__(appid, secret, access_token, session, timeout, auto_retry)
        self.fetch_access_token_lock = threading.Lock()
        self.clear_quota_lock = threading.Lock()
        self.last_clear_quota_time: float = -1.0

    def clear_quota(self) -> Dict:
        """清除API调用次数（旧版接口）"""
        return self.post("clear_quota", data={"appid": self.appid})

    def clear_quota_v2(self) -> Dict:
        """清除API调用次数（新版接口）"""
        return self.post("clear_quota/v2", params={"appid": self.appid, "appsecret": self.secret})

    def fetch_access_token(self) -> str:
        """线程安全获取access_token"""
        with self.fetch_access_token_lock:
            access_token = self.session.get(self.access_token_key)
            if access_token and self.expires_at and (self.expires_at - time.time() > 60):
                return access_token
            return super().fetch_access_token()

    def _request(self, method: str, url_or_endpoint: str, **kwargs) -> Dict:
        """重载请求方法，处理API限流异常"""
        try:
            return super()._request(method, url_or_endpoint, **kwargs)
        except APILimitedException as e:
            App().logger.error(f"[wechatmp] API quota has been used up. {e}")
            current_time = time.time()
            if self.last_clear_quota_time == -1 or current_time - self.last_clear_quota_time > 60:
                with self.clear_quota_lock:
                    if self.last_clear_quota_time == -1 or current_time - self.last_clear_quota_time > 60:
                        self.last_clear_quota_time = current_time
                        response = self.clear_quota_v2()
                        App().logger.debug(f"[wechatmp] API quota cleared: {response}")
                return super()._request(method, url_or_endpoint, **kwargs)
            raise
