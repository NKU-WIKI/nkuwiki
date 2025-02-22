# encoding:utf-8

import importlib
import importlib.util
import json
import os
import sys
from collections import defaultdict

from core.utils.common.singleton import singleton
from core.utils.common.sorted_dict import SortedDict
from config import Config
from core.utils.plugins.plugin import Plugin
from core.utils.plugins.event import EventContext, EventAction, Event
from loguru import logger   
@singleton
class PluginManager:
    def __init__(self):
        self.plugins = []
        self.listening_plugins = defaultdict(list)
        self.instances = {}
        self.pconf = {}
        self.current_plugin_path = None
        self.loaded = {}
        self.logger = logger
        self.logger.info("PluginManager initialized with {} plugins".format(len(self.plugins)))

    def register(self, name: str, desire_priority: int = 0, **kwargs):
        def wrapper(plugincls):
            plugincls.name = name
            plugincls.priority = desire_priority
            plugincls.desc = kwargs.get("desc")
            plugincls.author = kwargs.get("author")
            plugincls.path = self.current_plugin_path
            plugincls.version = kwargs.get("version") if kwargs.get("version") != None else "1.0"
            plugincls.namecn = kwargs.get("namecn") if kwargs.get("namecn") != None else name
            plugincls.hidden = kwargs.get("hidden") if kwargs.get("hidden") != None else False
            plugincls.enabled = True
            if self.current_plugin_path == None:
                raise Exception("Plugin path not set")
            self.plugins.append(plugincls)
            self.plugins.sort(key=lambda x: x.priority, reverse=True)
            self.logger.info("Plugin %s_v%s registered, path=%s" % (name, plugincls.version, plugincls.path))

            # 注册时自动绑定事件监听
            for event_type, handler in plugincls.handlers.items():
                self.listening_plugins[event_type].append({
                    "handler": handler,
                    "priority": plugincls.priority
                })
                self.logger.debug(f"[PluginManager] {name} registered for {event_type}")

        return wrapper

    def save_config(self):
        with open("./plugins.json", "w", encoding="utf-8") as f:
            json.dump(self.pconf, f, indent=4, ensure_ascii=False)

    def load_config(self):
        self.logger.info("Loading plugins config...")

        modified = False
        if os.path.exists("./plugins.json"):
            with open("./plugins.json", "r", encoding="utf-8") as f:
                pconf = json.load(f)
                pconf["plugins"] = SortedDict(lambda k, v: v["priority"], pconf["plugins"], reverse=True)
        else:
            modified = True
            pconf = {"plugins": SortedDict(lambda k, v: v["priority"], reverse=True)}
        self.pconf = pconf
        if modified:
            self.save_config()
        return pconf

    @staticmethod
    def _load_all_config(self):
        """
        背景: 目前插件配置存放于每个插件目录的config.json下，docker运行时不方便进行映射，故增加统一管理的入口，优先
        加载 plugins/config.json，原插件目录下的config.json 不受影响

        从 plugins/config.json 中加载所有插件的配置并写入 config.py 的全局配置中，供插件中使用
        插件实例中通过 config.pconf(plugin_name) 即可获取该插件的配置
        """
        all_config_path = "./plugins.json"
        try:
            if os.path.exists(all_config_path):
                # read from all plugins config
                with open(all_config_path, "r", encoding="utf-8") as f:
                    all_conf = json.load(f)
                    self.logger.info(f"load all config from plugins/config.json: {all_conf}")

                # write to global config
                Config.write_plugin_config(all_conf)
        except Exception as e:
            self.logger.error(e)

    def scan_plugins(self):
        """扫描插件目录"""
        plugin_dirs = ["plugins"]  # 插件目录
        for plugin_dir in plugin_dirs:
            if not os.path.exists(plugin_dir):
                continue
            self.logger.debug(f"Scanning plugins in {plugin_dir}")
            for name in os.listdir(plugin_dir):
                if name.startswith(".") or name.startswith("_"):
                    continue
                path = os.path.join(plugin_dir, name)
                if os.path.isdir(path):
                    self._load_plugin_from_path(path)

    def _load_plugin_from_path(self, path):
        """从指定路径加载插件"""
        init_path = os.path.join(path, "__init__.py")
        if not os.path.exists(init_path):
            return
        
        # 关键修改：设置当前插件路径
        self.current_plugin_path = path
        try:
            if path not in self.loaded or self.loaded[path] is None:
                name = os.path.basename(path)  # 新增name变量
                spec = importlib.util.spec_from_file_location(name, init_path)
                module = importlib.util.module_from_spec(spec)
                sys.modules[name] = module
                spec.loader.exec_module(module)
                self.loaded[path] = module
                self.logger.info(f"Loaded plugin from {path}")
        except Exception as e:
            self.logger.error(f"加载插件失败 {os.path.basename(path)}: {str(e)}")
            if Config().get("debug"):
                self.logger.exception(e)
        finally:
            # 重置当前插件路径
            self.current_plugin_path = None

    def refresh_order(self):
        for event in self.listening_plugins.keys():
            self.listening_plugins[event].sort(key=lambda name: self.plugins[name].priority, reverse=True)

    def get_plugin(self, name):
        """通过名称获取插件类实例"""
        name = name.upper()
        return next((p for p in self.plugins if p.name.upper() == name), None)

    def activate_plugins(self):
        """激活所有启用插件"""
        failed_plugins = []
        for plugincls in self.plugins:
            # 确保Godcmd插件始终启用
            if plugincls.name.upper() == "GODCMD":
                plugincls.enabled = True
                
            if plugincls.enabled:
                try:
                    if plugincls.name not in self.instances:
                        # 实例化插件并注册事件处理
                        instance = plugincls()
                        self.instances[plugincls.name] = instance
                        self.logger.info(f"插件 {plugincls.name} 已激活")
                except Exception as e:
                    self.logger.error(f"激活插件 {plugincls.name} 失败: {str(e)}")
                    failed_plugins.append(plugincls.name)
        return failed_plugins

    def reload_plugin(self, name: str):
        plugin = self.get_plugin(name)
        if not plugin:
            return False
        name = name.upper()
        Config.remove_plugin_config(name)
        if name in self.instances:
            for event in self.listening_plugins:
                if name in self.listening_plugins[event]:
                    self.listening_plugins[event].remove(name)
            if name in self.instances:
                self.instances[name].handlers.clear()
            del self.instances[name]
            self.activate_plugins()
            return True
        return False

    def load_plugins(self):
        self.load_config()
        self.scan_plugins()
        # 加载全量插件配置
        self._load_all_config()
        pconf = self.pconf
        self.logger.debug("plugins.json config={}".format(pconf))
        for name, plugin in pconf["plugins"].items():
            if name.upper() not in self.plugins:
                self.logger.error("Plugin %s not found, but found in plugins.json" % name)
        self.activate_plugins()

    def emit_event(self, e_context: EventContext, *args, **kwargs):
        """触发事件处理"""
        event_type = e_context.event
        if event_type in self.listening_plugins:
            # 按优先级排序处理
            sorted_plugins = sorted(
                self.listening_plugins[event_type],
                key=lambda x: x["priority"],
                reverse=True
            )
            
            for plugin_info in sorted_plugins:
                plugin_name = plugin_info["handler"].__self__.name  # 获取插件名称
                if self.get_plugin(plugin_name).enabled:
                    try:
                        plugin_info["handler"](e_context, *args, **kwargs)
                        if e_context.is_break():
                            self.logger.debug(f"插件 {plugin_name} 中断了事件处理")
                            break
                    except Exception as e:
                        self.logger.error(f"插件 {plugin_name} 处理事件 {event_type} 时出错: {str(e)}")
        return e_context

    def set_plugin_priority(self, name: str, priority: int):
        name = name.upper()
        if name not in self.plugins:
            return False
        if self.plugins[name].priority == priority:
            return True
        self.plugins[name].priority = priority
        self.plugins._update_heap(name)
        rawname = self.plugins[name].name
        self.pconf["plugins"][rawname]["priority"] = priority
        self.pconf["plugins"]._update_heap(rawname)
        self.save_config()
        self.refresh_order()
        return True

    def enable_plugin(self, name: str):
        name = name.upper()
        if name not in self.plugins:
            return False, "插件不存在"
        if not self.plugins[name].enabled:
            self.plugins[name].enabled = True
            rawname = self.plugins[name].name
            self.pconf["plugins"][rawname]["enabled"] = True
            self.save_config()
            failed_plugins = self.activate_plugins()
            if name in failed_plugins:
                return False, "插件开启失败"
            return True, "插件已开启"
        return True, "插件已开启"

    def disable_plugin(self, name: str):
        name = name.upper()
        if name not in self.plugins:
            return False
        if self.plugins[name].enabled:
            self.plugins[name].enabled = False
            rawname = self.plugins[name].name
            self.pconf["plugins"][rawname]["enabled"] = False
            self.save_config()
            return True
        return True

    def list_plugins(self):
        """获取排序后的插件列表"""
        return sorted(self.plugins, key=lambda x: x.priority, reverse=True)

    def exists(self, name):
        """检查插件是否存在"""
        return any(p.name.upper() == name.upper() for p in self.plugins)

    def install_plugin(self, repo: str):
        try:
            import common.package_manager as pkgmgr

            pkgmgr.check_dulwich()
        except Exception as e:
            self.logger.error("Failed to install plugin, {}".format(e))
            return False, "无法导入dulwich，安装插件失败"
        import re

        from dulwich import porcelain

        self.logger.info("clone git repo: {}".format(repo))

        match = re.match(r"^(https?:\/\/|git@)([^\/:]+)[\/:]([^\/:]+)\/(.+).git$", repo)

        if not match:
            try:
                with open("./plugins/source.json", "r", encoding="utf-8") as f:
                    source = json.load(f)
                if repo in source["repo"]:
                    repo = source["repo"][repo]["url"]
                    match = re.match(r"^(https?:\/\/|git@)([^\/:]+)[\/:]([^\/:]+)\/(.+).git$", repo)
                    if not match:
                        return False, "安装插件失败，source中的仓库地址不合法"
                else:
                    return False, "安装插件失败，仓库地址不合法"
            except Exception as e:
                self.logger.error("Failed to install plugin, {}".format(e))
                return False, "安装插件失败，请检查仓库地址是否正确"
        dirname = os.path.join("./plugins", match.group(4))
        try:
            repo = porcelain.clone(repo, dirname, checkout=True)
            if os.path.exists(os.path.join(dirname, "requirements.txt")):
                self.logger.info("detect requirements.txt，installing...")
            pkgmgr.install_requirements(os.path.join(dirname, "requirements.txt"))
            return True, "安装插件成功，请使用 #scanp 命令扫描插件或重启程序，开启前请检查插件是否需要配置"
        except Exception as e:
            self.logger.error("Failed to install plugin, {}".format(e))
            return False, "安装插件失败，" + str(e)

    def update_plugin(self, name: str):
        try:
            import common.package_manager as pkgmgr

            pkgmgr.check_dulwich()
        except Exception as e:
            self.logger.error("Failed to install plugin, {}".format(e))
            return False, "无法导入dulwich，更新插件失败"
        from dulwich import porcelain

        name = name.upper()
        if name not in self.plugins:
            return False, "插件不存在"
        if name in [
            "HELLO",
            "GODCMD",
            "ROLE",
            "TOOL",
            "BDUNIT",
            "BANWORDS",
            "FINISH",
            "DUNGEON",
        ]:
            return False, "预置插件无法更新，请更新主程序仓库"
        dirname = self.plugins[name].path
        try:
            porcelain.pull(dirname, "origin")
            if os.path.exists(os.path.join(dirname, "requirements.txt")):
                self.logger.info("detect requirements.txt，installing...")
                pkgmgr.install_requirements(os.path.join(dirname, "requirements.txt"))
            return True, "更新插件成功，请重新运行程序"
        except Exception as e:
            self.logger.error("Failed to update plugin, {}".format(e))
            return False, "更新插件失败，" + str(e)

    def uninstall_plugin(self, name: str):
        plugin = self.get_plugin(name)
        if not plugin:
            return False, "插件不存在"
        if name in self.instances:
            self.disable_plugin(name)
        dirname = self.plugins[name].path
        try:
            import shutil

            shutil.rmtree(dirname)
            rawname = self.plugins[name].name
            for event in self.listening_plugins:
                if name in self.listening_plugins[event]:
                    self.listening_plugins[event].remove(name)
            self.plugins = [p for p in self.plugins if p.name.upper() != name.upper()]
            del self.pconf["plugins"][rawname]
            self.loaded[dirname] = None
            self.save_config()
            return True, "卸载插件成功"
        except Exception as e:
            self.logger.error("Failed to uninstall plugin, {}".format(e))
            return False, "卸载插件失败，请手动删除文件夹完成卸载，" + str(e)

    def _load_all_config(self):
        # ...原有代码...
        for plugincls in self.plugins:  # 遍历列表替代字典
            name = plugincls.name
            if name in Config.pconf["plugins"]:
                # ...配置加载逻辑
                pass  # 添加空语句保持语法正确