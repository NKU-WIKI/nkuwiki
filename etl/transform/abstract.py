from .__init__ import *
from .__init__ import transform_logger
api_base_url = config.get("core.agent.coze.base_url", "https://api.coze.cn")
api_key = config.get("core.agent.coze.api_key", "")
bot_id = config.get("core.agent.coze.ab_bot_id", "")

def generate_abstract(file_path: str, max_length: int = 300) -> Optional[str]:
    """
    为指定的Markdown文件生成摘要
    
    Args:
        file_path: Markdown文件路径
        max_length: 摘要的最大长度
        
    Returns:
        生成的摘要文本，如果失败则返回None
    """     
    # 检查文件是否为Markdown文件
    if file_path.suffix.lower() not in ['.md', '.markdown']:
        transform_logger.error(f"文件不是Markdown格式: {file_path}")
        return None
    # 读取文件内容
    content = file_path.read_text(encoding='utf-8')
    if not content:
        transform_logger.error(f"文件内容为空: {file_path}")
        return None
    
    conversation_id, chat_id = coze_create_chat(content)
    if conversation_id is None or chat_id is None:
        transform_logger.error(f"创建对话失败，无法生成摘要: {file_path}")
        return None
        
    status = coze_poll_chat_status(conversation_id, chat_id)
    if status != "success":
        transform_logger.error(f"对话状态轮询失败，无法生成摘要: {file_path}")
        return None
        
    messages = coze_get_chat_messages(conversation_id, chat_id)
    if not messages:
        transform_logger.error(f"获取对话消息失败，无法生成摘要: {file_path}")
        return None
        
    for message in messages:
        if(message.get("role") == "assistant" and message.get("type") == "answer"):
            return message.get("content")
    
    transform_logger.error(f"未找到助手回复，无法生成摘要: {file_path}")
    return None

def coze_create_chat(content: str):
    # 构建请求URL
    url = f"{api_base_url}/v3/chat"
    
    # 构建请求头
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    # 构建请求体
    payload = {
        "bot_id": bot_id,
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
            transform_logger.error("API返回空响应")
            return None, None
            
        data = response_data.get("data")
        if not data:
            transform_logger.error(f"API响应中没有data字段: {response_data}")
            return None, None
            
        conversation_id = data.get("conversation_id")
        chat_id = data.get("id")
        
        return conversation_id, chat_id
    
    except Exception as e:
        transform_logger.exception(e)
        return None, None

def coze_poll_chat_status(conversation_id: str, chat_id: str, max_retries: int = 5, poll_interval: float = 20) -> Optional[str]:
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
        transform_logger.error("conversation_id或chat_id为空，无法轮询状态")
        return None
        
    url = f"{api_base_url}/v3/chat/retrieve?chat_id={chat_id}&conversation_id={conversation_id}"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    for attempt in range(max_retries):
        try:
            # 等待一段时间再查询
            time.sleep(poll_interval)
            # 发送请求
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            response_data = response.json()
            if not response_data:
                transform_logger.error("API返回空响应")
                continue
                
            data = response_data.get("data")
            if not data:
                transform_logger.error(f"API响应中没有data字段: {response_data}")
                continue
                
            status = data.get("status")
            transform_logger.debug(f"当前对话状态: {status}, 尝试次数: {attempt+1}/{max_retries}")
            if status in ["completed", "required_action"]:
                transform_logger.info(f"对话已完成，状态: {status}")
                return "success"
        except Exception as e:
            transform_logger.exception(e)
            continue
    transform_logger.warning(f"对话状态轮询达到最大次数 {max_retries}，可能未完成")
    return None

def coze_get_chat_messages(conversation_id: str, chat_id: str) -> Optional[list]:
    """
    获取对话消息列表
    
    Args:
        conversation_id: 对话ID
        chat_id: 聊天ID
        
    Returns:
        消息列表，如果获取失败则返回None
    """
    if not conversation_id or not chat_id:
        transform_logger.error("conversation_id或chat_id为空，无法获取消息")
        return None
        
    url = f"{api_base_url}/v3/chat/message/list?chat_id={chat_id}&conversation_id={conversation_id}"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        response_data = response.json()
        if not response_data:
            transform_logger.error("API返回空响应")
            return None
            
        data = response_data.get("data")
        if not data:
            transform_logger.error(f"API响应中没有data字段: {response_data}")
            return None
            
        transform_logger.info(f"成功获取对话消息列表，共 {len(data)} 条消息")
        return data
    except Exception as e:
        transform_logger.exception(e)
        return None


# 如果作为脚本直接运行
if __name__ == "__main__":
    file_path = Path("D:\\Code\\nkuwiki\\etl\\data\\raw\\wechat\\202303\\周池会开展纪念周恩来总理诞辰周年主题活动弘扬恩来精神做有志青年\\周池会开展纪念周恩来总理诞辰周年主题活动弘扬恩来精神做有志青年.md")
    abstract = generate_abstract(file_path)
    print(abstract)


