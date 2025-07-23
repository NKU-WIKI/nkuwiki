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

async def toggle_favorite(post_id: int):
    """切换收藏状态"""
    payload = {
        "target_id": post_id,
        "target_type": "post",
        "action_type": "favorite"
    }
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(f"{BASE_URL}/action/toggle", json=payload, headers=HEADERS)
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as exc:
            print(f"切换收藏状态时发生错误: {exc}")
            return None
        except httpx.HTTPStatusError as exc:
            print(f"切换收藏状态时服务器返回错误状态码: {exc.response.status_code}")
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
    print(f"初始收藏数: {initial_details.get('data', {}).get('favorite_count')}")
    with open("test_results/initial_details_favorite.json", "w", encoding="utf-8") as f:
        json.dump(initial_details, f, ensure_ascii=False, indent=4)
    print("初始详情已保存到 test_results/initial_details_favorite.json")

    # 2. 执行一次收藏/取消收藏操作
    print("\n2. 执行收藏/取消收藏操作...")
    toggle_result = await toggle_favorite(TEST_POST_ID)
    action = "收藏" if toggle_result.get('data', {}).get('is_active') else "取消收藏"
    print(f"操作完成: {action}")
    print(f"API返回的新计数值: {toggle_result.get('data', {}).get('count')}")
    with open(f"test_results/toggle_favorite_result.json", "w", encoding="utf-8") as f:
        json.dump(toggle_result, f, ensure_ascii=False, indent=4)
    print(f"操作结果已保存到 test_results/toggle_favorite_result.json")

    # 3. 再次获取帖子详情，验证计数是否正确更新
    print("\n3. 再次获取帖子详情以验证...")
    final_details = await get_post_details(TEST_POST_ID)
    print(f"更新后的收藏数: {final_details.get('data', {}).get('favorite_count')}")
    with open("test_results/final_details_favorite.json", "w", encoding="utf-8") as f:
        json.dump(final_details, f, ensure_ascii=False, indent=4)
    print("最终详情已保存到 test_results/final_details_favorite.json")

    # 4. 对比结果
    print("\n--- 结果对比 ---")
    initial_count = initial_details.get('data', {}).get('favorite_count', 0)
    final_count = final_details.get('data', {}).get('favorite_count', 0)
    api_count = toggle_result.get('data', {}).get('count', -1)

    print(f"初始收藏数: {initial_count}")
    print(f"操作后收藏数 (来自详情接口): {final_count}")
    print(f"操作后收藏数 (来自操作接口): {api_count}")

    if final_count == api_count:
        print("\n✅ 测试通过: 详情接口和操作接口返回的计数值一致。")
    else:
        print("\n❌ 测试失败: 详情接口和操作接口返回的计数值不一致！")

    expected_change = 1 if action == "收藏" else -1
    if final_count == initial_count + expected_change:
        print(f"✅ 测试通过: 计数值变化符合预期 ({expected_change})。")
    else:
        print(f"❌ 测试失败: 计数值变化不符合预期！应该是 {initial_count + expected_change}，但实际是 {final_count}。")

if __name__ == "__main__":
    import os
    if not os.path.exists("test_results"):
        os.makedirs("test_results")
    asyncio.run(main())