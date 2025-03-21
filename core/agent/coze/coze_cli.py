#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Coze命令行交互工具 - 轻量版
可以用于快速测试Coze对话功能，不依赖完整项目环境
"""

import sys
import os
import time
import json
import argparse
import logging
import requests
from pathlib import Path
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("coze_cli")

# 项目根目录
ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent

# 加载配置
def load_config():
    """加载配置文件"""
    config_path = ROOT_DIR / "config.json"
    if not config_path.exists():
        logger.warning(f"配置文件不存在: {config_path}")
        return {}
        
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"加载配置文件失败: {e}")
        return {}

CONFIG = load_config()

def get_config(key, default=None):
    """获取配置值"""
    parts = key.split(".")
    value = CONFIG
    for part in parts:
        if isinstance(value, dict) and part in value:
            value = value[part]
        else:
            return default
    return value

# 创建带重试功能的HTTP会话
def create_http_session():
    """创建HTTP会话，带连接池和重试功能"""
    session = requests.Session()
    
    # 设置重试策略
    retry_strategy = Retry(
        total=3,  # 最多重试3次
        backoff_factor=0.3,  # 重试等待时间
        status_forcelist=[429, 500, 502, 503, 504],  # 哪些状态码需要重试
        allowed_methods=["GET", "POST"]  # 允许重试的HTTP方法
    )
    
    # 创建适配器，最大连接数为10
    adapter = HTTPAdapter(
        max_retries=retry_strategy,
        pool_connections=10,
        pool_maxsize=10
    )
    
    # 注册适配器
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    # 设置超时时间
    session.timeout = (3.05, 60)  # (连接超时, 读取超时)
    
    return session

# 简化版的CozeAgentSDK，仅包含CLI工具需要的功能
class LiteCozeAgentSDK:
    def __init__(self, bot_id, use_cn_api=True, use_sdk=True):
        self.bot_id = bot_id
        self.use_cn_api = use_cn_api
        self.use_sdk = use_sdk
        
        # 获取API密钥
        self.api_key = get_config("core.agent.coze.api_key", "")
        
        if not self.api_key:
            raise ValueError("API 密钥未配置，请在config.json中配置 core.agent.coze.api_key")
            
        # 根据配置设置API基地址
        if use_cn_api:
            # 国内API
            self.base_url = "https://api.coze.cn"
        else:
            # 海外API
            self.base_url = "https://api.coze.com"
            
        # 如果使用SDK，检查是否可用
        if use_sdk:
            try:
                from cozepy import Coze, TokenAuth, Message, ChatEventType
                self.sdk_available = True
                
                # 初始化客户端
                self.client = Coze(
                    auth=TokenAuth(token=self.api_key),
                    base_url=self.base_url
                )
            except ImportError:
                logger.warning("无法导入cozepy SDK，切换到HTTP模式")
                self.sdk_available = False
                self.use_sdk = False
        else:
            self.sdk_available = False
            
        # 创建HTTP会话
        self.session = create_http_session()
            
        logger.info(f"LiteCozeAgentSDK 初始化完成: API={self.base_url}, 模式={'SDK' if self.use_sdk else 'HTTP'}")
        
    def _get_headers(self):
        """获取HTTP请求头"""
        return {
            'Authorization': f"Bearer {self.api_key}",
            'Content-Type': 'application/json'
        }
        
    def reply(self, query):
        """
        同步请求对话响应
        
        Args:
            query: 用户输入
            
        Returns:
            助手回复内容，如果失败则返回None
        """
        if self.use_sdk and self.sdk_available:
            return self._sdk_reply(query)
        else:
            return self._http_reply(query)
            
    def _sdk_reply(self, query):
        """使用SDK进行对话请求"""
        try:
            from cozepy import Message
            logger.info(f"开始请求(SDK): {query[:30]}...")
            
            # 创建对话
            chat = self.client.chat.create(
                bot_id=self.bot_id,
                user_id="default_user",
                additional_messages=[
                    Message.build_user_question_text(query)
                ]
            )
            
            # 获取会话ID和聊天ID
            conversation_id = chat.conversation_id
            chat_id = chat.id
            
            # 等待对话完成
            for attempt in range(60):  # 最多等待60次
                time.sleep(0.3)  # 每次等待0.3秒
                
                try:
                    chat_status = self.client.chat.retrieve(
                        conversation_id=conversation_id,
                        chat_id=chat_id
                    )
                    status = chat_status.status
                    
                    if status in ["completed", "required_action"]:
                        logger.info(f"对话完成，状态: {status}，尝试次数: {attempt+1}")
                        break
                except Exception as e:
                    logger.warning(f"获取对话状态时出错: {e}")
                    continue
                    
            # 获取消息列表
            messages = self.client.chat.messages.list(
                conversation_id=conversation_id,
                chat_id=chat_id
            )
            
            # 提取助手回复
            for message in messages:
                if message.role == "assistant" and message.type == "answer":
                    return message.content
                    
            logger.error("未找到助手回复")
            return None
            
        except Exception as e:
            logger.exception(f"SDK请求失败: {e}")
            # 尝试切换到HTTP模式
            logger.info("尝试切换到HTTP模式...")
            return self._http_reply(query)
            
    def _http_reply(self, query):
        """使用HTTP请求进行对话"""
        try:
            logger.info(f"开始请求(HTTP): {query[:30]}...")
            
            # 构建请求URL
            url = f"{self.base_url}/v3/chat"
            
            # 构建请求体
            payload = {
                "bot_id": self.bot_id,
                "user_id": "default_user",
                "stream": False,
                "additional_messages": [
                    {
                        "content": query,
                        "content_type": "text",
                        "role": "user",
                        "type": "question"
                    }
                ]
            }
            
            # 发送请求
            response = self.session.post(url, headers=self._get_headers(), json=payload)
            response.raise_for_status()
            
            response_data = response.json()
            conversation_id = response_data.get("data", {}).get("conversation_id")
            chat_id = response_data.get("data", {}).get("id")
            
            if not conversation_id or not chat_id:
                logger.error("创建对话失败，无法获取会话ID或聊天ID")
                return None
                
            # 轮询对话状态
            for attempt in range(60):  # 最多等待60次
                time.sleep(0.3)  # 每次等待0.3秒
                
                try:
                    # 构建请求URL
                    status_url = f"{self.base_url}/v3/chat/retrieve?chat_id={chat_id}&conversation_id={conversation_id}"
                    
                    # 发送请求
                    status_response = self.session.get(status_url, headers=self._get_headers())
                    status_response.raise_for_status()
                    
                    status_data = status_response.json()
                    status = status_data.get("data", {}).get("status")
                    
                    if status in ["completed", "required_action"]:
                        logger.info(f"对话完成，状态: {status}，尝试次数: {attempt+1}")
                        break
                except Exception as e:
                    logger.warning(f"获取对话状态时出错: {e}")
                    continue
                    
            # 获取消息列表
            try:
                # 构建请求URL
                messages_url = f"{self.base_url}/v3/chat/message/list?chat_id={chat_id}&conversation_id={conversation_id}"
                
                # 发送请求
                messages_response = self.session.get(messages_url, headers=self._get_headers())
                messages_response.raise_for_status()
                
                messages_data = messages_response.json()
                messages = messages_data.get("data", [])
                
                # 提取助手回复
                for message in messages:
                    if message.get("role") == "assistant" and message.get("type") == "answer":
                        return message.get("content")
                        
                logger.error("未找到助手回复")
                return None
            except Exception as e:
                logger.exception(f"获取消息列表失败: {e}")
                return None
                
        except Exception as e:
            logger.exception(f"HTTP请求失败: {e}")
            return None
            
    def stream_reply(self, query):
        """
        流式返回对话响应
        
        Args:
            query: 用户输入
            
        Returns:
            生成器，每次迭代返回一个响应片段
        """
        if self.use_sdk and self.sdk_available:
            return self._sdk_stream_reply(query)
        else:
            return self._http_stream_reply(query)
            
    def _sdk_stream_reply(self, query):
        """使用SDK进行流式对话请求"""
        try:
            from cozepy import Message, ChatEventType
            logger.info(f"开始流式请求(SDK): {query[:30]}...")
            
            # 使用SDK的流式接口
            stream = self.client.chat.stream(
                bot_id=self.bot_id,
                user_id="default_user",
                additional_messages=[
                    Message.build_user_question_text(query)
                ]
            )
            
            # 处理流式响应
            for event in stream:
                if event.event == ChatEventType.CONVERSATION_MESSAGE_DELTA:
                    if event.message and event.message.content:
                        yield event.message.content
                        
        except Exception as e:
            logger.exception(f"SDK流式请求失败: {e}")
            # 尝试切换到HTTP模式
            logger.info("尝试切换到HTTP模式...")
            for chunk in self._http_stream_reply(query):
                yield chunk
                
    def _http_stream_reply(self, query):
        """使用HTTP请求进行流式对话请求"""
        try:
            logger.info(f"开始流式请求(HTTP): {query[:30]}...")
            
            # 构建请求URL
            url = f"{self.base_url}/v3/chat"
            
            # 构建请求体
            payload = {
                "bot_id": self.bot_id,
                "user_id": "default_user",
                "stream": True,
                "additional_messages": [
                    {
                        "content": query,
                        "content_type": "text",
                        "role": "user",
                        "type": "question"
                    }
                ]
            }
            
            # 自定义请求头，优化流式传输
            headers = self._get_headers()
            headers.update({
                'Accept': 'text/event-stream',
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'X-Accel-Buffering': 'no'  # 禁用代理服务器的缓冲
            })
            
            # 发送请求
            with self.session.post(url, headers=headers, json=payload, stream=True) as response:
                response.raise_for_status()
                
                # 使用更高效的缓冲区处理
                buffer = b""
                last_chunk_time = time.time()
                
                for chunk in response.iter_content(chunk_size=1024):  # 提高块大小至1KB
                    if not chunk:
                        continue
                        
                    # 记录收到数据的时间
                    current_time = time.time()
                    if current_time - last_chunk_time > 1.0:  # 如果超过1秒没有收到数据，记录日志
                        logger.debug(f"数据流中断 {current_time - last_chunk_time:.2f}秒")
                    last_chunk_time = current_time
                    
                    buffer += chunk
                    
                    # 处理缓冲区中的行
                    while b'\n' in buffer:
                        try:
                            line, buffer = buffer.split(b'\n', 1)
                            if not line:  # 跳过空行
                                continue
                                
                            # 尝试解码行
                            try:
                                line = line.decode('utf-8')
                                
                                # 检查是否是SSE数据行
                                if line.startswith('data: '):
                                    data = line[6:]  # 去掉 'data: ' 前缀
                                    
                                    # 检查是否是结束标记
                                    if data == '[DONE]':
                                        logger.debug("流式响应结束")
                                        return
                                    
                                    # 尝试解析JSON数据
                                    try:
                                        json_data = json.loads(data)
                                        if 'data' in json_data and isinstance(json_data['data'], dict):
                                            content = json_data['data'].get('content', '')
                                            if content:
                                                yield content
                                    except json.JSONDecodeError:
                                        logger.debug(f"非JSON数据: {data[:30]}...")
                            except UnicodeDecodeError:
                                # 对于解码错误，跳过当前行
                                logger.debug("跳过无法解码的行")
                                continue
                        except Exception as e:
                            logger.debug(f"处理行时出错: {str(e)}")
                            continue
                
                # 处理剩余的buffer
                if buffer:
                    try:
                        line = buffer.decode('utf-8')
                        if line.startswith('data: '):
                            data = line[6:]
                            if data != '[DONE]':
                                try:
                                    json_data = json.loads(data)
                                    if 'data' in json_data and isinstance(json_data['data'], dict):
                                        content = json_data['data'].get('content', '')
                                        if content:
                                            yield content
                                except json.JSONDecodeError:
                                    logger.debug(f"剩余缓冲区非JSON数据: {data[:30]}...")
                    except Exception as e:
                        logger.debug(f"处理剩余缓冲区出错: {str(e)}")
                
        except Exception as e:
            logger.exception(f"HTTP流式请求失败: {e}")
            yield f"请求失败: {e}"

def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='Coze命令行交互工具 - 轻量版')
    
    parser.add_argument('--stream', '-s', action='store_true', 
                        help='使用流式响应模式')
    
    parser.add_argument('--http', action='store_true', 
                        help='使用HTTP模式而非SDK模式')
    
    parser.add_argument('--bot', '-b', type=str, 
                        help='指定Bot ID，不指定则使用配置文件中的值')
    
    parser.add_argument('--query', '-q', type=str, 
                        help='直接指定问题，而不进入交互模式')
    
    return parser.parse_args()

def clear_screen():
    """清屏"""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header():
    """打印标题"""
    clear_screen()
    print("\n" + "="*60)
    print("                  Coze 命令行交互工具 - 轻量版")
    print("="*60)
    print("输入问题与AI对话，输入'exit'或'quit'退出")
    print("输入'clear'清屏，输入'help'查看帮助")
    print("-"*60 + "\n")

def print_help():
    """打印帮助信息"""
    print("\n" + "-"*60)
    print("命令列表:")
    print("  exit, quit - 退出程序")
    print("  clear      - 清屏")
    print("  help       - 显示此帮助信息")
    print("  stream     - 切换到流式响应模式")
    print("  normal     - 切换到普通响应模式")
    print("  http       - 切换到HTTP请求模式")
    print("  sdk        - 切换到SDK请求模式")
    print("-"*60 + "\n")

def main():
    """主函数"""
    args = parse_arguments()
    
    # 获取bot_id
    bot_id = args.bot or get_config("core.agent.coze.flash_bot_id")
    
    if not bot_id:
        print("错误: 未配置bot_id，请在config.json中设置core.agent.coze.flash_bot_id或使用--bot参数")
        return
    
    # 初始化SDK配置
    use_stream = args.stream  # 是否启用流式响应
    use_sdk = not args.http   # 是否使用SDK模式
    
    # 创建SDK实例
    try:
        sdk = LiteCozeAgentSDK(
            bot_id=bot_id, 
            use_cn_api=True,
            use_sdk=use_sdk
        )
    except Exception as e:
        print(f"初始化失败: {e}")
        return
    
    # 单次查询模式
    if args.query:
        if use_stream:
            # 流模式
            print("问题: " + args.query)
            print("\n回答: ", end="")
            full_response = ""
            for chunk in sdk.stream_reply(args.query):
                print(chunk, end="", flush=True)
                full_response += chunk
            print("\n")
        else:
            # 非流式模式
            print("问题: " + args.query)
            print("正在生成回答...")
            response = sdk.reply(args.query)
            if response:
                print("\n回答:\n" + response + "\n")
            else:
                print("\n获取回答失败\n")
        return
    
    # 交互模式
    print_header()
    
    mode_str = "普通"
    if use_stream:
        mode_str = "流式"
    
    print(f"当前模式: {mode_str}响应, {'SDK' if use_sdk else 'HTTP'}请求")
    print(f"Bot ID: {bot_id}")
    print("\n开始对话吧！\n")
    
    while True:
        # 获取用户输入
        user_input = input("问题: ")
        
        # 处理特殊命令
        if user_input.lower() in ['exit', 'quit']:
            print("再见！")
            break
        elif user_input.lower() == 'clear':
            print_header()
            continue
        elif user_input.lower() == 'help':
            print_help()
            continue
        elif user_input.lower() == 'stream':
            use_stream = True
            print("已切换到流式响应模式")
            continue
        elif user_input.lower() == 'normal':
            use_stream = False
            print("已切换到普通响应模式")
            continue
        elif user_input.lower() == 'http':
            use_sdk = False
            sdk = LiteCozeAgentSDK(bot_id=bot_id, use_cn_api=True, use_sdk=False)
            print("已切换到HTTP请求模式")
            continue
        elif user_input.lower() == 'sdk':
            use_sdk = True
            sdk = LiteCozeAgentSDK(bot_id=bot_id, use_cn_api=True, use_sdk=True)
            print("已切换到SDK请求模式")
            continue
        elif not user_input.strip():
            continue
        
        # 开始计时
        start_time = time.time()
        
        try:
            if use_stream:
                # 流式回复
                print("\n回答: ", end="")
                full_response = ""
                for chunk in sdk.stream_reply(user_input):
                    print(chunk, end="", flush=True)
                    full_response += chunk
                
                # 计算响应时间和大小
                end_time = time.time()
                print(f"\n\n[用时: {end_time - start_time:.2f}秒, 长度: {len(full_response)}字符]")
            else:
                # 普通回复
                print("\n正在生成回答...")
                response = sdk.reply(user_input)
                
                # 计算响应时间
                end_time = time.time()
                
                if response:
                    print("\n回答:\n" + response)
                    print(f"\n[用时: {end_time - start_time:.2f}秒, 长度: {len(response)}字符]")
                else:
                    print("未收到回复")
        
        except Exception as e:
            print(f"\n发生错误: {e}")
            logger.exception("对话过程中发生异常")
        
        print("\n" + "-"*60)

if __name__ == "__main__":
    main() 