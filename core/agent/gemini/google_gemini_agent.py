"""
Google Gemini聊天机器人
"""
import requests
from config import Config
from core.bridge.reply import Reply
from core.bridge.context import Context
from core.agent.agent import Agent
from core.agent.gemini.google_gemini_session import GoogleGeminiSessionManager
from core.utils import singleton_decorator
from core.utils.logger import get_module_logger
logger = get_module_logger('core.agent.gemini')

@singleton_decorator
class GoogleGeminiAgent(Agent):
    def __init__(self):
        # 创建配置实例
        self.config = Config()
        
        # 获取配置
        self.api_key = self.config.get("core.agent.gemini.api_key")
        
        # 获取模型配置
        self.model = self.config.get("core.agent.gemini.model", "gemini-1.5-pro")
        
        # 初始化参数
        self.temperature = self.config.get("core.agent.gemini.temperature", 0.7)
        self.top_p = self.config.get("core.agent.gemini.top_p", 0.9)
        self.top_k = self.config.get("core.agent.gemini.top_k", 40)
        self.max_tokens = self.config.get("core.agent.gemini.max_tokens", 4096)
        
        # API基础URL
        self.api_base = self.config.get("core.agent.gemini.base_url", "https://generativelanguage.googleapis.com")
        
        # 会话管理
        self.session_manager = GoogleGeminiSessionManager()
        
        # 调试信息
        self.show_user_prompt = self.config.get("debug_info", False)
        
    def reply(self, query, context: Context = None) -> Reply:
        """
        回复消息
        :param query: 用户消息
        :param context: 上下文
        :return: 回复
        """
        if context.type == Context.TYPE_TEXT:
            session_id = context.get("session_id")
            reply = Reply()
            
            # 检查API参数是否已配置
            if not self.api_key:
                reply.content = "请先配置Google Gemini API Key"  # noqa: F841
                return reply
            
            # 获取会话
            session = self.session_manager.session_query(query, session_id)
            
            # 转换会话格式，Gemini接口需要特定格式
            contents = []
            for message in session.messages:
                role = message.get("role")
                content = message.get("content")  # noqa: F841
                
                if role == "system":
                    # Gemini没有system角色，将system消息作为用户消息添加
                    contents.append({
                        "role": "user",
                        "parts": [{"text": f"Instructions: {content}"}]
                    })
                elif role == "user":
                    contents.append({
                        "role": "user",
                        "parts": [{"text": content}]
                    })
                elif role == "assistant":
                    contents.append({
                        "role": "model",
                        "parts": [{"text": content}]
                    })
            
            # 构建请求
            url = f"{self.api_base}/v1beta/models/{self.model}:generateContent"
            if self.api_key:
                url += f"?key={self.api_key}"
                
            payload = {
                "contents": contents,
                "generationConfig": {
                    "temperature": self.temperature,
                    "topP": self.top_p,
                    "topK": self.top_k
                }
            }
            
            # 添加可选参数
            if self.max_tokens > 0:
                payload["generationConfig"]["maxOutputTokens"] = self.max_tokens
            
            # 设置请求头
            headers = {'Content-Type': 'application/json'}
            
            try:
                # 发送请求
                response = requests.post(url, headers=headers, json=payload)
                if response.status_code == 200:
                    result = response.json()
                    if "candidates" in result and len(result["candidates"]) > 0:
                        candidate = result["candidates"][0]
                        if "content" in candidate and "parts" in candidate["content"]:
                            parts = candidate["content"]["parts"]
                            if parts and "text" in parts[0]:
                                response_text = parts[0]["text"]
                                reply.content = response_text  # noqa: F841
                            else:
                                logger.error(f"Google Gemini响应格式异常: {result}")
                                reply.content = "Google Gemini响应格式异常"  # noqa: F841
                                return reply
                        else:
                            logger.error(f"Google Gemini响应格式异常: {result}")
                            reply.content = "Google Gemini响应格式异常"  # noqa: F841
                            return reply
                    else:
                        logger.error(f"Google Gemini响应格式异常: {result}")
                        reply.content = "Google Gemini响应格式异常"  # noqa: F841
                        return reply
                else:
                    error_message = response.text
                    try:
                        error_json = response.json()
                        if "error" in error_json and "message" in error_json["error"]:
                            error_message = error_json["error"]["message"]
                    except:
                        pass
                    
                    logger.error(f"Google Gemini请求失败: {response.status_code}, {error_message}")
                    reply.content = f"Google Gemini接口请求失败: {error_message}"  # noqa: F841
                    return reply
                
                # 保存会话并返回
                self.session_manager.session_reply(reply.content, session_id)
                if self.show_user_prompt:
                    logger.debug(f"[Google Gemini] {query} \n {reply.content}")
                return reply
                
            except Exception as e:
                logger.error(f"Google Gemini接口异常: {e}")
                reply.content = f"Google Gemini接口异常: {e}"  # noqa: F841
                return reply 