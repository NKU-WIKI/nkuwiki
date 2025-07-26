"""
翻译工具模块
提供多语言翻译功能的抽象基类和工厂方法
"""
from typing import Optional
import random
from hashlib import md5
import requests


class Translator:
    """
    翻译器抽象基类
    
    所有具体翻译实现都应继承此类并实现translate方法
    """
    
    def translate(self, query: str, from_lang: str = "", to_lang: str = "en") -> str:
        """
        将文本从一种语言翻译为另一种语言
        
        Args:
            query: 要翻译的文本
            from_lang: 源语言代码（ISO 639-1），空字符串表示自动检测
            to_lang: 目标语言代码（ISO 639-1），默认为英语
            
        Returns:
            翻译后的文本
            
        Raises:
            NotImplementedError: 子类需要实现此方法
        """
        raise NotImplementedError


class BaiduTranslator(Translator):
    """
    百度翻译API实现
    
    使用百度翻译API进行文本翻译
    """
    
    def __init__(self, app_id: Optional[str] = None, app_key: Optional[str] = None) -> None:
        """
        初始化百度翻译器
        
        Args:
            app_id: 百度翻译API的应用ID，如果为None则从配置中获取
            app_key: 百度翻译API的应用密钥，如果为None则从配置中获取
            
        Raises:
            Exception: 如果应用ID或密钥未设置
        """
        from config import Config
        
        super().__init__()
        endpoint = "http://api.fanyi.baidu.com"
        path = "/api/trans/vip/translate"
        self.url = endpoint + path
        
        config = Config()
        self.appid = app_id if app_id else config.get("baidu_translate_app_id")
        self.appkey = app_key if app_key else config.get("baidu_translate_app_key")
        
        if not self.appid or not self.appkey:
            raise Exception("百度翻译API的应用ID或密钥未设置")

    def translate(self, query: str, from_lang: str = "", to_lang: str = "en") -> str:
        """
        使用百度翻译API翻译文本
        
        Args:
            query: 要翻译的文本
            from_lang: 源语言代码，空字符串表示自动检测
            to_lang: 目标语言代码，默认为英语'en'
            
        Returns:
            翻译后的文本
            
        Raises:
            Exception: 翻译失败时抛出异常，包含错误信息
        """
        from core.utils.logger import logger
        
        if not from_lang:
            from_lang = "auto"  # 百度支持自动检测语言
            
        # 生成随机数和签名
        salt = random.randint(32768, 65536)
        sign = self._make_md5(f"{self.appid}{query}{salt}{self.appkey}")
        
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        payload = {
            "appid": self.appid,
            "q": query,
            "from": from_lang,
            "to": to_lang,
            "salt": salt,
            "sign": sign
        }

        retry_cnt = 3
        while retry_cnt:
            try:
                r = requests.post(self.url, params=payload, headers=headers)
                result = r.json()
                
                error_code = result.get("error_code", "52000")
                if error_code != "52000":
                    if error_code in ["52001", "52002"]:  # 临时性错误，可重试
                        retry_cnt -= 1
                        logger.warning(f"百度翻译临时错误 {error_code}，重试中...")
                        continue
                    else:
                        raise Exception(f"百度翻译错误: {result.get('error_msg', '未知错误')}")
                else:
                    # 成功获取翻译结果
                    text = "\n".join([item["dst"] for item in result["trans_result"]])
                    return text
            except Exception as e:
                logger.error(f"百度翻译失败: {str(e)}")
                retry_cnt -= 1
                if retry_cnt == 0:
                    raise
                
        return query  # 如果所有重试都失败，返回原文

    def _make_md5(self, s: str, encoding: str = "utf-8") -> str:
        """计算字符串的MD5哈希值"""
        return md5(s.encode(encoding)).hexdigest()


def create_translator(translator_type: str = "baidu") -> Translator:
    """
    创建翻译器实例
    
    Args:
        translator_type: 翻译器类型，当前支持"baidu"
        
    Returns:
        Translator: 指定类型的翻译器实例
        
    Raises:
        ValueError: 不支持的翻译器类型
    """
    if translator_type.lower() == "baidu":
        return BaiduTranslator()
    else:
        raise ValueError(f"不支持的翻译器类型: {translator_type}") 