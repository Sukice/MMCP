from typing import List, Deque, Optional
from collections import deque
from src.common.models import Task
from src.common.utils import generate_task_id
from src.common.utils import get_current_datetime, datetime_to_str
from src.common.utils.file_utils import build_file_metadata

# 全局任务队列（等待执行）
_task_queue: Deque[Task] = deque()
# 全局处理中任务列表
_handling_task_list: List[Task] = []


def init_task(task: Task) -> None:
    task.task_id = generate_task_id()
    task.create_time = datetime_to_str(get_current_datetime())

    task.session_history.append({
        "role": "system",
        "content": f"Your name is {task.model}. If you are provided tools, you should use tool until you know the final answer."
    })

    if task.file_path and len(task.file_path) > 0:
        content_list = []

        # 1. 文本提示词
        if task.task_content:
            content_list.append({
                "type": "text",
                "text": task.task_content
            })

        # 2. 处理附件
        for file_path in task.file_path:
            try:
                # build_file_metadata 现在返回 List[Dict]
                # 比如 PDF 可能返回 [{"type": "image_url"...}, {"type": "image_url"...}]
                media_payloads = build_file_metadata(file_path)

                # 使用 extend 将多个图片对象拍平加入 content_list
                content_list.extend(media_payloads)

            except Exception as e:
                print(f"Warning: 附件处理失败 {file_path}: {e}")
                content_list.append({
                    "type": "text",
                    "text": f"\n[System Error: {str(e)}]"
                })

        task.session_history.append({
            "role": "user",
            "content": content_list
        })

    else:
        # 纯文本模式
        task.session_history.append({
            "role": "user",
            "content": task.task_content
        })

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