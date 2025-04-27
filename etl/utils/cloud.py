# 云服务相关工具
# 合并wx_cloud.py内容
from etl.utils.wx_cloud import *

__all__ = []
if hasattr(wx_cloud, '__all__'):
    __all__ += wx_cloud.__all__ 