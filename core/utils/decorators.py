"""
装饰器工具模块
提供单例模式、时间检查等常用装饰器
"""
import re
import time
import functools
from typing import Any, Callable, TypeVar, cast, Dict
from singleton_decorator import singleton as singleton_decorator

T = TypeVar('T')


def time_checker(func: Callable) -> Callable:
    """
    时间检查装饰器
    
    检查当前时间是否在允许的服务时间范围内
    
    Args:
        func: 要装饰的函数
        
    Returns:
        包装后的函数
    """
    @functools.wraps(func)
    def _time_checker(self, *args, **kwargs):
        from core.utils.logger import logger
        from config import Config
        
        config = Config()
        chat_time_module = config.get("chat_time_module", False)

        if chat_time_module:
            chat_start_time = config.get("chat_start_time", "00:00")
            chat_stop_time = config.get("chat_stop_time", "24:00")

            time_regex = re.compile(r"^([01]?[0-9]|2[0-4])(:)([0-5][0-9])$")

            if not (time_regex.match(chat_start_time) and time_regex.match(chat_stop_time)):
                logger.warning("时间格式不正确，请在config.json中修改chat_start_time/chat_stop_time。")
                return None

            now_time = time.strptime(time.strftime("%H:%M"), "%H:%M")
            chat_start_time = time.strptime(chat_start_time, "%H:%M")
            chat_stop_time = time.strptime(chat_stop_time, "%H:%M")
            
            # 结束时间小于开始时间，跨天了
            if chat_stop_time < chat_start_time and (chat_start_time <= now_time or now_time <= chat_stop_time):
                return func(self, *args, **kwargs)
            # 结束大于开始时间代表，没有跨天
            elif chat_start_time < chat_stop_time and chat_start_time <= now_time <= chat_stop_time:
                return func(self, *args, **kwargs)
            else:
                # 定义匹配规则，如果以 #reconf 或者 #更新配置 结尾, 非服务时间可以修改开始/结束时间并重载配置
                pattern = re.compile(r"^.*#(?:reconf|更新配置)$")
                if args and hasattr(args[0], 'content') and pattern.match(args[0].content):
                    return func(self, *args, **kwargs)
                else:
                    logger.info("非服务时间内，不接受访问")
                    return None
        else:
            return func(self, *args, **kwargs)  # 未开启时间模块则直接回答

    return _time_checker


def retry(attempts: int = 3, delay: float = 1.0, backoff: float = 2.0, 
          exceptions: tuple = (Exception,)) -> Callable:
    """
    重试装饰器
    
    在遇到指定异常时自动重试函数
    
    Args:
        attempts: 最大重试次数
        delay: 初始延迟时间(秒)
        backoff: 延迟时间的增长因子
        exceptions: 需要重试的异常类型
        
    Returns:
        装饰器函数
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            from core.utils.logger import logger
            
            _delay = delay
            for attempt in range(1, attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt >= attempts:
                        logger.error(f"函数 {func.__name__} 在 {attempts} 次尝试后失败: {str(e)}")
                        raise
                    logger.warning(f"函数 {func.__name__} 第 {attempt} 次尝试失败: {str(e)}，{_delay}秒后重试")
                    time.sleep(_delay)
                    _delay *= backoff
        return wrapper
    return decorator


def timed(func: Callable) -> Callable:
    """
    计时装饰器
    
    记录函数执行时间
    
    Args:
        func: 要装饰的函数
        
    Returns:
        包装后的函数
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        from core.utils.logger import logger
        
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        logger.debug(f"函数 {func.__name__} 执行时间: {end - start:.4f}秒")
        return result
    return wrapper 