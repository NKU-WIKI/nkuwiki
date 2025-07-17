import asyncio
import requests
import json

from etl.load.db_pool_manager import init_db_pool, close_db_pool
from core.utils.logger import register_logger

logger = register_logger('temp.test_create_feedback')

async def run_test():
    """
    调用 /wxapp/feedback/ 接口创建一条新反馈
    """
    headers = {'Content-Type': 'application/json'}
    # 注意：当前接口不安全，直接接收openid
    payload = {
        "openid": "optX864KZIbWQz1GNszGD2fS-d5g", # 使用之前已知的测试用户openid
        "title": "Agent测试反馈-开放接口",
        "content": "这是一个由Agent自动测试脚本提交的反馈，用于验证开放接口。",
        "category": "bug",
        "contact": "agent_open@nkuwiki.com",
        "image": ["http://example.com/bug_screenshot_open.png"]
    }
    
    logger.info("开始调用 /api/wxapp/feedback/...")
    try:
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None, 
            lambda: requests.post('http://127.0.0.1:8000/api/wxapp/feedback/', headers=headers, json=payload)
        )
        response.raise_for_status()
        print("--- API响应 ---")
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
        print("-----------------")
    except requests.exceptions.RequestException as e:
        print(f"API调用失败: {e}")
        if e.response:
            print('错误响应:', e.response.text)

async def main():
    await init_db_pool()
    try:
        await run_test()
    finally:
        await close_db_pool()

if __name__ == "__main__":
    asyncio.run(main()) 