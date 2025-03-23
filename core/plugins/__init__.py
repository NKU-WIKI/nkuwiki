from .event import *
from .plugin import *
from .plugin_manager import PluginManager


instance = PluginManager()

register = instance.register
