"""
速率限制工具模块
提供令牌桶、滑动窗口等限流功能
"""
import threading
import time
from typing import Optional, Dict


class TokenBucket:
    """
    令牌桶限流器
    
    以固定速率生成令牌，请求需要消耗令牌才能执行，用于限制接口调用频率
    """
    def __init__(self, tpm: int, timeout: Optional[float] = None):
        """
        初始化令牌桶
        
        Args:
            tpm: 每分钟生成的令牌数量(tokens per minute)
            timeout: 获取令牌的超时时间(秒)，None表示无限等待
        """
        self.capacity = int(tpm)  # 令牌桶容量
        self.tokens = 0  # 初始令牌数为0
        self.rate = int(tpm) / 60  # 令牌每秒生成速率
        self.timeout = timeout  # 等待令牌超时时间
        self.cond = threading.Condition()  # 条件变量
        self.is_running = True
        # 开启令牌生成线程
        threading.Thread(target=self._generate_tokens, daemon=True).start()

    def _generate_tokens(self):
        """生成令牌的后台线程"""
        while self.is_running:
            with self.cond:
                if self.tokens < self.capacity:
                    self.tokens += 1
                self.cond.notify()  # 通知获取令牌的线程
            time.sleep(1 / self.rate)

    def get_token(self) -> bool:
        """
        获取令牌
        
        Returns:
            bool: 是否成功获取令牌，超时则返回False
        """
        with self.cond:
            while self.tokens <= 0:
                if not self.is_running:
                    return False
                if self.timeout is None:
                    self.cond.wait()  # 无限等待
                else:
                    flag = self.cond.wait(self.timeout)
                    if not flag:  # 超时
                        return False
            self.tokens -= 1
        return True

    def close(self):
        """关闭令牌桶，停止生成令牌"""
        self.is_running = False
        with self.cond:
            self.cond.notify_all()  # 通知所有等待的线程


class SlidingWindowCounter:
    """
    滑动窗口计数器
    
    按时间窗口统计请求次数，用于限制请求频率
    """
    def __init__(self, window_size: int = 60, max_requests: int = 100):
        """
        初始化滑动窗口计数器
        
        Args:
            window_size: 窗口大小(秒)
            max_requests: 窗口期内允许的最大请求数
        """
        self.window_size = window_size
        self.max_requests = max_requests
        self.requests: Dict[str, int] = {}  # 键是时间戳，值是该时间戳的请求数
        self.lock = threading.Lock()
    
    def can_request(self, key: str = "default") -> bool:
        """
        检查是否允许请求
        
        Args:
            key: 请求标识，用于区分不同来源的请求
            
        Returns:
            bool: 是否允许请求
        """
        now = int(time.time())
        
        with self.lock:
            # 清理过期的时间窗口
            cutoff = now - self.window_size
            self.requests = {ts: count for ts, count in self.requests.items() 
                            if int(ts) > cutoff}
            
            # 计算当前窗口内的请求总数
            total_requests = sum(self.requests.values())
            
            # 检查是否超过限制
            if total_requests >= self.max_requests:
                return False
            
            # 更新请求计数
            current_second = str(now)
            if current_second in self.requests:
                self.requests[current_second] += 1
            else:
                self.requests[current_second] = 1
                
            return True


class IPRateLimiter:
    """
    基于IP的速率限制器
    
    对不同的IP地址应用不同的速率限制
    """
    def __init__(self, requests_per_minute: int = 60, window_size: int = 60):
        """
        初始化IP速率限制器
        
        Args:
            requests_per_minute: 每分钟允许的请求数
            window_size: 滑动窗口大小(秒)
        """
        self.requests_per_minute = requests_per_minute
        self.window_size = window_size
        self.ip_counters: Dict[str, SlidingWindowCounter] = {}
        self.lock = threading.Lock()
    
    def can_request(self, ip: str) -> bool:
        """
        检查指定IP是否允许请求
        
        Args:
            ip: IP地址
            
        Returns:
            bool: 是否允许请求
        """
        with self.lock:
            if ip not in self.ip_counters:
                self.ip_counters[ip] = SlidingWindowCounter(
                    window_size=self.window_size,
                    max_requests=self.requests_per_minute
                )
        
        return self.ip_counters[ip].can_request() 