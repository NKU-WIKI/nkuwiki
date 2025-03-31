#!/usr/bin/env python3
"""
测试帖子相关API接口
主要测试以下接口：
1. POST /api/wxapp/post - 创建帖子
2. GET /api/wxapp/post/detail - 获取帖子详情
3. GET /api/wxapp/post/list - 查询帖子列表
4. POST /api/wxapp/post/delete - 删除帖子
5. POST /api/wxapp/post/like - 点赞帖子
6. POST /api/wxapp/post/favorite - 收藏帖子
7. GET /api/wxapp/post/status - 获取帖子交互状态
"""
import sys
import os
import json
import time
import random
import requests
from typing import Dict, Any, Optional

# 添加项目根目录到sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from core.utils.logger import register_logger

# 日志配置
logger = register_logger('api.test.post_api')

# 测试配置
BASE_URL = "http://localhost:8000/api"
TEST_OPENID = f"test_user_{int(time.time())}"

def check_api_service():
    """检查API服务是否运行"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=3)
        if response.status_code == 200:
            logger.debug("API服务正常运行")
            return True
        logger.error(f"API服务状态异常: {response.status_code}")
        return False
    except Exception as e:
        logger.error(f"无法连接到API服务: {str(e)}")
        return False

def sync_test_user():
    """同步测试用户信息，确保用户存在"""
    user_data = {
        "openid": TEST_OPENID,
        "nick_name": "测试用户",
        "avatar": "https://example.com/avatar.png"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/wxapp/user/sync", json=user_data)
        if response.status_code == 200:
            resp_data = response.json()
            if resp_data.get("code") == 200:
                logger.debug(f"测试用户同步成功: {TEST_OPENID}")
                return True
            logger.error(f"测试用户同步失败: {resp_data}")
            return False
        logger.error(f"测试用户同步请求失败: {response.status_code}")
        return False
    except Exception as e:
        logger.error(f"测试用户同步异常: {str(e)}")
        return False

def create_test_post() -> Optional[int]:
    """创建测试帖子"""
    post_data = {
        "openid": TEST_OPENID,
        "title": f"测试帖子标题 - {time.time()}",
        "content": "这是一个测试帖子内容，用于API测试。",
        "category_id": 1,
        "images": ["https://example.com/image1.jpg", "https://example.com/image2.jpg"],
        "tags": ["测试", "API"]
    }
    
    try:
        logger.debug(f"尝试创建帖子: {json.dumps(post_data, ensure_ascii=False)}")
        response = requests.post(f"{BASE_URL}/wxapp/post", json=post_data)
        
        logger.debug(f"API响应状态码: {response.status_code}")
        logger.debug(f"API响应内容: {response.text}")
        
        if response.status_code == 200:
            try:
                resp_data = response.json()
                logger.debug(f"创建帖子响应JSON: {json.dumps(resp_data, ensure_ascii=False)}")
                
                if resp_data.get("code") == 200:
                    # 检查具体的数据结构
                    logger.debug(f"响应数据结构: {type(resp_data.get('data'))}")
                    data = resp_data.get("data", {})
                    if isinstance(data, dict):
                        post_id = data.get("id")
                        if post_id:
                            logger.debug(f"测试帖子创建成功，ID: {post_id}")
                            return post_id
                    else:
                        logger.error(f"响应数据结构不是字典: {data}")
                        return None
                    
                    logger.error("帖子创建成功但ID为空")
                    return None
                
                logger.error(f"帖子创建失败: {resp_data}")
                return None
            except json.JSONDecodeError as e:
                logger.error(f"解析响应JSON失败: {str(e)}")
                return None
        
        logger.error(f"帖子创建请求失败: {response.status_code} - {response.text}")
        return None
    except Exception as e:
        logger.error(f"创建帖子异常: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return None

def test_get_post_detail(post_id: int) -> bool:
    """测试获取帖子详情"""
    try:
        logger.debug(f"尝试获取帖子详情，ID: {post_id}")
        response = requests.get(f"{BASE_URL}/wxapp/post/detail?post_id={post_id}")
        
        if response.status_code == 200:
            resp_data = response.json()
            logger.debug(f"帖子详情响应: {json.dumps(resp_data, ensure_ascii=False)}")
            
            if resp_data.get("code") == 200:
                post_data = resp_data.get("data", {})
                if post_data and post_data.get("id") == post_id:
                    logger.debug(f"帖子详情获取成功: {post_data.get('title')}")
                    return True
                
                logger.error(f"帖子详情不匹配: {post_data}")
                return False
            
            logger.error(f"获取帖子详情失败: {resp_data}")
            return False
        
        logger.error(f"获取帖子详情请求失败: {response.status_code} - {response.text}")
        return False
    except Exception as e:
        logger.error(f"获取帖子详情异常: {str(e)}")
        return False

def test_get_post_list() -> bool:
    """测试获取帖子列表"""
    try:
        logger.debug("尝试获取帖子列表")
        response = requests.get(f"{BASE_URL}/wxapp/post/list?page=1&limit=10")
        
        if response.status_code == 200:
            resp_data = response.json()
            logger.debug(f"帖子列表响应: {json.dumps(resp_data, ensure_ascii=False)}")
            
            if resp_data.get("code") == 200:
                posts = resp_data.get("data", {}).get("data", [])
                pagination = resp_data.get("data", {}).get("pagination", {})
                
                logger.debug(f"帖子数量: {len(posts)}, 分页信息: {pagination}")
                return True
            
            logger.error(f"获取帖子列表失败: {resp_data}")
            return False
        
        logger.error(f"获取帖子列表请求失败: {response.status_code} - {response.text}")
        return False
    except Exception as e:
        logger.error(f"获取帖子列表异常: {str(e)}")
        return False

def test_like_post(post_id: int) -> bool:
    """测试点赞帖子"""
    like_data = {
        "openid": TEST_OPENID,
        "post_id": post_id
    }
    
    try:
        logger.debug(f"尝试点赞帖子，ID: {post_id}")
        response = requests.post(f"{BASE_URL}/wxapp/post/like", json=like_data)
        
        if response.status_code == 200:
            resp_data = response.json()
            logger.debug(f"点赞帖子响应: {json.dumps(resp_data, ensure_ascii=False)}")
            
            if resp_data.get("code") == 200:
                like_count = resp_data.get("details", {}).get("like_count")
                if like_count is not None:
                    logger.debug(f"帖子点赞成功，当前点赞数: {like_count}")
                    return True
                
                logger.error("帖子点赞响应缺少点赞数信息")
                return False
            
            # 如果已经点赞过，也算成功
            if resp_data.get("code") == 400 and "已经点赞" in resp_data.get("message", ""):
                logger.debug("帖子已经被点赞过")
                return True
            
            logger.error(f"帖子点赞失败: {resp_data}")
            return False
        
        logger.error(f"帖子点赞请求失败: {response.status_code} - {response.text}")
        return False
    except Exception as e:
        logger.error(f"帖子点赞异常: {str(e)}")
        return False

def test_favorite_post(post_id: int) -> bool:
    """测试收藏帖子"""
    favorite_data = {
        "openid": TEST_OPENID,
        "post_id": post_id
    }
    
    try:
        logger.debug(f"尝试收藏帖子，ID: {post_id}")
        response = requests.post(f"{BASE_URL}/wxapp/post/favorite", json=favorite_data)
        
        if response.status_code == 200:
            resp_data = response.json()
            logger.debug(f"收藏帖子响应: {json.dumps(resp_data, ensure_ascii=False)}")
            
            if resp_data.get("code") == 200:
                status = resp_data.get("details", {}).get("status")
                favorite_count = resp_data.get("details", {}).get("favorite_count")
                is_favorited = resp_data.get("details", {}).get("is_favorited")
                
                # 如果已经收藏过，也算成功
                if status == "already_favorited":
                    logger.debug("帖子已经被收藏过")
                    return True
                
                if favorite_count is not None and is_favorited:
                    logger.debug(f"帖子收藏成功，当前收藏数: {favorite_count}")
                    return True
                
                logger.error("帖子收藏响应数据不完整")
                return False
            
            logger.error(f"帖子收藏失败: {resp_data}")
            return False
        
        logger.error(f"帖子收藏请求失败: {response.status_code} - {response.text}")
        return False
    except Exception as e:
        logger.error(f"帖子收藏异常: {str(e)}")
        return False

def test_get_post_status(post_id: int) -> bool:
    """测试获取帖子交互状态"""
    try:
        logger.debug(f"尝试获取帖子交互状态，ID: {post_id}")
        response = requests.get(f"{BASE_URL}/wxapp/post/status?post_id={post_id}&openid={TEST_OPENID}")
        
        if response.status_code == 200:
            resp_data = response.json()
            logger.debug(f"帖子状态响应: {json.dumps(resp_data, ensure_ascii=False)}")
            
            if resp_data.get("code") == 200:
                status_data = resp_data.get("data", {})
                logger.debug(f"帖子交互状态: 点赞={status_data.get('is_liked')}, 收藏={status_data.get('is_favorited')}")
                return True
            
            logger.error(f"获取帖子状态失败: {resp_data}")
            return False
        
        logger.error(f"获取帖子状态请求失败: {response.status_code} - {response.text}")
        return False
    except Exception as e:
        logger.error(f"获取帖子状态异常: {str(e)}")
        return False

def test_delete_post(post_id: int) -> bool:
    """测试删除帖子"""
    delete_data = {
        "openid": TEST_OPENID,
        "post_id": post_id
    }
    
    try:
        logger.debug(f"尝试删除帖子，ID: {post_id}")
        response = requests.post(f"{BASE_URL}/wxapp/post/delete", json=delete_data)
        
        if response.status_code == 200:
            resp_data = response.json()
            logger.debug(f"删除帖子响应: {json.dumps(resp_data, ensure_ascii=False)}")
            
            if resp_data.get("code") == 200:
                deleted_id = resp_data.get("details", {}).get("deleted_id")
                if deleted_id == post_id:
                    logger.debug(f"帖子删除成功，ID: {deleted_id}")
                    return True
                
                logger.error(f"删除帖子ID不匹配: 请求={post_id}, 响应={deleted_id}")
                return False
            
            logger.error(f"删除帖子失败: {resp_data}")
            return False
        
        logger.error(f"删除帖子请求失败: {response.status_code} - {response.text}")
        return False
    except Exception as e:
        logger.error(f"删除帖子异常: {str(e)}")
        return False

def run_tests():
    """运行所有测试"""
    # 检查API服务是否运行
    if not check_api_service():
        logger.error("API服务未运行，无法进行测试")
        return False
    
    # 同步测试用户
    if not sync_test_user():
        logger.error("测试用户同步失败，无法进行测试")
        return False
    
    # 创建测试帖子
    post_id = create_test_post()
    if not post_id:
        logger.error("测试帖子创建失败，无法进行后续测试")
        return False
    
    # 测试获取帖子详情
    if not test_get_post_detail(post_id):
        logger.error("获取帖子详情测试失败")
    
    # 测试获取帖子列表
    if not test_get_post_list():
        logger.error("获取帖子列表测试失败")
    
    # 测试点赞帖子
    if not test_like_post(post_id):
        logger.error("点赞帖子测试失败")
    
    # 测试收藏帖子
    if not test_favorite_post(post_id):
        logger.error("收藏帖子测试失败")
    
    # 测试获取帖子交互状态
    if not test_get_post_status(post_id):
        logger.error("获取帖子交互状态测试失败")
    
    # 测试删除帖子
    if not test_delete_post(post_id):
        logger.error("删除帖子测试失败")
    
    logger.debug("所有测试完成")
    return True

if __name__ == "__main__":
    print("开始测试帖子相关API...")
    success = run_tests()
    if success:
        print("所有测试完成")
    else:
        print("测试过程中出现错误，请查看日志") 