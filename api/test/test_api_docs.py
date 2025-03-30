"""
测试API文档中的所有接口
运行此脚本将测试主要API并生成结果
"""
import requests
import json
import time
import sys
import os
from datetime import datetime
import random

# 添加项目根目录到sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# 禁用代理设置
os.environ['NO_PROXY'] = 'localhost,127.0.0.1'
requests.packages.urllib3.disable_warnings()

# 基础配置
BASE_URL = "http://localhost:8000/api"
CONNECT_TIMEOUT = 3
READ_TIMEOUT = 10
MAX_RETRIES = 2

# 时间戳用于生成唯一ID
TIMESTAMP = int(time.time())

# 测试用户ID
TEST_USER_ID = f"test_user_{TIMESTAMP}"
TEST_USER_ID_2 = f"test_user_{TIMESTAMP + 1}"

# 日志和结果文件
LOG_DIR = os.path.join(os.path.dirname(__file__), "logs")
os.makedirs(LOG_DIR, exist_ok=True)
RESULTS_FILE = os.path.join(LOG_DIR, f"api_test_results_{TIMESTAMP}.json")
DETAILED_RESULTS_FILE = os.path.join(LOG_DIR, f"api_test_detailed_{TIMESTAMP}.json")

# 测试结果收集
TEST_RESULTS = {
    "total": 0,
    "success": 0,
    "failed": 0,
    "skipped": 0,
    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "test_ids": {
        "user_1": TEST_USER_ID,
        "user_2": TEST_USER_ID_2
    },
    "results": []
}

def make_request(method, endpoint, params=None, data=None):
    """发送API请求并处理响应"""
    url = f"{BASE_URL}{endpoint}"
    
    session = requests.Session()
    session.trust_env = False  # 禁用环境变量中的代理设置
    
    request_kwargs = {
        'timeout': (CONNECT_TIMEOUT, READ_TIMEOUT),
        'verify': False
    }
    
    for attempt in range(MAX_RETRIES + 1):
        try:
            if method.upper() == "GET":
                response = session.get(url, params=params, **request_kwargs)
            elif method.upper() == "POST":
                response = session.post(url, json=data, **request_kwargs)
            else:
                return {
                    "success": False,
                    "error": f"不支持的HTTP方法: {method}",
                    "status_code": None,
                    "data": None
                }
            
            # 请求成功，跳出重试循环
            break
        except (requests.ConnectionError, requests.Timeout) as e:
            if attempt < MAX_RETRIES:
                wait_time = 2 ** attempt
                time.sleep(wait_time)
            else:
                return {
                    "success": False,
                    "error": f"请求出错: {str(e)}，已重试{MAX_RETRIES}次",
                    "status_code": None,
                    "data": None
                }
        except requests.RequestException as e:
            return {
                "success": False,
                "error": f"请求出错: {str(e)}",
                "status_code": None,
                "data": None
            }
    
    try:
        json_response = response.json()
        return {
            "success": response.status_code == 200 and json_response.get("code") == 200,
            "status_code": response.status_code,
            "data": json_response,
            "raw_response": response
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"解析响应出错: {str(e)}",
            "status_code": response.status_code if 'response' in locals() else None,
            "data": None,
            "raw_response": response if 'response' in locals() else None
        }

