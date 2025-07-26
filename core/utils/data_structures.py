"""
数据结构工具模块
提供各种自定义数据结构实现，如过期字典、排序字典和双端队列等
"""
from datetime import datetime, timedelta
import heapq
from queue import Full, Queue
from time import monotonic as time


class ExpiredDict(dict):
    """
    带有过期时间的字典
    
    字典的每个键值对都有一个过期时间，当获取时如果已过期，会自动删除该项
    """
    def __init__(self, expires_in_seconds):
        """
        初始化过期字典
        
        Args:
            expires_in_seconds: 过期时间（秒）
        """
        super().__init__()
        self.expires_in_seconds = expires_in_seconds

    def __getitem__(self, key):
        value, expiry_time = super().__getitem__(key)
        if datetime.now() > expiry_time:
            del self[key]
            raise KeyError("expired {}".format(key))
        self.__setitem__(key, value)
        return value

    def __setitem__(self, key, value):
        expiry_time = datetime.now() + timedelta(seconds=self.expires_in_seconds)
        super().__setitem__(key, (value, expiry_time))

    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default

    def __contains__(self, key):
        try:
            self[key]
            return True
        except KeyError:
            return False

    def keys(self):
        keys = list(super().keys())
        return [key for key in keys if key in self]

    def items(self):
        return [(key, self[key]) for key in self.keys()]

    def __iter__(self):
        return self.keys().__iter__()


class SortedDict(dict):
    """
    排序字典
    
    一个保持键值对按某种方式排序的字典
    """
    def __init__(self, sort_func=lambda k, v: k, init_dict=None, reverse=False):
        """
        初始化排序字典
        
        Args:
            sort_func: 排序函数，接收key和value作为参数
            init_dict: 初始字典或键值对列表
            reverse: 是否反向排序
        """
        if init_dict is None:
            init_dict = []
        if isinstance(init_dict, dict):
            init_dict = init_dict.items()
        self.sort_func = sort_func
        self.sorted_keys = None
        self.reverse = reverse
        self.heap = []
        for k, v in init_dict:
            self[k] = v

    def __setitem__(self, key, value):
        if key in self:
            super().__setitem__(key, value)
            for i, (priority, k) in enumerate(self.heap):
                if k == key:
                    self.heap[i] = (self.sort_func(key, value), key)
                    heapq.heapify(self.heap)
                    break
            self.sorted_keys = None
        else:
            super().__setitem__(key, value)
            heapq.heappush(self.heap, (self.sort_func(key, value), key))
            self.sorted_keys = None

    def __delitem__(self, key):
        super().__delitem__(key)
        for i, (priority, k) in enumerate(self.heap):
            if k == key:
                del self.heap[i]
                heapq.heapify(self.heap)
                break
        self.sorted_keys = None

    def keys(self):
        if self.sorted_keys is None:
            self.sorted_keys = [k for _, k in sorted(self.heap, reverse=self.reverse)]
        return self.sorted_keys

    def items(self):
        if self.sorted_keys is None:
            self.sorted_keys = [k for _, k in sorted(self.heap, reverse=self.reverse)]
        sorted_items = [(k, self[k]) for k in self.sorted_keys]
        return sorted_items

    def _update_heap(self, key):
        for i, (priority, k) in enumerate(self.heap):
            if k == key:
                new_priority = self.sort_func(key, self[key])
                if new_priority != priority:
                    self.heap[i] = (new_priority, key)
                    heapq.heapify(self.heap)
                    self.sorted_keys = None
                break

    def __iter__(self):
        return iter(self.keys())

    def __repr__(self):
        return f"{type(self).__name__}({dict(self)}, sort_func={self.sort_func.__name__}, reverse={self.reverse})"


class Dequeue(Queue):
    """
    双端队列
    
    在标准Queue基础上增加了从左侧插入的功能
    """
    def putleft(self, item, block=True, timeout=None):
        """
        在队列左侧（头部）添加元素
        
        Args:
            item: 要添加的元素
            block: 是否阻塞
            timeout: 超时时间
            
        Raises:
            Full: 如果队列已满且非阻塞
            ValueError: 如果timeout为负数
        """
        with self.not_full:
            if self.maxsize > 0:
                if not block:
                    if self._qsize() >= self.maxsize:
                        raise Full
                elif timeout is None:
                    while self._qsize() >= self.maxsize:
                        self.not_full.wait()
                elif timeout < 0:
                    raise ValueError("'timeout' must be a non-negative number")
                else:
                    endtime = time() + timeout
                    while self._qsize() >= self.maxsize:
                        remaining = endtime - time()
                        if remaining <= 0.0:
                            raise Full
                        self.not_full.wait(remaining)
            self._putleft(item)
            self.unfinished_tasks += 1
            self.not_empty.notify()

    def putleft_nowait(self, item):
        """在队列左侧（头部）添加元素，不阻塞"""
        return self.putleft(item, block=False)

    def _putleft(self, item):
        """实际在队列左侧（头部）添加元素的方法"""
        self.queue.appendleft(item) 