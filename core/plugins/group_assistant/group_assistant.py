"""
群聊助手插件，适配企业微信群消息处理
"""

# encoding:utf-8
import json
import os

from core.utils.logger import register_logger
logger = register_logger("core.plugins.group_assistant")
from core.utils.plugins import register
from core.bridge.context import ContextType
from core.bridge.reply import Reply, ReplyType
from core.utils.plugins import Plugin, Event, EventContext
from config import Config


@register(
    name="group_assistant",
    desire_priority=20,
    hidden=False,
    desc="企业微信群助手，提供群聊邀请和管理功能",
    version="0.1",
    author="nkuwiki",
)
class GroupAssistant(Plugin):
    def __init__(self):
        super().__init__()
        try:
            # 获取当前文件的目录
            curdir = os.path.dirname(__file__)
            # 配置文件的路径
            config_path = os.path.join(curdir, "config.json")
            channel_type = Config().get("services.channel_type", "terminal")
            logger.debug(f"channel_type :{channel_type}")
            
            # 如果配置文件不存在
            if not os.path.exists(config_path):
                # 输出日志信息，配置文件不存在，将使用模板
                logger.error('[GroupAssistant] 配置文件不存在，无法启动群聊助手插件')
                return
            elif channel_type != "wework":
                logger.debug('[GroupAssistant] 当前使用的非企业微信通道，群聊助手插件将不执行')
                return
            
            # 打开并读取配置文件
            with open(config_path, "r", encoding="utf-8") as f:
                # 加载 JSON 文件
                self.config = json.load(f)
            
            # 设置事件处理函数
            self.handlers[Event.ON_HANDLE_CONTEXT] = self.on_handle_context
            # 输出日志信息，表示插件已初始化
            logger.info("[GroupAssistant] 群聊助手插件初始化成功")
        except Exception as e:  # 捕获所有的异常
            logger.warn("[GroupAssistant] 初始化失败: " + str(e))
            # 抛出异常，结束程序
            raise e

    def on_handle_context(self, e_context: EventContext):
        """处理上下文，匹配关键词"""
        
        # 获取上下文内容
        context = e_context['context']
        # 确认消息类型为文本，并且存在回复渠道
        if context.type != ContextType.TEXT:
            return
        
        # 获取消息内容和来源
        content = context.content
        # 确认是否是群聊消息
        isgroup = e_context['context'].get('isgroup', False)
        
        # 只处理群聊消息
        if not isgroup:
            return
            
        # 检查是否命中关键词
        if self._check_keyword(content):
            # 获取配置的回复内容
            reply_content = self.config.get("reply_content", "欢迎加入本群，请了解群规并友好交流！")
            
            # 回复消息
            reply = Reply()
            reply.type = ReplyType.TEXT
            reply.content = reply_content
            e_context["reply"] = reply
            e_context.action = EventAction.BREAK_PASS
            
    def _check_keyword(self, content):
        """检查关键词是否匹配"""
        keywords = self.config.get("keywords", [])
        for keyword in keywords:
            if keyword in content:
                return True
        return False

    def get_help_text(self, **kwargs):
        """获取帮助文本"""
        help_text = "🔸群聊助手\n"
        help_text += "功能：监控群聊关键词并进行回复\n"
        help_text += "配置：在config.json中设置关键词和回复内容\n"
        return help_text 