#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
南开Wiki所有API接口测试
"""
import requests
import json
import time
import os
import sys

# API基础URL，根据实际环境配置
BASE_URL = "http://127.0.0.1:8000"

# 测试用户数据
TEST_USER = {
    "openid": "test_user_openid",
    "nick_name": "测试用户",
    "avatar": "https://example.com/avatar.jpg",
    "gender": 1,
    "country": "中国",
    "province": "天津",
    "city": "南开区",
    "language": "zh_CN",
    "university": "南开大学",
    "login_type": "wechat"
}

# 测试帖子数据
TEST_POST = {
    "title": "测试帖子",
    "content": "这是一个测试帖子的内容",
    "tags": ["测试", "API"],
    "category": "问答",
    "openid": "test_user_openid"
}

# 测试评论数据
TEST_COMMENT = {
    "content": "这是一条测试评论",
    "post_id": 1,  # 将在测试中动态设置
    "openid": "test_user_openid"
}

# 测试反馈数据
TEST_FEEDBACK = {
    "content": "这是一条测试反馈",
    "type": "feature_request",
    "contact": "test@example.com",
    "openid": "test_user_openid"
}

def log_test(message):
    """输出测试日志"""
    print(f"\n[TEST] {message}")

def log_success(message):
    """输出成功日志"""
    print(f"[SUCCESS] {message}")

def log_error(message):
    """输出错误日志"""
    print(f"[ERROR] {message}")

def log_response(response):
    """输出响应日志"""
    try:
        print(f"状态码: {response.status_code}")
        print(f"响应数据: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    except:
        print(f"原始响应: {response.text}")

class APITester:
    """API测试器"""
    
    def __init__(self):
        """初始化测试器"""
        self.headers = {"Content-Type": "application/json"}
        self.test_results = {"success": 0, "failed": 0, "skipped": 0}
        self.post_id = None
        self.comment_id = None
        self.feedback_id = None
    
    def test_api(self, test_name, method, endpoint, data=None, params=None, expected_code=200, skip_on_error=False):
        """测试API接口"""
        log_test(f"测试 {test_name}")
        
        full_url = f"{BASE_URL}{endpoint}"
        try:
            if method.upper() == "GET":
                response = requests.get(full_url, params=params, headers=self.headers)
            elif method.upper() == "POST":
                response = requests.post(full_url, json=data, params=params, headers=self.headers)
            elif method.upper() == "PUT":
                response = requests.put(full_url, json=data, params=params, headers=self.headers)
            elif method.upper() == "DELETE":
                response = requests.delete(full_url, params=params, headers=self.headers)
            else:
                log_error(f"不支持的HTTP方法: {method}")
                self.test_results["failed"] += 1
                return None
            
            log_response(response)
            
            if response.status_code == expected_code:
                log_success(f"{test_name} 测试成功")
                self.test_results["success"] += 1
                return response.json() if response.status_code != 204 else None
            else:
                log_error(f"{test_name} 测试失败: 状态码 {response.status_code}, 预期 {expected_code}")
                self.test_results["failed"] += 1
                return None if skip_on_error else response.json()
                
        except Exception as e:
            log_error(f"{test_name} 测试异常: {str(e)}")
            self.test_results["failed"] += 1
            return None
    
    def test_wxapp_api(self):
        """测试微信小程序API"""
        log_test("开始测试微信小程序API...")
        
        # 1. 用户相关接口
        # 1.1 同步用户
        user_result = self.test_api(
            "同步用户信息", 
            "POST", 
            "/api/wxapp/users/sync", 
            data=TEST_USER
        )
        
        # 1.2 获取用户信息
        self.test_api(
            "获取用户信息", 
            "GET", 
            f"/api/wxapp/users/{TEST_USER['openid']}"
        )
        
        # 1.3 获取当前用户信息
        self.test_api(
            "获取当前用户信息", 
            "GET", 
            "/api/wxapp/users/me", 
            params={"openid": TEST_USER["openid"]}
        )
        
        # 1.4 获取用户列表
        self.test_api(
            "获取用户列表", 
            "GET", 
            "/api/wxapp/users", 
            params={"limit": 10, "offset": 0}
        )
        
        # 1.5 更新用户信息
        self.test_api(
            "更新用户信息", 
            "PUT", 
            f"/api/wxapp/users/{TEST_USER['openid']}", 
            data={"nick_name": "更新的测试用户"}
        )
        
        # 2. 帖子相关接口
        # 2.1 创建帖子
        post_result = self.test_api(
            "创建帖子", 
            "POST", 
            "/api/wxapp/posts", 
            data=TEST_POST
        )
        
        if post_result and "data" in post_result and "id" in post_result["data"]:
            self.post_id = post_result["data"]["id"]
            
            # 2.2 获取帖子详情
            self.test_api(
                "获取帖子详情", 
                "GET", 
                f"/api/wxapp/posts/{self.post_id}"
            )
            
            # 2.3 更新帖子
            self.test_api(
                "更新帖子", 
                "PUT", 
                f"/api/wxapp/posts/{self.post_id}", 
                data={"title": "更新的测试帖子标题"}
            )
            
            # 2.4 点赞帖子
            self.test_api(
                "点赞帖子", 
                "POST", 
                f"/api/wxapp/posts/{self.post_id}/like", 
                params={"openid": TEST_USER["openid"]}
            )
            
            # 2.5 取消点赞帖子
            self.test_api(
                "取消点赞帖子", 
                "DELETE", 
                f"/api/wxapp/posts/{self.post_id}/like", 
                params={"openid": TEST_USER["openid"]}
            )
            
            # 2.6 收藏帖子
            self.test_api(
                "收藏帖子", 
                "POST", 
                f"/api/wxapp/posts/{self.post_id}/favorite", 
                params={"openid": TEST_USER["openid"]}
            )
            
            # 2.7 取消收藏帖子
            self.test_api(
                "取消收藏帖子", 
                "DELETE", 
                f"/api/wxapp/posts/{self.post_id}/favorite", 
                params={"openid": TEST_USER["openid"]}
            )
        else:
            log_error("创建帖子失败，跳过相关测试")
            self.test_results["skipped"] += 7
        
        # 2.8 获取帖子列表
        self.test_api(
            "获取帖子列表", 
            "GET", 
            "/api/wxapp/posts", 
            params={"limit": 10, "offset": 0}
        )
        
        # 3. 评论相关接口
        if self.post_id:
            # 3.1 创建评论
            TEST_COMMENT["post_id"] = self.post_id
            comment_result = self.test_api(
                "创建评论", 
                "POST", 
                "/api/wxapp/comments", 
                data=TEST_COMMENT
            )
            
            if comment_result and "data" in comment_result and "id" in comment_result["data"]:
                self.comment_id = comment_result["data"]["id"]
                
                # 3.2 获取评论详情
                self.test_api(
                    "获取评论详情", 
                    "GET", 
                    f"/api/wxapp/comments/{self.comment_id}"
                )
                
                # 3.3 点赞评论
                self.test_api(
                    "点赞评论", 
                    "POST", 
                    f"/api/wxapp/comments/{self.comment_id}/like", 
                    params={"openid": TEST_USER["openid"]}
                )
                
                # 3.4 取消点赞评论
                self.test_api(
                    "取消点赞评论", 
                    "DELETE", 
                    f"/api/wxapp/comments/{self.comment_id}/like", 
                    params={"openid": TEST_USER["openid"]}
                )
            else:
                log_error("创建评论失败，跳过相关测试")
                self.test_results["skipped"] += 3
                
            # 3.5 获取帖子评论列表
            self.test_api(
                "获取帖子评论列表", 
                "GET", 
                f"/api/wxapp/posts/{self.post_id}/comments"
            )
        else:
            log_error("没有可用的帖子ID，跳过评论相关测试")
            self.test_results["skipped"] += 5
        
        # 4. 反馈相关接口
        # 4.1 创建反馈
        feedback_result = self.test_api(
            "创建反馈", 
            "POST", 
            "/api/wxapp/feedback", 
            data=TEST_FEEDBACK
        )
        
        if feedback_result and "data" in feedback_result and "id" in feedback_result["data"]:
            self.feedback_id = feedback_result["data"]["id"]
        
        # 4.2 获取用户反馈列表
        self.test_api(
            "获取用户反馈列表", 
            "GET", 
            f"/api/wxapp/users/{TEST_USER['openid']}/feedback"
        )
        
        # 5. 通知相关接口
        # 5.1 获取用户通知列表
        self.test_api(
            "获取用户通知列表", 
            "GET", 
            f"/api/wxapp/users/{TEST_USER['openid']}/notifications"
        )
        
        # 6. 搜索相关接口
        # 6.1 搜索帖子
        self.test_api(
            "搜索帖子", 
            "GET", 
            "/api/wxapp/search/posts", 
            params={"keyword": "测试", "page": 1, "page_size": 10}
        )
        
        # 7. 清理数据
        # 7.1 删除评论
        if self.comment_id:
            self.test_api(
                "删除评论", 
                "DELETE", 
                f"/api/wxapp/comments/{self.comment_id}", 
                params={"openid": TEST_USER["openid"]}
            )
        
        # 7.2 删除帖子
        if self.post_id:
            self.test_api(
                "删除帖子", 
                "DELETE", 
                f"/api/wxapp/posts/{self.post_id}", 
                params={"openid": TEST_USER["openid"]}
            )
    
    def test_agent_api(self):
        """测试智能体API"""
        log_test("开始测试智能体API...")
        
        # 1. Coze RAG接口
        # 1.1 RAG查询
        self.test_api(
            "RAG查询", 
            "POST", 
            "/api/agent/coze_rag/query", 
            data={
                "query": "南开大学的校训是什么？",
                "openid": TEST_USER["openid"]
            }
        )
        
        # 1.2 RAG帮助
        self.test_api(
            "RAG帮助", 
            "GET", 
            "/api/agent/coze_rag/help"
        )
        
        # 2. 搜索接口
        # 2.1 知识库搜索
        self.test_api(
            "知识库搜索", 
            "GET", 
            "/api/agent/search", 
            params={"query": "南开大学", "limit": 5}
        )
        
        # 3. 聊天接口
        # 3.1 聊天消息
        self.test_api(
            "聊天消息", 
            "POST", 
            "/api/agent/chat", 
            data={
                "message": "你好，请介绍一下南开大学",
                "openid": TEST_USER["openid"]
            }
        )
    
    def run_all_tests(self):
        """运行所有测试"""
        log_test("开始运行所有API测试...")
        
        # 测试微信小程序API
        self.test_wxapp_api()
        
        # 测试智能体API
        self.test_agent_api()
        
        # 输出测试结果
        log_test("测试结果汇总:")
        print(f"成功: {self.test_results['success']}")
        print(f"失败: {self.test_results['failed']}")
        print(f"跳过: {self.test_results['skipped']}")
        
        return self.test_results["failed"] == 0

if __name__ == "__main__":
    tester = APITester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1) 