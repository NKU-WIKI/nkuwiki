import time

from openai import OpenAI, RateLimitError
from app import App
from config import Config
from core.utils.common.token_bucket import TokenBucket


# OPENAI提供的画图接口
class OpenAIImage(object):
    def __init__(self):
        self.config = Config()
        self.client = OpenAI(
            api_key=self.config.get("core.agent.openai.voice.api_key", self.config.get("core.agent.openai.api_key")),
            base_url=self.config.get("core.agent.openai.voice.base_url", self.config.get("core.agent.openai.base_url"))
        )
        if self.config.get("core.agent.openai.dalle_rate_limit"):
            self.tb4dalle = TokenBucket(self.config.get("core.agent.openai.dalle_rate_limit", 50))

    def create_img(self, query, retry_count=0, api_key=None):
        try:
            if self.config.get("core.agent.openai.dalle_rate_limit") and not self.tb4dalle.get_token():
                return False, "请求太快了，请休息一下再问我吧"
            App().logger.info("[OPEN_AI] image_query={}".format(query))
            response = self.client.images.generate(
                prompt=query,
                n=1,
                size=self.config.get("core.agent.openai.image_size", "256x256"),
            )
            image_url = response.data[0].url
            App().logger.info("[OPEN_AI] image_url={}".format(image_url))
            return True, image_url
        except RateLimitError as e:
            App().logger.warn(e)
            if retry_count < 1:
                time.sleep(5)
                App().logger.warn("[OPEN_AI] ImgCreate RateLimit exceed, 第{}次重试".format(retry_count + 1))
                return self.create_img(query, retry_count + 1)
            else:
                return False, "提问太快啦，请休息一下再问我吧"
        except Exception as e:
            App().logger.exception(e)
            return False, str(e)

