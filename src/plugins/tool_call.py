import asyncio
import importlib
import sys
from pathlib import Path
from src.common.models.tool_record import ToolRecord
from src.plugins.plugin_manager import get_plugin_config


async def call_plugin_function(record: ToolRecord):
    """
    动态调用插件函数（直接导入插件目录包，调用函数）
    """
    mcp_type = record.mcp_type
    func_name = record.tool_name

    plugin_config = get_plugin_config(mcp_type)
    if not plugin_config:
        raise ValueError(f"未找到插件配置：{mcp_type}")

    func_config = plugin_config.get("functions", {}).get(func_name, {})
    if not func_config:
        raise ValueError(f"插件{mcp_type}无函数配置：{func_name}")

    current_script_dir = Path(__file__).parent.resolve()
    plugin_dir = (current_script_dir / plugin_config["dir_path"]).resolve()
    print(f"DEBUG: 定位到的插件绝对路径: {plugin_dir}")

    plugin_collection_dir = plugin_dir.parent
    if str(plugin_collection_dir) not in sys.path:
        sys.path.append(str(plugin_collection_dir))

    # 验证插件包（必须有__init__.py）
    init_file = plugin_dir / "__init__.py"
    if not plugin_dir.is_dir():
        raise ValueError(f"插件目录不存在：{plugin_dir}")
    if not init_file.exists():
        raise ValueError(f"插件目录缺少__init__.py：{init_file}")

    # 直接导入插件包
    try:
        plugin_module = importlib.import_module(mcp_type)  # mcp_type=插件目录名=包名
    except ImportError as e:
        raise ValueError(f"导入插件包失败 {mcp_type}：{str(e)}")

    # 执行函数
    if not hasattr(plugin_module, func_name):
        raise ValueError(f"插件包{mcp_type}中无函数：{func_name}")

    target_func = getattr(plugin_module, func_name)
    if asyncio.iscoroutinefunction(target_func):
        return await target_func(**record.arguments)
    else:
        return target_func(**record.arguments)