def run_test(test_name, method, endpoint, params=None, data=None, expected_status=200):
    """运行单个测试并记录结果"""
    print(f"\n测试: {test_name}")
    print(f"请求: {method} {endpoint}")
    if params:
        print(f"参数: {json.dumps(params, ensure_ascii=False)}")
    if data:
        print(f"数据: {json.dumps(data, ensure_ascii=False)}")
    
    start_time = time.time()
    result = make_request(method, endpoint, params, data)
    duration = time.time() - start_time
    
    TEST_RESULTS["total"] += 1
    
    if not result["success"]:
        TEST_RESULTS["failed"] += 1
        test_status = "❌ 失败"
        if "error" in result:
            print(f"错误: {result['error']}")
        elif result["status_code"] != expected_status:
            print(f"状态码错误: 期望 {expected_status}，实际 {result['status_code']}")
        else:
            print(f"响应错误: {json.dumps(result.get('data', {}), ensure_ascii=False)[:200]}...")
    else:
        TEST_RESULTS["success"] += 1
        test_status = "✅ 成功" 
        print(f"状态码: {result['status_code']}")
        # 简化输出，只打印响应的code和message
        if result.get("data"):
            simplified = {
                "code": result["data"].get("code"),
                "message": result["data"].get("message")
            }
            print(f"响应: {json.dumps(simplified, ensure_ascii=False)}")
    
    test_result = {
        "name": test_name,
        "method": method,
        "endpoint": endpoint,
        "params": params,
        "data": data,
        "status": test_status,
        "status_code": result.get("status_code"),
        "duration_ms": round(duration * 1000, 2),
        "time": datetime.now().strftime("%H:%M:%S"),
        "success": result["success"]
    }
    
    # 只在详细结果中保存完整响应
    detailed_result = test_result.copy()
    detailed_result["response"] = result.get("data")
    
    TEST_RESULTS["results"].append(test_result)
    
    # 定期保存结果，避免长时间运行中断丢失数据
    if TEST_RESULTS["total"] % 5 == 0:
        save_results()
    
    return result

def save_results():
    """保存测试结果到文件"""
    # 保存简要结果
    with open(RESULTS_FILE, "w", encoding="utf-8") as f:
        json.dump(TEST_RESULTS, f, ensure_ascii=False, indent=2)
    
    # 保存详细结果（包含完整响应）
    with open(DETAILED_RESULTS_FILE, "w", encoding="utf-8") as f:
        # 复制一份结果，但包含完整响应
        detailed_results = TEST_RESULTS.copy()
        json.dump(detailed_results, f, ensure_ascii=False, indent=2)

def print_summary():
    """打印测试总结"""
    total = TEST_RESULTS["total"]
    success = TEST_RESULTS["success"]
    failed = TEST_RESULTS["failed"]
    skipped = TEST_RESULTS["skipped"]
    
    success_rate = (success / total) * 100 if total > 0 else 0
    
    print("\n" + "=" * 50)
    print(f"测试总结")
    print("=" * 50)
    print(f"总测试数: {total}")
    print(f"成功: {success} ({success_rate:.1f}%)")
    print(f"失败: {failed}")
    print(f"跳过: {skipped}")
    print("=" * 50)
    
    # 打印失败的测试
    if failed > 0:
        print("\n失败的测试:")
        for result in TEST_RESULTS["results"]:
            if "失败" in result["status"]:
                print(f"- {result['name']}: {result['method']} {result['endpoint']}")
    
    # 最终保存测试结果
    save_results()
    print(f"\n测试结果已保存到: {RESULTS_FILE}")
    print(f"详细结果: {DETAILED_RESULTS_FILE}")

def test_health():
    """测试健康检查接口"""
    return run_test("健康检查", "GET", "/health")

def test_user_sync():
    """测试用户同步"""
    data = {"openid": TEST_USER_ID}
    return run_test("用户同步", "POST", "/wxapp/user/sync", data=data)

def test_user_profile():
    """测试获取用户信息"""
    params = {"openid": TEST_USER_ID}
    return run_test("获取用户信息", "GET", "/wxapp/user/profile", params=params)

def test_create_post():
    """测试创建帖子"""
    data = {
        "openid": TEST_USER_ID,
        "category_id": 1,
        "title": f"测试帖子 {datetime.now().strftime('%H:%M:%S')}",
        "content": "这是一个用于测试的帖子内容"
    }
    return run_test("创建帖子", "POST", "/wxapp/post", data=data)

def test_post_list():
    """测试获取帖子列表"""
    params = {"page": 1, "limit": 5}
    return run_test("获取帖子列表", "GET", "/wxapp/post/list", params=params)

