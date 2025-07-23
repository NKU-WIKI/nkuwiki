import httpx
import asyncio
import time

# 测试配置
BASE_URL = "http://127.0.0.1:8001/api/wxapp/post"
# 替换为你的测试用户的有效Token
TEST_USER_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwidXNlcl9pZCI6MSwiZXhwIjoxNzUzODgwODY2fQ.E9klN_Vn5lc3BN-a1GrBIaMsStvGrqa3X7cTMSG2HrQ"

headers = {
    "Authorization": f"Bearer {TEST_USER_TOKEN}",
    "x-branch": 'dev'
}

async def create_post():
    """调用创建帖子的接口"""
    url = f"{BASE_URL}/create"
    post_data = {
        "title": f"测试帖子 {int(time.time())}",
        "content": "这是一个通过自动化脚本创建的测试帖子内容。",
        "category_id": 1,
        "is_public": True
    }
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=post_data, headers=headers)
            response.raise_for_status()  # 如果状态码是 4xx 或 5xx，则引发异常
            return response.json()
    except httpx.RequestError as exc:
        print(f"请求失败: {exc}")
    except httpx.HTTPStatusError as exc:
        print(f"HTTP错误: {exc.response.status_code} - {exc.response.text}")
    return None

async def main():
    """主执行函数"""
    print("开始创建测试帖子...")
    creation_response = await create_post()

    if creation_response and creation_response.get("code") == 200:
        post_id = creation_response.get("data", {}).get("id")
        if post_id:
            print(f"帖子创建成功！ Post ID: {post_id}")
            print(f"请使用此ID更新 test_action_count.py 中的 TEST_POST_ID")
        else:
            print("帖子创建成功，但未返回ID。")
            print(f"完整响应: {creation_response}")
    else:
        print("帖子创建失败。")
        if creation_response:
            print(f"响应: {creation_response}")

if __name__ == "__main__":
    asyncio.run(main())