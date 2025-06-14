import requests
import os
import docker
from config import Config

# 获取项目根目录
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def get_es_container():
    """获取正在运行的Elasticsearch容器对象"""
    try:
        client = docker.from_env()
        containers = client.containers.list()
        for container in containers:
            if 'elasticsearch' in container.name:
                return container
        return None
    except Exception as e:
        print(f"[-] Docker环境异常: {e}")
        return None

def copy_dict_to_container(container, src_path, dest_path):
    """将本地词典文件复制到容器内"""
    try:
        # Docker SDK for Python没有直接的cp命令，我们通过tar流来实现
        import tarfile
        from io import BytesIO

        # 创建一个内存中的tar归档
        pw_tarstream = BytesIO()
        pw_tar = tarfile.TarFile(fileobj=pw_tarstream, mode='w')
        
        file_info = tarfile.TarInfo(name=os.path.basename(src_path))
        with open(src_path, 'rb') as f:
            content = f.read()
            file_info.size = len(content)
            pw_tar.addfile(file_info, BytesIO(content))
            
        pw_tar.close()
        pw_tarstream.seek(0)
        
        # 将tar流放入容器
        container.put_archive(path=os.path.dirname(dest_path), data=pw_tarstream)
        print(f"[+] 成功将 {src_path} 复制到容器 {container.name}:{dest_path}")
        return True
    except Exception as e:
        print(f"[-] 复制文件到容器失败: {e}")
        return False

def reload_es_analyzer(host, port, index_name):
    """请求Elasticsearch重新加载分词器"""
    reload_url = f"http://{host}:{port}/{index_name}/_reload_search_analyzers"
    try:
        response = requests.post(reload_url)
        response.raise_for_status()
        if response.json().get("_shards", {}).get("total", 0) > 0:
            print("[+] Elasticsearch分词器已成功热加载！")
            return True
        else:
            print(f"[-] 热加载请求失败: {response.text}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"[-] 请求ES热加载API失败: {e}")
        return False

def main():
    """主函数：复制词典并热加载"""
    print("--- 开始更新Elasticsearch自定义词典 ---")
    
    # 1. 获取ES配置
    config = Config()
    es_host = config.get("etl.data.elasticsearch.host", "localhost")
    es_port = config.get("etl.data.elasticsearch.port", 9200)
    index_name = config.get("etl.data.elasticsearch.index_name", "nkuwiki")
    
    # 2. 定位文件路径
    local_dict_path = os.path.join(BASE_DIR, "etl", "utils", "dictionary", "custom_dictionary.dic")
    container_dict_path = "/usr/share/elasticsearch/config/analysis-ik/custom_dictionary.dic"

    if not os.path.exists(local_dict_path):
        print(f"[-] 错误: 本地词典文件未找到 {local_dict_path}")
        return

    # 3. 获取ES容器
    es_container = get_es_container()
    if not es_container:
        print("[-] 错误: 未找到正在运行的Elasticsearch容器。")
        return
        
    print(f"[+] 找到Elasticsearch容器: {es_container.name} ({es_container.short_id})")

    # 4. 复制文件到容器
    if not copy_dict_to_container(es_container, local_dict_path, container_dict_path):
        return

    # 5. 热加载分词器
    reload_es_analyzer(es_host, es_port, index_name)
    
    print("--- 更新流程结束 ---")


if __name__ == "__main__":
    # 确保安装了必要的库
    try:
        import requests
        import docker
    except ImportError:
        print("请先安装依赖: pip install requests docker")
    else:
        main() 