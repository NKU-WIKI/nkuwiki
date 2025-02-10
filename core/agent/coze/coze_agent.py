from core.agent import Agent
from core.agent.session_manager import SessionManager
from core.agent.coze.coze_session import CozeSession
from core.bridge.reply import Reply, ReplyType
from core.utils.common.log import logger
from config import conf
import requests
import json
import time
from collections import defaultdict

class CozeBot(Agent):
    def __init__(self):
        super().__init__()
        self.sessions = SessionManager(CozeSession, model=conf().get("model") or "coze-pro")
        self.api_key = conf().get("coze_api_key")
        self.app_id = conf().get("coze_app_id")
        self.api_base = conf().get("coze_api_base", "https://coze.nankai.edu.cn/api/proxy/api/v1")
        self.user_id = conf().get("coze_user_id", "default_user")
        self.max_retries = 3  # 固定重试次数

    def _create_conversation(self, session_id):
        """创建Coze会话"""
        url = f"{self.api_base}/create_conversation"
        headers = {
            "Apikey": self.api_key,
            "AppID": self.app_id,  # 添加AppID到请求头
            "Content-Type": "application/json"
        }
        payload = {
            "AppKey": self.api_key,
            "UserID": self.user_id,
            "Inputs": {},
            "AppID": self.app_id  # 添加缺失的AppID参数
        }
        
        try:
            logger.debug(f"[COZE] 创建会话请求参数: {json.dumps(payload)}")
            response = requests.post(url, headers=headers, json=payload)
            logger.debug(f"[COZE] 创建会话响应: {response.status_code} {response.text}")
            response.raise_for_status()
            return response.json().get("Conversation", {}).get("AppConversationID")
        except requests.exceptions.HTTPError as e:
            logger.error(f"[COZE] API错误: {e.response.text}")
        except Exception as e:
            logger.error(f"[COZE] 创建会话失败: {str(e)}")
        return None


    def _stream_chat_query(self, session, conversation_id):
        """流式对话请求"""
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
            "ResponseMode": "streaming",
            "UserID": self.user_id
        }

        try:
            answer_content = ""      # 主要回答内容
            knowledge_content = ""   # 知识引用部分
            suggestion_content = ""  # 建议问题部分
            knowledge_refs = []
            total_docs = 0
            event_counter = defaultdict(int)
            
            with requests.post(url, headers=headers, json=payload, stream=True, timeout=30) as response:
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
                            logger.error(f"解析JSON失败: {data_line}")
                            continue
                        if event_data.get("event").startswith("message"):
                            chunk = event_data.get("answer", "")
                            if chunk:
                                answer_content += chunk
                        elif event_data.get("event") == "knowledge_retrieve_end":
                            output_list = event_data.get("docs", {}).get("outputList", [])
                            total_docs = len(output_list)
                            max_count = conf().get("max_knowledge_display", 3)
                            max_length = conf().get("max_knowledge_length", 100)
                            # 处理知识引用
                            if output_list:
                                knowledge_content = f"\n\n📃\n找到 {total_docs} 个回答来源，显示{min(total_docs,max_count)}个："
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
            logger.info(f"[COZE] 事件统计: {dict(event_counter)}")
            full_response = answer_content
            if knowledge_content:
                full_response += knowledge_content
            if suggestion_content:
                full_response += suggestion_content
            return full_response
                
        except Exception as e:
            logger.error(f"[COZE] 流式请求失败: {str(e)}")
            raise

    def reply(self, query, context=None):
        retry_count = 0
        max_retries = self.max_retries
        
        while retry_count < max_retries:
            try:
                session_id = context["session_id"]
                session = self.sessions.session_query(query, session_id)
                
                # 创建或获取会话ID
                conversation_id = session.conversation_id or self._create_conversation(session_id)
                if not conversation_id:
                    return Reply(ReplyType.ERROR, "无法创建会话")

                # 流式处理
                full_content = ""
                for chunk in self._stream_chat_query(session, conversation_id):
                    full_content += chunk
                
                # 更新会话
                session.add_response(full_content)
                self.sessions.session_reply(full_content, session_id)
                
                return Reply(ReplyType.TEXT, full_content)
                
            except requests.exceptions.RequestException as e:
                logger.error(f"[COZE] 网络请求异常: {str(e)}")
                retry_count += 1
                time.sleep(2 ** retry_count)  # 指数退避
            except json.JSONDecodeError as e:
                logger.error(f"[COZE] JSON解析失败: {str(e)}")
                return Reply(ReplyType.ERROR, "响应解析错误")
        
        return Reply(ReplyType.ERROR, "请求失败，请稍后再试")