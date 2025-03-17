import sys
import time
import os
from typing import Optional, Union
from loguru import logger

from core.bridge.context import *
from core.bridge.reply import Reply, ReplyType
from services.chat_channel import ChatChannel, check_prefix
from services.chat_message import ChatMessage
from config import Config


class TerminalMessage(ChatMessage):
    def __init__(
        self,
        msg_id: str,
        content: str,
        ctype: ContextType = ContextType.TEXT,
        from_user_id: str = "User",
        to_user_id: str = "coze",
        other_user_id: str = "coze",
    ):
        self.msg_id = msg_id
        self.ctype = ctype
        self.content = content
        self.from_user_id = from_user_id
        self.to_user_id = to_user_id
        self.other_user_id = other_user_id


class TerminalChannel(ChatChannel):
    NOT_SUPPORT_REPLYTYPE = [ReplyType.VOICE]

    def __init__(self):
        super().__init__()
        self._last_response_time = 0
        self._min_response_interval = Config().get("services.terminal.min_response_interval", 0.1)

    def send(self, reply: Reply, context: Context):
        """发送回复到终端"""
        # 控制响应频率
        current_time = time.time()
        if current_time - self._last_response_time < self._min_response_interval:
            time.sleep(self._min_response_interval)
        self._last_response_time = current_time

        try:
            if reply.type == ReplyType.IMAGE:
                # 保持图片显示的换行，因为图片需要更多空间
                print("\n\033[36m南开小知>\033[0m ", end="", flush=True)
                self._handle_image_reply(reply)
            elif reply.type == ReplyType.IMAGE_URL:
                # 保持图片URL显示的换行
                print("\n\033[36m南开小知>\033[0m ", end="", flush=True)
                self._handle_image_url_reply(reply)
            elif reply.type == ReplyType.TEXT or reply.type == ReplyType.STREAM:
                # 减少文本回复前的空行
                print("\033[36m南开小知>\033[0m ", end="", flush=True)
                self._handle_text_reply(reply)
            else:
                print(f"\033[36m南开小知>\033[0m [不支持的消息类型: {reply.type}]")
        except Exception as e:
            print(f"[发送回复失败: {str(e)}]")
        
        # 确保回复结束后添加User>前缀并立即刷新输出
        print("\n\033[33mUser>\033[0m ", end="")
        sys.stdout.flush()
        logger.debug("[DEBUG] 显示用户提示符完成")  # 添加调试信息

    def _handle_image_reply(self, reply: Reply):
        """处理图片回复"""
        try:
            from PIL import Image
            image_storage = reply.content
            image_storage.seek(0)
            img = Image.open(image_storage)
            print("\n<IMAGE>")
            img.show()
        except Exception as e:
            logger.error(f"显示图片失败: {str(e)}")
            print(f"\n[显示图片失败: {str(e)}]")

    def _handle_image_url_reply(self, reply: Reply):
        """处理图片URL回复"""
        try:
            import io
            import requests
            from PIL import Image
            
            img_url = reply.content
            print(f"\n<IMAGE URL: {img_url}>")
            
            with requests.get(img_url, stream=True) as response:
                response.raise_for_status()
                image_storage = io.BytesIO()
                for block in response.iter_content(1024):
                    image_storage.write(block)
                image_storage.seek(0)
                img = Image.open(image_storage)
                img.show()
        except Exception as e:
            logger.error(f"显示网络图片失败: {str(e)}")
            print(f"\n[显示网络图片失败: {str(e)}]")

    def _handle_text_reply(self, reply: Reply):
        """处理文本回复"""
        try:
            content = reply.content
            
            # 首先检查是否为生成器对象
            if hasattr(content, '__iter__') and hasattr(content, '__next__') and not isinstance(content, (str, list, tuple)):
                # 处理生成器对象
                logger.debug("[DEBUG] 处理生成器类型的内容")
                for chunk in content:
                    print(chunk, end="", flush=True)
                # 确保流式输出完成后立即刷新
                sys.stdout.flush()
            elif isinstance(content, (list, tuple)):
                # 处理列表或元组类型的流式输出
                logger.debug("[DEBUG] 处理列表/元组类型的内容")
                for chunk in content:
                    print(chunk, end="", flush=True)
                # 确保流式输出完成后立即刷新
                sys.stdout.flush()
            elif isinstance(content, str):
                # 处理字符串类型的内容，按行添加前缀
                logger.debug("[DEBUG] 处理字符串类型的内容")
                lines = content.split('\n')
                for i, line in enumerate(lines):
                    if i > 0:  # 如果不是第一行，先换行
                        print("\n\033[36m南开小知>\033[0m ", end="", flush=True)
                    print(line, end="", flush=True)
                # 确保文本输出完成后立即刷新
                sys.stdout.flush()
            else:
                # 未知类型的内容，尝试直接打印
                logger.debug(f"[DEBUG] 处理未知类型的内容: {type(content)}")
                print(str(content), end="", flush=True)
                sys.stdout.flush()
        except Exception as e:
            logger.error(f"显示文本失败: {str(e)}")
            print(f"\n[显示文本失败: {str(e)}]")

    def startup(self):
        """启动终端交互"""
        context = Context()

        # 显示欢迎信息
        show_welcome = Config().get("services.terminal.show_welcome", True)
        if show_welcome:
            # 清屏
            os.system('cls' if os.name == 'nt' else 'clear')
            
            # 模拟终端窗口顶部的红黄绿三个按钮
            print("\033[31m●\033[33m●\033[32m●\033[0m")
            
            # 线条风格的NKUWIKI ASCII艺术LOGO - 更清晰的字母版本
            logo = """
  _   _ _  __ _   _ __        __ _  _   ___
 | \\ | | |/ /| | | / /       / /| |/ | |_ _|
 |  \\| | ' / | | |/ /  /\\  / / | ' |  | |
 | |\\  | . \\ | |< <  /  \\/  /  | . |  | |
 |_| \\_|_|\\_\\|_| \\_\\/    \\/   |_|\\_| |___|"""
            # 使用绿色显示ASCII艺术
            print("\033[32m" + logo + "\033[0m")
            
            # 简洁的欢迎信息 - 不再添加额外空行
            print("🎓 南开知识共同体 - 开源·共治·普惠")
            print("输入 'exit' 退出 | 'help' 获取帮助 | 'clear' 清屏")
        
        # 减少初始问候语前的空行
        print("\033[36m南开小知>\033[0m 你好！请问有什么可以帮你的吗？")
        print("\033[33mUser>\033[0m ", end="")
        sys.stdout.flush()
        logger.debug("[DEBUG] 初始用户提示符显示完成")  # 添加调试信息
        
        msg_id = 0
        # 获取默认的流式模式设置
        stream_mode = Config().get("services.terminal.stream_output", True)
        
        while True:
            try:
                logger.debug("[DEBUG] 等待用户输入...")  # 添加调试信息
                prompt = self.get_input()
                logger.debug(f"[DEBUG] 用户输入: {prompt}")  # 添加调试信息
                
                # 处理特殊命令
                if prompt.lower() == 'exit':
                    print("\n感谢使用，再见! 👋")
                    sys.exit(0)
                elif prompt.lower() == 'help':
                    self._show_help()
                    continue
                elif prompt.lower() == 'stream on':
                    stream_mode = True
                    print("\n已启用流式输出模式")
                    print("\033[33mUser>\033[0m ", end="")
                    sys.stdout.flush()
                    continue
                elif prompt.lower() == 'stream off':
                    stream_mode = False
                    print("\n已关闭流式输出模式")
                    print("\033[33mUser>\033[0m ", end="")
                    sys.stdout.flush()
                    continue
                elif prompt.lower() == 'clear':
                    # 清屏命令
                    os.system('cls' if os.name == 'nt' else 'clear')
                    # 显示简化的标志
                    print("\033[31m●\033[33m●\033[32m●\033[0m")
                    print("\033[32m __    _ ____  ___    ___      _ ____  ___ \033[0m")
                    print("\033[33mUser>\033[0m ", end="")
                    sys.stdout.flush()
                    continue
                elif prompt.lower() == 'debug':
                    # 添加调试命令
                    print("\n[DEBUG MODE] 输出调试信息")
                    self._diagnostic_check()  # 调用诊断检查函数
                    print("\033[33mUser>\033[0m ", end="")
                    sys.stdout.flush()
                    continue
                elif not prompt.strip():
                    print("\033[33mUser>\033[0m ", end="")
                    sys.stdout.flush()
                    continue
                
                logger.debug("[DEBUG] 处理用户输入...")  # 添加调试信息
                msg_id += 1
                trigger_prefixs = Config().get("services.terminal.single_chat_prefix", 
                                              Config().get("single_chat_prefix", [""]))
                if check_prefix(prompt, trigger_prefixs) is None:
                    prompt = trigger_prefixs[0] + prompt

                context = self._compose_context(
                    ContextType.TEXT, 
                    prompt, 
                    msg=TerminalMessage(msg_id, prompt)
                )
                context["isgroup"] = False
                context["stream_output"] = stream_mode
                
                if context:
                    logger.debug("[DEBUG] 生产消息到处理队列")  # 添加调试信息
                    self.produce(context)
                else:
                    raise Exception("context is None")
                    
            except KeyboardInterrupt:
                print("\n\n感谢使用，再见! 👋")
                sys.exit(0)
            except Exception as e:
                logger.error(f"处理用户输入出错: {str(e)}")
                print(f"\n[错误: {str(e)}]")
                print("\n\033[33mUser>\033[0m ", end="")
                sys.stdout.flush()

    def _show_help(self):
        """显示帮助信息"""
        help_text = """
\033[32m======================= 南开小知使用帮助 =======================\033[0m
  \033[36m基础命令:\033[0m
    help    - 显示此帮助信息
    exit    - 退出程序
    clear   - 清屏
    stream  - on/off 开关流式输出

  \033[36m使用提示:\033[0m
    1. 直接输入问题即可与智能助手对话
    2. 流式输出模式会实时显示回复内容
    3. 支持图片显示和网络图片加载
    4. 按 Ctrl+C 可随时退出程序

  \033[36m示例问题:\033[0m
    - 介绍一下南开大学的历史
    - 南开有哪些知名校友
    - 本科生选课系统在哪里
    - 图书馆开放时间
\033[32m============================================================\033[0m"""
        print(help_text)
        print("\033[33mUser>\033[0m ", end="")
        sys.stdout.flush()

    def get_input(self) -> str:
        """获取用户输入"""
        # 确保提示符已经显示
        sys.stdout.flush()
        try:
            return input()
        except EOFError as e:
            logger.error(f"获取用户输入时出错: {str(e)}")
            return ""

    def _diagnostic_check(self):
        """诊断检查函数，用于调试终端I/O问题"""
        try:
            print("\n========== 终端I/O诊断 ==========")
            
            # 检查标准输入输出
            print(f"stdin isatty: {sys.stdin.isatty()}")
            print(f"stdout isatty: {sys.stdout.isatty()}")
            print(f"stderr isatty: {sys.stderr.isatty()}")
            
            # 检查环境信息
            import os
            print(f"终端类型: {os.environ.get('TERM', '未知')}")
            print(f"操作系统: {os.name}")
            
            # 测试不同方式的输出
            print("\n测试输出方式:")
            print("1. 普通print输出", flush=True)
            sys.stdout.write("2. sys.stdout.write输出\n")
            sys.stdout.flush()
            
            # 测试颜色
            print("\n测试颜色输出:")
            print("\033[31m红色\033[0m \033[32m绿色\033[0m \033[33m黄色\033[0m \033[36m青色\033[0m")
            
            # 测试换行
            print("\n测试换行和刷新:")
            for i in range(3):
                print(f"行 {i+1}", end="")
                sys.stdout.flush()
                time.sleep(0.3)
                print("", flush=True)
            
            # 提示符测试
            print("\n提示符测试:")
            print("\033[36m南开小知>\033[0m 测试消息")
            print("\033[33mUser>\033[0m ", end="")
            sys.stdout.write("模拟用户输入\n")
            sys.stdout.flush()
            
            print("\n=================================")
        except Exception as e:
            print(f"诊断过程发生错误: {str(e)}")
