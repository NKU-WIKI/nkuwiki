from .event import Event, EventAction, EventContext
from .plugin import Plugin
from .plugin_manager import PluginManager


instance = PluginManager()

register = instance.register
