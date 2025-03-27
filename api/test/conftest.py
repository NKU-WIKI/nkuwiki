"""
pytest配置文件
提供测试所需的fixture
"""
import pytest
from fastapi.testclient import TestClient
from typing import Generator
import os
import sys

# 添加Python环境路径
VENV_PATH = "/opt/venvs/nkuwiki"
if VENV_PATH not in sys.path:
    sys.path.insert(0, VENV_PATH)

from api import register_routers
from fastapi import FastAPI

@pytest.fixture(scope="session")
def test_env():
    """测试环境配置"""
    return {
        "api_base_url": "http://localhost:8000",
        "python_path": "/opt/venvs/nkuwiki/bin/python",
        "service_name": "nkuwiki.service"
    }

@pytest.fixture
def app() -> FastAPI:
    """创建测试用FastAPI应用"""
    app = FastAPI(title="NkuWiki API Test")
    register_routers(app)
    return app

@pytest.fixture
def client(app: FastAPI, test_env: dict) -> Generator:
    """创建测试用HTTP客户端"""
    with TestClient(app, base_url=test_env["api_base_url"]) as client:
        yield client

@pytest.fixture
def test_user() -> dict:
    """测试用户数据"""
    return {
        "openid": "test_openid",
        "nick_name": "测试用户",
        "avatar": "https://example.com/avatar.jpg",
        "gender": 1,
        "country": "China",
        "province": "Tianjin",
        "city": "Tianjin",
        "language": "zh_CN",
        # 以下保留原有字段，给其他测试用
        "code": "test_code"
    }

@pytest.fixture
def test_post() -> dict:
    """测试帖子数据"""
    return {
        "title": "测试帖子",
        "content": "这是一个测试帖子的内容",
        "type": "question",
        "tags": ["测试", "问题"],
        "openid": "test_openid",
        "images": ["https://example.com/image.jpg"],
        "location": {
            "latitude": 39.1,
            "longitude": 117.2,
            "name": "南开大学"
        }
    }

@pytest.fixture
def test_comment() -> dict:
    """测试评论数据"""
    return {
        "post_id": 1,
        "content": "这是一个测试评论",
        "openid": "test_openid",
        "parent_id": None,
        "images": ["https://example.com/image.jpg"]
    }

@pytest.fixture
def test_feedback() -> dict:
    """测试反馈数据"""
    return {
        "type": "bug",
        "content": "发现了一个bug",
        "openid": "test_openid",
        "contact": "test@example.com",
        "images": ["https://example.com/bug.jpg"]
    }

@pytest.fixture
def test_rag_query() -> dict:
    """测试RAG查询数据"""
    return {
        "query": "南开大学的校训是什么？",
        "tables": ["wxapp_posts"],
        "max_results": 5,
        "format": "markdown",
        "stream": False
    }

@pytest.fixture
def test_mysql_query():
    """测试MySQL查询数据"""
    return {
        "query": "SELECT * FROM wxapp_posts WHERE id = ?",
        "params": [1]
    }

@pytest.fixture
def test_batch_mysql_query():
    """测试批量MySQL查询数据"""
    return {
        "queries": [
            {
                "query": "SELECT COUNT(*) as count FROM wxapp_posts",
                "params": []
            },
            {
                "query": "SELECT COUNT(*) as count FROM wxapp_comments",
                "params": []
            }
        ]
    } 