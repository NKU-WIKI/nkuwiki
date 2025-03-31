#!/usr/bin/env python3
"""
测试配置加载并检查默认头像URL
"""
import sys
import os
import json
from pathlib import Path

# 添加项目根目录到Python路径
root_dir = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(root_dir))

from config import Config
from core.utils.logger import register_logger

# 创建脚本专用日志记录器
logger = register_logger('etl.load.test_config')

def main():
    """测试配置加载情况"""
    try:
        print("开始测试配置加载...")
        
        # 获取配置信息
        config = Config()
        print(f"配置类型: {type(config)}")
        print(f"Config是Dict子类: {isinstance(config, dict)}")
        
        # 查看services节点
        services = config.get('services')
        print(f"services节点类型: {type(services)}")
        if services:
            print(f"services节点内容: {list(services.keys())}")
            
            # 查看app节点
            app = services.get('app')
            print(f"app节点类型: {type(app)}")
            if app:
                print(f"app节点内容: {app}")
                
                # 查看default节点
                default = app.get('default')
                print(f"default节点: {default}")
                
                if default:
                    print(f"default_avatar: {default.get('default_avatar')}")
        
        # 输出配置文件路径
        config_path = os.path.join(root_dir, 'config.json')
        print(f"配置文件路径: {config_path}")
        if os.path.exists(config_path):
            print(f"配置文件存在，大小: {os.path.getsize(config_path)} 字节")
            
            # 直接读取配置文件查看内容
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    config_json = json.loads(content)
                    
                    # 提取app节点信息
                    if 'services' in config_json and 'app' in config_json['services']:
                        app_node = config_json['services']['app']
                        print(f"从文件读取的app节点: {app_node}")
                        
                        if 'default' in app_node:
                            default_node = app_node['default']
                            print(f"从文件读取的default节点: {default_node}")
                            
                            if 'default_avatar' in default_node:
                                print(f"从文件读取的default_avatar: {default_node['default_avatar']}")
            except Exception as e:
                print(f"读取配置文件失败: {str(e)}")
        else:
            print(f"配置文件不存在: {config_path}")
        
        return 0
    except Exception as e:
        print(f"测试配置失败: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return 1

if __name__ == "__main__":
    sys.exit(main()) 