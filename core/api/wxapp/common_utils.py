"""
微信小程序公共工具模块
提供在各API模块之间共享的工具函数和方法
"""
from datetime import datetime
from typing import Dict, Any, List

# 日期时间格式化
def format_datetime(dt):
    """格式化日期时间"""
    if not dt:
        # 如果dt为None，使用当前时间
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return dt.strftime("%Y-%m-%d %H:%M:%S")

# 数据库准备
def prepare_db_data(data_dict, is_create=False):
    """
    准备数据库数据，处理通用字段
    
    Args:
        data_dict: 原始数据字典
        is_create: 是否为创建操作
        
    Returns:
        处理后的数据字典
    """
    result = dict(data_dict)
    
    # 处理JSON字段
    for field in ['images', 'tags', 'liked_users', 'favorite_users']:
        if field in result and result[field] is not None:
            result[field] = str(result[field])
    
    # 添加创建/更新时间
    current_time = format_datetime(datetime.now())
    if is_create:
        result['create_time'] = current_time
    result['update_time'] = current_time
    
    return result

# JSON字段处理
def process_json_fields(data_dict, json_fields=None):
    """
    处理JSON字段，确保格式正确
    
    Args:
        data_dict: 数据字典
        json_fields: 需要处理的JSON字段列表
        
    Returns:
        处理后的数据字典
    """
    if json_fields is None:
        json_fields = ['images', 'tags', 'liked_users', 'favorite_users']
    
    if not data_dict:
        return data_dict
    
    result = dict(data_dict)
    
    for field in json_fields:
        if field in result:
            value = result[field]
            if isinstance(value, str):
                try:
                    import json
                    parsed_value = json.loads(value)
                    result[field] = parsed_value
                except:
                    # 如果解析失败，设置为空列表
                    result[field] = []
            elif value is None:
                result[field] = []
    
    # 为了兼容前端，增加author_name和author_avatar字段
    if 'user_name' in result and 'author_name' not in result:
        result['author_name'] = result['user_name']
    
    if 'user_avatar' in result and 'author_avatar' not in result:
        result['author_avatar'] = result['user_avatar']
    
    return result 