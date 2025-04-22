#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
定时删除无标题帖子的脚本

此脚本会连接数据库，删除所有标题为"无标题"的帖子。
可以设置为定时任务运行。

版本: 1.0.0
创建日期: 2025-04-21
维护者: NKU Wiki Team
用法: 
    python cleanup_untitled_posts.py

定时任务设置:
    可以通过 setup_cleanup_cron.sh 脚本设置每天凌晨3点执行此脚本
"""

import os
import sys
import json
import logging
import datetime
import pymysql
from pathlib import Path

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(os.path.join('logs', 'cleanup_untitled_posts.log'))
    ]
)
logger = logging.getLogger(__name__)

def load_db_config():
    """从config.json加载数据库配置信息"""
    try:
        # 定位到项目根目录
        project_root = Path(__file__).parent.parent.parent
        config_path = project_root / 'config.json'
        
        if not config_path.exists():
            logger.error(f"配置文件不存在: {config_path}")
            return None
            
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # 提取数据库配置
        mysql_config = config.get('etl', {}).get('data', {}).get('mysql', {})
        
        if not mysql_config:
            logger.error("配置文件中未找到MySQL配置信息")
            return None
            
        db_config = {
            'host': mysql_config.get('host', 'localhost'),
            'port': int(mysql_config.get('port', 3306)),
            'user': mysql_config.get('user', 'root'),
            'password': mysql_config.get('password', ''),
            'db': mysql_config.get('name', 'nkuwiki'),
            'charset': 'utf8mb4'
        }
        return db_config
    except Exception as e:
        logger.error(f"加载数据库配置出错: {e}")
        return None

def delete_untitled_posts():
    """删除所有标题为"无标题"的帖子"""
    db_config = load_db_config()
    if not db_config:
        logger.error("无法加载数据库配置，退出任务")
        return False
    
    try:
        # 连接数据库
        connection = pymysql.connect(
            host=db_config['host'],
            port=db_config['port'],
            user=db_config['user'],
            password=db_config['password'],
            db=db_config['db'],
            charset=db_config['charset'],
            cursorclass=pymysql.cursors.DictCursor
        )
        
        with connection.cursor() as cursor:
            # 查询无标题帖子数量
            cursor.execute("SELECT COUNT(*) as count FROM wxapp_post WHERE title='无标题'")
            result = cursor.fetchone()
            count = result['count']
            
            if count > 0:
                # 删除无标题帖子
                cursor.execute("DELETE FROM wxapp_post WHERE title='无标题'")
                connection.commit()
                logger.info(f"成功删除 {count} 个无标题帖子")
            else:
                logger.info("没有找到无标题帖子")
                
        connection.close()
        return True
    
    except Exception as e:
        logger.error(f"删除无标题帖子时出错: {e}")
        return False

if __name__ == "__main__":
    logger.info("开始执行无标题帖子清理任务...")
    start_time = datetime.datetime.now()
    
    # 确保日志目录存在
    os.makedirs('logs', exist_ok=True)
    
    # 执行删除操作
    success = delete_untitled_posts()
    
    end_time = datetime.datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    if success:
        logger.info(f"清理任务完成，耗时 {duration:.2f} 秒")
    else:
        logger.error(f"清理任务失败，耗时 {duration:.2f} 秒") 