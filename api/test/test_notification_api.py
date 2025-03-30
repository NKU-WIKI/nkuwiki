#!/usr/bin/env python3
"""
测试通知触发API
测试点赞、评论等行为是否能正确触发通知
"""
import sys
import os
import json
import time
import requests
from datetime import datetime
from pathlib import Path

# 添加项目根目录到Python路径
root_dir = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(root_dir))

from core.utils.logger import register_logger

logger = register_logger('api.test.notification_api')

BASE_URL = "http://localhost:8000/api"

# 测试用户信息
USER_A = {
    "openid": "test_user_a",
    "nickname": "测试用户A",
    "avatar": "https://example.com/avatarA.png"
}

USER_B = {
    "openid": "test_user_b",
    "nickname": "测试用户B",
    "avatar": "https://example.com/avatarB.png"
}

def make_request(method, endpoint, params=None, data=None):
    """发送API请求"""
    url = f"{BASE_URL}{endpoint}"
    print(f"发送请求: {method} {url}")
    if params:
        print(f"参数: {params}")
    if data:
        print(f"数据: {data}")
    
    try:
        if method.upper() == "GET":
            response = requests.get(url, params=params, timeout=10)
        else:
            response = requests.post(url, json=data, timeout=10)
        
        print(f"状态码: {response.status_code}")
        json_response = response.json()
        print(json.dumps(json_response, ensure_ascii=False, indent=2))
        return json_response
    except Exception as e:
        print(f"请求失败: {str(e)}")
        return None

def sync_users():
    """同步测试用户信息"""
    print("\n===== 同步测试用户 =====")
    make_request("POST", "/wxapp/user/sync", data=USER_A)
    make_request("POST", "/wxapp/user/sync", data=USER_B)

def create_post():
    """创建测试帖子"""
    print("\n===== 创建测试帖子 =====")
    data = {
        "openid": USER_A["openid"],
        "category_id": 1,
        "title": f"测试帖子 {datetime.now().strftime('%H:%M:%S')}",
        "content": "这是用于测试通知的帖子"
    }
    
    response = make_request("POST", "/wxapp/post", data=data)
    if response and response.get("code") == 200:
        return response.get("details", {}).get("post_id")
    return None

def create_comment(post_id):
    """创建评论"""
    print("\n===== 创建评论 =====")
    data = {
        "openid": USER_B["openid"],
        "post_id": post_id,
        "content": "这是一条测试评论"
    }
    
    response = make_request("POST", "/wxapp/comment", data=data)
    if response and response.get("code") == 200:
        return response.get("details", {}).get("comment_id")
    return None

def like_post(post_id):
    """点赞帖子"""
    print("\n===== 点赞帖子 =====")
    data = {
        "openid": USER_B["openid"],
        "post_id": post_id
    }
    
    return make_request("POST", "/wxapp/post/like", data=data)

def favorite_post(post_id):
    """收藏帖子"""
    print("\n===== 收藏帖子 =====")
    data = {
        "openid": USER_B["openid"],
        "post_id": post_id
    }
    
    return make_request("POST", "/wxapp/post/favorite", data=data)

def like_comment(comment_id):
    """点赞评论"""
    print("\n===== 点赞评论 =====")
    data = {
        "openid": USER_B["openid"],
        "comment_id": comment_id
    }
    
    return make_request("POST", "/wxapp/comment/like", data=data)

def get_notifications(openid):
    """获取用户通知"""
    print(f"\n===== 获取用户 {openid} 的通知 =====")
    params = {
        "openid": openid,
        "limit": 10,
        "offset": 0
    }
    
    return make_request("GET", "/wxapp/notification/list", params=params)

def check_notification(response, type_value, target_type, sender_openid):
    """检查通知"""
    if not response or not response.get("data"):
        print(f"❌ 未找到通知")
        return False
    
    for notification in response.get("data", []):
        if (notification.get("type") == type_value and 
            notification.get("target_type") == target_type):
            
            sender = notification.get("sender")
            if isinstance(sender, str):
                try:
                    sender = json.loads(sender)
                except:
                    sender = {}
            
            if sender and sender.get("openid") == sender_openid:
                print(f"✅ 找到符合条件的通知: {notification.get('title')}")
                return True
    
    print(f"❌ 未找到符合条件的通知")
    return False

