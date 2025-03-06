# 删除get_yaml_data函数

from config import Config

def get_rag_config():
    """
    从全局配置中获取RAG相关配置，兼容原easyrag.yaml的结构
    使用Config类的get_rag_config方法
    
    Returns:
        dict: 与原easyrag.yaml结构相同的配置字典
    """
    return Config().get_rag_config()

def get_config_value(key, default=None):
    """
    直接从全局配置获取指定键的值
    兼容项目中的Config().get("key")模式
    
    Args:
        key: 配置键名
        default: 默认值
        
    Returns:
        配置值
    """
    return Config().get(key, default)
