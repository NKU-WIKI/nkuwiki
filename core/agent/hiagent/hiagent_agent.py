from core.agent import Agent
from core.agent.session_manager import SessionManager
from core.agent.hiagent.hiagent_session import HiAgentSession
from core.bridge.reply import Reply, ReplyType
from app import App
from config import Config
import requests
import json
import time
from collections import defaultdict

class HiAgentAgent(Agent):
    def __init__(self):
        super().__init__()
        self.config = Config()
        self.sessions = SessionManager(HiAgentSession, model=self.config.get("core.agent.hiagent.model") or "hiagent-pro")
        self.api_key = self.config.get("core.agent.hiagent.api_key")
        self.app_id = self.config.get("core.agent.hiagent.app_id")
        self.api_base = self.config.get("core.agent.hiagent.base_url")
        self.user_id = self.config.get("core.agent.hiagent.user_id", "default_user")
        self.max_retries = 3  

    def _create_conversation(self, session_id):
        """创建HiAgent会话"""
        url = f"{self.api_base}/create_conversation"
        headers = {
            "Apikey": self.api_key,
            "AppID": self.app_id,  
            "Content-Type": "application/json"
        }
        payload = {
            "AppKey": self.api_key,
            "UserID": self.user_id,
            "Inputs": {},
            "AppID": self.app_id  
        }
        
        try:
            # logger.debug(f"[HIAGENT] 创建会话请求参数: {json.dumps(payload)}")
            response = requests.post(url, headers=headers, json=payload)
            # logger.debug(f"[HIAGENT] 创建会话响应: {response.status_code} {response.text}")
            response.raise_for_status()
            App().logger.debug(f"[HIAGENT] 创建会话响应成功: {response.status_code} {response.text}")
            return response.json().get("Conversation", {}).get("AppConversationID")
        except requests.exceptions.HTTPError as e:
            App().logger.exception(f"[HIAGENT] API错误")
        except Exception as e:
            App().logger.exception(f"[HIAGENT] 创建会话失败")
        return None


    def _stream_chat_query(self, session, conversation_id):
        """流式对话请求"""
        mode = "streaming"
        url = f"{self.api_base}/chat_query"
        headers = {
            "Apikey": self.api_key,
            "AppID": self.app_id,
            "Content-Type": "application/json",
            "Accept": "text/event-stream"
        }
        
        payload = {
            "AppKey": self.api_key,
            "AppConversationID": conversation_id,
            "query": session.get_last_query(),
            "ResponseMode": mode,
            "UserID": self.user_id
        }

        try:
            answer_content = ""      # 主要回答内容
            knowledge_content = ""   # 知识引用部分
            suggestion_content = ""  # 建议问题部分
            knowledge_refs = []
            total_docs = 0
            event_counter = defaultdict(int)
            
            with requests.post(url, headers=headers, json=payload, stream=True, timeout=10000) as response:
                response.raise_for_status()
                
                for line in response.iter_lines():
                    if not line:
                        continue
                    line = line.decode('utf-8').strip()
                    if line.startswith("event:"):
                        event_type = line.split(":", 1)[1].strip()
                        event_counter[event_type] += 1
                        continue
                    elif line.startswith("data:data: "):
                        data_line = line[len("data:data: "):]
                        try:
                            event_data = json.loads(data_line)
                        except json.JSONDecodeError:
                            App().logger.exception(f"解析JSON失败")
                            continue
                        if event_data.get("event").startswith("message"):
                            chunk = event_data.get("answer", "")
                            if chunk:
                                if(chunk == '['):
                                    App().logger.debug(f"chunk: {chunk}")
                                    answer_content += "【"
                                elif(chunk == ']'):
                                    answer_content += '】'
                                else:
                                    answer_content += chunk
                        elif event_data.get("event") == "knowledge_retrieve_end":
                            output_list = event_data.get("docs", {}).get("outputList", [])
                            total_docs = len(output_list)
                            max_count = self.config.get("max_knowledge_display", 3)
                            max_length = self.config.get("max_knowledge_length", 100)
                            # 处理知识引用
                            if output_list:
                                knowledge_content = f"\n\n📃找到 {total_docs} 个回答来源，显示{min(total_docs,max_count)}个：\n"
                                for i, doc in enumerate(output_list[:max_count], 1):
                                    content = doc.get("output", "")
                                    if not content:
                                        parts = [f"{k}:{v[:30]}" for k, v in doc.items() 
                                                if isinstance(v, str) and v.strip()]
                                        content = "，".join(parts)
                                    
                                    if len(content) > max_length:
                                        content = content[:max_length-3] + "..."
                                    if content:
                                        knowledge_refs.append(f"{i}. {content}")
                                knowledge_content += "\n".join(knowledge_refs)
                        elif event_data.get("event") == "suggestion":
                            # 处理建议问题
                            suggestions = event_data.get("suggested_questions", [])[:3]
                            if suggestions:
                                suggestion_content = "\n\n💡猜你想问：\n" + "\n".join(suggestions)
            App().logger.debug(f"[HIAGENT] 成功接收流式响应，事件统计: {dict(event_counter)}")
            full_response = answer_content
            if knowledge_content:
                full_response += knowledge_content
            if suggestion_content:
                full_response += suggestion_content
            return full_response
                
        except Exception as e:
            App().logger.exception(f"[HIAGENT] 流式请求失败")
            raise

    def _blocking_chat_query(self, session, conversation_id):
        """流式对话请求"""
        mode = "blocking"
        url = f"{self.api_base}/chat_query"
        headers = {
            "Apikey": self.api_key,
            "AppID": self.app_id,
            "Content-Type": "application/json",
            "Accept": "text/event-stream"
        }
        
        payload = {
            "AppKey": self.api_key,
            "AppConversationID": conversation_id,
            "query": session.get_last_query(),
            "ResponseMode": mode,
            "UserID": self.user_id
        }

        try:
            answer_content = ""      # 主要回答内容
            # knowledge_content = ""   # 知识引用部分
            # suggestion_content = ""  # 建议问题部分
            # knowledge_refs = []
            # total_docs = 0
            event_counter = defaultdict(int)
            
            with requests.post(url, headers=headers, json=payload, stream=True, timeout=15000) as response:
                response.raise_for_status()
                
                for line in response.iter_lines():
                    if not line:
                        continue
                    line = line.decode('utf-8').strip()
                    if line.startswith("event:"):
                        event_type = line.split(":", 1)[1].strip()
                        event_counter[event_type] += 1
                        continue
                    elif line.startswith("data:data: "):
                        data_line = line[len("data:data: "):]
                        try:
                            event_data = json.loads(data_line)
                        except json.JSONDecodeError:
                            App().logger.exception(f"解析JSON失败")
                            continue
                        if event_data.get("event").startswith("message"):
                            answer_content = event_data.get("answer", "")
                                
            App().logger.debug(f"[HIAGENT] 成功接收块式响应，事件统计: {dict(event_counter)}")
            full_response = answer_content
            # if knowledge_content:
            #     full_response += knowledge_content
            # if suggestion_content:
            #     full_response += suggestion_content
            return full_response
        except Exception as e:
            App().logger.exception(f"[HIAGENT] 块式请求失败")
            raise

    def reply(self, query, context=None):
        # 新增代码开始
        if context and context.get("reply"):
            App().logger.debug("[HIAGENT] 检测到插件回复，直接返回")
            return context["reply"]
        # 新增代码结束
        retry_count = 0
        max_retries = self.max_retries
        while retry_count < max_retries:
            try:
                session_id = context["session_id"]
                session = self.sessions.session_query(query, session_id)
                # 创建或获取会话ID（修改部分）
                if not session.conversation_id:
                    # 首次创建会话
                    conversation_id = self._create_conversation(session_id)
                    if not conversation_id:
                        return Reply(ReplyType.ERROR, "无法创建会话")
                    # 保存会话ID到session对象
                    session.conversation_id = conversation_id
                    # logger.debug(f"[HIAGENT] 创建新会话ID: {conversation_id}")
                else:
                    # 使用已有会话ID
                    conversation_id = session.conversation_id
                    App().logger.debug(f"[HIAGENT] 使用现有会话ID: {conversation_id}")

                if(self.config.get("response_mode") == "streaming"):
                    full_content = self._stream_chat_query(session, conversation_id)
                else:
                    full_content = self._blocking_chat_query(session, conversation_id)
                
                # 更新会话
                session.add_response(full_content)
                self.sessions.session_reply(full_content, session_id)
                
                return Reply(ReplyType.TEXT, full_content)
                
            except requests.exceptions.RequestException as e:
                App().logger.exception(f"[HIAGENT] 网络请求异常")
                retry_count += 1
                time.sleep(2 ** retry_count)  # 指数退避
            except json.JSONDecodeError as e:
                App().logger.exception(f"[HIAGENT] JSON解析失败")
                return Reply(ReplyType.ERROR, "响应解析错误")
        
        return Reply(ReplyType.ERROR, "请求失败，请稍后再试")