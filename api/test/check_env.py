"""
测试环境检查脚本
"""
import os
import sys
import requests
import subprocess
from typing import Dict, List, Tuple

def check_python_env() -> Tuple[bool, str]:
    """检查Python环境"""
    required_path = "/opt/venvs/nkuwiki/bin/python"
    if not os.path.exists(required_path):
        return False, f"Python环境不存在: {required_path}"
    
    try:
        version = subprocess.check_output([required_path, "--version"]).decode().strip()
        return True, f"Python环境正常: {version}"
    except Exception as e:
        return False, f"Python环境异常: {str(e)}"

def check_service() -> Tuple[bool, str]:
    """检查服务状态"""
    try:
        status = subprocess.check_output(["systemctl", "status", "nkuwiki.service"]).decode()
        if "active (running)" in status:
            return True, "服务运行正常"
        return False, f"服务未运行: {status}"
    except Exception as e:
        return False, f"服务状态检查失败: {str(e)}"

def check_api() -> Tuple[bool, str]:
    """检查API可用性"""
    try:
        response = requests.get("http://localhost:8000/agent/status")
        if response.status_code == 200:
            return True, "API可访问"
        return False, f"API返回异常状态码: {response.status_code}"
    except Exception as e:
        return False, f"API不可访问: {str(e)}"

def check_database() -> Tuple[bool, str]:
    """检查数据库连接"""
    try:
        response = requests.get("http://localhost:8000/mysql/tables")
        if response.status_code == 200:
            tables = response.json()["data"]["tables"]
            required_tables = ["wxapp_users", "wxapp_posts", "wxapp_comments", "wxapp_notifications", "wxapp_feedback"]
            missing_tables = [table for table in required_tables if table not in tables]
            if missing_tables:
                return False, f"缺少必需的数据表: {', '.join(missing_tables)}"
            return True, f"数据库正常，包含所有必需的表"
        return False, f"数据库检查失败: {response.status_code}"
    except Exception as e:
        return False, f"数据库连接失败: {str(e)}"

def main():
    """主函数"""
    checks = [
        ("Python环境", check_python_env),
        ("服务状态", check_service),
        ("API可用性", check_api),
        ("数据库连接", check_database)
    ]
    
    all_passed = True
    print("\n=== 测试环境检查 ===")
    
    for name, check in checks:
        print(f"\n检查{name}...")
        passed, message = check()
        print(f"结果: {'✓' if passed else '✗'} {message}")
        if not passed:
            all_passed = False
    
    print("\n=== 检查结果 ===")
    if all_passed:
        print("✓ 所有检查通过，可以开始测试")
        sys.exit(0)
    else:
        print("✗ 存在环境问题，请解决后再测试")
        sys.exit(1)

if __name__ == "__main__":
    main() 