"""
企业微信自建应用通道
"""
import json
import time
import asyncio
import threading
from typing import List
from core.utils.logger import register_logger
from config import Config
from services.channel import Channel
from services.chat_message import ChatMessage
from .http_server import WeWorkTopServer
from .weworktop_message import WeWorkTopMessage
from .weworkapi_model import WeworkApiClient
from core.bridge.bridge import Bridge
from core.utils.voice import Voice

logger = register_logger("services.weworktop")

class WeWorkTopChannel(Channel):
    """企业微信自建应用通道"""
    def __init__(self) -> None:
        """初始化"""
        super().__init__()
        # 配置解析
        config = Config()
        self.corp_id = config.get("services.weworktop.corp_id")
        self.corp_secret = config.get("services.weworktop.corp_secret")
        self.agent_id = config.get("services.weworktop.agent_id")
        self.port = config.get("services.weworktop.port", 5001)
        self.token = config.get("services.weworktop.token", "")
        self.aes_key = config.get("services.weworktop.aes_key", "")
        
        # 会话配置
        self.conversation_max_tokens = config.get("services.weworktop.conversation_max_tokens", 4000)
        self.max_single_msg_tokens = config.get("services.weworktop.max_single_msg_tokens", 1000)
        self.single_chat_prefix = config.get("services.weworktop.single_chat_prefix", [""])
        self.group_chat_prefix = config.get("services.weworktop.group_chat_prefix", ["@小知"])
        self.group_name_white_list = config.get("services.weworktop.group_name_white_list", [])
        self.image_create_prefix = config.get("services.weworktop.image_create_prefix", ["画", "生成图片", "创建图像"])
        self.speech_recognition = config.get("services.weworktop.speech_recognition", False)
        self.single_chat_reply_prefix = config.get("services.weworktop.single_chat_reply_prefix", "")
        
        # 运行时变量
        self.wework_client = None
        self.running = True
        self.bridge = None
        self.voice = Voice()
        self.sessions = {}  # 会话缓存，用于消息去重
        self.thread_pool = []  # 线程池

    def startup(self):
        """启动通道服务"""
        # 初始化Bridge
        self.bridge = Bridge()
        
        # 初始化企业微信API客户端
        self.wework_client = WeworkApiClient(self.corp_id, self.corp_secret, self.agent_id)
        
        # 启动HTTP服务器接收企业微信事件
        logger.info("正在启动企业微信自建应用服务器...")
        self.server = WeWorkTopServer(self.port, self.token, self.aes_key, self)
        self.server_thread = threading.Thread(target=self.server.run)
        self.server_thread.daemon = True
        self.server_thread.start()
        self.thread_pool.append(self.server_thread)
        
        # 启动消息处理线程
        logger.info("启动企业微信自建应用消息处理线程...")
        self.process_thread = threading.Thread(target=self._process_msg_loop)
        self.process_thread.daemon = True
        self.process_thread.start()
        self.thread_pool.append(self.process_thread)
        
        # 定期刷新token
        self.token_thread = threading.Thread(target=self._refresh_token_loop)
        self.token_thread.daemon = True
        self.token_thread.start()
        self.thread_pool.append(self.token_thread)
        
        logger.info("企业微信自建应用通道启动完成")
        
        # 阻塞主线程
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.running = False
            logger.info("正在关闭企业微信自建应用通道...")
            for thread in self.thread_pool:
                if thread.is_alive():
                    thread.join(timeout=5)
            logger.info("企业微信自建应用通道已关闭")

    def _refresh_token_loop(self):
        """定期刷新token的线程"""
        while self.running:
            try:
                self.wework_client.refresh_token()
                logger.debug("企业微信token刷新成功")
                # 每30分钟刷新一次
                time.sleep(30 * 60)
            except Exception as e:
                logger.error(f"企业微信token刷新失败: {str(e)}")
                time.sleep(60)  # 出错后等待1分钟再试

    def _process_msg_loop(self):
        """消息处理主循环"""
        while self.running:
            try:
                time.sleep(0.1)  # 避免CPU占用过高
            except Exception as e:
                logger.error(f"企业微信消息处理线程异常: {str(e)}")
    
    async def handle_message(self, msg_data):
        """处理企业微信消息"""
        try:
            # 消息去重
            if msg_data.get("MsgId") in self.sessions:
                logger.debug(f"忽略重复消息: {msg_data.get('MsgId')}")
                return None
            
            self.sessions[msg_data.get("MsgId")] = True
            # 限制会话缓存大小
            if len(self.sessions) > 1000:
                # 只保留最近的100条消息ID
                self.sessions = {k: self.sessions[k] for k in list(self.sessions.keys())[-100:]}
            
            logger.debug(f"收到企业微信消息: {json.dumps(msg_data, ensure_ascii=False)}")
            
            # 转换为通用消息格式
            msg_type = msg_data.get("MsgType", "text")
            content = msg_data.get("Content", "")
            user_id = msg_data.get("FromUserName", "")
            create_time = msg_data.get("CreateTime", int(time.time()))
            chat_id = msg_data.get("ChatId", "")  # 群聊ID，单聊为空
            
            # 判断是否为群聊
            is_group = True if chat_id else False
            room_id = chat_id if is_group else user_id
            context = {}
            
            # 处理不同类型的消息
            if msg_type == "text":
                # 文本消息处理
                chat_msg = WeWorkTopMessage(content)
                chat_msg.from_user_id = user_id
                chat_msg.from_user_nickname = await self._get_user_name(user_id)
                chat_msg.create_time = create_time
                chat_msg.is_group = is_group
                chat_msg.room_id = room_id
                chat_msg.msg_id = msg_data.get("MsgId")
                chat_msg.msg_type = "text"
                
                # 检查前缀，判断是否需要响应
                if is_group:
                    # 群聊需要检查前缀或@机器人
                    should_reply = False
                    for prefix in self.group_chat_prefix:
                        if prefix and content.startswith(prefix):
                            # 去除前缀
                            chat_msg.content = content[len(prefix):].strip()
                            should_reply = True
                            break
                    
                    # 检查是否@机器人 (TODO: 企业微信自建应用无法获取@信息，未来可能支持)
                    if not should_reply:
                        return None
                else:
                    # 私聊检查前缀
                    should_reply = False
                    for prefix in self.single_chat_prefix:
                        if not prefix or content.startswith(prefix):
                            if prefix:
                                chat_msg.content = content[len(prefix):].strip()
                            should_reply = True
                            break
                    
                    if not should_reply:
                        return None
                
                await self._handle_text_message(chat_msg)
                
            elif msg_type == "voice":
                # 语音消息处理
                if not self.speech_recognition:
                    return None
                
                # TODO: 实现语音识别
                logger.debug("企业微信自建应用语音识别功能尚未实现")
                
            elif msg_type == "image":
                # 图片消息处理
                logger.debug("收到图片消息，暂不处理")
                
            else:
                logger.debug(f"暂不支持的消息类型: {msg_type}")
                
        except Exception as e:
            logger.error(f"处理企业微信消息异常: {str(e)}")
    
    async def _get_user_name(self, user_id):
        """获取用户名称"""
        try:
            user_info = self.wework_client.get_user_info(user_id)
            if user_info and "name" in user_info:
                return user_info["name"]
        except Exception as e:
            logger.error(f"获取用户名称失败: {str(e)}")
        return user_id
    
    async def _handle_text_message(self, chat_msg: ChatMessage):
        """处理文本消息"""
        try:
            if chat_msg.content.strip() == "":
                return
            
            # 图片生成指令判断
            for prefix in self.image_create_prefix:
                if chat_msg.content.startswith(prefix):
                    await self._create_image(chat_msg)
                    return
            
            # 创建响应消息
            reply_msg = WeWorkTopMessage("")
            reply_msg.from_user_id = "bot"
            reply_msg.from_user_nickname = "AI助手"
            reply_msg.to_user_id = chat_msg.from_user_id
            reply_msg.room_id = chat_msg.room_id
            reply_msg.is_group = chat_msg.is_group
            reply_msg.msg_type = "text"
            
            if chat_msg.is_group and self.single_chat_reply_prefix:
                reply_msg.content = f"{self.single_chat_reply_prefix}"
            
            # 使用Bridge处理消息
            self.bridge.on_handle_context(chat_msg)
            
            # 创建响应任务
            async def send_reply():
                try:
                    # 等待桥接层处理完成
                    response_content = self.bridge.on_get_context_reply(chat_msg)
                    if response_content:
                        reply_msg.content += response_content
                        await self.send(reply_msg)
                except Exception as e:
                    logger.error(f"发送回复消息异常: {str(e)}")
            
            # 异步发送响应
            asyncio.create_task(send_reply())
            
        except Exception as e:
            logger.error(f"处理文本消息异常: {str(e)}")
    
    async def _create_image(self, chat_msg: ChatMessage):
        """处理图片生成请求"""
        try:
            # TODO: 实现图片生成功能
            reply_msg = WeWorkTopMessage("图片生成功能尚未实现")
            reply_msg.from_user_id = "bot"
            reply_msg.from_user_nickname = "AI助手"
            reply_msg.to_user_id = chat_msg.from_user_id
            reply_msg.room_id = chat_msg.room_id
            reply_msg.is_group = chat_msg.is_group
            reply_msg.msg_type = "text"
            
            await self.send(reply_msg)
        except Exception as e:
            logger.error(f"处理图片生成请求异常: {str(e)}")
    
    async def send(self, msg: WeWorkTopMessage):
        """发送消息"""
        try:
            content = msg.content
            # 如果内容过长，分段发送
            if len(content) > self.max_single_msg_tokens:
                chunks = self._split_text_by_length(content, self.max_single_msg_tokens)
                for chunk in chunks:
                    await self._send_text(msg.to_user_id, chunk, msg.room_id, msg.is_group)
            else:
                await self._send_text(msg.to_user_id, content, msg.room_id, msg.is_group)
        except Exception as e:
            logger.error(f"发送消息异常: {str(e)}")
    
    async def _send_text(self, user_id, content, room_id, is_group):
        """发送文本消息"""
        try:
            if not content.strip():
                return
                
            if is_group:
                # 发送群聊消息
                self.wework_client.send_group_text(room_id, content)
            else:
                # 发送私聊消息
                self.wework_client.send_text(user_id, content)
            logger.debug(f"企业微信消息发送成功: {content[:30]}..." if len(content) > 30 else content)
        except Exception as e:
            logger.error(f"发送文本消息失败: {str(e)}")
    
    def _split_text_by_length(self, text, max_length):
        """按长度分割文本"""
        chunks = []
        while text:
            if len(text) <= max_length:
                chunks.append(text)
                break
            # 查找合适的分割点
            split_point = max_length
            while split_point > 0 and not (text[split_point] in ".,!?;，。！？；\n"):
                split_point -= 1
            if split_point == 0:
                # 没找到合适的分割点，强制分割
                split_point = max_length
            chunks.append(text[:split_point+1])
            text = text[split_point+1:]
        return chunks 