from typing import List

from src.common.models import ToolRecord

_executing_tool_list: List[ToolRecord] = []


def add_executing_tool(tool: ToolRecord) -> None:
    """添加到处理中列表"""
    if tool not in _executing_tool_list:
        tool.state = "executing"
        _executing_tool_list.append(tool)

def remove_executing_tool(tool: ToolRecord) -> None:
    """从处理中列表移除"""
    if tool in _executing_tool_list:
        tool.state = "completed"
        _executing_tool_list.remove(tool)

def get_handling_tool_count() -> int:
    """获取处理中任务数"""
    return len(_executing_tool_list)
