"""
cozepy兼容模块
当真正的cozepy库不存在时提供基本功能和类型
"""

import logging
logger = logging.getLogger(__name__)

# 基本常量
__version__ = "0.1.0"
USER_ROLE = "user"
ASSISTANT_ROLE = "assistant"
SYSTEM_ROLE = "system"
FUNCTION_ROLE = "function"

try:
    # 尝试导入真正的cozepy库
    from cozepy.sdk import CozeAgentSDK
    logger.debug("成功导入cozepy库")
except ImportError:
    logger.warning("cozepy库未安装，使用兼容模块")
    
    # 定义占位类
    class CozeAgentSDK:
        """Coze Agent SDK占位类"""
        
        def __init__(self, agent_id=None, api_key=None, base_url=None):
            self.agent_id = agent_id
            self.api_key = api_key
            self.base_url = base_url
            logger.warning("使用了cozepy兼容模块中的CozeAgentSDK，请安装真正的cozepy库")
        
        def chat(self, messages, stream=False, timeout=None, extra_info=None):
            """占位聊天方法"""
            logger.error("cozepy库未安装，无法使用chat方法")
            return {
                "status": "error",
                "message": "cozepy库未安装，请运行 pip install cozepy 安装",
                "response": "请安装cozepy库以使用Coze功能",
                "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
            } 