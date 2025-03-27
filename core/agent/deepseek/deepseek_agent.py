"""
DeepSeek AI智能体实现
"""
import time
import requests
from core.utils.logger import register_logger
logger = register_logger("core.agent.deepseek")
from config import Config
from core.bridge.reply import Reply, ReplyType
from core.bridge.context import Context
from core.agent.agent import Agent
from core.agent.session_manager import Session, SessionManager
from core.utils import singleton_decorator


class DeepSeekSession(Session):
    def __init__(self, session_id, system_prompt=None, model="deepseek-chat"):
        super().__init__(session_id, system_prompt)
        self.config = Config()
        self.model = model
        self.max_tokens = self.config.get("core.agent.deepseek.max_tokens", 4000)
        self.reset()

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
            elif len(self.messages) == 2 and self.messages[1]["role"] == "assistant":
                self.messages.pop(1)
                if precise:
                    cur_tokens = self.calc_tokens()
                else:
                    cur_tokens = cur_tokens - max_tokens
                break
            elif len(self.messages) == 2 and self.messages[1]["role"] == "user":
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
        """简单估算token数量"""
        tokens = 0
        for msg in messages:
            tokens += len(msg["content"]) * 4  # 简单估算
        return tokens


class DeepSeekSessionManager(SessionManager):
    def __init__(self):
        super().__init__(DeepSeekSession)


@singleton_decorator
class DeepSeekAgent(Agent):
    def __init__(self):
        # 创建配置实例
        self.config = Config()
        
        # 获取配置
        self.api_key = self.config.get("core.agent.deepseek.api_key")
        
        # 获取模型配置
        self.model = self.config.get("core.agent.deepseek.model", "deepseek-chat")
        
        # 初始化参数
        self.temperature = self.config.get("core.agent.deepseek.temperature", 0.3)
        self.top_p = self.config.get("core.agent.deepseek.top_p", 1.0)
        
        # API基础URL
        self.api_base = self.config.get("core.agent.deepseek.base_url", "https://api.deepseek.com/v1/chat/completions")
        
        # 会话管理
        self.session_manager = DeepSeekSessionManager()
        
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
            logger.debug(f"[DeepSeek] 接收到文本请求: {query}")
            
            # 检查API参数是否已配置
            if not self.api_key:
                return Reply(ReplyType.ERROR, "请先配置DeepSeek API参数")
            
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
            model = context.get("deepseek_model")
            args = {
                "model": model if model else self.model,
                "temperature": self.temperature,
                "top_p": self.top_p
            }
            
            # 调用API获取回复
            reply_content = self._reply_text(session, args)
            
            # 处理回复
            logger.debug(
                f"[DeepSeek] 会话ID={session_id}, 内容={reply_content['content']}, tokens={reply_content['completion_tokens']}"
            )
            
            # 根据回复内容返回不同类型的响应
            if reply_content["completion_tokens"] == 0 and len(reply_content["content"]) > 0:
                return Reply(ReplyType.ERROR, reply_content["content"])
            elif reply_content["completion_tokens"] > 0:
                self.session_manager.session_reply(reply_content["content"], session_id, reply_content["total_tokens"])
                if self.show_user_prompt:
                    logger.debug(f"[DeepSeek] {query} \n {reply_content['content']}")
                return Reply(ReplyType.TEXT, reply_content["content"])
            else:
                logger.error(f"[DeepSeek] 回复使用了0个token: {reply_content}")
                return Reply(ReplyType.ERROR, reply_content["content"])
        else:
            return Reply(ReplyType.ERROR, f"不支持处理{context.type}类型的消息")

    def _reply_text(self, session, args=None, retry_count=0):
        """调用DeepSeek API获取回复"""
        try:
            # 设置请求头
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            # 构建请求体
            body = args.copy() if args else {}
            body["messages"] = session.messages
            
            # 发送请求
            response = requests.post(
                self.api_base,
                headers=headers,
                json=body
            )
            
            # 处理响应
            if response.status_code == 200:
                result = response.json()
                return {
                    "total_tokens": result["usage"]["total_tokens"],
                    "completion_tokens": result["usage"]["completion_tokens"],
                    "content": result["choices"][0]["message"]["content"]
                }
            else:
                # 处理错误
                result = response.json()
                error = result.get("error", {})
                logger.error(f"[DeepSeek] 请求失败: 状态码={response.status_code}, "
                            f"错误信息={error.get('message')}, 类型={error.get('type')}")

                # 默认回复
                result = {"completion_tokens": 0, "content": "提问太快啦，请休息一下再问我吧"}
                
                # 根据错误类型决定是否重试
                need_retry = False
                if response.status_code >= 500:
                    # 服务器错误，需要重试
                    logger.warning(f"[DeepSeek] 进行第{retry_count+1}次重试")
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
            logger.exception(f"[DeepSeek] 发生异常: {e}")
            need_retry = retry_count < 2
            result = {"completion_tokens": 0, "content": "我现在有点累了，等会再来吧"}
            
            if need_retry:
                time.sleep(3)
                return self._reply_text(session, args, retry_count + 1)
            else:
                return result 