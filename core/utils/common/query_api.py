import requests
from concurrent.futures import ThreadPoolExecutor
import argparse

# 默认配置参数
DEFAULT_TARGET_IP = "10.137.144.40"
DEFAULT_PORTS = [80, 443, 8000, 8080, 44517, 3306, 21, 22, 25, 53, 3389]
TIMEOUT = 10
THREADS = 20

def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='高级端口扫描工具')
    parser.add_argument('-i', '--ip', default=DEFAULT_TARGET_IP, 
                      help=f'目标IP地址 (默认: {DEFAULT_TARGET_IP})')
    parser.add_argument('-p', '--ports', default=','.join(map(str, DEFAULT_PORTS)),
                      help='端口列表，支持逗号分隔或范围（如1-100）(默认: 常见端口)')
    return parser.parse_args()

def parse_port_input(port_input):
    """解析端口输入"""
    ports = set()
    parts = port_input.replace('，', ',').split(',')
    
    for part in parts:
        if '-' in part:
            start, end = map(int, part.split('-'))
            ports.update(range(start, end+1))
        else:
            ports.add(int(part))
    
    return sorted([p for p in ports if 1 <= p <= 65535])

def check_port(port, target_ip):
    """检查单个端口是否可连接"""
    try:
        # 尝试HTTP协议
        with requests.Session() as s:
            response = s.get(
                url=f"http://{target_ip}:{port}",
                timeout=TIMEOUT,
                headers={'User-Agent': 'PortScanner/1.0'}
            )
            if response.status_code < 400:
                return (port, "HTTP", "Open")
                
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        try:
            # 尝试HTTPS协议
            with requests.Session() as s:
                response = s.get(
                    url=f"https://{target_ip}:{port}",
                    timeout=TIMEOUT,
                    verify=False,  # 忽略证书验证
                    headers={'User-Agent': 'PortScanner/1.0'}
                )
                if response.status_code < 400:
                    return (port, "HTTPS", "Open")
                    
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            pass
        except Exception as e:
            return (port, "Unknown", f"Error: {str(e)}")
            
    except Exception as e:
        return (port, "Unknown", f"Error: {str(e)}")
        
    return (port, "TCP", "Closed")

def port_scan(target_ip, ports):
    """执行端口扫描"""
    print(f"开始扫描 {target_ip} 的端口...")
    with ThreadPoolExecutor(max_workers=THREADS) as executor:
        results = executor.map(lambda p: check_port(p, target_ip), ports)
        
    print("\n扫描结果：")
    print("端口\t协议\t状态")
    print("----------------------")
    for result in results:
            print(f"{result[0]}\t{result[1]}\t{result[2]}")

def query_http_service(port=80):
    """向指定端口发送详细GET请求"""
    try:
        url = f"http://{DEFAULT_TARGET_IP}:{port}/api/v2/query"
        print(f"\n正在向 {url} 发送请求...")
        
        payload = {
            "sql": "SELECT * FROM wechat_articles limit 10"
        }
        response = requests.get(
            url=url,
            timeout=TIMEOUT,
            headers={
                'accept': 'application/json'
            }
            # json=payload
        )
        
        print(f"HTTP状态码: {response.status_code}")
        # print("响应头信息:")
        # for header, value in response.headers.items():
        #     print(f"  {header}: {value}")
            
        # 尝试显示文本内容（前200字符）
        print("\n响应内容预览:")
        print(response.text)
        
        return response
        
    except Exception as e:
        print(f"请求失败: {str(e)}")
        return None

if __name__ == "__main__":
    args = parse_arguments()
    target_ip = args.ip
    ports = parse_port_input(args.ports)
    
    print(f"目标IP: {target_ip}")
    # print(f"扫描端口: {ports}")
    
    # port_scan(target_ip, ports)
    
    # 示例：扫描后自动查询44517端口
    query_http_service(port=80) 