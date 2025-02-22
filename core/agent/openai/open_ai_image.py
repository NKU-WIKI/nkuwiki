import time

from openai import OpenAI, RateLimitError
from app import App
from config import Config
from core.utils.common.token_bucket import TokenBucket


# OPENAI提供的画图接口
class OpenAIImage(object):
    def __init__(self):
        self.client = OpenAI(
            api_key=Config().get("voice_openai_api_key", Config().get("open_ai_api_key")),
            base_url=Config().get("voice_openai_api_base", Config().get("open_ai_api_base"))
        )
        if Config().get("rate_limit_dalle"):
            self.tb4dalle = TokenBucket(Config().get("rate_limit_dalle", 50))

    def create_img(self, query, retry_count=0, api_key=None):
        try:
            if Config().get("rate_limit_dalle") and not self.tb4dalle.get_token():
                return False, "请求太快了，请休息一下再问我吧"
            App().logger.info("[OPEN_AI] image_query={}".format(query))
            response = self.client.images.generate(
                prompt=query,
                n=1,
                size=Config().get("image_create_size", "256x256"),
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

