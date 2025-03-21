"""
智谱AI聊天机器人接口
"""
import json
import time
import requests
from loguru import logger
from config import Config
from core.bridge.reply import Reply
from core.bridge.context import Context
from core.agent.agent import Agent
from core.agent.zhipuai.zhipu_ai_session import ZhipuAISession
from core.utils.common import singleton_decorator


@singleton_decorator
class ZHIPUAIAgent(Agent):
    def __init__(self):
        self.config = Config()
        self.api_key = self.config.get("core.agent.zhipu.api_key")
        
        # 兼容zhipu_ai_general_chat
        self.show_user_prompt = self.config.get("debug_info", True)
        # 获取模型配置
        self.model = self.config.get("core.agent.zhipu.model")  # 默认使用glm-4
        # 获取智谱ID配置
        self.zhipu_ai_id = self.config.get("core.agent.zhipu.id")
        # 初始化通用实时模型参数
        self.gen_param_dict = {
            "top_p": self.config.get("core.agent.zhipu.top_p", 0.7),
            "temperature": self.config.get("core.agent.zhipu.temperature", 0.9),
            "request_id": None,
        }
        
        # 是否流式响应
        self.stream = self.config.get("core.agent.zhipu.stream", True)
        # 设置对话字数限制
        self.conversation_max_tokens = self.config.get("core.agent.zhipu.max_tokens", 1500)
        self.api_base = self.config.get("core.agent.zhipu.base_url", "https://open.bigmodel.cn/api/paas/v4/chat/completions")
        # 初始化session
        self.session_manager = ZhipuAISession()
        
    def reply(self, query, context: Context = None) -> Reply:
        if context.type == Context.TYPE_TEXT:
            request_id = context.get("request_id")
            if request_id:
                self.gen_param_dict["request_id"] = request_id
            session_id = context.get("session_id")
            reply = Reply()
            if not self.api_key:
                reply.content = "请先设置智谱API Key"
                return reply
            session = self.session_manager.session_query(query, session_id)
            api_key = self.api_key

            # 设置请求头和请求体
            payload = {
                "messages": session.messages,
                "model": self.model,
                "top_p": self.gen_param_dict.get("top_p"),
                "temperature": self.gen_param_dict.get("temperature"),
                "stream": self.stream,
                "request_id": self.gen_param_dict.get("request_id"),
            }
            # 添加token限制
            max_tokens = int(self.config.get("core.agent.zhipu.max_tokens", 1500))
            if max_tokens > 0:
                payload["max_tokens"] = max_tokens

            # 设置请求头
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"}
            try:
                # 如果使用流式响应
                if self.stream:
                    response_text = ""
                    for response_item in self.fetch_sse_stream(self.api_base, headers, json.dumps(payload)):
                        if response_item:
                            res_choices = response_item.get("choices", [])
                            if res_choices:
                                delta = res_choices[0].get("delta", {})
                                if delta.get("content"):
                                    response_text += delta["content"]
                                    reply.content = response_text
                                    if context.get("stream"):
                                        yield reply
                    if not context.get("stream"):
                        reply.content = response_text
                # 如果不使用流式响应
                else:
                    res = requests.post(self.api_base, headers=headers, data=json.dumps(payload))
                    if res.status_code == 200:
                        json_data = res.json()
                        response_text = json_data["choices"][0]["message"]["content"]
                        reply.content = response_text
                    else:
                        logger.error(f"Error: {res.status_code} {res.text}")
                        reply.content = f"请求API失败，错误代码：{res.status_code}"
                        return reply

                self.session_manager.session_reply(reply.content, session_id)
                if self.show_user_prompt:
                    logger.debug(f"[ZHIPU-AI] {query} \n {reply.content}")
                return reply

            except Exception as e:
                logger.error(f"智谱AI接口异常: {e}")
                reply.content = f"智谱AI接口异常: {e}"
                return reply
        
    @staticmethod
    def fetch_sse_stream(api_base, headers, payload, retry=2):
        while retry:
            try:
                response = requests.post(api_base, data=payload, headers=headers, stream=True)
                if response.status_code == 200:
                    for line in response.iter_lines():
                        if line:
                            decoded_line = line.decode('utf-8')
                            if decoded_line.startswith("data:"):
                                data_str = decoded_line[5:].strip()
                                if data_str == "[DONE]":
                                    break
                                try:
                                    data = json.loads(data_str)
                                    yield data
                                except json.JSONDecodeError:
                                    logger.exception(f"无法解析数据: {data_str}")
                                    continue
                else:
                    raise Exception(f"{response.status_code} {response.text}")
                break
            except Exception as e:
                logger.error(f"获取SSE流时出错: {e}")
                retry -= 1
                if retry == 0:
                    raise
                time.sleep(1) 