# encoding:utf-8
import datetime
import time
import openai  # 添加openai模块导入

import requests
from openai import OpenAI
from core.agent import Agent
from core.agent.chatgpt.prompt_dict import get_prompt
from core.agent.chatgpt.chat_gpt_session import ChatGPTSession
from core.agent.openai.open_ai_image import OpenAIImage
from core.agent.session_manager import SessionManager
from core.bridge.context import ContextType
from core.bridge.reply import Reply, ReplyType
from app import App
from config import Config               
from core.utils.common.token_bucket import TokenBucket



class ChatGPTAgent(Agent, OpenAIImage):
    def __init__(self):
        super().__init__()
        # 替换旧版API初始化方式
        self.client = OpenAI(
            api_key=Config().get("open_ai_api_key"),
            base_url=Config().get("open_ai_api_base"),
        )
        if Config().get("proxy"):
            self.client.proxy = Config().get("proxy")
        if Config().get("rate_limit_chatgpt"):
            self.tb4chatgpt = TokenBucket(Config().get("rate_limit_chatgpt", 20))

        self.sessions = SessionManager(ChatGPTSession, model=Config().get("model") or "gpt-3.5-turbo")
        self.args = {
            "model": Config().get("model") or "gpt-3.5-turbo",  # 对话模型的名称
            "temperature": Config().get("temperature", 0.9),  # 值在[0,1]之间，越大表示回复越具有不确定性
            # "max_tokens":4096,  # 回复最大的字符数
            "top_p": Config().get("top_p", 1),
            "frequency_penalty": Config().get("frequency_penalty", 0.0),  # [-2,2]之间，该值越大则更倾向于产生不同的内容
            "presence_penalty": Config().get("presence_penalty", 0.0),  # [-2,2]之间，该值越大则更倾向于产生不同的内容
            "request_timeout": Config().get("request_timeout", None),  # 请求超时时间，openai接口默认设置为600，对于难问题一般需要较长时间
            "timeout": Config().get("request_timeout", None),  # 重试超时时间，在这个时间内，将会自动重试
        }

    def reply(self, query, context=None):
        # acquire reply content
        if context.type == ContextType.TEXT:
            App().logger.info("[CHATGPT] query={}".format(query))

            session_id = context["session_id"]
            reply = None
            clear_memory_commands = Config().get("clear_memory_commands", ["#清除记忆"])
            if query in clear_memory_commands:
                self.sessions.clear_session(session_id)
                reply = Reply(ReplyType.INFO, "记忆已清除")
            elif query == "#清除所有":
                self.sessions.clear_all_session()
                reply = Reply(ReplyType.INFO, "所有人记忆已清除")
            elif query == "#更新配置":
                Config().load_config()
                reply = Reply(ReplyType.INFO, "配置已更新")
            if reply:
                return reply
            session = self.sessions.session_query(query, session_id)
            App().logger.debug("[CHATGPT] session query={}".format(session.messages))
            group_system_template = Config().get("group_character_desc", "")
            system_template = Config().get("character_desc", "")

            msg = context.kwargs['msg']
            isgroup = context.kwargs['isgroup']
            App().logger.debug(f"context.kwargs={context.kwargs}")
            current_date = datetime.datetime.now().strftime("%Y年%m月%d日%H时%M分")

            for message in session.messages:
                # 在每次循环时重新获取botname和name
                bot_name = msg.to_user_nickname

                if isgroup:  # 如果是群聊
                    if message['role'] == 'system':  # 如果是system message
                        name = msg.actual_user_nickname  # 使用实际的用户名
                        group_name = msg.other_user_nickname
                        prompt = get_prompt(group_name)
                        if prompt:
                            group_system_template = prompt
                        try:
                            message['content'] = group_system_template.format(time=current_date, group_name=group_name,
                                                                              bot_name=bot_name,
                                                                              name=name)  # 使用初始的模板
                        except KeyError:
                            # Handle the exception as needed
                            pass
                else:
                    if message['role'] == 'system':
                        name = msg.from_user_nickname  # 使用发送消息的用户名
                        try:
                            message['content'] = system_template.format(time=current_date, bot_name=bot_name, name=name)
                        except KeyError:
                            # Handle the exception as needed
                            pass

            api_key_list = Config().get("fastgpt_list", {})
            receiver = context.kwargs.get("receiver")
            api_key = api_key_list.get(receiver, Config().get("open_ai_api_key")) \
                if Config().get("fast_gpt") and isgroup else Config().get("open_ai_api_key")
            api_base = Config().get("open_ai_api_base")

            model = context.get("gpt_model")
            new_args = None
            if model:
                new_args = self.args.copy()
                new_args["model"] = model
            # if context.get('stream'):
            #     # reply in stream
            #     return self.reply_text_stream(query, new_query, session_id)

            reply_content = self.reply_text(session, api_key, api_base, args=new_args)
            App().logger.debug(f"reply_content = {reply_content}")
            App().logger.debug(
                "[CHATGPT] new_query={}, session_id={}, reply_cont={}, completion_tokens={}".format(
                    session.messages,
                    session_id,
                    reply_content["content"],
                    reply_content["completion_tokens"],
                )
            )

            if Config().get("fast_gpt", False):
                self.sessions.session_reply(reply_content["content"], session_id, reply_content["total_tokens"])
                reply = Reply(ReplyType.TEXT, reply_content["content"])
            elif reply_content["completion_tokens"] == 0 and len(reply_content["content"]) > 0:
                reply = Reply(ReplyType.ERROR, reply_content["content"])
            elif reply_content["completion_tokens"] > 0:
                self.sessions.session_reply(reply_content["content"], session_id, reply_content["total_tokens"])
                reply = Reply(ReplyType.TEXT, reply_content["content"])
            else:
                reply = Reply(ReplyType.ERROR, reply_content["content"])
                App().logger.debug("[CHATGPT] reply {} used 0 tokens.".format(reply_content))
            return reply

        elif context.type == ContextType.IMAGE_CREATE:
            ok, retstring = self.create_img(query, 0)
            reply = None
            if ok:
                reply = Reply(ReplyType.IMAGE_URL, retstring)
            else:
                reply = Reply(ReplyType.ERROR, retstring)
            return reply
        else:
            reply = Reply(ReplyType.ERROR, "Bot不支持处理{}类型的消息".format(context.type))
            return reply

    def reply_text(self, session: ChatGPTSession, api_key=None, api_base=None, args=None, retry_count=0) -> dict:
        """
        call openai's ChatCompletion to get the answer
        :param session: a conversation session
        :param session_id: session id
        :param retry_count: retry count
        :return: {}
        """
        try:
            if Config().get("rate_limit_chatgpt") and not self.tb4chatgpt.get_token():
                raise openai.error.RateLimitError("RateLimitError: rate limit exceeded")
            # if api_key == None, the default openai.api_key will be used
            if args is None:
                args = self.args
            App().logger.debug("[CHATGPT] session_id={}".format(session.session_id))
            # Check if "_" is in the session_id string
            response = self.client.chat.completions.create(
                messages=session.messages,
                **args
            )
            App().logger.debug("[CHATGPT] response={}".format(response))
            # logger.info("[ChatGPT] reply={}, total_tokens={}".format(response.choices[0]['message']['content'], response["usage"]["total_tokens"]))
            return {
                "total_tokens": response.usage.total_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "content": response.choices[0].message.content,
            }
        except Exception as e:
            need_retry = retry_count < 10
            result = {"completion_tokens": 0, "content": "我现在有点累了，等会再来吧"}
            if isinstance(e, openai.error.RateLimitError):
                App().logger.warn("[CHATGPT] RateLimitError: {}".format(e))
                result["content"] = "提问太快啦，请休息一下再问我吧"
                if need_retry:
                    time.sleep(20)
            elif isinstance(e, openai.error.Timeout):
                App().logger.warn("[CHATGPT] Timeout: {}".format(e))
                result["content"] = "我没有收到你的消息"
                if need_retry:
                    time.sleep(5)
            elif isinstance(e, openai.error.APIError):
                App().logger.warn("[CHATGPT] Bad Gateway: {}".format(e))
                result["content"] = "请再问我一次"
                if need_retry:
                    time.sleep(10)
            elif isinstance(e, openai.error.APIConnectionError):
                App().logger.warn("[CHATGPT] APIConnectionError: {}".format(e))
                need_retry = False
                result["content"] = "我连接不到你的网络"
            else:
                App().logger.exception("[CHATGPT] Exception: {}".format(e))
                need_retry = False
                self.sessions.clear_session(session.session_id)

            if need_retry:
                App().logger.warn("[CHATGPT] 第{}次重试".format(retry_count + 1))
                return self.reply_text(session, api_key, api_base, args, retry_count + 1)
            else:
                return result


