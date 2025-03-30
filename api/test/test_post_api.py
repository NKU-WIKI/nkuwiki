#!/usr/bin/env python3
"""
测试帖子相关API接口
"""
import sys
import os
import json
import asyncio
import time

# 添加项目根目录到sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from fastapi.testclient import TestClient
from core.utils.logger import register_logger
from api.main import app
from etl.load.db_core import execute_custom_query, query_records, async_query_records, get_connection, async_insert, async_get_by_id
import traceback

# 创建测试客户端
client = TestClient(app)
logger = register_logger('api.test.post_api')

TEST_OPENID = "test_debug_user"

def test_create_post():
    """测试创建帖子API，并排查错误"""
    # 1. 检查表结构
    sql = "DESCRIBE wxapp_post"
    try:
        with get_connection() as conn:
            logger.debug("获取数据库连接成功")
        
        post_fields = execute_custom_query(sql)
        logger.debug(f"wxapp_post表结构: {json.dumps(post_fields, default=str)}")
        
        # 2. 同步用户信息
        user_data = {
            "openid": TEST_OPENID,
            "nickname": "调试用户",
            "avatar": "https://example.com/avatar.png"
        }
        
        # 检查用户是否存在
        user = query_records("wxapp_user", {"openid": TEST_OPENID}, limit=1)
        if not user:
            logger.debug(f"用户不存在，创建新用户: {TEST_OPENID}")
            user_id = execute_custom_query(
                "INSERT INTO wxapp_user (openid, nickname, avatar) VALUES (%s, %s, %s) RETURNING id",
                [TEST_OPENID, user_data["nickname"], user_data["avatar"]]
            )
            logger.debug(f"用户创建成功，ID: {user_id}")
        else:
            logger.debug(f"用户已存在: {user}")
        
        # 3. 测试创建帖子
        post_data = {
            "openid": TEST_OPENID,
            "category_id": 1,
            "title": f"测试帖子 {time.time()}",
            "content": "这是一个用于调试的帖子"
        }
        
        logger.debug(f"尝试直接插入数据库")
        try:
            # 构造帖子数据
            db_post_data = {
                "openid": post_data["openid"],
                "category_id": post_data["category_id"],
                "title": post_data["title"],
                "content": post_data["content"],
                "nickname": user_data["nickname"], 
                "avatar": user_data["avatar"],
                "status": 1
            }
            
            logger.debug(f"插入帖子数据: {json.dumps(db_post_data, default=str)}")
            post_id = execute_custom_query(
                "INSERT INTO wxapp_post (openid, title, content, nickname, avatar) VALUES (%s, %s, %s, %s, %s) RETURNING id",
                [db_post_data["openid"], db_post_data["title"], db_post_data["content"], db_post_data["nickname"], db_post_data["avatar"]]
            )
            logger.debug(f"帖子插入结果: {post_id}")
            
            if post_id:
                post = execute_custom_query(f"SELECT * FROM wxapp_post WHERE id = {post_id}")
                logger.debug(f"新创建的帖子数据: {json.dumps(post, default=str)}")
        except Exception as e:
            logger.error(f"直接插入数据库失败: {str(e)}")
            logger.error(traceback.format_exc())
        
        # 4. 通过API创建帖子
        logger.debug(f"通过API创建帖子: {json.dumps(post_data)}")
        response = client.post("/api/wxapp/post", json=post_data)
        logger.debug(f"API响应状态码: {response.status_code}")
        logger.debug(f"API响应内容: {response.text}")
        
        # 5. 分析响应
        resp_json = response.json()
        post_id = resp_json.get("details", {}).get("post_id")
        
        if post_id == -1:
            logger.error("帖子创建失败，返回ID为-1")
            # 尝试获取最新错误信息
            error_logs = execute_custom_query("SELECT * FROM wxapp_error_log ORDER BY create_time DESC LIMIT 5")
            if error_logs:
                logger.debug(f"最近的错误日志: {json.dumps(error_logs, default=str)}")
        else:
            # 获取创建的帖子信息
            post = execute_custom_query(f"SELECT * FROM wxapp_post WHERE id = {post_id}")
            logger.debug(f"通过API创建的帖子: {json.dumps(post, default=str)}")
    
    except Exception as e:
        logger.error(f"测试过程发生错误: {str(e)}")
        logger.error(traceback.format_exc())

async def async_test_create_post():
    """异步测试创建帖子"""
    try:
        # 异步测试部分，如果需要
        user = await async_query_records("wxapp_user", {"openid": TEST_OPENID}, limit=1)
        logger.debug(f"异步查询用户: {json.dumps(user, default=str)}")
        
        # 尝试使用async_insert创建帖子
        db_post_data = {
            "openid": TEST_OPENID,
            "title": f"异步测试帖子 {time.time()}",
            "content": "这是一个通过async_insert创建的帖子",
            "nickname": "异步测试用户",
            "avatar": "https://example.com/avatar.png",
            "status": 1
        }
        
        post_id = await async_insert("wxapp_post", db_post_data)
        logger.debug(f"异步插入帖子结果: {post_id}")
        
        if post_id > 0:
            post = await async_get_by_id("wxapp_post", post_id)
            logger.debug(f"异步插入的帖子: {json.dumps(post, default=str)}")
    except Exception as e:
        logger.error(f"异步测试过程发生错误: {str(e)}")
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    print("开始测试帖子API...")
    test_create_post()
    
    # 运行异步测试
    print("\n开始异步测试...")
    asyncio.run(async_test_create_post())
    
    print("\n测试完成.") 