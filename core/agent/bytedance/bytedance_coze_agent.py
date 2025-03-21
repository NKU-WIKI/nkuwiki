"""
字节跳动Coze智能体实现
"""
import re
import time  # noqa: F401
import requests
from typing import List, Tuple  # noqa: F401
from requests import Response
from loguru import logger  # noqa: F401
from config import Config
from core.bridge.reply import Reply, ReplyType
from core.bridge.context import Context
from core.agent.agent import Agent
from core.agent.session_manager import Session, SessionManager
from core.utils.common import singleton_decorator


class ByteDanceCozeSession(Session):
    def __init__(self, session_id, system_prompt=None):
        super().__init__(session_id, system_prompt)
        self.config = Config()
        self.max_tokens = self.config.get("core.agent.bytedance.coze.max_tokens", 4000)
        self.reset()

    def reset(self):
        system_content = self.system_prompt
        self.messages = []
        if system_content:
            system_item = {"role": "system", "content": system_content}
            self.messages.append(system_item)
    
    def discard_exceeding(self, max_tokens=None, cur_tokens=None):
        if max_tokens is None:
            max_tokens = self.max_tokens
        if max_tokens <= 0:
            return 0

        # 根据约束，计算要保留的消息数量
        num_of_tokens = 0
        for idx, message in enumerate(self.messages[::-1]):
            content = message.get("content", "")
            num_of_tokens += len(content) * 4  # 简单字数估算
            if num_of_tokens > max_tokens and idx > 0:
                self.messages = self.messages[-(idx):]
                break
        return num_of_tokens

    def calc_tokens(self):
        num_of_tokens = 0
        for message in self.messages:
            content = message.get("content", "")
            num_of_tokens += len(content) * 4  # 简单字数估算
        return num_of_tokens


class ByteDanceCozeSessionManager(SessionManager):
    def __init__(self):
        super().__init__(ByteDanceCozeSession)


