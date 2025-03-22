"""处理JSON字段的工具函数"""
import json
from loguru import logger
from typing import Dict, Any, List, Optional

def process_post_json_fields(post_data: Dict[str, Any]) -> Dict[str, Any]:
    """处理帖子数据中的JSON字段，确保格式正确并计算相关计数
    
    Args:
        post_data: 帖子数据字典
        
    Returns:
        处理后的帖子数据字典
    """
    try:
        post_copy = post_data.copy()
        
        # 处理images字段
        if 'images' in post_copy:
            try:
                if isinstance(post_copy['images'], str) and post_copy['images'].strip():
                    post_copy['images'] = json.loads(post_copy['images'])
                elif post_copy['images'] is None or post_copy['images'] == '':
                    post_copy['images'] = []
            except Exception as e:
                logger.error(f"解析帖子images字段失败: {str(e)}, 原值: {post_copy.get('images')}")
                post_copy['images'] = []
        
        # 处理tags字段
        if 'tags' in post_copy:
            try:
                if isinstance(post_copy['tags'], str) and post_copy['tags'].strip():
                    post_copy['tags'] = json.loads(post_copy['tags'])
                elif post_copy['tags'] is None or post_copy['tags'] == '':
                    post_copy['tags'] = []
            except Exception as e:
                logger.error(f"解析帖子tags字段失败: {str(e)}, 原值: {post_copy.get('tags')}")
                post_copy['tags'] = []
        
        # 处理liked_users字段
        if 'liked_users' in post_copy:
            try:
                if isinstance(post_copy['liked_users'], str) and post_copy['liked_users'].strip():
                    post_copy['liked_users'] = json.loads(post_copy['liked_users'])
                elif post_copy['liked_users'] is None or post_copy['liked_users'] == '':
                    post_copy['liked_users'] = []
            except Exception as e:
                logger.error(f"解析帖子liked_users字段失败: {str(e)}, 原值: {post_copy.get('liked_users')}")
                post_copy['liked_users'] = []
                
        # 处理favorite_users字段
        if 'favorite_users' in post_copy:
            try:
                if isinstance(post_copy['favorite_users'], str) and post_copy['favorite_users'].strip():
                    post_copy['favorite_users'] = json.loads(post_copy['favorite_users'])
                elif post_copy['favorite_users'] is None or post_copy['favorite_users'] == '':
                    post_copy['favorite_users'] = []
            except Exception as e:
                logger.error(f"解析帖子favorite_users字段失败: {str(e)}, 原值: {post_copy.get('favorite_users')}")
                post_copy['favorite_users'] = []
        
        # 确保likes和favorite_count计数正确
        if 'liked_users' in post_copy and isinstance(post_copy['liked_users'], list):
            # 如果存在liked_users，确保likes字段与点赞用户数量一致
            post_copy['likes'] = len(post_copy['liked_users'])
            
        if 'favorite_users' in post_copy and isinstance(post_copy['favorite_users'], list):
            # 如果存在favorite_users，确保favorite_count字段与收藏用户数量一致
            post_copy['favorite_count'] = len(post_copy['favorite_users'])
        
        return post_copy
    except Exception as e:
        logger.error(f"处理JSON字段失败: {str(e)}")
        return post_data  # 如果处理失败，返回原始数据

def process_post_create_data(post_data: Dict[str, Any]) -> Dict[str, Any]:
    """处理创建帖子时的数据，确保所有字段格式正确
    
    Args:
        post_data: 创建帖子的数据字典
        
    Returns:
        处理后的帖子数据字典
    """
    try:
        post_copy = post_data.copy()
        
        # 确保必要的JSON字段为空数组字符串
        json_fields = ['images', 'tags', 'liked_users', 'favorite_users']
        for field in json_fields:
            if field not in post_copy or post_copy[field] is None:
                post_copy[field] = '[]'
            elif isinstance(post_copy[field], list):
                post_copy[field] = json.dumps(post_copy[field])
        
        # 确保计数字段初始化
        post_copy['likes'] = post_copy.get('likes', 0)
        post_copy['favorite_count'] = post_copy.get('favorite_count', 0)
        post_copy['comment_count'] = post_copy.get('comment_count', 0)
        
        return post_copy
    except Exception as e:
        logger.error(f"处理创建帖子数据失败: {str(e)}")
        return post_data 