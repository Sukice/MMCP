import json
import os
from src.common.models import Task
from src.config.settings import TASK_HISTORY_FILE

import asyncio
from typing import Dict, Any

_pending_futures: Dict[str, asyncio.Future] = {}

def init_waiter(task_name: str):
    """任务开始时调用：创建一个等待凭证"""
    loop = asyncio.get_running_loop()
    _pending_futures[task_name] = loop.create_future()

def add_model_task_result(task_name: str, content: Any) -> None:
    """任务完成时调用：填入结果"""
    if task_name in _pending_futures:
        future = _pending_futures[task_name]
        if not future.done():
            future.set_result(content)

async def get_model_task_result(task_name: str) -> Any:
    """前端调用：挂起等待结果"""
    # 如果没有初始化过等待凭证，说明逻辑有问题（或者任务还没创建）
    if task_name not in _pending_futures:
         # 可以在这里做一个容错，如果找不到就补一个
         init_waiter(task_name)

    future = _pending_futures[task_name]

    try:
        # await 会让出 CPU，直到 set_result 被调用，无延迟！
        result = await asyncio.wait_for(future, timeout=300)

        return result
    except asyncio.TimeoutError:
        return "调用超时"
    finally:
        _pending_futures.pop(task_name, None)








def write_task_history(task_data: Dict[str, Any]) -> None:
    """
    写入任务历史到文件
    :param task_data: 包含任务关键信息的字典 (task_id, task_name, task_result, etc.)
    """

    task_dict = task_data

    history_list = []
    if not os.path.exists(TASK_HISTORY_FILE):
        with open(TASK_HISTORY_FILE, "w", encoding="utf-8") as f:
            f.write('[]')

    if os.path.exists(TASK_HISTORY_FILE):
        try:
            with open(TASK_HISTORY_FILE, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    history_list = json.loads(content)
                    if not isinstance(history_list, list):
                        history_list = [history_list]
        except Exception as e:
            print(f"读取历史文件失败：{e}")
            return

    history_list.append(task_dict)

    try:
        with open(TASK_HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history_list, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"写入任务历史失败：{e}")