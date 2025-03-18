"""
Dify AI智能体实现
"""
import json
import threading
import requests
from loguru import logger
from config import Config
from core.bridge.reply import Reply, ReplyType
from core.bridge.context import Context
from core.agent.agent import Agent
from core.utils.common import singleton_decorator, ExpiredDict


class DifySession:
    def __init__(self, session_id: str, user: str, conversation_id: str = ''):
        self.__session_id = session_id
        self.__user = user
        self.__conversation_id = conversation_id
        self.__user_message_counter = 0
        self.config = Config()

    def get_session_id(self):
        return self.__session_id

    def get_user(self):
        return self.__user

    def get_conversation_id(self):
        return self.__conversation_id

    def set_conversation_id(self, conversation_id):
        self.__conversation_id = conversation_id

    def count_user_message(self):
        """
        计数用户消息并在达到最大值时重置会话
        """
        if self.__user_message_counter >= self.config.get("core.agent.dify.conversation_max_messages", 5):
            self.__user_message_counter = 0
            # 注意: Dify目前不支持设置历史消息长度，暂时使用超过指定条数清空会话的策略
            self.__conversation_id = ''

        self.__user_message_counter += 1


class DifySessionManager:
    def __init__(self):
        self.config = Config()
        if self.config.get("expires_in_seconds"):
            self.sessions = ExpiredDict(self.config.get("expires_in_seconds"))
        else:
            self.sessions = dict()

    def _build_session(self, session_id: str, user: str):
        """
        如果session_id不在sessions中，创建一个新的session并添加到sessions中
        """
        if session_id is None:
            return DifySession(session_id, user)

        if session_id not in self.sessions:
            self.sessions[session_id] = DifySession(session_id, user)
        session = self.sessions[session_id]
        return session

    def get_session(self, session_id, user):
        """获取会话实例"""
        session = self._build_session(session_id, user)
        return session

    def clear_session(self, session_id):
        """清除指定会话"""
        if session_id in self.sessions:
            del self.sessions[session_id]

    def clear_all_session(self):
        """清除所有会话"""
        self.sessions.clear()


