"""
测试微信小程序搜索API接口
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

def test_search_function():
    """测试综合搜索接口"""
    # 测试默认搜索（all类型）
    response = session.get(
        f"{BASE_URL}/wxapp/search",
        params={"keyword": "测试", "page": 1, "limit": 10}
    )
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["code"] == 200
    assert "data" in json_data
    assert "pagination" in json_data
    
    # 测试帖子搜索
    response = session.get(
        f"{BASE_URL}/wxapp/search",
        params={"keyword": "测试", "search_type": "post", "page": 1, "limit": 10}
    )
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["code"] == 200
    
    # 测试用户搜索
    response = session.get(
        f"{BASE_URL}/wxapp/search",
        params={"keyword": "测试", "search_type": "user", "page": 1, "limit": 10}
    )
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["code"] == 200

def test_search_suggestion():
    """测试搜索建议接口"""
    response = session.get(
        f"{BASE_URL}/wxapp/suggestion",
        params={"keyword": "测"}
    )
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["code"] == 200
    assert "data" in json_data

def test_search_history():
    """测试获取搜索历史接口"""
    # 先执行一次搜索，以确保有历史记录
    session.get(
        f"{BASE_URL}/wxapp/search",
        params={"keyword": f"测试历史记录{int(time.time())}", "page": 1, "limit": 10}
    )
    
    # 获取搜索历史
    response = session.get(
        f"{BASE_URL}/wxapp/history",
        params={"openid": TEST_OPENID, "limit": 10}
    )
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["code"] == 200
    assert "data" in json_data

def test_clear_search_history():
    """测试清空搜索历史接口"""
    data = {
        "openid": TEST_OPENID
    }
    response = session.post(f"{BASE_URL}/wxapp/history/clear", json=data)
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["code"] == 200
    
    # 验证历史已清空
    response = session.get(
        f"{BASE_URL}/wxapp/history",
        params={"openid": TEST_OPENID, "limit": 10}
    )
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["code"] == 200
    assert len(json_data.get("data", [])) == 0

def test_hot_searches():
    """测试热门搜索接口"""
    response = session.get(
        f"{BASE_URL}/wxapp/hot",
        params={"limit": 10}
    )
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["code"] == 200
    assert "data" in json_data

if __name__ == "__main__":
    pytest.main(["-v", "test_search_api.py"]) 