#!/usr/bin/env python3
"""
修复MySQL用户权限脚本
解决nkuwiki用户无法连接的问题
"""

import subprocess
import json
import sys
from pathlib import Path

def load_config():
    """加载配置文件"""
    config_path = Path("config.json")
    if not config_path.exists():
        print("❌ config.json文件不存在")
        return None
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    return config['etl']['data']['mysql']

def get_mysql_container():
    """获取MySQL容器ID"""
    try:
        result = subprocess.run(
            ["docker", "ps", "--filter", "ancestor=mysql", "--format", "{{.ID}}"],
            capture_output=True, text=True, check=True
        )
        
        containers = result.stdout.strip().split('\n')
        if containers and containers[0]:
            return containers[0]
        else:
            print("❌ 没有找到运行中的MySQL容器")
            return None
    except subprocess.CalledProcessError:
        print("❌ 无法获取Docker容器信息")
        return None

def execute_mysql_command(container_id, sql_command, root_password="123456"):
    """在MySQL容器中执行SQL命令"""
    try:
        cmd = [
            "docker", "exec", "-i", container_id,
            "mysql", "-u", "root", f"-p{root_password}", "-e", sql_command
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        return False, e.stderr

def fix_mysql_user():
    """修复MySQL用户权限"""
    print("🔧 开始修复MySQL用户权限...")
    
    # 加载配置
    mysql_config = load_config()
    if not mysql_config:
        return False
    
    print(f"📋 MySQL配置:")
    print(f"   用户: {mysql_config['user']}")
    print(f"   密码: {mysql_config['password']}")
    print(f"   数据库: {mysql_config['name']}")
    
    # 获取容器ID
    container_id = get_mysql_container()
    if not container_id:
        return False
    
    print(f"🐳 MySQL容器ID: {container_id}")
    
    # 尝试不同的root密码
    root_passwords = ["123456", "password", "root", ""]
    
    for root_pwd in root_passwords:
        print(f"\n🔑 尝试root密码: {'[空密码]' if root_pwd == '' else root_pwd}")
        
        # 测试连接
        test_sql = "SELECT 1;"
        success, output = execute_mysql_command(container_id, test_sql, root_pwd)
        
        if success:
            print(f"✅ root密码正确: {root_pwd}")
            
            # 创建数据库和用户
            commands = [
                f"CREATE DATABASE IF NOT EXISTS `{mysql_config['name']}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;",
                f"CREATE USER IF NOT EXISTS '{mysql_config['user']}'@'%' IDENTIFIED BY '{mysql_config['password']}';",
                f"GRANT ALL PRIVILEGES ON `{mysql_config['name']}`.* TO '{mysql_config['user']}'@'%';",
                f"GRANT ALL PRIVILEGES ON `{mysql_config['name']}`.* TO '{mysql_config['user']}'@'localhost';",
                "FLUSH PRIVILEGES;"
            ]
            
            print("🛠️  执行修复命令...")
            for i, cmd in enumerate(commands, 1):
                print(f"   {i}. {cmd[:50]}...")
                success, output = execute_mysql_command(container_id, cmd, root_pwd)
                if success:
                    print(f"      ✅ 成功")
                else:
                    print(f"      ❌ 失败: {output}")
            
            # 验证修复结果
            print("\n🔍 验证用户权限...")
            verify_sql = f"SHOW GRANTS FOR '{mysql_config['user']}'@'%';"
            success, output = execute_mysql_command(container_id, verify_sql, root_pwd)
            
            if success:
                print("✅ 用户权限验证成功:")
                print(output)
            else:
                print(f"⚠️  权限验证失败: {output}")
            
            return True
    
    print("❌ 所有root密码都无效")
    return False

def test_connection():
    """测试应用连接"""
    print("\n🧪 测试应用数据库连接...")
    
    try:
        # 测试配置是否正确
        mysql_config = load_config()
        
        import pymysql
        
        connection = pymysql.connect(
            host=mysql_config['host'],
            port=mysql_config['port'],
            user=mysql_config['user'],
            password=mysql_config['password'],
            database=mysql_config['name'],
            charset='utf8mb4'
        )
        
        with connection.cursor() as cursor:
            cursor.execute("SELECT VERSION();")
            version = cursor.fetchone()
            print(f"✅ 连接成功! MySQL版本: {version[0]}")
        
        connection.close()
        return True
        
    except Exception as e:
        print(f"❌ 连接失败: {e}")
        return False

def main():
    """主函数"""
    print("🚀 MySQL用户权限修复工具")
    print("=" * 50)
    
    # 检查Docker是否运行
    try:
        subprocess.run(["docker", "--version"], capture_output=True, check=True)
    except subprocess.CalledProcessError:
        print("❌ Docker未安装或未运行")
        return
    
    # 修复用户权限
    if fix_mysql_user():
        print("\n" + "=" * 50)
        
        # 测试连接
        if test_connection():
            print("\n🎉 修复完成！数据库连接正常")
        else:
            print("\n⚠️  修复完成，但连接测试失败")
            print("请检查:")
            print("1. 防火墙设置")
            print("2. MySQL容器端口映射")
            print("3. 网络配置")
    else:
        print("\n❌ 修复失败")
        print("手动修复步骤:")
        print("1. docker exec -it <container_id> mysql -u root -p")
        print("2. CREATE DATABASE nkuwiki;")
        print("3. CREATE USER 'nkuwiki'@'%' IDENTIFIED BY 'Nkuwiki0!';")
        print("4. GRANT ALL PRIVILEGES ON nkuwiki.* TO 'nkuwiki'@'%';")
        print("5. FLUSH PRIVILEGES;")

if __name__ == "__main__":
    main() 