@singleton_decorator
class DifyAgent(Agent):
    def __init__(self):
        # 创建配置实例
        self.config = Config()
        
        # 获取配置
        self.api_key = self.config.get("core.agent.dify.api_key")
        self.api_base = self.config.get("core.agent.dify.api_base")
        
        # 代理配置
        self.proxy = self.config.get("proxy")
        
        # 会话管理
        self.sessions = DifySessionManager()
        
    def reply(self, query, context: Context = None) -> Reply:
        """
        回复消息
        :param query: 用户消息
        :param context: 上下文
        :return: 回复
        """
        if context.type == Context.TYPE_TEXT or context.type == Context.TYPE_IMAGE_CREATE:
            # 处理创建图片的请求
            if context.type == Context.TYPE_IMAGE_CREATE:
                prefix = self.config.get('image_create_prefix', ['画'])[0]
                query = prefix + query
                
            logger.debug(f"[Dify] 接收到请求: {query}")
            
            # 获取会话ID
            session_id = context.get("session_id")
            
            # 从上下文获取用户信息
            channel_type = self.config.get("channel_type")
            user = self._get_user_from_context(context, channel_type)
            
            if not user:
                return Reply(ReplyType.ERROR, 
                            f"不支持的渠道类型: {channel_type}，Dify目前仅支持wx, wechatcom_app, wechatmp, wechatmp_service, dingtalk等渠道")
            
            logger.debug(f"[Dify] dify_user={user}")
            user = user if user else "default"  # 防止用户名为None
            
            # 获取会话
            session = self.sessions.get_session(session_id, user)
            logger.debug(f"[Dify] session={session} query={query}")
            
            # 调用API获取回复
            reply, err = self._reply(query, session, context)
            if err is not None:
                logger.error(f"[Dify] 回复出错: {err}")
                return Reply(ReplyType.TEXT, "我暂时遇到了一些问题，请您稍后重试~")
            
            return reply
        else:
            return Reply(ReplyType.ERROR, f"不支持处理{context.type}类型的消息")
    
    def _get_user_from_context(self, context, channel_type):
        """从上下文获取用户信息"""
        user = None
        if channel_type == "wx":
            user = context.get("msg", {}).other_user_nickname if context.get("msg") else "default"
        elif channel_type in ["wechatcom_app", "wechatmp", "wechatmp_service", "wechatcom_service", "wework", "dingtalk"]:
            user = context.get("msg", {}).other_user_id if context.get("msg") else "default"
        return user
            
    def _get_api_base_url(self):
        """获取API基础URL"""
        return self.api_base

    def _get_headers(self):
        """获取请求头"""
        return {
            'Authorization': f"Bearer {self.api_key}"
        }

    def _get_payload(self, query, session: DifySession, response_mode):
        """构建请求载荷"""
        return {
            'inputs': {},
            "query": query,
            "response_mode": response_mode,
            "conversation_id": session.get_conversation_id(),
            "user": session.get_user()
        }
        
    def _reply(self, query: str, session: DifySession, context: Context):
        """处理回复逻辑"""
        try:
            # 计数用户消息
            session.count_user_message()
            
            # 根据配置的应用类型选择处理方式
            dify_app_type = self.config.get('core.agent.dify.app_type', 'chatbot')
            if dify_app_type == 'chatbot':
                return self._handle_chatbot(query, session)
            elif dify_app_type == 'agent':
                return self._handle_agent(query, session, context)
            elif dify_app_type == 'workflow':
                return self._handle_workflow(query, session)
            else:
                return None, "dify_app_type必须是agent、chatbot或workflow"

        except Exception as e:
            error_info = f"[Dify] 异常: {e}"
            logger.exception(error_info)
            return None, error_info

    def _handle_chatbot(self, query: str, session: DifySession):
        """处理聊天机器人模式"""
        base_url = self._get_api_base_url()
        chat_url = f'{base_url}/chat-messages'
        headers = self._get_headers()
        response_mode = 'blocking'
        payload = self._get_payload(query, session, response_mode)
        
        response = requests.post(chat_url, headers=headers, json=payload)
        if response.status_code != 200:
            error_info = f"[Dify] 请求失败: 状态码={response.status_code}, 响应={response.text}"
            logger.warning(error_info)
            return None, error_info
            
        rsp_data = response.json()
        logger.debug(f"[Dify] 使用量: {rsp_data.get('metadata', {}).get('usage', 0)}")
        
        # 创建回复
        reply = Reply(ReplyType.TEXT, rsp_data['answer'])
        
        # 设置dify conversation_id, 依靠dify管理上下文
        if session.get_conversation_id() == '':
            session.set_conversation_id(rsp_data['conversation_id'])
            
        return reply, None

    def _handle_agent(self, query: str, session: DifySession, context: Context):
        """处理智能体模式"""
        base_url = self._get_api_base_url()
        chat_url = f'{base_url}/chat-messages'
        headers = self._get_headers()
        response_mode = 'streaming'
        payload = self._get_payload(query, session, response_mode)
        
        response = requests.post(chat_url, headers=headers, json=payload)
        if response.status_code != 200:
            error_info = f"[Dify] 请求失败: 状态码={response.status_code}, 响应={response.text}"
            logger.warning(error_info)
            return None, error_info
            
        msgs, conversation_id = self._handle_sse_response(response)
        channel = context.get("channel")
        is_group = context.get("isgroup", False)
        
        # 处理中间消息
        for msg in msgs[:-1]:
            if msg['type'] == 'agent_message':
                if is_group:
                    at_prefix = "@" + context.get("msg", {}).actual_user_nickname + "\n"
                    msg['content'] = at_prefix + msg['content']
                reply = Reply(ReplyType.TEXT, msg['content'])
                channel.send(reply, context)
            elif msg['type'] == 'message_file':
                url = self._fill_file_base_url(msg['content']['url'])
                reply = Reply(ReplyType.IMAGE_URL, url)
                thread = threading.Thread(target=channel.send, args=(reply, context))
                thread.start()
        
        # 处理最后一条消息
        final_msg = msgs[-1]
        reply = None
        if final_msg['type'] == 'agent_message':
            reply = Reply(ReplyType.TEXT, final_msg['content'])
        elif final_msg['type'] == 'message_file':
            url = self._fill_file_base_url(final_msg['content']['url'])
            reply = Reply(ReplyType.IMAGE_URL, url)
        
        # 设置dify conversation_id
        if session.get_conversation_id() == '':
            session.set_conversation_id(conversation_id)
            
        return reply, None

    def _handle_workflow(self, query: str, session: DifySession):
        """处理工作流模式"""
        base_url = self._get_api_base_url()
        workflow_url = f'{base_url}/workflows/run'
        headers = self._get_headers()
        payload = self._get_workflow_payload(query, session)
        
        response = requests.post(workflow_url, headers=headers, json=payload)
        if response.status_code != 200:
            error_info = f"[Dify] 请求失败: 状态码={response.status_code}, 响应={response.text}"
            logger.warning(error_info)
            return None, error_info
            
        rsp_data = response.json()
        reply = Reply(ReplyType.TEXT, rsp_data['data']['outputs']['text'])
        return reply, None

    def _fill_file_base_url(self, url: str):
        """补全文件URL"""
        if url.startswith("https://") or url.startswith("http://"):
            return url
        # 补全文件base url, 默认使用去掉"/v1"的dify api base url
        return self._get_file_base_url() + url

    def _get_file_base_url(self) -> str:
        """获取文件基础URL"""
        return self._get_api_base_url().replace("/v1", "")

    def _get_workflow_payload(self, query, session: DifySession):
        """获取工作流请求载荷"""
        return {
            'inputs': {
                "query": query
            },
            "response_mode": "blocking",
            "user": session.get_user()
        }

    def _parse_sse_event(self, event_str):
        """解析SSE事件字符串"""
        event_prefix = "data: "
        if not event_str.startswith(event_prefix):
            return None
            
        trimmed_event_str = event_str[len(event_prefix):]

        # 检查是否为有效的JSON字符串
        if trimmed_event_str:
            try:
                event = json.loads(trimmed_event_str)
                return event
            except json.JSONDecodeError:
                logger.error(f"无法解析SSE事件: {trimmed_event_str}")
                return None
        else:
            logger.warning("接收到空的SSE事件")
            return None

    def _handle_sse_response(self, response: requests.Response):
        """处理SSE响应流"""
        events = []
        for line in response.iter_lines():
            if line:
                decoded_line = line.decode('utf-8')
                event = self._parse_sse_event(decoded_line)
                if event:
                    events.append(event)

        merged_message = []
        accumulated_agent_message = ''
        conversation_id = None
        
        for event in events:
            event_name = event['event']
            if event_name == 'agent_message' or event_name == 'message':
                accumulated_agent_message += event['answer']
                logger.debug(f"[Dify] 累积消息: {accumulated_agent_message}")
                # 保存conversation_id
                if not conversation_id:
                    conversation_id = event['conversation_id']
            elif event_name == 'agent_thought':
                self._append_agent_message(accumulated_agent_message, merged_message)
                accumulated_agent_message = ''
                logger.debug(f"[Dify] 智能体思考: {event}")
            elif event_name == 'message_file':
                self._append_agent_message(accumulated_agent_message, merged_message)
                accumulated_agent_message = ''
                self._append_message_file(event, merged_message)
            elif event_name == 'message_replace':
                # TODO: 处理消息替换
                pass
            elif event_name == 'error':
                logger.error(f"[Dify] 错误: {event}")
                raise Exception(event)
            elif event_name == 'message_end':
                self._append_agent_message(accumulated_agent_message, merged_message)
                logger.debug(f"[Dify] 消息结束, 使用量: {event['metadata']['usage']}")
                break
            else:
                logger.warning(f"[Dify] 未知事件: {event}")

        if not conversation_id:
            raise Exception("未找到conversation_id")

        return merged_message, conversation_id

    def _append_agent_message(self, accumulated_agent_message, merged_message):
        """添加智能体消息到合并消息列表"""
        if accumulated_agent_message:
            merged_message.append({
                'type': 'agent_message',
                'content': accumulated_agent_message,
            })

    def _append_message_file(self, event: dict, merged_message: list):
        """添加文件消息到合并消息列表"""
        if event.get('type') != 'image':
            logger.warning(f"[Dify] 不支持的文件类型: {event}")
        merged_message.append({
            'type': 'message_file',
            'content': event,
        }) 