def test_post_detail(post_id):
    """测试获取帖子详情"""
    if not post_id:
        TEST_RESULTS["skipped"] += 1
        print("\n测试: 获取帖子详情 - ⚠️ 跳过 (无可用帖子ID)")
        return None
    
    params = {"post_id": post_id}
    return run_test("获取帖子详情", "GET", "/wxapp/post/detail", params=params)

def test_create_comment(post_id):
    """测试创建评论"""
    if not post_id:
        TEST_RESULTS["skipped"] += 1
        print("\n测试: 创建评论 - ⚠️ 跳过 (无可用帖子ID)")
        return None
    
    data = {
        "openid": TEST_USER_ID,
        "post_id": post_id,
        "content": f"测试评论 {datetime.now().strftime('%H:%M:%S')}"
    }
    return run_test("创建评论", "POST", "/wxapp/comment", data=data)

def test_comment_list(post_id):
    """测试获取评论列表"""
    if not post_id:
        TEST_RESULTS["skipped"] += 1
        print("\n测试: 获取评论列表 - ⚠️ 跳过 (无可用帖子ID)")
        return None
    
    params = {"post_id": post_id}
    return run_test("获取评论列表", "GET", "/wxapp/comment/list", params=params)

def test_like_post(post_id):
    """测试点赞帖子"""
    if not post_id:
        TEST_RESULTS["skipped"] += 1
        print("\n测试: 点赞帖子 - ⚠️ 跳过 (无可用帖子ID)")
        return None
    
    data = {
        "openid": TEST_USER_ID_2,
        "post_id": post_id
    }
    return run_test("点赞帖子", "POST", "/wxapp/post/like", data=data)

def test_favorite_post(post_id):
    """测试收藏帖子"""
    if not post_id:
        TEST_RESULTS["skipped"] += 1
        print("\n测试: 收藏帖子 - ⚠️ 跳过 (无可用帖子ID)")
        return None
    
    data = {
        "openid": TEST_USER_ID_2,
        "post_id": post_id
    }
    return run_test("收藏帖子", "POST", "/wxapp/post/favorite", data=data)

def test_like_comment(comment_id):
    """测试点赞评论"""
    if not comment_id:
        TEST_RESULTS["skipped"] += 1
        print("\n测试: 点赞评论 - ⚠️ 跳过 (无可用评论ID)")
        return None
    
    data = {
        "openid": TEST_USER_ID_2,
        "comment_id": comment_id
    }
    return run_test("点赞评论", "POST", "/wxapp/comment/like", data=data)

def test_user_follow():
    """测试关注用户"""
    # 先获取用户资料以获取用户ID
    params = {"openid": TEST_USER_ID}
    user_result = make_request("GET", "/wxapp/user/profile", params=params)
    
    if not user_result["success"] or not user_result.get("data", {}).get("data", {}).get("id"):
        TEST_RESULTS["skipped"] += 1
        print("\n测试: 关注用户 - ⚠️ 跳过 (无法获取用户ID)")
        return None
    
    user_id = user_result["data"]["data"]["id"]
    
    data = {
        "openid": TEST_USER_ID_2,
        "followed_id": user_id
    }
    return run_test("关注用户", "POST", "/wxapp/user/follow", data=data)

def test_notification_list():
    """测试获取通知列表"""
    params = {"openid": TEST_USER_ID, "limit": 10, "offset": 0}
    return run_test("获取通知列表", "GET", "/wxapp/notification/list", params=params)

def test_notification_count():
    """测试获取未读通知数量"""
    params = {"openid": TEST_USER_ID}
    return run_test("获取未读通知数量", "GET", "/wxapp/notification/count", params=params)

def test_notification_detail(notification_id):
    """测试获取通知详情"""
    if not notification_id:
        TEST_RESULTS["skipped"] += 1
        print("\n测试: 获取通知详情 - ⚠️ 跳过 (无可用通知ID)")
        return None
    
    params = {"notification_id": notification_id}
    return run_test("获取通知详情", "GET", "/wxapp/notification/detail", params=params)

