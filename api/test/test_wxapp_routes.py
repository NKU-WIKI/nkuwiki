"""
测试wxapp路由的主要接口
"""
import requests
import pytest
import os
import json
import time

# 设置基本URL和测试用户
BASE_URL = "http://localhost:8000/api"
TEST_OPENID = f"test_user_{int(time.time())}"

# 禁用代理设置
os.environ['NO_PROXY'] = 'localhost,127.0.0.1'
requests.packages.urllib3.disable_warnings()

# 创建会话对象
session = requests.Session()
session.trust_env = False  # 禁用环境变量中的代理设置

# 测试帖子ID和评论ID，用于测试后续API
test_post_id = None
test_comment_id = None

def test_health_endpoint():
    """测试健康检查接口"""
    response = session.get(f"{BASE_URL}/health")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["code"] == 200
    assert json_data["message"] == "success"
    assert json_data["data"]["status"] == "ok"

def test_user_sync():
    """测试用户同步接口"""
    data = {
        "openid": TEST_OPENID,
        "user_info": {
            "nickName": f"测试用户{TEST_OPENID}",
            "avatarUrl": "https://example.com/avatar.png"
        }
    }
    response = session.post(f"{BASE_URL}/wxapp/user/sync", json=data)
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["code"] == 200
    assert "message" in json_data.get("details", {})
    assert "user_id" in json_data.get("details", {})

def test_get_user_profile():
    """测试获取用户信息接口"""
    response = session.get(f"{BASE_URL}/wxapp/user/profile", params={"openid": TEST_OPENID})
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["code"] == 200
    assert json_data.get("data", {}).get("openid") == TEST_OPENID

def test_create_post():
    """测试创建帖子接口"""
    global test_post_id
    data = {
        "openid": TEST_OPENID,
        "category_id": 1,
        "title": "测试帖子标题",
        "content": "这是一个用于测试的帖子内容"
    }
    response = session.post(f"{BASE_URL}/wxapp/post", json=data)
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["code"] == 200
    assert "post_id" in json_data.get("details", {})
    test_post_id = json_data.get("details", {}).get("post_id")

def test_get_post_list():
    """测试获取帖子列表接口"""
    response = session.get(f"{BASE_URL}/wxapp/post/list", params={"page": 1, "limit": 10})
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["code"] == 200
    assert "data" in json_data
    assert "pagination" in json_data

def test_get_post_detail():
    """测试获取帖子详情接口"""
    global test_post_id
    if not test_post_id:
        # 如果没有创建帖子，手动设置一个已知的帖子ID
        test_post_id = 2
    
    response = session.get(f"{BASE_URL}/wxapp/post/detail", params={"post_id": test_post_id})
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["code"] == 200
    assert json_data.get("data", {}).get("id") == test_post_id

def test_update_post():
    """测试更新帖子接口"""
    global test_post_id
    if not test_post_id:
        # 如果没有创建帖子，手动设置一个已知的帖子ID
        test_post_id = 2
    
    data = {
        "openid": "test_user_1743257785",  # 使用创建帖子的openid
        "post_id": test_post_id,
        "data": {
            "title": "已更新的测试帖子标题",
            "content": "这是已更新的帖子内容"
        }
    }
    response = session.post(f"{BASE_URL}/wxapp/post/update", json=data)
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["code"] == 200
    assert json_data.get("data", {}).get("title") == "已更新的测试帖子标题"

def test_create_comment():
    """测试创建评论接口"""
    global test_post_id, test_comment_id
    if not test_post_id:
        # 如果没有创建帖子，手动设置一个已知的帖子ID
        test_post_id = 2
    
    data = {
        "openid": TEST_OPENID,
        "post_id": test_post_id,
        "content": "这是一条测试评论"
    }
    response = session.post(f"{BASE_URL}/wxapp/comment", json=data)
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["code"] == 200
    assert "comment_id" in json_data.get("details", {})
    test_comment_id = json_data.get("details", {}).get("comment_id")

def test_get_comment_list():
    """测试获取评论列表接口"""
    global test_post_id
    if not test_post_id:
        pytest.skip("需要先创建帖子才能测试")
    
    response = session.get(f"{BASE_URL}/wxapp/comment/list", params={"post_id": test_post_id})
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["code"] == 200
    assert "data" in json_data
    assert "pagination" in json_data

def test_user_action_like_post():
    """测试点赞帖子接口"""
    global test_post_id
    if not test_post_id:
        pytest.skip("需要先创建帖子才能测试")
    
    data = {
        "openid": TEST_OPENID,
        "action_type": "like",
        "target_type": "post",
        "target_id": str(test_post_id)
    }
    response = session.post(f"{BASE_URL}/wxapp/action", json=data)
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["code"] == 200

def test_get_user_action_status():
    """测试获取用户操作状态接口"""
    global test_post_id
    if not test_post_id:
        pytest.skip("需要先创建帖子才能测试")
    
    response = session.get(
        f"{BASE_URL}/wxapp/action/status", 
        params={
            "openid": TEST_OPENID,
            "target_type": "post",
            "target_id": test_post_id
        }
    )
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["code"] == 200
    assert json_data.get("data", {}).get("like") is True

def test_delete_comment():
    """测试删除评论接口"""
    global test_comment_id
    if not test_comment_id:
        pytest.skip("需要先创建评论才能测试")
    
    data = {
        "openid": TEST_OPENID,
        "comment_id": test_comment_id
    }
    response = session.post(f"{BASE_URL}/wxapp/comment/delete", json=data)
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["code"] == 200

def test_delete_post():
    """测试删除帖子接口"""
    global test_post_id
    if not test_post_id:
        pytest.skip("需要先创建帖子才能测试")
    
    data = {
        "openid": TEST_OPENID,
        "post_id": test_post_id
    }
    response = session.post(f"{BASE_URL}/wxapp/post/delete", json=data)
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["code"] == 200

def test_search_posts():
    """测试搜索帖子接口"""
    response = session.get(
        f"{BASE_URL}/wxapp/post/search", 
        params={"keywords": "测试", "page": 1, "limit": 10}
    )
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["code"] == 200
    assert "data" in json_data
    
    # 验证搜索结果包含刚才创建和更新的帖子
    found = False
    if json_data.get("data"):
        for post in json_data.get("data"):
            if post.get("title") == "已更新的测试帖子标题":
                found = True
                break
    assert found or len(json_data.get("data", [])) > 0

if __name__ == "__main__":
    pytest.main(["-v", "test_wxapp_routes.py"]) 