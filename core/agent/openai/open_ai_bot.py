import time
import httpx  

from openai import OpenAI, RateLimitError

from core.agent import Agent
from core.agent.openai.open_ai_image import OpenAIImage
from core.agent.openai.open_ai_session import OpenAISession
from core.agent.session_manager import SessionManager
from core.bridge.context import ContextType
from core.bridge.reply import Reply, ReplyType
from app import App
from config import Config

user_session = dict()


# OpenAI对话模型API (可用)
class OpenAIAgent(Agent, OpenAIImage):
    def __init__(self):
        super().__init__()
        proxy = Config().get("proxy")
        self.client = OpenAI(
            api_key=Config().get("open_ai_api_key"),
            base_url=Config().get("open_ai_api_base"),
            http_client=httpx.Client(proxies=proxy) if proxy else None  # 修正代理配置
        )

        self.sessions = SessionManager(OpenAISession, model=Config().get("model") or "gpt-3.5-turbo")
        self.args = {
            "model": Config().get("model") or "gpt-3.5-turbo",  # 更新默认模型
            "temperature": Config().get("temperature", 0.9),  # 值在[0,1]之间，越大表示回复越具有不确定性
            "max_tokens": 1200,  # 回复最大的字符数
            "top_p": 1,
            "frequency_penalty": Config().get("frequency_penalty", 0.0),  # [-2,2]之间，该值越大则更倾向于产生不同的内容
            "presence_penalty": Config().get("presence_penalty", 0.0),  # [-2,2]之间，该值越大则更倾向于产生不同的内容
            "request_timeout": Config().get("request_timeout", None),  # 请求超时时间，openai接口默认设置为600，对于难问题一般需要较长时间
            "timeout": Config().get("request_timeout", None),  # 重试超时时间，在这个时间内，将会自动重试
            "stop": ["\n\n\n"],
        }

    def reply(self, query, context=None):
        # acquire reply content
        if context and context.type:
            if context.type == ContextType.TEXT:
                App().logger.info("[OPEN_AI] query={}".format(query))  # 统一日志调用
                session_id = context["session_id"]
                reply = None
                if query == "#清除记忆":
                    self.sessions.clear_session(session_id)
                    reply = Reply(ReplyType.INFO, "记忆已清除")
                elif query == "#清除所有":
                    self.sessions.clear_all_session()
                    reply = Reply(ReplyType.INFO, "所有人记忆已清除")
                else:
                    session = self.sessions.session_query(query, session_id)
                    result = self.reply_text(session)
                    total_tokens, completion_tokens, reply_content = (
                        result["total_tokens"],
                        result["completion_tokens"],
                        result["content"],
                    )
                    App().logger.debug(
                        "[OPEN_AI] new_query={}, session_id={}, reply_cont={}, completion_tokens={}".format(str(session), session_id, reply_content, completion_tokens)
                    )

                    if total_tokens == 0:
                        reply = Reply(ReplyType.ERROR, reply_content)
                    else:
                        self.sessions.session_reply(reply_content, session_id, total_tokens)
                        reply = Reply(ReplyType.TEXT, reply_content)
                return reply
            elif context.type == ContextType.IMAGE_CREATE:
                ok, retstring = self.create_img(query, 0)
                reply = None
                if ok:
                    reply = Reply(ReplyType.IMAGE_URL, retstring)
                else:
                    reply = Reply(ReplyType.ERROR, retstring)
                return reply

    def reply_text(self, session: OpenAISession, retry_count=0):
        try:
            response = self.client.chat.completions.create(
                model=self.args["model"],
                messages=[{"role": "user", "content": str(session)}],
                temperature=self.args["temperature"],
                max_tokens=self.args["max_tokens"]
            )
            res_content = response.choices[0].message.content
            total_tokens = response.usage.total_tokens
            completion_tokens = response.usage.completion_tokens
            App().logger.info("[OPEN_AI] reply={}".format(res_content))
            return {
                "total_tokens": total_tokens,
                "completion_tokens": completion_tokens,
                "content": res_content,
            }
        except RateLimitError as e:
            need_retry = retry_count < 2
            result = {"completion_tokens": 0, "content": "我现在有点累了，等会再来吧"}
            App().logger.warn("[OPEN_AI] RateLimitError: {}".format(e))
            result["content"] = "提问太快啦，请休息一下再问我吧"
            if need_retry:
                time.sleep(20)

            if need_retry:
                App().logger.warn("[OPEN_AI] 第{}次重试".format(retry_count + 1))
                return self.reply_text(session, retry_count + 1)
            else:
                return result
