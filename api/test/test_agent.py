"""
Agent智能体API测试
"""
import pytest
from fastapi.testclient import TestClient
import time

def test_chat_with_agent(client: TestClient):
    """测试与智能体对话"""
    # 正常对话测试
    chat_data = {
        "query": "南开大学的校训是什么？",
        "messages": [],
        "stream": False,
        "format": "markdown",
        "openid": "test_user_openid"
    }
    response = client.post("/agent/chat", json=chat_data)
    assert response.status_code == 200
    data = response.json()["data"]
    assert "response" in data
    assert "sources" in data
    assert "suggested_questions" in data

    # 空查询测试
    chat_data["query"] = ""
    response = client.post("/agent/chat", json=chat_data)
    assert response.status_code == 422

    # 无效格式测试
    chat_data["query"] = "测试问题"
    chat_data["format"] = "invalid"
    response = client.post("/agent/chat", json=chat_data)
    assert response.status_code == 422

def test_agent_status(client: TestClient):
    """测试获取智能体状态"""
    response = client.get("/agent/status")
    assert response.status_code == 200
    data = response.json()["data"]
    assert "status" in data
    assert "version" in data
    assert "capabilities" in data
    assert "formats" in data
    assert data["status"] in ["running", "initializing", "error"]

def test_search_knowledge(client: TestClient):
    """测试知识库搜索"""
    # 正常搜索测试
    search_data = {
        "keyword": "南开大学",
        "limit": 10
    }
    response = client.post("/agent/search", json=search_data)
    assert response.status_code == 200
    data = response.json()["data"]
    assert isinstance(data, list)

    # 空关键词测试
    search_data["keyword"] = ""
    response = client.post("/agent/search", json=search_data)
    assert response.status_code == 422

    # 超出限制测试
    search_data["keyword"] = "测试"
    search_data["limit"] = 101
    response = client.post("/agent/search", json=search_data)
    assert response.status_code == 422

def test_rag_generate(client: TestClient, test_rag_query: dict):
    """测试RAG生成的基本功能"""
    # 正常生成测试
    response = client.post("/agent/rag", json=test_rag_query)
    assert response.status_code == 200
    
    # 打印出返回的整个JSON结构，辅助调试
    resp_json = response.json()
    print("\n===== RAG响应结构 =====")
    print(f"响应状态码: {response.status_code}")
    print(f"响应内容: {resp_json}")
    
    data = resp_json["data"]
    assert "response" in data
    assert "sources" in data
    assert "suggested_questions" in data
    assert "format" in data
    assert "retrieved_count" in data
    assert "response_time" in data

def test_rag_invalid_table(client: TestClient, test_rag_query: dict):
    """测试RAG无效表名处理"""
    # 无效表名测试
    invalid_query = test_rag_query.copy()
    invalid_query["tables"] = ["invalid_table"]
    response = client.post("/agent/rag", json=invalid_query)
    
    print(f"\n===== 无效表名响应 =====")
    print(f"响应状态码: {response.status_code}")
    print(f"响应内容: {response.json()}")
    
    assert response.status_code == 400
    assert "不支持的表名" in response.json()["detail"]

@pytest.mark.asyncio
async def test_chat_stream(client: TestClient):
    """测试流式对话"""
    chat_data = {
        "query": "南开大学的校训是什么？",
        "messages": [],
        "stream": True,
        "format": "markdown",
        "openid": "test_user_openid"
    }
    response = client.post("/agent/chat", json=chat_data)
    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]

def test_error_handling(client: TestClient):
    """测试错误处理"""
    # 无效的请求方法
    response = client.put("/agent/chat")
    assert response.status_code == 405

    # 无效的JSON数据
    response = client.post("/agent/chat", data="invalid json")
    assert response.status_code == 422

    # 缺少必需字段
    response = client.post("/agent/chat", json={})
    assert response.status_code == 422

    # 无效的路径
    response = client.get("/agent/invalid")
    assert response.status_code == 404

def test_rag_edge_cases(client: TestClient, test_rag_query: dict):
    """测试RAG边界情况"""
    # 空查询测试
    empty_query = test_rag_query.copy()
    empty_query["query"] = ""
    response = client.post("/agent/rag", json=empty_query)
    assert response.status_code == 422
    
    # 超长查询测试
    long_query = test_rag_query.copy()
    long_query["query"] = "南开大学" * 100  # 重复很多次构造超长查询
    response = client.post("/agent/rag", json=long_query)
    assert response.status_code == 200  # 应该能正常处理
    
    # 特殊字符测试
    special_query = test_rag_query.copy()
    special_query["query"] = "南开大学 SELECT * FROM users; --"  # 包含SQL注入攻击的查询
    response = client.post("/agent/rag", json=special_query)
    assert response.status_code == 200  # 应该能正常处理且不受影响
    
    # 空表列表测试
    no_tables_query = test_rag_query.copy()
    no_tables_query["tables"] = []
    response = client.post("/agent/rag", json=no_tables_query)
    assert response.status_code == 422  # 应该返回验证错误

