import asyncio
import httpx
import json
import os
import traceback

# 定义测试用的API基础URL和token
BASE_URL = "http://127.0.0.1:8001/api/wxapp"
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwidXNlcl9pZCI6MSwiZXhwIjoxNzUzODg2NzUwfQ.WF12jRWZglle8IP7D-FxtgvCh8QUrjk6nQ9LsWORofE"
HEADERS = {"Authorization": f"Bearer {TOKEN}"}

# 结果保存路径
OUTPUT_DIR = "../../test_results"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "comment_test_responses.json")

# 确保目录存在
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

responses_log = []

def log_response(name, response):
    print(f"--- {name} ---")
    print(f"Status Code: {response.status_code}")
    try:
        response_json = response.json()
        print("Response JSON:")
        print(json.dumps(response_json, indent=2, ensure_ascii=False))
        responses_log.append({"name": name, "status_code": response.status_code, "body": response_json})
    except json.JSONDecodeError:
        print("Response Body (not JSON):")
        print(response.text)
        responses_log.append({"name": name, "status_code": response.status_code, "body": response.text})
    print("--------------------\n")

async def main():
    async with httpx.AsyncClient(base_url=BASE_URL, headers=HEADERS) as client:
        # 1. 创建一个帖子
        print("1. 创建帖子...")
        response = await client.post("/post/create", json={"title": "测试评论的帖子", "content": "这是一个用于测试评论功能的帖子"})
        log_response("创建帖子", response)
        assert response.status_code == 200
        post_id = response.json()["data"]["id"]

        # 2. 创建一条顶级评论
        print("2. 创建顶级评论...")
        comment_content = "这是一条顶级评论"
        response = await client.post("/comment/create", json={
            "resource_id": post_id,
            "resource_type": "post",
            "content": comment_content
        })
        log_response("创建顶级评论", response)
        assert response.status_code == 200
        comment_id = response.json()["data"]["id"]

        # 等待一小段时间，确保数据库计数更新对后续读取可见
        await asyncio.sleep(1.0)

        # 3. 验证帖子的评论数
        print("3. 验证帖子评论数...")
        response = await client.get(f"/post/detail?post_id={post_id}")
        log_response("获取帖子详情 (验证评论数)", response)
        assert response.json()["data"]["comment_count"] == 1

        # 4. 创建一条回复
        print("4. 创建回复...")
        reply_content = "这是对顶级评论的回复"
        response = await client.post("/comment/create", json={
            "resource_id": post_id,
            "resource_type": "post",
            "content": reply_content,
            "parent_id": comment_id
        })
        log_response("创建回复", response)
        assert response.status_code == 200
        reply_id = response.json()["data"]["id"]

        # 5. 验证顶级评论的回复数
        print("5. 验证顶级评论回复数...")
        response = await client.get(f"/comment/detail?comment_id={comment_id}")
        log_response("获取评论详情 (验证回复数)", response)
        assert response.json()["data"]["reply_count"] == 1

        # 6. 更新评论
        print("6. 更新评论...")
        updated_content = "更新后的顶级评论内容"
        response = await client.post("/comment/update", json={"id": comment_id, "content": updated_content})
        log_response("更新评论", response)
        assert response.status_code == 200

        # 7. 验证评论内容已更新
        print("7. 验证评论内容更新...")
        response = await client.get(f"/comment/detail?comment_id={comment_id}")
        log_response("获取评论详情 (验证更新)", response)
        
        assert response.json()["data"]["content"] == updated_content

        # 8. 删除回复
        print("8. 删除回复...")
        response = await client.post("/comment/delete", json={"id": reply_id})
        log_response("删除回复", response)
        assert response.status_code == 200

        # 9. 验证顶级评论的回复数已减少
        print("9. 验证回复数减少...")
        response = await client.get(f"/comment/detail?comment_id={comment_id}")
        log_response("获取评论详情 (验证回复数减少)", response)
        assert response.json()["data"]["reply_count"] == 0

        # 10. 删除顶级评论
        print("10. 删除顶级评论...")
        response = await client.post("/comment/delete", json={"id": comment_id})
        log_response("删除顶级评论", response)
        assert response.status_code == 200

        # 11. 验证帖子的评论数已减少
        print("11. 验证帖子评论数减少...")
        response = await client.get(f"/post/detail?post_id={post_id}")
        log_response("获取帖子详情 (验证评论数减少)", response)
        assert response.json()["data"]["comment_count"] == 0

        print("\n所有测试步骤执行完毕！")

if __name__ == "__main__":
    try:
        asyncio.run(main())
        print(f"\n测试成功完成。响应已记录在 {OUTPUT_FILE}")
    except httpx.RequestError as e:
        print(f"\n请求失败: {e}")
        traceback.print_exc()
    except Exception as e:
        print(f"\n测试过程中发生未知错误: {e}")
        traceback.print_exc()
    finally:
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(responses_log, f, indent=2, ensure_ascii=False)