def test_mark_notification_read(notification_id):
    """测试标记通知已读"""
    if not notification_id:
        TEST_RESULTS["skipped"] += 1
        print("\n测试: 标记通知已读 - ⚠️ 跳过 (无可用通知ID)")
        return None
    
    data = {
        "notification_id": notification_id,
        "openid": TEST_USER_ID
    }
    return run_test("标记通知已读", "POST", "/wxapp/notification/mark-read", data=data)

def test_mark_notifications_read_batch(notification_ids):
    """测试批量标记通知已读"""
    if not notification_ids or len(notification_ids) == 0:
        TEST_RESULTS["skipped"] += 1
        print("\n测试: 批量标记通知已读 - ⚠️ 跳过 (无可用通知ID)")
        return None
    
    data = {
        "openid": TEST_USER_ID,
        "notification_ids": notification_ids
    }
    return run_test("批量标记通知已读", "POST", "/wxapp/notification/mark-read-batch", data=data)

def test_feedback():
    """测试提交反馈"""
    data = {
        "openid": TEST_USER_ID,
        "content": f"测试反馈内容 {datetime.now().strftime('%H:%M:%S')}",
        "type": "suggestion",
        "contact": "test@example.com",
        "device_info": {
            "system": "iOS 14.7.1",
            "model": "iPhone 12",
            "platform": "ios",
            "brand": "Apple"
        }
    }
    return run_test("提交反馈", "POST", "/wxapp/feedback", data=data)

def test_feedback_list():
    """测试获取反馈列表"""
    params = {"openid": TEST_USER_ID, "limit": 10, "offset": 0}
    return run_test("获取反馈列表", "GET", "/wxapp/feedback/list", params=params)

def test_delete_notification(notification_id):
    """测试删除通知"""
    if not notification_id:
        TEST_RESULTS["skipped"] += 1
        print("\n测试: 删除通知 - ⚠️ 跳过 (无可用通知ID)")
        return None
    
    data = {
        "notification_id": notification_id,
        "openid": TEST_USER_ID
    }
    return run_test("删除通知", "POST", "/wxapp/notification/delete", data=data)

def run_all_tests():
    """运行所有测试"""
    print("=" * 50)
    print(f"开始API接口测试 ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})")
    print(f"测试用户: {TEST_USER_ID}, {TEST_USER_ID_2}")
    print("=" * 50)
    
    try:
        # 基础接口测试
        test_health()
        
        # 用户接口测试
        user_sync_result = test_user_sync()
        test_user_profile()
        
        # 帖子和评论测试
        post_result = test_create_post()
        test_post_list()
        
        post_id = None
        if post_result and post_result["success"]:
            post_id = post_result["data"].get("details", {}).get("post_id")
        
        test_post_detail(post_id)
        
        # 评论测试
        comment_result = test_create_comment(post_id)
        test_comment_list(post_id)
        
        comment_id = None
        if comment_result and comment_result["success"]:
            comment_id = comment_result["data"].get("details", {}).get("comment_id")
        
        # 用户交互测试
        test_like_post(post_id)
        test_favorite_post(post_id)
        test_like_comment(comment_id)
        test_user_follow()
        
        # 等待通知处理
        print("\n等待2秒让通知处理完成...")
        time.sleep(2)
        
        # 通知接口测试
        notification_result = test_notification_list()
        test_notification_count()
        
        notification_id = None
        notification_ids = []
        
        if notification_result and notification_result["success"]:
            if notification_result["data"].get("data"):
                notifications = notification_result["data"]["data"]
                if len(notifications) > 0:
                    notification_id = notifications[0]["id"]
                    notification_ids = [n["id"] for n in notifications[:min(3, len(notifications))]]
        
        test_notification_detail(notification_id)
        test_mark_notification_read(notification_id)
        test_mark_notifications_read_batch(notification_ids)
        test_delete_notification(notification_id)
        
        # 反馈接口测试
        test_feedback()
        test_feedback_list()
    
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
    except Exception as e:
        print(f"\n\n测试执行出错: {str(e)}")
    finally:
        # 打印测试总结
        print_summary()

if __name__ == "__main__":
    run_all_tests() 