class AzureChatGPTAgent(ChatGPTAgent):
    def __init__(self):
        super().__init__()
        # 修改Azure初始化方式
        self.client = OpenAI(
            api_key=Config().get("azure_api_key"),
            api_version=Config().get("azure_api_version", "2023-06-01-preview"),
            base_url=f"{Config().get('azure_api_base')}/openai/deployments/{Config().get('azure_deployment_id')}",
            default_headers={"api-key": Config().get("azure_api_key")}
        )
        self.args["model"] = Config().get("azure_deployment_id")

    def create_img(self, query, retry_count=0, api_key=None):
        text_to_image_model = Config().get("text_to_image")
        if text_to_image_model == "dall-e-2":
            api_version = "2023-06-01-preview"
            endpoint = Config().get("azure_openai_dalle_api_base","open_ai_api_base")
            # 检查endpoint是否以/结尾
            if not endpoint.endswith("/"):
                endpoint = endpoint + "/"
            url = "{}openai/images/generations:submit?api-version={}".format(endpoint, api_version)
            api_key = Config().get("azure_openai_dalle_api_key","open_ai_api_key")
            headers = {"api-key": api_key, "Content-Type": "application/json"}
            try:
                body = {"prompt": query, "size": Config().get("image_create_size", "256x256"),"n": 1}
                submission = requests.post(url, headers=headers, json=body)
                operation_location = submission.headers['operation-location']
                status = ""
                while (status != "succeeded"):
                    if retry_count > 3:
                        return False, "图片生成失败"
                    response = requests.get(operation_location, headers=headers)
                    status = response.json()['status']
                    retry_count += 1
                image_url = response.json()['result']['data'][0]['url']
                return True, image_url
            except Exception as e:
                App().logger.error("create image error: {}".format(e))
                return False, "图片生成失败"
        elif text_to_image_model == "dall-e-3":
            api_version = Config().get("azure_api_version", "2024-02-15-preview")
            endpoint = Config().get("azure_openai_dalle_api_base","open_ai_api_base")
            # 检查endpoint是否以/结尾
            if not endpoint.endswith("/"):
                endpoint = endpoint + "/"
            url = "{}openai/deployments/{}/images/generations?api-version={}".format(endpoint, Config().get("azure_openai_dalle_deployment_id","text_to_image"),api_version)
            api_key = Config().get("azure_openai_dalle_api_key","open_ai_api_key")
            headers = {"api-key": api_key, "Content-Type": "application/json"}
            try:
                body = {"prompt": query, "size": Config().get("image_create_size", "1024x1024"), "quality": Config().get("dalle3_image_quality", "standard")}
                response = requests.post(url, headers=headers, json=body)
                response.raise_for_status()  # 检查请求是否成功
                data = response.json()

                # 检查响应中是否包含图像 URL
                if 'data' in data and len(data['data']) > 0 and 'url' in data['data'][0]:
                    image_url = data['data'][0]['url']
                    return True, image_url
                else:
                    error_message = "响应中没有图像 URL"
                    App().logger.error(error_message)
                    return False, "图片生成失败"

            except requests.exceptions.RequestException as e:
                # 捕获所有请求相关的异常
                try:
                    error_detail = response.json().get('error', {}).get('message', str(e))
                except ValueError:
                    error_detail = str(e)
                error_message = f"{error_detail}"
                App().logger.error(error_message)
                return False, error_message

            except Exception as e:
                # 捕获所有其他异常
                error_message = f"生成图像时发生错误: {e}"
                App().logger.error(error_message)
                return False, "图片生成失败"
        else:
            return False, "图片生成失败，未配置text_to_image参数"
