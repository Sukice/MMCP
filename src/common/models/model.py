from typing import Optional


class Model:
    VALID_STATES = ("idle", "think", "wait")

    def __init__(
        self,
        name: str,
        state: str = "idle",
        task_name: Optional[str] = None,
        task_id: Optional[str] = None
    ):
        if not name.strip():
            raise ValueError("模型名（name）不能为空")
        self.name = name.strip()

        self._state = None
        self.state = state

        self.task_name = task_name
        self.task_id = task_id

    @property
    def state(self) -> str:
        return self._state

    @state.setter
    def state(self, value: str) -> None:
        if value not in self.VALID_STATES:
            raise ValueError(f"模型状态必须是 {self.VALID_STATES} 中的一种，当前值：{value}")
        self._state = value

    def bind_task(self, task_id: str, task_name: str) -> None:
        """绑定当前执行的任务"""
        self.task_id = task_id
        self.task_name = task_name

    def unbind_task(self) -> None:
        """解绑任务"""
        self.task_id = None
        self.task_name = None

    def __repr__(self) -> str:
        return (
            f"Model(name={self.name!r}, state={self.state!r}, "
            f"task_id={self.task_id!r})"
        )