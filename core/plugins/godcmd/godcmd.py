# encoding:utf-8

import json  # noqa: F401
import os
import random  # noqa: F401
import string  # noqa: F401
import logging
from typing import Tuple

import core.bridge.bridge
from core.bridge.bridge import Bridge
from core.bridge.context import ContextType
from core.bridge.reply import Reply, ReplyType
from core.utils import const
from core.plugins.plugin_manager import plugins  # 导入全局实例
from core.plugins.plugin import Plugin
from core.plugins.event import Event, EventAction, EventContext
from app import App
from config import Config   

# 定义指令集
COMMANDS = {
    "help": {
        "alias": ["help", "帮助"],
        "desc": "回复此帮助",
    },
    "helpp": {
        "alias": ["help", "帮助"],  # 与help指令共用别名，根据参数数量区分
        "args": ["插件名"],
        "desc": "回复指定插件的详细帮助",
    },
    "auth": {
        "alias": ["auth", "认证"],
        "args": ["口令"],
        "desc": "管理员认证",
    },
    "model": {
        "alias": ["model", "模型"],
        "desc": "查看和设置全局模型",
    },
    "set_openai_api_key": {
        "alias": ["set_openai_api_key"],
        "args": ["api_key"],
        "desc": "设置你的OpenAI私有api_key",
    },
    "reset_openai_api_key": {
        "alias": ["reset_openai_api_key"],
        "desc": "重置为默认的api_key",
    },
    "set_gpt_model": {
        "alias": ["set_gpt_model"],
        "desc": "设置你的私有模型",
    },
    "reset_gpt_model": {
        "alias": ["reset_gpt_model"],
        "desc": "重置你的私有模型",
    },
    "gpt_model": {
        "alias": ["gpt_model"],
        "desc": "查询你使用的模型",
    },
    "id": {
        "alias": ["id", "用户"],
        "desc": "获取用户id",  # wechaty和wechatmp的用户id不会变化，可用于绑定管理员
    },
    "reset": {
        "alias": ["reset", "重置会话"],
        "desc": "重置会话",
    },
}

ADMIN_COMMANDS = {
    "resume": {
        "alias": ["resume", "恢复服务"],
        "desc": "恢复服务",
    },
    "stop": {
        "alias": ["stop", "暂停服务"],
        "desc": "暂停服务",
    },
    "reconf": {
        "alias": ["reconf", "重载配置"],
        "desc": "重载配置(不包含插件配置)",
    },
    "resetall": {
        "alias": ["resetall", "重置所有会话"],
        "desc": "重置所有会话",
    },
    "scanp": {
        "alias": ["scanp", "扫描插件"],
        "desc": "扫描插件目录是否有新插件",
    },
    "plist": {
        "alias": ["plist", "插件"],
        "desc": "打印当前插件列表",
    },
    "setpri": {
        "alias": ["setpri", "设置插件优先级"],
        "args": ["插件名", "优先级"],
        "desc": "设置指定插件的优先级，越大越优先",
    },
    "reloadp": {
        "alias": ["reloadp", "重载插件"],
        "args": ["插件名"],
        "desc": "重载指定插件配置",
    },
    "enablep": {
        "alias": ["enablep", "启用插件"],
        "args": ["插件名"],
        "desc": "启用指定插件",
    },
    "disablep": {
        "alias": ["disablep", "禁用插件"],
        "args": ["插件名"],
        "desc": "禁用指定插件",
    },
    "installp": {
        "alias": ["installp", "安装插件"],
        "args": ["仓库地址或插件名"],
        "desc": "安装指定插件",
    },
    "uninstallp": {
        "alias": ["uninstallp", "卸载插件"],
        "args": ["插件名"],
        "desc": "卸载指定插件",
    },
    "updatep": {
        "alias": ["updatep", "更新插件"],
        "args": ["插件名"],
        "desc": "更新指定插件",
    },
    "debug": {
        "alias": ["debug", "调试模式", "DEBUG"],
        "desc": "开启机器调试日志",
    },
}


# 定义帮助函数
trigger_prefix = Config().get("plugin_trigger_prefix", "&")

