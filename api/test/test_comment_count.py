import asyncio
import httpx
import json

# --- 配置 ---
BASE_URL = "http://127.0.0.1:8001/api/wxapp"
# 替换为你的测试用户的有效Token
TEST_USER_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwidXNlcl9pZCI6MSwiZXhwIjoxNzUzODgwODY2fQ.E9klN_Vn5lc3BN-a1GrBIaMsStvGrqa3X7cTMSG2HrQ"
# 替换为你要测试的帖子ID
TEST_POST_ID = 27

HEADERS = {
    "Authorization": f"Bearer {TEST_USER_TOKEN}",
    "Content-Type": "application/json"
}

async def get_post_details(post_id: int):
    """获取帖子详情"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{BASE_URL}/post/detail?post_id={post_id}", headers=HEADERS)
            response.raise_for_status()  # 如果状态码不是 2xx，则引发异常
            return response.json()
        except httpx.RequestError as exc:
            print(f"请求帖子详情时发生错误: {exc}")
            return None
        except httpx.HTTPStatusError as exc:
            print(f"请求帖子详情时服务器返回错误状态码: {exc.response.status_code}")
            print(f"响应内容: {exc.response.text}")
            return None

async def add_comment(post_id: int, content: str):
    """发布评论"""
    payload = {
        "resource_id": post_id,
        "resource_type": "post",
        "content": content
    }
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(f"{BASE_URL}/comment/create", json=payload, headers=HEADERS)
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as exc:
            print(f"发布评论时发生错误: {exc}")
            return None
        except httpx.HTTPStatusError as exc:
            print(f"发布评论时服务器返回错误状态码: {exc.response.status_code}")
            print(f"响应内容: {exc.response.text}")
            return None

async def main():
    """测试主函数"""
    print(f"--- 测试开始: 帖子ID {TEST_POST_ID} ---")

    # 1. 获取初始状态
    print("\n1. 获取初始帖子详情...")
    initial_details = await get_post_details(TEST_POST_ID)
    if initial_details is None:
        print("获取初始帖子详情失败，测试终止")
        return
    initial_count = initial_details.get('data', {}).get('comment_count', 0)
    print(f"初始评论数: {initial_count}")
    with open("test_results/initial_details_comment.json", "w", encoding="utf-8") as f:
        json.dump(initial_details, f, ensure_ascii=False, indent=4)
    print("初始详情已保存到 test_results/initial_details_comment.json")

    # 2. 发布一条新评论
    print("\n2. 发布一条新评论...")
    comment_content = "这是一条测试评论。"
    add_comment_result = await add_comment(TEST_POST_ID, comment_content)
    if add_comment_result is None:
        print("发布评论失败，测试终止")
        return
    print(f"评论发布成功")
    with open(f"test_results/add_comment_result.json", "w", encoding="utf-8") as f:
        json.dump(add_comment_result, f, ensure_ascii=False, indent=4)
    print(f"操作结果已保存到 test_results/add_comment_result.json")

    # 3. 再次获取帖子详情，验证计数是否正确更新
    print("\n3. 再次获取帖子详情以验证...")
    final_details = await get_post_details(TEST_POST_ID)
    final_count = final_details.get('data', {}).get('comment_count', 0)
    print(f"更新后的评论数: {final_count}")
    with open("test_results/final_details_comment.json", "w", encoding="utf-8") as f:
        json.dump(final_details, f, ensure_ascii=False, indent=4)
    print("最终详情已保存到 test_results/final_details_comment.json")

    # 4. 对比结果
    print("\n--- 结果对比 ---")
    print(f"初始评论数: {initial_count}")
    print(f"操作后评论数: {final_count}")

    expected_change = 1
    if final_count == initial_count + expected_change:
        print(f"\n✅ 测试通过: 计数值变化符合预期 ({expected_change})。")
    else:
        print(f"\n❌ 测试失败: 计数值变化不符合预期！应该是 {initial_count + expected_change}，但实际是 {final_count}。")

if __name__ == "__main__":
    import os
    if not os.path.exists("test_results"):
        os.makedirs("test_results")
    asyncio.run(main())