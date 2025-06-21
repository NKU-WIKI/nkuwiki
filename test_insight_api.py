import requests
import json

def test_insight_api():
    """
    测试 /api/knowledge/insight 接口
    """
    base_url = "http://127.0.0.1:8000"
    endpoint = "/api/knowledge/insight"
    url = f"{base_url}{endpoint}"
    
    print(f"🚀  正在测试接口: GET {url}")
    
    try:
        # 发送GET请求
        response = requests.get(url, params={"page": 1, "page_size": 5})
        
        # 1. 检查状态码
        if response.status_code == 200:
            print(f"✅ (1/4) 状态码检查通过: {response.status_code}")
        else:
            print(f"❌ (1/4) 状态码检查失败: {response.status_code}")
            print(f"    响应内容: {response.text}")
            return

        # 2. 检查响应是否为有效JSON
        try:
            data = response.json()
            print("✅ (2/4) JSON格式检查通过")
        except json.JSONDecodeError:
            print("❌ (2/4) JSON格式检查失败: 响应不是有效的JSON")
            return

        # 3. 检查核心字段是否存在
        expected_keys = ["code", "message", "data", "pagination"]
        if all(key in data for key in expected_keys):
            print(f"✅ (3/4) 核心字段检查通过 (存在: {', '.join(expected_keys)})")
        else:
            missing_keys = [key for key in expected_keys if key not in data]
            print(f"❌ (3/4) 核心字段检查失败 (缺失: {', '.join(missing_keys)})")
            return
            
        # 4. 检查data和pagination是否为预期类型
        if isinstance(data.get('data'), list) and isinstance(data.get('pagination'), dict):
             print(f"✅ (4/4) 数据类型检查通过 (`data` is list, `pagination` is dict)")
        else:
            print(f"❌ (4/4) 数据类型检查失败")
            return

        print("\n🎉  接口测试成功!")
        
        # 打印部分返回数据
        print("\n--- 响应预览 ---")
        print(f"消息: {data.get('message')}")
        if data.get('pagination'):
            print(f"分页信息: {data.get('pagination')}")
        if data.get('data'):
            print(f"返回 {len(data['data'])} 条洞察数据，预览第一条:")
            # 使用json.dumps美化输出
            print(json.dumps(data['data'][0], indent=2, ensure_ascii=False))
        else:
            print("数据为空")
        print("----------------\n")


    except requests.exceptions.RequestException as e:
        print(f"\n❌ 请求失败: 请确认API服务是否已在 {base_url} 启动。")
        print(f"   错误详情: {e}")

if __name__ == "__main__":
    test_insight_api()
