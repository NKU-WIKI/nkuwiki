"""
MiniMax AI智能体实现
"""
import time
import requests
from loguru import logger
from config import Config
from core.bridge.reply import Reply, ReplyType
from core.bridge.context import Context
from core.agent.agent import Agent
from core.agent.session_manager import Session, SessionManager
from core.utils.common import singleton_decorator


class MinimaxSession(Session):
    def __init__(self, session_id, system_prompt=None, model="abab6.5"):
        super().__init__(session_id, system_prompt)
        self.config = Config()
        self.model = model
        self.max_tokens = self.config.get("core.agent.minimax.max_tokens", 4000)
        self.reset()

    def add_query(self, query):
        """添加用户查询消息"""
        user_item = {"sender_type": "USER", "sender_name": self.session_id, "text": query}
        self.messages.append(user_item)

    def add_reply(self, reply):
        """添加智能体回复消息"""
        assistant_item = {"sender_type": "BOT", "sender_name": "MM智能助理", "text": reply}
        self.messages.append(assistant_item)

    def discard_exceeding(self, max_tokens=None, cur_tokens=None):
        if max_tokens is None:
            max_tokens = self.max_tokens
        if max_tokens <= 0:
            return 0

        precise = True
        try:
            cur_tokens = self.calc_tokens()
        except Exception as e:
            precise = False
            if cur_tokens is None:
                raise e
            logger.debug(f"计算token时出现异常: {e}")
            
        while cur_tokens > max_tokens:
            if len(self.messages) > 2:
                self.messages.pop(1)
            elif len(self.messages) == 2 and self.messages[1]["sender_type"] == "BOT":
                self.messages.pop(1)
                if precise:
                    cur_tokens = self.calc_tokens()
                else:
                    cur_tokens = cur_tokens - max_tokens
                break
            elif len(self.messages) == 2 and self.messages[1]["sender_type"] == "USER":
                logger.warning(f"用户消息超出最大token限制. 总token数={cur_tokens}")
                break
            else:
                logger.debug(f"max_tokens={max_tokens}, total_tokens={cur_tokens}, 消息数={len(self.messages)}")
                break
                
            if precise:
                cur_tokens = self.calc_tokens()
            else:
                cur_tokens = cur_tokens - max_tokens
                
        return cur_tokens

    def calc_tokens(self):
        return self._num_tokens_from_messages(self.messages)
        
    def _num_tokens_from_messages(self, messages):
        """简单估算token数量
        
        对于中文文本来说，1个token通常对应一个汉字
        对于英文文本来说，1个token通常对应3至4个字母或1个单词
        """
        tokens = 0
        for msg in messages:
            tokens += len(msg["text"])
        return tokens


class MinimaxSessionManager(SessionManager):
    def __init__(self):
        super().__init__(MinimaxSession)
        
    def session_query(self, query, session_id):
        """重写session_query方法以适配MiniMax的消息格式"""
        session = self.build_session(session_id)
        session.add_query(query)
        try:
            max_tokens = self.config.get("core.agent.minimax.max_tokens", 1000)
            total_tokens = session.discard_exceeding(max_tokens, None)
            logger.debug(f"prompt tokens used={total_tokens}")
        except Exception as e:
            logger.exception(f"计算token时出现异常: {e}")
        return session

    def session_reply(self, reply, session_id, total_tokens=None):
        """重写session_reply方法以适配MiniMax的消息格式"""
        session = self.build_session(session_id)
        session.add_reply(reply)
        try:
            max_tokens = self.config.get("core.agent.minimax.max_tokens", 1000)
            tokens_cnt = session.discard_exceeding(max_tokens, total_tokens)
            logger.debug(f"raw total_tokens={total_tokens}, savesession tokens={tokens_cnt}")
        except Exception as e:
            logger.exception(f"计算token时出现异常: {e}")
        return session


