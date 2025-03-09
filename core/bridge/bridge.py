from core.agent.agent_factory import create_agent
from core.bridge.context import Context
from core.bridge.reply import Reply
from core.utils.common import const
# from app import App
from core.utils.common.singleton import singleton
from config import Config
from core.utils.translate.factory import create_translator
from core.utils.voice.factory import create_voice


@singleton
class Bridge(object):
    def __init__(self):
        self.agent_type = {
            "chat": const.COZE,
            "voice_to_text": Config().get("voice_to_text", "openai"),
            "text_to_voice": Config().get("text_to_voice", "google"),
            "translate": Config().get("translate", "baidu"),
        }
        # 这边取配置的模型
        model = Config().get("model")
        if model:
            self.agent_type["chat"] = model
        else:
            model_type = Config().get("model") or const.GPT35
            if model_type in ["text-davinci-003"]:
                self.agent_type["chat"] = const.OPEN_AI
            if Config().get("use_azure_chatgpt", False):
                self.agent_type["chat"] = const.CHATGPTONAZURE
            if model_type in ["wenxin", "wenxin-4"]:
                self.agent_type["chat"] = const.BAIDU
            if model_type in ["xunfei"]:
                self.agent_type["chat"] = const.XUNFEI
            if model_type in [const.QWEN]:
                self.agent_type["chat"] = const.QWEN
            if model_type in [const.QWEN_TURBO, const.QWEN_PLUS, const.QWEN_MAX]:
                self.agent_type["chat"] = const.QWEN_DASHSCOPE
            if model_type and model_type.startswith("gemini"):
                self.agent_type["chat"] = const.GEMINI
            if model_type and model_type.startswith("glm"):
                self.agent_type["chat"] = const.ZHIPU_AI
            if model_type and model_type.startswith("claude-3"):
                self.agent_type["chat"] = const.CLAUDEAPI
            if model_type in ["claude"]:
                self.agent_type["chat"] = const.CLAUDEAI
            if model_type in [const.MOONSHOT, "moonshot-v1-8k", "moonshot-v1-32k", "moonshot-v1-128k"]:
                self.agent_type["chat"] = const.MOONSHOT
            if model_type in ["abab6.5-chat"]:
                self.agent_type["chat"] = const.MiniMax
        self.agents = {}
        self.chat_agents = {}

    # 模型对应的接口
    def get_agent(self, typename):
        if self.agents.get(typename) is None:
            # logger.debug("create bot {} for {}".format(self.btype[typename], typename))
            if typename == "text_to_voice":
                self.agents[typename] = create_voice(self.agent_type[typename])
            elif typename == "voice_to_text":
                self.agents[typename] = create_voice(self.agent_type[typename])
            elif typename == "chat":
                self.agents[typename] = create_agent(self.agent_type[typename])
            elif typename == "translate":
                self.agents[typename] = create_translator(self.agent_type[typename])
        return self.agents[typename]

    def get_agent_type(self, typename):
        return self.agent_type[typename]

    def fetch_reply_content(self, query, context: Context) -> Reply:
        return self.get_agent("chat").reply(query, context)

    def fetch_voice_to_text(self, voiceFile) -> Reply:
        return self.get_agent("voice_to_text").voiceToText(voiceFile)

    def fetch_text_to_voice(self, text) -> Reply:
        return self.get_agent("text_to_voice").textToVoice(text)

    def fetch_translate(self, text, from_lang="", to_lang="en") -> Reply:
        return self.get_agent("translate").translate(text, from_lang, to_lang)

    def find_chat_agent(self, agent_type: str):
        if self.chat_agents.get(agent_type) is None:
            self.chat_agents[agent_type] = create_agent(agent_type)
        return self.chat_agents.get(agent_type)

    def reset_agent(self):
        """
        重置agent路由
        """
        self.__init__()
