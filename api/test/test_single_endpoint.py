"""
单接口测试工具
用于快速测试单个API接口
"""
import requests
import json
import sys
import time
import argparse
import socket
import subprocess
import os

# 禁用代理设置
os.environ['NO_PROXY'] = 'localhost,127.0.0.1'
requests.packages.urllib3.disable_warnings()

BASE_URL = "http://localhost:8000/api"
TEST_OPENID = "test_user_" + str(int(time.time()))
CONNECT_TIMEOUT = 3  # 连接超时设置为3秒
READ_TIMEOUT = 10    # 读取超时设置为10秒
MAX_RETRIES = 2      # 最大重试次数

def check_api_running():
    """检查API服务是否运行"""
    try:
        # 使用直接HTTP请求检查健康状态端点
        session = requests.Session()
        session.trust_env = False  # 禁用环境变量中的代理设置
        response = session.get(f"{BASE_URL}/health", timeout=2, verify=False)
        return response.status_code == 200
    except:
        # 尝试使用socket连接
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex(('localhost', 8000))
            sock.close()
            return result == 0
        except:
            return False

def start_api_service():
    """尝试启动API服务"""
    try:
        print("API服务未运行，尝试启动...")
        # 尝试停止旧进程
        subprocess.run("lsof -t -i:8000 | xargs -r kill -9", shell=True, stderr=subprocess.DEVNULL)
        time.sleep(1)
        
        # 获取项目根目录的绝对路径
        root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
        app_path = os.path.join(root_dir, "app.py")
        
        print(f"使用应用程序路径: {app_path}")
        
        # 启动API服务 - 使用不同的启动方式
        cmd = f"cd {root_dir} && python {app_path} --api --port 8000"
        subprocess.Popen(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # 等待服务启动
        for i in range(15):  # 增加等待时间
            print(f"等待API服务启动 {i+1}/15...", end="\r")
            time.sleep(1)
            if check_api_running():
                print("\nAPI服务已启动")
                return True
                
        print("\nAPI服务启动失败")
        return False
    except Exception as e:
        print(f"启动API服务出错: {str(e)}")
        return False

def test_endpoint(endpoint, method="GET", params=None, data=None):
    """测试单个接口"""
    url = f"{BASE_URL}{endpoint}"
    print(f"\n测试接口: {method} {url}")
    print(f"参数: {params}")
    print(f"数据: {data}")
    
    # 检查API服务是否运行
    if not check_api_running():
        if not start_api_service():
            print("❌ 无法连接到API服务，请确保服务正在运行")
            return
    
    # 创建会话对象，禁用代理
    session = requests.Session()
    session.trust_env = False  # 禁用环境变量中的代理设置
    
    # 设置请求参数
    request_kwargs = {
        'timeout': (CONNECT_TIMEOUT, READ_TIMEOUT),
        'verify': False  # 禁用SSL验证
    }
    
    # 添加重试机制
    for attempt in range(MAX_RETRIES + 1):
        try:
            if method.upper() == "GET":
                response = session.get(url, params=params, **request_kwargs)
            elif method.upper() == "POST":
                response = session.post(url, json=data, **request_kwargs)
            else:
                print(f"不支持的HTTP方法: {method}")
                return
            
            # 请求成功，跳出重试循环
            break
        
        except KeyboardInterrupt:
            print("\n⚠️ 测试被用户中断")
            return
        
        except (requests.ConnectionError, requests.Timeout) as e:
            if attempt < MAX_RETRIES:
                wait_time = 2 ** attempt  # 指数退避策略
                print(f"连接失败，{wait_time}秒后重试 ({attempt+1}/{MAX_RETRIES})...")
                time.sleep(wait_time)
            else:
                print(f"\n❌ 请求出错: {str(e)}，已重试{MAX_RETRIES}次")
                return
        
        except requests.RequestException as e:
            print(f"\n❌ 请求出错: {str(e)}")
            return
    
    try:
        # 检查状态码
        print(f"状态码: {response.status_code}")
        
        # 打印响应头信息
        print("响应头:")
        for key, value in response.headers.items():
            print(f"  {key}: {value}")
        
        # 打印响应内容
        try:
            json_response = response.json()
            print("\n响应内容:")
            print(json.dumps(json_response, ensure_ascii=False, indent=2))
            
            # 检查响应状态
            if "code" in json_response:
                if json_response["code"] == 200:
                    print("\n✅ 测试通过")
                else:
                    print(f"\n❌ 接口返回错误码: {json_response['code']}")
                    if "message" in json_response:
                        print(f"错误信息: {json_response['message']}")
            else:
                print("\n⚠️ 响应格式不符合规范，缺少code字段")
                
        except json.JSONDecodeError:
            print("\n⚠️ 响应不是有效的JSON格式")
            print(response.text)
    
    except Exception as e:
        print(f"\n❌ 处理响应时出错: {str(e)}")

def test_wxapp_user_sync():
    """测试用户同步接口"""
    endpoint = "/wxapp/user/sync"
    data = {"openid": TEST_OPENID}
    test_endpoint(endpoint, method="POST", data=data)

def test_wxapp_user_profile():
    """测试获取用户信息接口"""
    endpoint = "/wxapp/user/profile"
    params = {"openid": TEST_OPENID}
    test_endpoint(endpoint, method="GET", params=params)

def test_health():
    """测试健康检查接口"""
    endpoint = "/health"
    test_endpoint(endpoint, method="GET")

def test_wxapp_post_list():
    """测试获取帖子列表接口"""
    endpoint = "/wxapp/post/list"
    params = {"page": 1, "limit": 10}
    test_endpoint(endpoint, method="GET", params=params)

def test_wxapp_create_post():
    """测试创建帖子接口"""
    endpoint = "/wxapp/post"
    data = {
        "openid": TEST_OPENID,
        "category_id": 1,
        "title": "测试帖子标题",
        "content": "这是一个测试帖子内容"
    }
    test_endpoint(endpoint, method="POST", data=data)

def test_create_comment():
    """测试创建评论接口"""
    endpoint = "/wxapp/comment"
    data = {
        "openid": TEST_OPENID,
        "post_id": 2,  # 使用已知的帖子ID
        "content": "这是一条测试评论"
    }
    test_endpoint(endpoint, method="POST", data=data)

def test_notification_list():
    """测试获取通知列表接口"""
    endpoint = "/wxapp/notification/list"
    params = {"openid": TEST_OPENID, "limit": 10, "offset": 0}
    test_endpoint(endpoint, method="GET", params=params)

def test_notification_count():
    """测试获取未读通知数量接口"""
    endpoint = "/wxapp/notification/count"
    params = {"openid": TEST_OPENID}
    test_endpoint(endpoint, method="GET", params=params)

def test_notification_detail():
    """测试获取通知详情接口"""
    # 先创建一个测试通知
    create_test_notification()
    # 获取最新通知ID
    notification_id = get_latest_notification_id()
    if notification_id:
        endpoint = "/wxapp/notification/detail"
        params = {"notification_id": notification_id}
        test_endpoint(endpoint, method="GET", params=params)
    else:
        print("❌ 找不到通知ID，无法测试详情接口")

def test_mark_notification_read():
    """测试标记通知已读接口"""
    # 先创建一个测试通知
    create_test_notification()
    # 获取最新通知ID
    notification_id = get_latest_notification_id()
    
    if notification_id:
        endpoint = "/wxapp/notification/mark-read"
        data = {
            "notification_id": notification_id,
            "openid": TEST_OPENID
        }
        test_endpoint(endpoint, method="POST", data=data)
    else:
        print("❌ 找不到通知ID，无法测试标记已读接口")

def create_test_notification():
    """创建测试通知（直接向数据库插入）"""
    import pymysql
    import datetime
    import sys
    import os
    
    # 添加项目根目录到sys.path
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
    from config import Config
    
    config = Config()
    db_config = config.get("etl.data.mysql")
    
    try:
        conn = pymysql.connect(
            host=db_config.get("host", "localhost"),
            port=db_config.get("port", 3306),
            user=db_config.get("user", "root"),
            password=db_config.get("password", ""),
            database=db_config.get("name", "nkuwiki")
        )
        
        cursor = conn.cursor()
        
        # 创建测试通知
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sql = """
        INSERT INTO wxapp_notification 
        (openid, title, content, type, is_read, create_time, update_time, status) 
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        cursor.execute(sql, (
            TEST_OPENID, 
            "测试通知标题", 
            "这是一条测试通知内容", 
            "system",
            False,
            current_time,
            current_time,
            1
        ))
        
        conn.commit()
        print("✅ 测试通知创建成功")
        return cursor.lastrowid
    except Exception as e:
        print(f"❌ 创建测试通知失败: {str(e)}")
        return None
    finally:
        if 'conn' in locals() and conn:
            conn.close()

def get_latest_notification_id():
    """获取最新的通知ID"""
    import pymysql
    import sys
    import os
    
    # 添加项目根目录到sys.path
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
    from config import Config
    
    config = Config()
    db_config = config.get("etl.data.mysql")
    
    try:
        conn = pymysql.connect(
            host=db_config.get("host", "localhost"),
            port=db_config.get("port", 3306),
            user=db_config.get("user", "root"),
            password=db_config.get("password", ""),
            database=db_config.get("name", "nkuwiki")
        )
        
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        # 获取最新的通知
        sql = """
        SELECT id FROM wxapp_notification 
        WHERE openid = %s AND status = 1
        ORDER BY create_time DESC
        LIMIT 1
        """
        
        cursor.execute(sql, (TEST_OPENID,))
        result = cursor.fetchone()
        
        if result:
            return result['id']
        return None
    except Exception as e:
        print(f"❌ 获取通知ID失败: {str(e)}")
        return None
    finally:
        if 'conn' in locals() and conn:
            conn.close()

def test_mark_notifications_read_batch():
    """测试批量标记通知已读接口"""
    # 创建多个测试通知
    create_test_notification()
    create_test_notification()
    
    # 获取该用户的所有通知ID
    notification_ids = get_user_notification_ids()
    if notification_ids and len(notification_ids) > 0:
        endpoint = "/wxapp/notification/mark-read-batch"
        data = {
            "openid": TEST_OPENID,
            "notification_ids": notification_ids
        }
        test_endpoint(endpoint, method="POST", data=data)
    else:
        print("❌ 找不到通知ID，无法测试批量标记已读接口")

def test_delete_notification():
    """测试删除通知接口"""
    # 先创建一个测试通知
    create_test_notification()
    # 获取最新通知ID
    notification_id = get_latest_notification_id()
    if notification_id:
        endpoint = "/wxapp/notification/delete"
        data = {
            "notification_id": notification_id,
            "openid": TEST_OPENID
        }
        test_endpoint(endpoint, method="POST", data=data)
    else:
        print("❌ 找不到通知ID，无法测试删除通知接口")

def get_user_notification_ids():
    """获取用户的所有通知ID"""
    import pymysql
    import sys
    import os
    
    # 添加项目根目录到sys.path
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
    from config import Config
    
    config = Config()
    db_config = config.get("etl.data.mysql")
    
    try:
        conn = pymysql.connect(
            host=db_config.get("host", "localhost"),
            port=db_config.get("port", 3306),
            user=db_config.get("user", "root"),
            password=db_config.get("password", ""),
            database=db_config.get("name", "nkuwiki")
        )
        
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        # 获取用户的所有通知
        sql = """
        SELECT id FROM wxapp_notification 
        WHERE openid = %s AND status = 1
        ORDER BY create_time DESC
        """
        
        cursor.execute(sql, (TEST_OPENID,))
        results = cursor.fetchall()
        
        if results:
            return [result['id'] for result in results]
        return []
    except Exception as e:
        print(f"❌ 获取用户通知ID失败: {str(e)}")
        return []
    finally:
        if 'conn' in locals() and conn:
            conn.close()

def main():
    """主函数"""
    # 定义所有可用测试
    tests = {
        "health": ("健康检查", test_health),
        "user_sync": ("用户同步", test_wxapp_user_sync),
        "user_profile": ("用户信息", test_wxapp_user_profile),
        "post_list": ("帖子列表", test_wxapp_post_list),
        "create_post": ("创建帖子", test_wxapp_create_post),
        "create_comment": ("创建评论", test_create_comment),
        "notification_list": ("通知列表", test_notification_list),
        "notification_count": ("未读通知数量", test_notification_count),
        "notification_detail": ("通知详情", test_notification_detail),
        "mark_notification_read": ("标记通知已读", test_mark_notification_read),
        "mark_notifications_read_batch": ("批量标记通知已读", test_mark_notifications_read_batch),
        "delete_notification": ("删除通知", test_delete_notification)
    }
    
    # 设置命令行参数
    parser = argparse.ArgumentParser(description="API接口测试工具")
    parser.add_argument('-t', '--test', help='要运行的测试名称')
    parser.add_argument('-l', '--list', action='store_true', help='列出所有可用测试')
    parser.add_argument('--no-auto-start', action='store_true', help='不自动启动API服务')
    args = parser.parse_args()
    
    # 显示所有可用测试
    if args.list or not args.test:
        print("可用测试:")
        for key, (name, _) in tests.items():
            print(f"{key}: {name}")
        return
    
    # 如果需要，检查API服务并自动启动
    if not args.no_auto_start and not check_api_running():
        if not start_api_service():
            print("❌ 无法启动API服务，测试终止")
            return
    
    # 运行指定测试
    if args.test in tests:
        print(f"执行测试: {tests[args.test][0]}")
        tests[args.test][1]()
    else:
        print(f"错误: 未知的测试 '{args.test}'")
        print("使用 --list 查看所有可用测试")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n测试被用户中断")
        sys.exit(1) 