def get_help_text(isadmin, isgroup):
    help_text = "通用指令\n"
    for cmd, info in COMMANDS.items():
        if cmd in ["auth"]:  # 仅过滤认证指令
            continue
        if cmd == "id" and Config().get("channel_type", "wx") not in ["wxy", "wechatmp"]:
            continue
        alias = [trigger_prefix + a for a in info["alias"][:1]]
        help_text += f"{','.join(alias)} "
        if "args" in info:
            args = [a for a in info["args"]]
            help_text += f"{' '.join(args)}"
        help_text += f": {info['desc']}\n"

    # 插件指令
    all_plugins = plugins.list_plugins()  # 重命名变量避免冲突
    help_text += "\n可用插件"
    for plugin in all_plugins:
        if all_plugins[plugin].enabled and not all_plugins[plugin].hidden:
            namecn = all_plugins[plugin].namecn
            help_text += "\n%s:" % namecn
            help_text += all_plugins.instances[plugin].get_help_text(verbose=False).strip()

    if ADMIN_COMMANDS and isadmin:
        help_text += "\n\n管理员指令：\n"
        for cmd, info in ADMIN_COMMANDS.items():
            alias = [trigger_prefix + a for a in info["alias"][:1]]
            help_text += f"{','.join(alias)} "
            if "args" in info:
                args = [a for a in info["args"]]
                help_text += f"{' '.join(args)}"
            help_text += f": {info['desc']}\n"
    return help_text