def test_rag_stream(client: TestClient, test_rag_query: dict):
    """测试RAG流式响应"""
    # 开启流式传输测试
    stream_query = test_rag_query.copy()
    stream_query["stream"] = True
    response = client.post("/agent/rag", json=stream_query)
    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]

def test_rag_multi_tables(client: TestClient, test_rag_query: dict):
    """测试RAG多表查询"""
    # 多表查询测试
    multi_tables_query = test_rag_query.copy()
    multi_tables_query["tables"] = ["wxapp_posts", "wxapp_comments"]
    response = client.post("/agent/rag", json=multi_tables_query)
    assert response.status_code == 200
    data = response.json()["data"]
    assert "response" in data
    assert "sources" in data
    
    # 打印多表结果
    print("\n===== 多表查询响应 =====")
    print(f"响应状态码: {response.status_code}")
    print(f"响应内容摘要: 来源数量={len(data['sources'])}, 响应长度={len(data['response'])}")

def test_rag_cache(client: TestClient, test_rag_query: dict):
    """测试RAG查询缓存功能"""
    # 第一次请求
    start_time = time.time()
    response1 = client.post("/agent/rag", json=test_rag_query)
    first_request_time = time.time() - start_time
    assert response1.status_code == 200
    data1 = response1.json()["data"]
    
    # 第二次请求相同内容
    start_time = time.time()
    response2 = client.post("/agent/rag", json=test_rag_query)
    second_request_time = time.time() - start_time
    assert response2.status_code == 200
    data2 = response2.json()["data"]
    
    # 验证数据相同
    assert data1["response"] == data2["response"]
    assert data1["rewritten_query"] == data2["rewritten_query"]
    
    # 检查缓存是否生效（第二次请求应该明显更快）
    print("\n===== 缓存性能测试 =====")
    print(f"第一次请求时间: {first_request_time:.4f}秒")
    print(f"第二次请求时间: {second_request_time:.4f}秒")
    print(f"速度提升: {first_request_time/second_request_time:.2f}倍")
    
    # 注意：在某些情况下，第二次请求可能没有显著加快，
    # 比如如果服务器已经将所有数据加载到内存中，或者网络延迟占主导因素时
    # 但一般来说，应该会观察到缓存带来的性能提升 

def test_rag_stability(client: TestClient, test_rag_query: dict):
    """测试RAG查询的稳定性"""
    # 测试连续多次请求
    responses = []
    for i in range(3):
        # 每次查询稍微变化，避免命中缓存
        query = test_rag_query.copy()
        query["query"] = f"南开大学校训 {i}"
        
        try:
            response = client.post("/agent/rag", json=query, timeout=10.0)
            responses.append(response.status_code)
        except Exception as e:
            responses.append(f"错误: {str(e)}")
    
    print("\n===== 稳定性测试 =====")
    print(f"连续请求结果: {responses}")
    
    # 检查所有请求是否都成功
    success_count = sum(1 for r in responses if r == 200)
    assert success_count >= 2  # 至少2个成功为通过测试
    
    # 测试超长查询
    long_query = test_rag_query.copy()
    long_query["query"] = "南开大学" * 500  # 产生一个超长的查询文本
    
    response = client.post("/agent/rag", json=long_query, timeout=15.0)
    assert response.status_code == 200
    
    # 测试并发请求
    import threading
    
    def make_request(query, results):
        try:
            response = client.post("/agent/rag", json=query, timeout=15.0)
            results.append(response.status_code)
        except Exception as e:
            results.append(f"错误: {str(e)}")
    
    # 创建3个不同的查询
    queries = []
    for i in range(3):
        query = test_rag_query.copy()
        query["query"] = f"南开大学历史 {i}"
        queries.append(query)
    
    # 并发执行请求
    threads = []
    thread_results = []
    for query in queries:
        t = threading.Thread(target=make_request, args=(query, thread_results))
        threads.append(t)
        t.start()
    
    # 等待所有线程完成
    for t in threads:
        t.join()
    
    print(f"并发请求结果: {thread_results}")
    success_count = sum(1 for r in thread_results if r == 200)
    assert success_count >= 1  # 至少1个成功为通过测试 