@singleton_decorator
class MinimaxAgent(Agent):
    def __init__(self):
        # 创建配置实例
        self.config = Config()
        
        # 获取配置
        self.api_key = self.config.get("core.agent.minimax.api_key")
        self.group_id = self.config.get("core.agent.minimax.group_id")
        
        # 获取模型配置
        self.model = self.config.get("core.agent.minimax.model", "abab6.5")
        
        # 初始化参数
        self.temperature = self.config.get("core.agent.minimax.temperature", 0.3)
        self.top_p = self.config.get("core.agent.minimax.top_p", 0.95)
        
        # API基础URL
        self.api_base = self.config.get("core.agent.minimax.base_url", 
                                        f"https://api.minimax.chat/v1/text/chatcompletion_pro?GroupId={self.group_id}")
        
        # 会话管理
        self.session_manager = MinimaxSessionManager()
        
        # MiniMax特有的请求体设置
        self.request_body = {
            "model": self.model,
            "tokens_to_generate": 2048,
            "reply_constraints": {"sender_type": "BOT", "sender_name": "MM智能助理"},
            "messages": [],
            "bot_setting": [
                {
                    "bot_name": "MM智能助理",
                    "content": "MM智能助理是一款由MiniMax自研的，没有调用其他产品的接口的大型语言模型。MiniMax是一家中国科技公司，一直致力于进行大模型相关的研究。",
                }
            ],
        }
        
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
            logger.debug(f"[MiniMax] 接收到文本请求: {query}")
            
            # 检查API参数是否已配置
            if not self.api_key or not self.group_id:
                return Reply(ReplyType.ERROR, "请先配置MiniMax API参数")
            
            # 获取会话
            session_id = context.get("session_id")
            
            # 处理清除记忆等特殊命令
            clear_memory_commands = self.config.get("clear_memory_commands", ["#清除记忆"])
            if query in clear_memory_commands:
                self.session_manager.clear_session(session_id)
                return Reply(ReplyType.INFO, "记忆已清除")
            elif query == "#清除所有":
                self.session_manager.clear_all_session()
                return Reply(ReplyType.INFO, "所有人记忆已清除")
            
            # 获取会话
            session = self.session_manager.session_query(query, session_id)
            
            # 根据上下文获取特定模型
            model = context.get("minimax_model")
            args = {
                "model": model if model else self.model,
                "temperature": self.temperature,
                "top_p": self.top_p
            }
            
            # 调用API获取回复
            reply_content = self._reply_text(session, args)
            
            # 处理回复
            logger.debug(
                f"[MiniMax] 会话ID={session_id}, 内容={reply_content['content']}, tokens={reply_content['completion_tokens']}"
            )
            
            # 根据回复内容返回不同类型的响应
            if reply_content["completion_tokens"] == 0 and len(reply_content["content"]) > 0:
                return Reply(ReplyType.ERROR, reply_content["content"])
            elif reply_content["completion_tokens"] > 0:
                self.session_manager.session_reply(reply_content["content"], session_id, reply_content["total_tokens"])
                if self.show_user_prompt:
                    logger.debug(f"[MiniMax] {query} \n {reply_content['content']}")
                return Reply(ReplyType.TEXT, reply_content["content"])
            else:
                logger.error(f"[MiniMax] 回复使用了0个token: {reply_content}")
                return Reply(ReplyType.ERROR, reply_content["content"])
        else:
            return Reply(ReplyType.ERROR, f"不支持处理{context.type}类型的消息")

    def _reply_text(self, session, args=None, retry_count=0):
        """调用MiniMax API获取回复"""
        try:
            # 设置请求头
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            # 构建请求体
            self.request_body["messages"] = session.messages
            if args and "model" in args:
                self.request_body["model"] = args["model"]
            
            # 发送请求
            logger.debug(f"[MiniMax] 请求参数: {self.request_body}")
            response = requests.post(
                self.api_base,
                headers=headers,
                json=self.request_body
            )
            
            # 处理响应
            if response.status_code == 200:
                result = response.json()
                return {
                    "total_tokens": result["usage"]["total_tokens"],
                    "completion_tokens": result["usage"]["total_tokens"],  # MiniMax API返回格式不同，使用total_tokens
                    "content": result["reply"]  # MiniMax API返回格式使用reply字段
                }
            else:
                # 处理错误
                result = response.json()
                error = result.get("error", {})
                logger.error(f"[MiniMax] 请求失败: 状态码={response.status_code}, "
                            f"错误信息={error.get('message')}, 类型={error.get('type')}")

                # 默认回复
                result = {"completion_tokens": 0, "content": "提问太快啦，请休息一下再问我吧"}
                
                # 根据错误类型决定是否重试
                need_retry = False
                if response.status_code >= 500:
                    # 服务器错误，需要重试
                    logger.warning(f"[MiniMax] 进行第{retry_count+1}次重试")
                    need_retry = retry_count < 2
                elif response.status_code == 401:
                    result["content"] = "授权失败，请检查API Key是否正确"
                elif response.status_code == 429:
                    result["content"] = "请求过于频繁，请稍后再试"
                    need_retry = retry_count < 2
                
                # 执行重试
                if need_retry:
                    time.sleep(3)
                    return self._reply_text(session, args, retry_count + 1)
                else:
                    return result
                    
        except Exception as e:
            logger.exception(f"[MiniMax] 发生异常: {e}")
            need_retry = retry_count < 2
            result = {"completion_tokens": 0, "content": "我现在有点累了，等会再来吧"}
            
            if need_retry:
                time.sleep(3)
                return self._reply_text(session, args, retry_count + 1)
            else:
                return result 