@plugins.register(
    name="Godcmd",
    desire_priority=999,
    hidden=True,
    desc="为你的机器人添加指令集，有用户和管理员两种角色，加载顺序请放在首位，初次运行后插件目录会生成配置文件, 填充管理员密码后即可认证",
    version="1.0",
    author="lanvent",
)
class Godcmd(Plugin):
    def __init__(self):
        super().__init__()

        config_path = os.path.join(os.path.dirname(__file__), "config.json")
        gconf = super().load_config()
        if not gconf:
            if not os.path.exists(config_path):
                gconf = {"password": "", "admin_users": []}
                with open(config_path, "w") as f:
                    json.dump(gconf, f, indent=4)
        if gconf["password"] == "":
            self.temp_password = "".join(random.sample(string.digits, 4))
            App().logger.info("[Godcmd] 因未设置口令，本次的临时口令为%s。" % self.temp_password)
        else:
            self.temp_password = None
        custom_commands = Config().get("clear_memory_commands", [])
        for custom_command in custom_commands:
            if custom_command and custom_command.startswith("#"):
                custom_command = custom_command[1:]
                if custom_command and custom_command not in COMMANDS["reset"]["alias"]:
                    COMMANDS["reset"]["alias"].append(custom_command)

        self.password = gconf["password"]
        self.admin_users = gconf["admin_users"]  # 预存的管理员账号，这些账号不需要认证。itchat的用户名每次都会变，不可用
        Config().global_config["admin_users"] = self.admin_users
        self.isrunning = True  # 机器人是否运行中

        self.handlers[Event.ON_HANDLE_CONTEXT] = self.on_handle_context
        App().logger.info(f"[Godcmd] 事件处理器已注册: {self.handlers}")

    def on_handle_context(self, e_context: EventContext):
        content = e_context["context"].content  # noqa: F841
        App().logger.debug(f"[Godcmd] 收到消息: {content}")  # 新增
        
        if content.startswith(trigger_prefix):
            App().logger.debug(f"[Godcmd] 识别到指令前缀: {trigger_prefix}")
            if len(content) == 1:
                reply = Reply()
                reply.type = ReplyType.ERROR
                reply.content = f"空指令，输入{trigger_prefix}help查看指令列表\n"  # noqa: F841
                e_context["reply"] = reply
                e_context.action = EventAction.BREAK_PASS
                return
            # msg = e_context['context']['msg']
            channel = e_context["channel"]
            user = e_context["context"]["receiver"]
            session_id = e_context["context"]["session_id"]
            isgroup = e_context["context"].get("isgroup", False)
            bottype = Bridge().get_agent_type("chat")
            agent = Bridge().get_agent("chat")
            # 将命令和参数分割
            command_parts = content[1:].strip().split()
            cmd = command_parts[0]
            args = command_parts[1:]
            isadmin = False
            if user in self.admin_users:
                isadmin = True
            ok = False
            result = "string"
            if any(cmd in info["alias"] for info in COMMANDS.values()):
                cmd = next(c for c, info in COMMANDS.items() if cmd in info["alias"])
                if cmd == "auth":
                    ok, result = self.authenticate(user, args, isadmin, isgroup)
                elif cmd == "help":  # 独立处理help指令
                    if len(args) == 0:
                        ok, result = True, get_help_text(isadmin, isgroup)
                    else:
                        ok, result = False, f"参数错误，正确格式：{trigger_prefix}help"
                elif cmd == "helpp":  # 独立处理helpp指令
                    if len(args) == 0:
                        ok, result = False, f"请提供插件名，格式：{trigger_prefix}helpp 插件名"
                    else:
                        # 原有的helpp处理逻辑
                        all_plugins = plugins.list_plugins()
                        query_name = args[0].upper()
                        # search name and namecn
                        for name, plugincls in all_plugins.items():
                            if not plugincls.enabled:
                                continue
                            if query_name == name or query_name == plugincls.namecn:
                                ok, result = True, all_plugins.instances[name].get_help_text(isgroup=isgroup, isadmin=isadmin, verbose=True)
                                break
                        if not ok:
                            result = "插件不存在或未启用"
                elif cmd == "model":
                    if not isadmin and not self.is_admin_in_group(e_context["context"]):
                        ok, result = False, "需要管理员权限执行"
                    elif len(args) == 0:
                        model = Config().get("model") or const.GPT35
                        ok, result = True, "当前模型为: " + str(model)
                    elif len(args) == 1:
                        if args[0] not in const.MODEL_LIST:
                            ok, result = False, "模型名称不存在"
                        else:
                            Config().set("model", self.model_mapping(args[0]))
                            Bridge().reset_bot()
                            model = Config().get("model") or const.GPT35
                            ok, result = True, "模型设置为: " + str(model)
                elif cmd == "id":
                    ok, result = True, user
                elif cmd == "set_openai_api_key":
                    if len(args) == 1:
                        user_data = Config().get_user_data(user)
                        user_data["openai_api_key"] = args[0]
                        ok, result = True, "你的OpenAI私有api_key已设置为" + args[0]
                    else:
                        ok, result = False, "请提供一个api_key"
                elif cmd == "reset_openai_api_key":
                    try:
                        user_data = Config().get_user_data(user)
                        user_data.pop("openai_api_key")
                        ok, result = True, "你的OpenAI私有api_key已清除"
                    except Exception as e:
                        ok, result = False, "你没有设置私有api_key"
                elif cmd == "set_gpt_model":
                    if len(args) == 1:
                        user_data = Config().get_user_data(user)
                        user_data["gpt_model"] = args[0]
                        ok, result = True, "你的GPT模型已设置为" + args[0]
                    else:
                        ok, result = False, "请提供一个GPT模型"
                elif cmd == "gpt_model":
                    user_data = Config().get_user_data(user)
                    model = Config().get("model")
                    if "gpt_model" in user_data:
                        model = user_data["gpt_model"]
                    ok, result = True, "你的GPT模型为" + str(model)
                elif cmd == "reset_gpt_model":
                    try:
                        user_data = Config().get_user_data(user)
                        user_data.pop("gpt_model")
                        ok, result = True, "你的GPT模型已重置"
                    except Exception as e:
                        ok, result = False, "你没有设置私有GPT模型"
                elif cmd == "reset":
                    if bottype in [const.OPEN_AI, const.CHATGPT, const.CHATGPTONAZURE, const.LINKAI, const.BAIDU, const.XUNFEI, const.QWEN, const.GEMINI, const.ZHIPU_AI, const.CLAUDEAPI]:
                        agent.sessions.clear_session(session_id)
                        if Bridge().chat_bots.get(bottype):
                            Bridge().chat_bots.get(bottype).sessions.clear_session(session_id)
                        channel.cancel_session(session_id)
                        ok, result = True, "会话已重置"
                    else:
                        ok, result = False, "当前对话机器人不支持重置会话"
                App().logger.debug("[Godcmd] command: %s by %s" % (cmd, user))
            elif any(cmd in info["alias"] for info in ADMIN_COMMANDS.values()):
                if isadmin:
                    if isgroup:
                        ok, result = False, "群聊不可执行管理员指令"
                    else:
                        cmd = next(c for c, info in ADMIN_COMMANDS.items() if cmd in info["alias"])
                        if cmd == "stop":
                            self.isrunning = False
                            ok, result = True, "服务已暂停"
                        elif cmd == "resume":
                            self.isrunning = True
                            ok, result = True, "服务已恢复"
                        elif cmd == "reconf":
                            config = Config()
                            ok, result = True, "配置已重载"
                        elif cmd == "resetall":
                            if bottype in [const.OPEN_AI, const.CHATGPT, const.CHATGPTONAZURE, const.LINKAI,
                                           const.BAIDU, const.XUNFEI, const.QWEN, const.GEMINI, const.ZHIPU_AI, const.MOONSHOT]:
                                channel.cancel_all_session()
                                agent.sessions.clear_all_session()
                                ok, result = True, "重置所有会话成功"
                            else:
                                ok, result = False, "当前对话机器人不支持重置会话"
                        elif cmd == "debug":
                            if App().logger.getEffectiveLevel() == logging.DEBUG:  # 判断当前日志模式是否DEBUG
                                App().logger.setLevel(logging.INFO)
                                ok, result = True, "DEBUG模式已关闭"
                            else:
                                App().logger.setLevel(logging.DEBUG)
                                ok, result = True, "DEBUG模式已开启"
                        elif cmd == "plist":
                            all_plugins = plugins.list_plugins()
                            ok = True
                            result = "插件列表：\n"
                            for plugincls in all_plugins:
                                result += f"{plugincls.name}_v{plugincls.version} {plugincls.priority} - "
                                result += "已启用\n" if plugincls.enabled else "未启用\n"
                        elif cmd == "scanp":
                            new_plugins = all_plugins.scan_plugins()
                            ok, result = True, "插件扫描完成"
                            all_plugins.activate_plugins()
                            if len(new_plugins) > 0:
                                result += "\n发现新插件：\n"
                                result += "\n".join([f"{p.name}_v{p.version}" for p in new_plugins])
                            else:
                                result += ", 未发现新插件"
                        elif cmd == "setpri":
                            if len(args) != 2:
                                ok, result = False, "请提供插件名和优先级"
                            else:
                                ok = all_plugins.set_plugin_priority(args[0], int(args[1]))
                                if ok:
                                    result = "插件" + args[0] + "优先级已设置为" + args[1]
                                else:
                                    result = "插件不存在"
                        elif cmd == "reloadp":
                            if len(args) != 1:
                                ok, result = False, "请提供插件名"
                            else:
                                ok = all_plugins.reload_plugin(args[0])
                                if ok:
                                    result = "插件配置已重载"
                                else:
                                    result = "插件不存在"
                        elif cmd == "enablep":
                            if len(args) != 1:
                                ok, result = False, "请提供插件名"
                            else:
                                ok, result = all_plugins.enable_plugin(args[0])
                        elif cmd == "disablep":
                            if len(args) != 1:
                                ok, result = False, "请提供插件名"
                            else:
                                ok = all_plugins.disable_plugin(args[0])
                                if ok:
                                    result = "插件已禁用"
                                else:
                                    result = "插件不存在"
                        elif cmd == "installp":
                            if len(args) != 1:
                                ok, result = False, "请提供插件名或.git结尾的仓库地址"
                            else:
                                ok, result = all_plugins.install_plugin(args[0])
                        elif cmd == "uninstallp":
                            if len(args) != 1:
                                ok, result = False, "请提供插件名"
                            else:
                                ok, result = all_plugins.uninstall_plugin(args[0])
                        elif cmd == "updatep":
                            if len(args) != 1:
                                ok, result = False, "请提供插件名"
                            else:
                                ok, result = all_plugins.update_plugin(args[0])
                        App().logger.debug("[Godcmd] admin command: %s by %s" % (cmd, user))
                else:
                    ok, result = False, "需要管理员权限才能执行该指令"
            else:
                ok, result = False, f"未知指令：{cmd}\n查看指令列表请输入{trigger_prefix}help \n"

            reply = Reply()
            reply.type = ReplyType.INFO
            reply.content = result  # noqa: F841
            e_context["reply"] = reply

            App().logger.debug(f"[Godcmd] 最终回复内容: {result}")
            e_context.action = EventAction.BREAK_PASS
        elif not self.isrunning:
            e_context.action = EventAction.BREAK_PASS

    def authenticate(self, userid, args, isadmin, isgroup) -> Tuple[bool, str]:
        if isgroup:
            return False, "请勿在群聊中认证"

        if isadmin:
            return False, "管理员账号无需认证"

        if len(args) != 1:
            return False, "请提供口令"

        password = args[0]
        if password == self.password:
            self.admin_users.append(userid)
            Config().global_config["admin_users"].append(userid)
            return True, "认证成功"
        elif password == self.temp_password:
            self.admin_users.append(userid)
            Config().global_config["admin_users"].append(userid)
            return True, "认证成功，请尽快设置口令"
        else:
            return False, "认证失败"

    def get_help_text(self, isadmin=False, isgroup=False, **kwargs):
        return get_help_text(isadmin, isgroup)

    def is_admin_in_group(self, context):
        if context["isgroup"]:
            return context.kwargs.get("msg").actual_user_id in Config().global_config["admin_users"]
        return False

    def model_mapping(self, model) -> str:
        if model == "gpt-4-turbo":
            return const.GPT4_TURBO_PREVIEW
        return model

    def reload(self):
        gconf = Config().pconf(self.name)
        if gconf:
            if gconf.get("password"):
                self.password = gconf["password"]
            if gconf.get("admin_users"):
                self.admin_users = gconf["admin_users"]