@singleton_decorator
class ByteDanceCozeAgent(Agent):
    def __init__(self):
        # 创建配置实例
        self.config = Config()
        
        # 获取配置
        self.api_key = self.config.get("core.agent.bytedance.coze.api_key")
        self.bot_id = self.config.get("core.agent.bytedance.coze.bot_id")
        
        # API基础URL
        self.api_base = self.config.get("core.agent.bytedance.coze.api_base", "https://api.coze.cn/open_api/v2")
        
        # 会话管理
        self.session_manager = ByteDanceCozeSessionManager()
        
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
            logger.debug(f"[Coze] 接收到文本请求: {query}")
            
            # 检查API参数是否已配置
            if not self.api_key or not self.bot_id:
                return Reply(ReplyType.ERROR, "请先配置Coze API参数")
            
            # 获取会话
            session_id = context.get("session_id")
            session = self.session_manager.session_query(query, session_id)
            
            # 调用API获取回复
            reply_content, err = self._reply_text(session_id, session)
            if err is not None:
                logger.error(f"[Coze] 回复出错: {err}")
                return Reply(ReplyType.ERROR, "我暂时遇到了一些问题，请您稍后重试~")
            
            # 记录会话信息
            logger.debug(
                f"[Coze] 会话ID={session_id}, 内容={reply_content['content']}, tokens={reply_content['completion_tokens']}"
            )
            
            # 保存会话
            self.session_manager.session_reply(reply_content["content"], session_id, reply_content["total_tokens"])
            
            # 处理回复内容
            response = reply_content["content"]
            
            # 提取图片URL
            image_url = self._extract_markdown_image_url(response)
            url = image_url if image_url else self._has_url(response)
            
            # 清理Markdown格式
            result = self._remove_markdown(response)
            
            # 如果包含URL，返回图片
            if url:
                return Reply(ReplyType.IMAGE_URL, url)
            # 否则返回纯文本
            return Reply(ReplyType.TEXT, result)
        else:
            return Reply(ReplyType.ERROR, f"不支持处理{context.type}类型的消息")

    def _get_headers(self):
        """获取请求头"""
        return {
            'Authorization': f"Bearer {self.api_key}"
        }

    def _get_payload(self, user: str, query: str, chat_history: List[dict]):
        """构建请求载荷"""
        return {
            'bot_id': self.bot_id,
            "user": user,
            "query": query,
            "chat_history": chat_history,
            "stream": False
        }

    def _reply_text(self, session_id: str, session, retry_count=0):
        """发送请求并获取回复"""
        try:
            # 转换消息格式
            query, chat_history = self._convert_messages_format(session.messages)
            
            # 请求URL和参数
            chat_url = f'{self.api_base}/chat'
            headers = self._get_headers()
            payload = self._get_payload(session_id, query, chat_history)
            
            # 发送请求
            response = requests.post(chat_url, headers=headers, json=payload)
            if response.status_code != 200:
                error_info = f"[Coze] 请求失败: 状态码={response.status_code}, 响应={response.text}"
                logger.warning(error_info)
                return None, error_info
            
            # 解析回复
            answer, err = self._get_completion_content(response)
            if err is not None:
                return None, err
            
            # 计算token数量
            completion_tokens, total_tokens = self._calc_tokens(session.messages, answer)
            
            return {
                "total_tokens": total_tokens,
                "completion_tokens": completion_tokens,
                "content": answer
            }, None
            
        except Exception as e:
            # 重试逻辑
            if retry_count < 2:
                time.sleep(3)
                logger.warning(f"[Coze] 异常: {repr(e)} 第{retry_count + 1}次重试")
                return self._reply_text(session_id, session, retry_count + 1)
            else:
                return None, f"[Coze] 异常: {repr(e)} 超过最大重试次数"

    def _convert_messages_format(self, messages) -> Tuple[str, List[dict]]:
        """转换消息格式为Coze API需要的格式"""
        chat_history = []
        for message in messages:
            role = message.get('role')
            if role == 'user':
                content = message.get('content')
                chat_history.append({"role":"user", "content": content, "content_type":"text"})
            elif role == 'assistant':
                content = message.get('content')
                chat_history.append({"role":"assistant", "type":"answer", "content": content, "content_type":"text"})
            elif role == 'system':
                # 系统消息暂不处理
                pass
                
        # 提取最后一条用户消息作为查询
        user_message = chat_history.pop()
        if user_message.get('role') != 'user' or user_message.get('content', '') == '':
            raise Exception('没有有效的用户消息')
            
        query = user_message.get('content')
        logger.debug(f"[Coze] 转换后的消息历史: {chat_history}")
        logger.debug(f"[Coze] 用户查询: {query}")
        
        return query, chat_history

    def _get_completion_content(self, response: Response):
        """从响应中提取回复内容"""
        json_response = response.json()
        if json_response['msg'] != 'success':
            return None, f"[Coze] 错误: {json_response['msg']}"
            
        answer = None
        for message in json_response['messages']:
            if message.get('type') == 'answer':
                answer = message.get('content')
                break
                
        if not answer:
            return None, "[Coze] 错误: 回复为空"
            
        return answer, None

    def _calc_tokens(self, messages, answer):
        """简单估算token数量"""
        completion_tokens = len(answer)
        prompt_tokens = 0
        for message in messages:
            prompt_tokens += len(message["content"])
        return completion_tokens, prompt_tokens + completion_tokens

    def _remove_markdown(self, text):
        """移除Markdown格式"""
        # 替换Markdown的粗体标记
        text = text.replace("**", "")
        # 替换Markdown的标题标记
        text = text.replace("### ", "").replace("## ", "").replace("# ", "")
        # 去除链接外部括号
        text = re.sub(r'\((https?://[^\s\)]+)\)', r'\1', text)
        text = re.sub(r'\[(https?://[^\s\]]+)\]', r'\1', text)
        return text

    def _extract_markdown_image_url(self, content):
        """提取包含s.coze.cn域名的图片URL"""
        coze_image_pattern = r'(https://s\.coze\.cn[^\s\)]+)'
        image_url = re.search(coze_image_pattern, content)
        return image_url.group(1) if image_url else None

    def _has_url(self, content):
        """检测内容是否包含URL"""
        # 优先提取Coze图片URL
        image_url = self._extract_markdown_image_url(content)
        if image_url:
            return image_url
        
        # 匹配普通URL
        url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        url = re.search(url_pattern, content)
        return url.group() if url else None 