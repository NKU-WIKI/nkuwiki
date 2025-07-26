import os
import sys
# 获取当前文件的绝对路径
current_file = os.path.abspath(__file__)
# 获取上级目录路径
parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_file))))
# 将上级目录添加到 sys.path
sys.path.append(parent_dir)
from config import *
