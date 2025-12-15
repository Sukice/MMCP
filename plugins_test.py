import time

from src.plugins.plugin_manager import unregister_plugin, register_plugin

if __name__ == "__main__":
    unregister_plugin("base_tools")
    time.sleep(5)
    register_plugin("base_tools")
    time.sleep(5)

