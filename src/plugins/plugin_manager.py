import os
import yaml
from typing import Dict, Optional


GLOBAL_TOOL_YAML = os.path.join(os.path.dirname(__file__), "tool.yaml")
PLUGIN_COLLECTION_DIR = os.path.join(os.path.dirname(__file__), "plugin_collection")

def load_global_tool_yaml() -> Dict:
    """加载全局tool.yaml配置（返回扁平字典，顶层为mcp_type）"""
    try:
        with open(GLOBAL_TOOL_YAML, "r", encoding="utf-8") as f:
            # 安全加载YAML，避免恶意代码执行
            config_data = yaml.safe_load(f) or {}
        # 校验加载结果是否为字典
        if not isinstance(config_data, dict):
            raise TypeError(f"tool.yaml格式错误，需为字典结构（当前类型：{type(config_data)}）")
        return config_data
    except yaml.YAMLError as e:
        raise ValueError(f"解析tool.yaml失败：{str(e)}")
    except Exception as e:
        raise RuntimeError(f"加载tool.yaml异常：{str(e)}")

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
        global_config = load_global_tool_yaml()
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