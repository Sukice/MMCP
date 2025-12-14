import json
from src.common.models import Task
from src.config.settings import TASK_HISTORY_FILE


def write_task_history(task: Task) -> None:
    """写入任务历史到文件"""
    task_dict = task.to_dict()
    try:
        # 追加写入
        with open(TASK_HISTORY_FILE, "a+", encoding="utf-8") as f:
            f.write(json.dumps(task_dict, ensure_ascii=False) + "\n")
    except Exception as e:
        print(f"写入任务历史失败：{e}")
