from wechatpy.crypto import WeChatCrypto
from wechatpy.exceptions import InvalidSignatureException, InvalidAppIdException
from wechatpy.utils import check_signature

from config import conf
import logging

MAX_UTF8_LEN = 2048

logger = logging.getLogger(__name__)


class WeChatAPIException(Exception):
    pass


def verify_server(params: dict) -> str:
    """
    验证微信服务器有效性
    :param params: 请求参数字典，包含 signature, timestamp, nonce, echostr
    :return: 验证成功返回echostr，失败抛出异常
    """
    required = ["signature", "timestamp", "nonce"]
    if not all(k in params for k in required):
        raise InvalidAppIdException("缺少必要参数")
    
    signature = params["signature"]
    timestamp = params["timestamp"]
    nonce = params["nonce"]
    echostr = params.get("echostr", "")
    token = conf().get("wechatmp_token")
    
    try:
        check_signature(token, signature, timestamp, nonce)
        return echostr
    except InvalidSignatureException as e:
        logger.error(f"签名验证失败: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"服务器验证异常: {str(e)}")
        raise
