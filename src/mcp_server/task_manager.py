from typing import List, Deque, Optional
from collections import deque
from src.common.models import Task
from src.common.utils import generate_task_id
from src.common.utils import get_current_datetime, datetime_to_str

# 全局任务队列（等待执行）
_task_queue: Deque[Task] = deque()
# 全局处理中任务列表
_handling_task_list: List[Task] = []

def init_task(task: Task) -> None:
    """初始化任务：生成ID、添加创建时间、初始化会话历史、加入队列"""
    task.task_id = generate_task_id()

    task.create_time = datetime_to_str(get_current_datetime())

    task.session_history.append({
        "role": "user",
        "content": task.task_content
    })



    # 标记为waiting并加入队列
    task.state = "waiting"
    _task_queue.append(task)

def get_pending_task() -> Optional[Task]:
    """获取队列首任务（非阻塞）"""
    if _task_queue:
        return _task_queue.popleft()
    return None

def add_handling_task(task: Task) -> None:
    """添加到处理中列表"""
    if task not in _handling_task_list:
        _handling_task_list.append(task)

def remove_handling_task(task: Task) -> None:
    """从处理中列表移除"""
    if task in _handling_task_list:
        _handling_task_list.remove(task)

def get_handling_task_count() -> int:
    """获取处理中任务数"""
    return len(_handling_task_list)


def get_task_queue_size() -> int:
    """获取队列大小"""
    return len(_task_queue)

def requeue_task(task: Task) -> None:
    if task not in _task_queue:
        _task_queue.append(task)