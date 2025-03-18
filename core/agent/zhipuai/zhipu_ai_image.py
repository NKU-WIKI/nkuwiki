"""
智谱AI图像生成接口
"""
import json
import requests
from loguru import logger
from config import Config


def create_image_with_zhipuai(query, retry_count=2):
    """
    使用智谱AI创建图像
    :param query: 图像描述
    :param retry_count: 重试次数
    :return: 图像URL
    """
    config = Config()
    api_key = config.get("core.agent.zhipu.api_key")
    model = config.get("core.agent.zhipu.image_model", "cogview-3")
    api_base = config.get("core.agent.zhipu.image_api_base", "https://open.bigmodel.cn/api/paas/v4/images/generations")

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    payload = {
        "model": model,
        "prompt": query
    }

    while retry_count > 0:
        try:
            response = requests.post(api_base, json=payload, headers=headers)
            if response.status_code == 200:
                result = response.json()
                if "data" in result and len(result["data"]) > 0:
                    image_url = result["data"][0]["url"]
                    logger.debug(f"智谱AI图像生成成功: {image_url}")
                    return image_url
                else:
                    logger.error(f"智谱AI返回数据格式异常: {result}")
            else:
                logger.error(f"智谱AI图像生成请求失败: {response.status_code}, {response.text}")
        except Exception as e:
            logger.error(f"智谱AI图像生成异常: {e}")
        
        retry_count -= 1
    
    logger.error("智谱AI图像生成失败，已达最大重试次数")
    return None 