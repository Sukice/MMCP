import os
import yaml
from typing import Dict, Optional, List

GLOBAL_TOOL_YAML = os.path.join(os.path.dirname(__file__), "tool.yaml")
PLUGIN_COLLECTION_DIR = os.path.join(os.path.dirname(__file__), "plugin_collection")

CONFIG_DATA = {}

def load_global_tool_yaml() -> Dict:
    """加载全局tool.yaml配置（返回扁平字典，顶层为mcp_type）"""
    try:
        with open(GLOBAL_TOOL_YAML, "r", encoding="utf-8") as f:
            # 安全加载YAML，避免恶意代码执行
            global CONFIG_DATA
            CONFIG_DATA = yaml.safe_load(f) or {}
        # 校验加载结果是否为字典
        if not isinstance(CONFIG_DATA, dict):
            raise TypeError(f"tool.yaml格式错误，需为字典结构（当前类型：{type(CONFIG_DATA)}）")
        return CONFIG_DATA
    except yaml.YAMLError as e:
        raise ValueError(f"解析tool.yaml失败：{str(e)}")
    except Exception as e:
        raise RuntimeError(f"加载tool.yaml异常：{str(e)}")

def get_config_data():
    return CONFIG_DATA

def init_config_data():
    load_global_tool_yaml()

def get_plugin_config(mcp_type: str) -> Optional[Dict]:
    """
    根据mcp_type读取插件完整配置
    :param mcp_type: 插件标识（如 base_tools、math_tool）
    :return: 插件完整配置字典（None表示未找到）
    :raises: 仅在配置文件异常时抛出，未找到插件返回None（非异常）
    """
    if not isinstance(mcp_type, str) or not mcp_type.strip():
        raise ValueError("mcp_type必须是非空字符串")
    try:
        global_config = get_config_data()
        plugin_config = global_config.get(mcp_type)

        # 若找到配置，补充校验核心字段（保证配置完整性）
        if plugin_config:
            functions = plugin_config.get("functions", {})
            if not functions:
                raise ValueError(f"插件{mcp_type}未配置任何functions")

            # 遍历每个函数，校验parameters和required
            for func_key, func_config in functions.items():
                # 校验function节点存在
                func_detail = func_config.get("function", {})
                if not func_detail:
                    raise ValueError(f"插件{mcp_type}的函数{func_key}缺失function节点")

                # 校验parameters节点存在且为字典
                params = func_detail.get("parameters")
                if not isinstance(params, dict):
                    raise ValueError(f"插件{mcp_type}的函数{func_key}的parameters必须是字典")

                # 校验required字段（可选：如果有则必须是列表）
                required = params.get("required", [])
                if not isinstance(required, list):
                    raise ValueError(f"插件{mcp_type}的函数{func_key}的required必须是列表")

                # 校验properties（如果有则必须是字典）
                properties = params.get("properties", {})
                if not isinstance(properties, dict):
                    raise ValueError(f"插件{mcp_type}的函数{func_key}的properties必须是字典")

            return plugin_config
        else:
            raise ValueError(f"插件{mcp_type}不存在")
    except Exception as e:
        print(f"加载配置发生错误：{e}")
        return {}


def get_plugin_tool_info(tools: List[str]) -> Optional[List[Dict]]:
    global_config = get_config_data()
    tool_pool = []
    for tool in tools:
        try:
            mcp_type = tool.split('/')[0]
            func_name = tool.split('/')[1]
            # 修正：需要先访问 'functions' 节点
            if mcp_type in global_config and 'functions' in global_config[mcp_type]:
                tool_config = global_config[mcp_type]['functions'].get(func_name)
                if tool_config:
                    tool_pool.append(tool_config)
                else:
                    print(f"Warning: 函数 {func_name} 未在 {mcp_type} 中定义")
            else:
                print(f"Warning: 插件类型 {mcp_type} 不存在或无 functions 配置")
        except Exception as e:
            print(f"Error getting tool info for {tool}: {e}")
            continue
    return tool_pool


def register_plugin(plugin_name: str) -> bool:
    """
    注册插件：将 plugin_collection/{plugin_name}/{plugin_name}.yaml 合并到 tool.yaml
    """
    print(f"正在尝试注册插件: {plugin_name} ...")

    # 1. 检查插件目录和配置文件是否存在
    plugin_dir = os.path.join(PLUGIN_COLLECTION_DIR, plugin_name)
    config_file = os.path.join(plugin_dir, f"{plugin_name}.yaml")

    if not os.path.isdir(plugin_dir):
        print(f"错误：插件目录不存在 -> {plugin_dir}")
        return False

    if not os.path.isfile(config_file):
        print(f"错误：插件配置文件不存在 -> {config_file}")
        return False

    try:
        # 2. 读取插件本身的配置
        with open(config_file, 'r', encoding='utf-8') as f:
            new_plugin_config = yaml.safe_load(f)
            if not new_plugin_config:
                print(f"错误：配置文件 {config_file} 为空")
                return False

        # 兼容性处理：如果yaml里包含顶层key(plugin_name)，则取其value；否则整个作为value
        final_config_content = new_plugin_config
        if isinstance(new_plugin_config, dict) and len(new_plugin_config) == 1 and plugin_name in new_plugin_config:
            final_config_content = new_plugin_config[plugin_name]

        # 3. 读取全局 tool.yaml
        current_global_config = {}
        if os.path.exists(GLOBAL_TOOL_YAML):
            with open(GLOBAL_TOOL_YAML, 'r', encoding='utf-8') as f:
                current_global_config = yaml.safe_load(f) or {}

        # 4. 检查是否已存在
        if plugin_name in current_global_config:
            print(f"提示：插件 '{plugin_name}' 已存在于配置中，跳过注册")
            return True

        # 5. 写入配置
        current_global_config[plugin_name] = final_config_content

        with open(GLOBAL_TOOL_YAML, 'w', encoding='utf-8') as f:
            # allow_unicode=True 保证中文正常显示
            yaml.dump(current_global_config, f, allow_unicode=True, sort_keys=False, indent=2)

        # 刷新内存中的配置
        init_config_data()
        print(f"成功：插件 '{plugin_name}' 已注册。")
        return True

    except Exception as e:
        print(f"注册插件时发生异常：{e}")
        return False


def unregister_plugin(plugin_name: str) -> bool:
    """
    注销插件：从 tool.yaml 中移除指定插件
    """
    print(f"正在尝试注销插件: {plugin_name} ...")

    if not os.path.exists(GLOBAL_TOOL_YAML):
        print("错误：全局配置文件 tool.yaml 不存在")
        return False

    try:
        # 1. 读取全局 tool.yaml
        with open(GLOBAL_TOOL_YAML, 'r', encoding='utf-8') as f:
            current_global_config = yaml.safe_load(f) or {}

        # 2. 检查并删除
        if plugin_name not in current_global_config:
            print(f"提示：插件 '{plugin_name}' 不在配置中，无需注销。")
            return True

        del current_global_config[plugin_name]

        # 3. 回写文件
        with open(GLOBAL_TOOL_YAML, 'w', encoding='utf-8') as f:
            yaml.dump(current_global_config, f, allow_unicode=True, sort_keys=False, indent=2)

        # 刷新内存中的配置
        init_config_data()
        print(f"成功：插件 '{plugin_name}' 已注销。")
        return True

    except Exception as e:
        print(f"注销插件时发生异常：{e}")
        return False