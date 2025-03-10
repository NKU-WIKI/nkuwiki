import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from agent import config,agent_logger,requests,time
base_url = config.get("core.agent.coze.base_url", "")
api_key = config.get("core.agent.coze.api_key", "")
class CozeAgentNew(object):
    def __init__(self, bot_id: str):
        super().__init__()
        self.bot_id = bot_id
        
    def _get_headers(self):
        return {
            'Authorization': f"Bearer {api_key}",
            'Content-Type': 'application/json'
        }   
    
    def reply(self, query):
        conversation_id, chat_id = self.create_chat(query)

        if conversation_id is None or chat_id is None:
            agent_logger.error(f"创建对话失败: {query}")
            return None
              
        status = self.coze_poll_chat_status(conversation_id, chat_id)
        if status != "success":
            agent_logger.error(f"对话状态轮询失败: {conversation_id} {chat_id}")
            return None
            
        messages = self.coze_get_chat_messages(conversation_id, chat_id)
        if not messages:
            agent_logger.error(f"获取对话消息失败: {conversation_id} {chat_id}")
            return None
            
        for message in messages:
            if(message.get("role") == "assistant" and message.get("type") == "answer"):
                return message.get("content")
        
        agent_logger.error(f"未找到助手回复: {conversation_id} {chat_id}")
        return None

    def create_chat(self,content: str):
        # 构建请求URL
        url = f"{base_url}/v3/chat"
        
        # 构建请求头
        headers = self._get_headers()
        
        # 构建请求体
        payload = {
            "bot_id": self.bot_id,
            "user_id": "default_user",
            "stream": False,
            "additional_messages": [
                {
                    "content": content,
                    "content_type": "text",
                    "role": "user",
                    "type": "question"
                }
            ]
        }
        
        try:
            # 发送请求
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            
            response_data = response.json()
            if not response_data:
                agent_logger.error("API返回空响应")
                return None, None
                
            data = response_data.get("data")
            if not data:
                agent_logger.error(f"API响应中没有data字段: {response_data}")
                return None, None
                
            conversation_id = data.get("conversation_id")
            chat_id = data.get("id")
            
            return conversation_id, chat_id
        
        except Exception as e:
            agent_logger.exception(e)
            return None, None

    def coze_poll_chat_status(self, conversation_id: str, chat_id: str, max_retries: int = 3, poll_interval: float = 5):
        """
        轮询检查对话状态
        
        Args:
            conversation_id: 对话ID
            chat_id: 聊天ID
            max_retries: 最大重试次数
            poll_interval: 轮询间隔时间(秒)
            
        Returns:
            对话状态，如果获取失败则返回None
        """
        if not conversation_id or not chat_id:
            agent_logger.error("conversation_id或chat_id为空，无法轮询状态")
            return None
            
        url = f"{base_url}/v3/chat/retrieve?chat_id={chat_id}&conversation_id={conversation_id}"
        headers = self._get_headers()
        
        for attempt in range(max_retries):
            try:
                # 等待一段时间再查询
                time.sleep(poll_interval)
                # 发送请求
                response = requests.get(url, headers=headers)
                response.raise_for_status()
                response_data = response.json()
                if not response_data:
                    agent_logger.error("API返回空响应")
                    continue
                    
                data = response_data.get("data")
                if not data:
                    agent_logger.error(f"API响应中没有data字段: {response_data}")
                    continue
                    
                status = data.get("status")
                agent_logger.debug(f"当前对话状态: {status}, 尝试次数: {attempt+1}/{max_retries}")
                if status in ["completed", "required_action"]:
                    agent_logger.info(f"对话已完成，状态: {status}")
                    return "success"
            except Exception as e:
                agent_logger.exception(e)
                continue
        agent_logger.warning(f"对话状态轮询达到最大次数 {max_retries}，可能未完成")
        return None

    def coze_get_chat_messages(self,conversation_id: str, chat_id: str):
        """
        获取对话消息列表
        
        Args:
            conversation_id: 对话ID
            chat_id: 聊天ID
            
        Returns:
            消息列表，如果获取失败则返回None
        """
        if not conversation_id or not chat_id:
            agent_logger.error("conversation_id或chat_id为空，无法获取消息")
            return None
            
        url = f"{base_url}/v3/chat/message/list?chat_id={chat_id}&conversation_id={conversation_id}"
        headers = self._get_headers()
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            response_data = response.json()
            if not response_data:
                agent_logger.error("API返回空响应")
                return None
                
            data = response_data.get("data")
            if not data:
                agent_logger.error(f"API响应中没有data字段: {response_data}")
                return None
                
            agent_logger.info(f"成功获取对话消息列表，共 {len(data)} 条消息")
            return data
        except Exception as e:
            agent_logger.exception(e)
            return None