def test_comment_notification():
    """测试评论通知"""
    print("\n========== 测试评论通知 ==========")
    
    # 创建帖子
    post_id = create_post()
    if not post_id:
        print("❌ 创建帖子失败，无法继续测试")
        return
    
    print(f"创建帖子成功，ID: {post_id}")
    
    # 创建评论
    comment_id = create_comment(post_id)
    if not comment_id:
        print("❌ 创建评论失败，无法继续测试")
        return
    
    print(f"创建评论成功，ID: {comment_id}")
    
    # 等待通知处理
    print("等待2秒让通知处理完成...")
    time.sleep(2)
    
    # 检查通知
    notifications = get_notifications(USER_A["openid"])
    success = check_notification(notifications, "comment", "comment", USER_B["openid"])
    
    return success

def test_like_notification():
    """测试点赞通知"""
    print("\n========== 测试点赞通知 ==========")
    
    # 创建帖子
    post_id = create_post()
    if not post_id:
        print("❌ 创建帖子失败，无法继续测试")
        return
    
    print(f"创建帖子成功，ID: {post_id}")
    
    # 点赞帖子
    like_result = like_post(post_id)
    if not like_result or like_result.get("code") != 200:
        print("❌ 点赞失败，无法继续测试")
        return
    
    # 等待通知处理
    print("等待2秒让通知处理完成...")
    time.sleep(2)
    
    # 检查通知
    notifications = get_notifications(USER_A["openid"])
    success = check_notification(notifications, "like", "post", USER_B["openid"])
    
    return success

def test_favorite_notification():
    """测试收藏通知"""
    print("\n========== 测试收藏通知 ==========")
    
    # 创建帖子
    post_id = create_post()
    if not post_id:
        print("❌ 创建帖子失败，无法继续测试")
        return
    
    print(f"创建帖子成功，ID: {post_id}")
    
    # 收藏帖子
    favorite_result = favorite_post(post_id)
    if not favorite_result or favorite_result.get("code") != 200:
        if favorite_result and "already_favorited" in str(favorite_result):
            print("⚠️ 已经收藏过，继续测试")
        else:
            print("❌ 收藏失败，无法继续测试")
            return
    
    # 等待通知处理
    print("等待2秒让通知处理完成...")
    time.sleep(2)
    
    # 检查通知
    notifications = get_notifications(USER_A["openid"])
    success = check_notification(notifications, "favorite", "post", USER_B["openid"])
    
    return success

def test_comment_like_notification():
    """测试评论点赞通知"""
    print("\n========== 测试评论点赞通知 ==========")
    
    # 创建帖子
    post_id = create_post()
    if not post_id:
        print("❌ 创建帖子失败，无法继续测试")
        return
    
    print(f"创建帖子成功，ID: {post_id}")
    
    # 用户A创建评论
    data = {
        "openid": USER_A["openid"],
        "post_id": post_id,
        "content": "这是用户A的评论，待会用户B会点赞"
    }
    
    response = make_request("POST", "/wxapp/comment", data=data)
    if not response or response.get("code") != 200:
        print("❌ 创建评论失败，无法继续测试")
        return
    
    comment_id = response.get("details", {}).get("comment_id")
    print(f"用户A创建评论成功，ID: {comment_id}")
    
    # 用户B点赞评论
    like_result = like_comment(comment_id)
    if not like_result or like_result.get("code") != 200:
        print("❌ 点赞评论失败，无法继续测试")
        return
    
    # 等待通知处理
    print("等待2秒让通知处理完成...")
    time.sleep(2)
    
    # 检查通知
    notifications = get_notifications(USER_A["openid"])
    success = check_notification(notifications, "like", "comment", USER_B["openid"])
    
    return success

if __name__ == "__main__":
    print("===== 开始测试通知触发API =====")
    
    # 同步测试用户
    sync_users()
    
    # 测试评论通知
    test_comment_notification()
    
    # 测试点赞通知
    test_like_notification()
    
    # 测试收藏通知
    test_favorite_notification()
    
    # 测试评论点赞通知
    test_comment_like_notification()
    
    print("\n===== 测试完成 =====") 