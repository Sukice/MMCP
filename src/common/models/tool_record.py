
from typing import Optional


class ToolRecord:
    VALID_STATES = ("executing", "completed")

    def __init__(
        self,
        task_id: str,
        task_name: str,
        mcp_type: str,
        tool_name: str,
        model: str,
        arguments: str,
        call_id: Optional[str] = None,
        call_time: Optional[str] = None,
        finish_time: Optional[str] = None,
        state: str = "executing"
    ):
        # 必选字段校验
        if not task_id.strip():
            raise ValueError("任务ID（task_id）不能为空")
        if not task_name.strip():
            raise ValueError("任务名（task_name）不能为空")
        if not mcp_type.strip():
            raise ValueError("MCP插件类型（mcp_type）不能为空")
        if not tool_name.strip():
            raise ValueError("工具名（tool_name）不能为空")
        if not model.strip():
            raise ValueError("模型名（model）不能为空")

        self.task_id = task_id.strip()
        self.task_name = task_name.strip()
        self.mcp_type = mcp_type.strip()
        self.tool_name = tool_name.strip()
        self.model = model.strip()
        self.arguments = arguments

        # 可选字段

        self.call_id = call_id
        self.call_time = call_time
        self.finish_time = finish_time

        # 状态校验
        self._state = None
        self.state = state

    @property
    def state(self) -> str:
        return self._state

    @state.setter
    def state(self, value: str) -> None:
        if value not in self.VALID_STATES:
            raise ValueError(f"工具调用状态必须是 {self.VALID_STATES} 中的一种，当前值：{value}")
        self._state = value

    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "task_name": self.task_name,
            "call_id": self.call_id,
            "mcp_type": self.mcp_type,
            "tool_name": self.tool_name,
            "call_time": self.call_time,
            "finish_time": self.finish_time,
            "model": self.model,
            "state": self.state
        }

    def __repr__(self) -> str:
        return (
            f"ToolRecord(call_id={self.call_id!r}, task_id={self.task_id!r}, "
            f"tool_name={self.tool_name!r}, state={self.state!r})"
        )