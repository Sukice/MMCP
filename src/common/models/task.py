from typing import List, Dict, Optional


class Task:
    """
    核心职责：存储任务的全生命周期信息，包含初始化、属性访问、状态校验等基础逻辑
    """
    # 类常量：限定合法的任务状态，避免非法值
    VALID_STATES = ("waiting", "handling", "completed")

    def __init__(
        self,
        task_name: str,
        model: str,
        task_content: str,
        available_tools: List,
        task_id: Optional[str] = None,
        create_time: Optional[str] = None,
        session_history: Optional[List[Dict]] = None,
        state: str = "waiting",
        finish_time: Optional[str] = None
    ):
        """
        初始化任务实例
        :param task_name: 任务名（必填）
        :param model: 任务派发的模型名（必填）
        :param task_content: 任务内容（必填）
        :param available_tools: 工具权限列表（必填）
        :param task_id: 任务ID（可选，外部生成后传入）
        :param create_time: 创建时间（可选，默认None，由MCP服务器初始化）
        :param session_history: 会话历史（可选，默认空列表）
        :param state: 任务状态（可选，默认waiting，仅支持VALID_STATES）
        :param finish_time: 完成时间（可选，任务完成后赋值）
        """
        # 必选属性（无默认值，强制校验非空）
        if not task_name.strip():
            raise ValueError("任务名（task_name）不能为空")
        if not model.strip():
            raise ValueError("模型名（model）不能为空")
        if not task_content.strip():
            raise ValueError("任务内容（task_content）不能为空")
        if not isinstance(available_tools, list):
            raise TypeError("可用工具（available_tools）必须是列表类型")

        self.task_name = task_name.strip()
        self.model = model.strip()
        self.task_content = task_content.strip()
        self.available_tools = available_tools

        # 可选属性（带默认值/类型校验）
        self.task_id = task_id
        self.create_time = create_time  # 由MCP服务器调用init_task时赋值
        self.finish_time = finish_time

        # 会话历史：处理可变默认值问题（避免多个实例共享同一列表）
        self.session_history = session_history if isinstance(session_history, list) else []

        # 任务状态：校验合法性
        self._state = None
        self.state = state  # 通过属性方法赋值，触发合法性校验

    @property
    def state(self) -> str:
        """任务状态属性（只读，通过setter修改）"""
        return self._state

    @state.setter
    def state(self, value: str) -> None:
        """任务状态赋值器，强制校验合法性"""
        if value not in self.VALID_STATES:
            raise ValueError(f"任务状态（state）必须是 {self.VALID_STATES} 中的一种，当前值：{value}")
        self._state = value

    def add_session_history(self, record: Dict) -> None:
        """
        新增会话历史记录（封装逻辑，避免直接操作列表）
        :param record: 会话记录字典（需包含role和content字段）
        """
        if not isinstance(record, dict) or "role" not in record or "content" not in record:
            raise ValueError("会话记录必须是包含role和content字段的字典")
        # 可扩展：会话历史最大条数限制（从配置读取）
        # from config.settings import SESSION_MAX_SIZE
        # if len(self.session_history) >= SESSION_MAX_SIZE:
        #     self.session_history.pop(0)  # 移除最早的记录
        self.session_history.append(record)

    def get_tool_info(self) -> List[Dict]:
        from src.plugins.plugin_manager import get_plugin_tool_info
        return get_plugin_tool_info(self.available_tools)

    def to_dict(self) -> Dict:
        """
        转换为字典（用于序列化/持久化）
        将datetime类型转换为字符串，方便存储和传输
        """

        return {
            "task_id": self.task_id,
            "task_name": self.task_name,
            "model": self.model,
            "create_time": self.create_time,
            "task_content": self.task_content,
            "available_tools": self.available_tools,
            "session_history": self.session_history,
            "state": self.state,
            "finish_time": self.finish_time
        }

    def __repr__(self) -> str:
        """
        自定义实例打印格式（方便调试）
        示例输出：Task(task_id=task_123456, name=测试任务, model=gpt-4, state=waiting)
        """
        return (
            f"Task(task_id={self.task_id!r}, name={self.task_name!r}, "
            f"model={self.model!r}, state={self.state!r})"
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Task):
            return False
        return self.task_id == other.task_id and self.task_id is not None