import os

def is_running_in_docker() -> bool:
    """
    通过检查特定文件的存在来判断程序是否在Docker容器中运行。
    这是一个常用且简单的方法。
    """
    return os.path.exists('/.dockerenv') 